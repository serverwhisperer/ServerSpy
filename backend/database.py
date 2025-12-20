"""
Database module for ServerScout
Handles all SQLite operations for server inventory management
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

# Database path - use AppData in packaged mode, project folder in dev mode
import sys

if getattr(sys, 'frozen', False):
    # Running as exe - use AppData
    appdata_path = os.path.join(os.getenv('APPDATA'), 'ServerScout', 'data')
    DB_PATH = os.path.join(appdata_path, 'inventory.db')
else:
    # Running as script - use project data folder
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'inventory.db')


def ensure_db_directory():
    """Ensure the data directory exists"""
    import logging
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
            logging.info(f"Created database directory: {db_dir}")
        except Exception as e:
            logging.error(f"Failed to create database directory {db_dir}: {e}", exc_info=True)
            raise
    
    # Check write permissions
    if not os.access(db_dir, os.W_OK):
        logging.error(f"No write permission for database directory: {db_dir}")
        raise PermissionError(f"Cannot write to database directory: {db_dir}")


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    import logging
    try:
        ensure_db_directory()
        logging.debug(f"Connecting to database: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Database error: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    except sqlite3.OperationalError as e:
        logging.error(f"Database operational error: {e}. DB_PATH: {DB_PATH}", exc_info=True)
        raise
    except Exception as e:
        logging.error(f"Database connection error: {e}. DB_PATH: {DB_PATH}", exc_info=True)
        raise


def init_db():
    """Initialize the database with required tables"""
    ensure_db_directory()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TEXT
            )
        ''')
        
        # Create servers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT UNIQUE NOT NULL,
                username TEXT DEFAULT '',
                password TEXT DEFAULT '',
                os_type TEXT DEFAULT 'Windows',
                hostname TEXT,
                domain TEXT,
                brand TEXT,
                model TEXT,
                serial TEXT,
                motherboard TEXT,
                cpu_count INTEGER,
                cpu_cores TEXT,
                cpu_logical_processors TEXT,
                cpu_model TEXT,
                ram_physical TEXT,
                ram_logical INTEGER,
                disk_info TEXT,
                network_primary TEXT,
                network_all TEXT,
                os_version TEXT,
                service_pack TEXT,
                status TEXT DEFAULT 'Not Scanned',
                last_scan TEXT,
                created_at TEXT,
                updated_at TEXT,
                project_id INTEGER DEFAULT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        ''')
        
        # Migration: Add project_id column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE servers ADD COLUMN project_id INTEGER DEFAULT NULL')
        except sqlite3.OperationalError:
            # Column already exists
            pass
        
        conn.commit()


def add_server(ip, username, password, os_type, project_id=None):
    """Add a new server to the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        # Use placeholder for empty credentials (will use defaults during scan)
        if not username:
            username = ''
        if not password:
            password = ''
        if not os_type:
            os_type = 'Windows'
            
        try:
            cursor.execute('''
                INSERT INTO servers (ip, username, password, os_type, status, created_at, updated_at, project_id)
                VALUES (?, ?, ?, ?, 'Not Scanned', ?, ?, ?)
            ''', (ip, username, password, os_type, now, now, project_id))
            conn.commit()
            return {'success': True, 'id': cursor.lastrowid}
        except sqlite3.IntegrityError:
            return {'success': False, 'error': 'Server with this IP already exists'}


def get_all_servers():
    """Get all servers from the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM servers ORDER BY id')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_server(server_id):
    """Get a single server by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM servers WHERE id = ?', (server_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_server_by_ip(ip):
    """Get a single server by IP"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM servers WHERE ip = ?', (ip,))
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_server(server_id):
    """Delete a server from the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM servers WHERE id = ?', (server_id,))
        conn.commit()
        return cursor.rowcount > 0


def update_server_credentials(server_id, username, password):
    """Update credentials for a specific server"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            UPDATE servers SET username = ?, password = ?, updated_at = ?
            WHERE id = ?
        ''', (username, password, now, server_id))
        conn.commit()
        return cursor.rowcount > 0


def clear_all_servers():
    """Delete all servers from the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM servers')
        conn.commit()
        return cursor.rowcount


