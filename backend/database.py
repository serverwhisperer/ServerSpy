"""
Database module for ServerScout
Handles all SQLite operations for server inventory management
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'inventory.db')


def ensure_db_directory():
    """Ensure the data directory exists"""
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    ensure_db_directory()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the database with required tables"""
    ensure_db_directory()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                os_type TEXT NOT NULL,
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
                updated_at TEXT
            )
        ''')
        conn.commit()


def add_server(ip, username, password, os_type):
    """Add a new server to the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        try:
            cursor.execute('''
                INSERT INTO servers (ip, username, password, os_type, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'Not Scanned', ?, ?)
            ''', (ip, username, password, os_type, now, now))
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


def bulk_add_servers(servers_list):
    """Add multiple servers from a list"""
    results = {'success': 0, 'failed': 0, 'errors': []}
    for server in servers_list:
        result = add_server(
            server.get('ip'),
            server.get('username'),
            server.get('password'),
            server.get('os_type', 'Windows')
        )
        if result['success']:
            results['success'] += 1
        else:
            results['failed'] += 1
            results['errors'].append({'ip': server.get('ip'), 'error': result['error']})
    return results


def get_server_stats():
    """Get statistics about servers"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
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


# Initialize database on module import
init_db()