def clear_servers_by_project(project_id):
    """Delete all servers in a specific project"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM servers WHERE project_id = ?', (project_id,))
        conn.commit()
        return cursor.rowcount


def clear_unassigned_servers():
    """Delete all servers without a project"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM servers WHERE project_id IS NULL')
        conn.commit()
        return cursor.rowcount


def clear_all_data():
    """Clear all servers and projects - fresh start"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM servers')
        cursor.execute('DELETE FROM projects')
        # Reset auto-increment counters
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='servers'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='projects'")
        conn.commit()


def update_server_scan_data(server_id, scan_data):
    """Update server with scan results"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE servers SET
                hostname = ?,
                domain = ?,
                brand = ?,
                model = ?,
                serial = ?,
                motherboard = ?,
                cpu_count = ?,
                cpu_cores = ?,
                cpu_logical_processors = ?,
                cpu_model = ?,
                ram_physical = ?,
                ram_logical = ?,
                disk_info = ?,
                network_primary = ?,
                network_all = ?,
                os_version = ?,
                service_pack = ?,
                status = ?,
                last_scan = ?,
                updated_at = ?
            WHERE id = ?
        ''', (
            scan_data.get('hostname'),
            scan_data.get('domain'),
            scan_data.get('brand'),
            scan_data.get('model'),
            scan_data.get('serial'),
            scan_data.get('motherboard'),
            scan_data.get('cpu_count'),
            scan_data.get('cpu_cores'),
            scan_data.get('cpu_logical_processors'),
            scan_data.get('cpu_model'),
            scan_data.get('ram_physical'),
            scan_data.get('ram_logical'),
            scan_data.get('disk_info'),
            scan_data.get('network_primary'),
            scan_data.get('network_all'),
            scan_data.get('os_version'),
            scan_data.get('service_pack'),
            scan_data.get('status', 'Online'),
            now,
            now,
            server_id
        ))
        conn.commit()
        return cursor.rowcount > 0


def update_server_status(server_id, status):
    """Update only the status of a server"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            UPDATE servers SET status = ?, last_scan = ?, updated_at = ?
            WHERE id = ?
        ''', (status, now, now, server_id))
        conn.commit()
        return cursor.rowcount > 0


def bulk_add_servers(servers_list, project_id=None):
    """Add multiple servers from a list"""
    results = {'success': 0, 'failed': 0, 'errors': []}
    for server in servers_list:
        result = add_server(
            server.get('ip'),
            server.get('username'),
            server.get('password'),
            server.get('os_type', 'Windows'),
            project_id
        )
        if result['success']:
            results['success'] += 1
        else:
            results['failed'] += 1
            results['errors'].append({'ip': server.get('ip'), 'error': result['error']})
    return results


def get_server_stats(project_id=None):
    """Get statistics about servers, optionally filtered by project"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if project_id is not None:
            cursor.execute('SELECT COUNT(*) as total FROM servers WHERE project_id = ?', (project_id,))
            total = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as online FROM servers WHERE status = 'Online' AND project_id = ?", (project_id,))
            online = cursor.fetchone()['online']
            
            cursor.execute("SELECT COUNT(*) as offline FROM servers WHERE status = 'Offline' AND project_id = ?", (project_id,))
            offline = cursor.fetchone()['offline']
            
            cursor.execute("SELECT COUNT(*) as not_scanned FROM servers WHERE status = 'Not Scanned' AND project_id = ?", (project_id,))
            not_scanned = cursor.fetchone()['not_scanned']
            
            cursor.execute('SELECT MAX(last_scan) as last_scan FROM servers WHERE project_id = ?', (project_id,))
            last_scan = cursor.fetchone()['last_scan']
        else:
            cursor.execute('SELECT COUNT(*) as total FROM servers')
            total = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as online FROM servers WHERE status = 'Online'")
            online = cursor.fetchone()['online']
            
            cursor.execute("SELECT COUNT(*) as offline FROM servers WHERE status = 'Offline'")
            offline = cursor.fetchone()['offline']
            
            cursor.execute("SELECT COUNT(*) as not_scanned FROM servers WHERE status = 'Not Scanned'")
            not_scanned = cursor.fetchone()['not_scanned']
            
            cursor.execute('SELECT MAX(last_scan) as last_scan FROM servers')
            last_scan = cursor.fetchone()['last_scan']
        
        return {
            'total': total,
            'online': online,
            'offline': offline,
            'not_scanned': not_scanned,
            'last_scan': last_scan
        }


# ==================== PROJECT FUNCTIONS ====================

def create_project(name):
    """Create a new project"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        try:
            cursor.execute('''
                INSERT INTO projects (name, created_at)
                VALUES (?, ?)
            ''', (name, now))
            conn.commit()
            return {'success': True, 'id': cursor.lastrowid}
        except sqlite3.IntegrityError:
            return {'success': False, 'error': 'Project with this name already exists'}


def get_all_projects():
    """Get all projects from the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects ORDER BY name')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_project(project_id):
    """Get a single project by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_project_by_name(name):
    """Get a single project by name"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects WHERE name = ?', (name,))
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_project(project_id):
    """Delete a project from the database (servers become unassigned)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # First, unassign servers from this project
        cursor.execute('UPDATE servers SET project_id = NULL WHERE project_id = ?', (project_id,))
        # Then delete the project
        cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        conn.commit()
        return cursor.rowcount > 0


def rename_project(project_id, new_name):
    """Rename a project"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE projects SET name = ? WHERE id = ?', (new_name, project_id))
            conn.commit()
            return {'success': True}
        except sqlite3.IntegrityError:
            return {'success': False, 'error': 'Project with this name already exists'}


def get_servers_by_project(project_id):
    """Get all servers for a specific project"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if project_id is None:
            # Get unassigned servers
            cursor.execute('SELECT * FROM servers WHERE project_id IS NULL ORDER BY id')
        else:
            cursor.execute('SELECT * FROM servers WHERE project_id = ? ORDER BY id', (project_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_unassigned_servers():
    """Get all servers without a project"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM servers WHERE project_id IS NULL ORDER BY id')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def assign_servers_to_project(server_ids, project_id):
    """Assign multiple servers to a project"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        for server_id in server_ids:
            cursor.execute('''
                UPDATE servers SET project_id = ?, updated_at = ?
                WHERE id = ?
            ''', (project_id, now, server_id))
        conn.commit()
        return {'success': True, 'updated': len(server_ids)}


def get_all_projects_with_stats():
    """Get all projects with their server statistics"""
    projects = get_all_projects()
    result = []
    
    for project in projects:
        stats = get_server_stats(project['id'])
        project['stats'] = stats
        result.append(project)
    
    # Also get unassigned servers stats
    unassigned_stats = get_server_stats_unassigned()
    
    return {
        'projects': result,
        'unassigned': unassigned_stats
    }


def get_server_stats_unassigned():
    """Get statistics for servers without a project"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM servers WHERE project_id IS NULL')
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as online FROM servers WHERE status = 'Online' AND project_id IS NULL")
        online = cursor.fetchone()['online']
        
        cursor.execute("SELECT COUNT(*) as offline FROM servers WHERE status = 'Offline' AND project_id IS NULL")
        offline = cursor.fetchone()['offline']
        
        cursor.execute("SELECT COUNT(*) as not_scanned FROM servers WHERE status = 'Not Scanned' AND project_id IS NULL")
        not_scanned = cursor.fetchone()['not_scanned']
        
        cursor.execute('SELECT MAX(last_scan) as last_scan FROM servers WHERE project_id IS NULL')
        last_scan = cursor.fetchone()['last_scan']
        
        return {
            'total': total,
            'online': online,
            'offline': offline,
            'not_scanned': not_scanned,
            'last_scan': last_scan
        }


# Initialize database on module import
init_db()

# Clear all data on startup for fresh session
clear_all_data()

