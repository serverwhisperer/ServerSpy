# Database operations
# Note: Data is cleared on startup - temporary storage only

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager
from encryption import encrypt_password, decrypt_password
from config import get_data_path, DB_NAME

DB_PATH = os.path.join(get_data_path(), DB_NAME)


def ensure_db_directory():
    import logging
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
            logging.info(f"Created DB dir: {db_dir}")
        except Exception as e:
            logging.error(f"DB dir create failed: {e}", exc_info=True)
            raise
    
    if not os.access(db_dir, os.W_OK):
        logging.error(f"No write access: {db_dir}")
        raise PermissionError(f"Cannot write to: {db_dir}")


@contextmanager
def get_db_connection():
    import logging
    try:
        ensure_db_directory()
        logging.debug(f"DB connect: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"DB error: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    except sqlite3.OperationalError as e:
        logging.error(f"DB op error: {e}. Path: {DB_PATH}", exc_info=True)
        raise
    except Exception as e:
        logging.error(f"DB connection error: {e}. Path: {DB_PATH}", exc_info=True)
        raise


def init_db():
    ensure_db_directory()
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Projects table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TEXT
            )
        ''')
        
        # Servers table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT UNIQUE NOT NULL,
                username TEXT DEFAULT '',
                password TEXT DEFAULT '',
                os_type TEXT DEFAULT 'Windows',
                hostname TEXT, domain TEXT, brand TEXT, model TEXT, serial TEXT,
                motherboard TEXT, cpu_count INTEGER, cpu_cores TEXT,
                cpu_logical_processors TEXT, cpu_model TEXT, ram_physical TEXT,
                ram_logical INTEGER, disk_info TEXT, network_primary TEXT,
                network_all TEXT, os_version TEXT, service_pack TEXT,
                status TEXT DEFAULT 'Not Scanned', last_scan TEXT,
                created_at TEXT, updated_at TEXT, project_id INTEGER DEFAULT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        ''')
        
        # Migration for project_id
        try:
            cur.execute('ALTER TABLE servers ADD COLUMN project_id INTEGER DEFAULT NULL')
        except sqlite3.OperationalError:
            pass
        
        conn.commit()


def add_server(ip_addr, user, pwd, os_t, proj_id=None):
    with get_db_connection() as conn:
        cur = conn.cursor()
        ts = datetime.now().isoformat()
        
        # Defaults
        if not user:
            user = ''
        if not pwd:
            pwd = ''
        if not os_t:
            os_t = 'Windows'
        
        # Encrypt the password
        enc_pwd = encrypt_password(pwd)
            
        try:
            cur.execute('''
                INSERT INTO servers (ip, username, password, os_type, status, created_at, updated_at, project_id)
                VALUES (?, ?, ?, ?, 'Not Scanned', ?, ?, ?)
            ''', (ip_addr, user, enc_pwd, os_t, ts, ts, proj_id))
            conn.commit()
            return {'success': True, 'id': cur.lastrowid}
        except sqlite3.IntegrityError:
            return {'success': False, 'error': 'Server with this IP already exists'}


def get_all_servers():
    # Get all servers, decrypt passwords
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM servers ORDER BY id')
        rows = cur.fetchall()
        result = []
        for r in rows:
            srv = dict(r)
            if srv.get('password'):
                srv['password'] = decrypt_password(srv['password'])
            result.append(srv)
        return result


def get_server(srv_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM servers WHERE id = ?', (srv_id,))
        r = cur.fetchone()
        if r:
            srv = dict(r)
            if srv.get('password'):
                srv['password'] = decrypt_password(srv['password'])
            return srv
        return None


def get_server_by_ip(ip_addr):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM servers WHERE ip = ?', (ip_addr,))
        r = cur.fetchone()
        if r:
            srv = dict(r)
            if srv.get('password'):
                srv['password'] = decrypt_password(srv['password'])
            return srv
        return None


def delete_server(srv_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM servers WHERE id = ?', (srv_id,))
        conn.commit()
        return cur.rowcount > 0


def update_server_credentials(srv_id, user, pwd):
    with get_db_connection() as conn:
        cur = conn.cursor()
        ts = datetime.now().isoformat()
        enc_pwd = encrypt_password(pwd)
        cur.execute('UPDATE servers SET username = ?, password = ?, updated_at = ? WHERE id = ?',
                   (user, enc_pwd, ts, srv_id))
        conn.commit()
        return cur.rowcount > 0


def clear_all_servers():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM servers')
        conn.commit()
        return cur.rowcount


def clear_servers_by_project(proj_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM servers WHERE project_id = ?', (proj_id,))
        conn.commit()
        return cur.rowcount


def clear_unassigned_servers():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM servers WHERE project_id IS NULL')
        conn.commit()
        return cur.rowcount


def clear_all_data():
    # Wipe everything - fresh start each session
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM servers')
        cur.execute('DELETE FROM projects')
        # Reset counters
        cur.execute("DELETE FROM sqlite_sequence WHERE name='servers'")
        cur.execute("DELETE FROM sqlite_sequence WHERE name='projects'")
        conn.commit()


def update_server_scan_data(srv_id, data):
    # Save scan results to DB
    with get_db_connection() as conn:
        cur = conn.cursor()
        ts = datetime.now().isoformat()
        
        cur.execute('''
            UPDATE servers SET
                hostname = ?, domain = ?, brand = ?, model = ?, serial = ?,
                motherboard = ?, cpu_count = ?, cpu_cores = ?, cpu_logical_processors = ?,
                cpu_model = ?, ram_physical = ?, ram_logical = ?, disk_info = ?,
                network_primary = ?, network_all = ?, os_version = ?, service_pack = ?,
                status = ?, last_scan = ?, updated_at = ?
            WHERE id = ?
        ''', (
            data.get('hostname'), data.get('domain'), data.get('brand'), data.get('model'),
            data.get('serial'), data.get('motherboard'), data.get('cpu_count'),
            data.get('cpu_cores'), data.get('cpu_logical_processors'), data.get('cpu_model'),
            data.get('ram_physical'), data.get('ram_logical'), data.get('disk_info'),
            data.get('network_primary'), data.get('network_all'), data.get('os_version'),
            data.get('service_pack'), data.get('status', 'Online'), ts, ts, srv_id
        ))
        conn.commit()
        return cur.rowcount > 0


def update_server_status(srv_id, stat):
    with get_db_connection() as conn:
        cur = conn.cursor()
        ts = datetime.now().isoformat()
        cur.execute('UPDATE servers SET status = ?, last_scan = ?, updated_at = ? WHERE id = ?',
                   (stat, ts, ts, srv_id))
        conn.commit()
        return cur.rowcount > 0


def bulk_add_servers(srv_list, proj_id=None):
    # Add multiple servers
    res = {'success': 0, 'failed': 0, 'errors': []}
    for srv in srv_list:
        r = add_server(srv.get('ip'), srv.get('username'), srv.get('password'),
                      srv.get('os_type', 'Windows'), proj_id)
        if r['success']:
            res['success'] += 1
        else:
            res['failed'] += 1
            res['errors'].append({'ip': srv.get('ip'), 'error': r['error']})
    return res


def get_server_stats(proj_id=None):
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        if proj_id is not None:
            cur.execute('SELECT COUNT(*) as total FROM servers WHERE project_id = ?', (proj_id,))
            total = cur.fetchone()['total']
            cur.execute("SELECT COUNT(*) as online FROM servers WHERE status = 'Online' AND project_id = ?", (proj_id,))
            online = cur.fetchone()['online']
            cur.execute("SELECT COUNT(*) as offline FROM servers WHERE status = 'Offline' AND project_id = ?", (proj_id,))
            offline = cur.fetchone()['offline']
            cur.execute("SELECT COUNT(*) as not_scanned FROM servers WHERE status = 'Not Scanned' AND project_id = ?", (proj_id,))
            not_scanned = cur.fetchone()['not_scanned']
            cur.execute('SELECT MAX(last_scan) as last_scan FROM servers WHERE project_id = ?', (proj_id,))
            last_scan = cur.fetchone()['last_scan']
        else:
            cur.execute('SELECT COUNT(*) as total FROM servers')
            total = cur.fetchone()['total']
            cur.execute("SELECT COUNT(*) as online FROM servers WHERE status = 'Online'")
            online = cur.fetchone()['online']
            cur.execute("SELECT COUNT(*) as offline FROM servers WHERE status = 'Offline'")
            offline = cur.fetchone()['offline']
            cur.execute("SELECT COUNT(*) as not_scanned FROM servers WHERE status = 'Not Scanned'")
            not_scanned = cur.fetchone()['not_scanned']
            cur.execute('SELECT MAX(last_scan) as last_scan FROM servers')
            last_scan = cur.fetchone()['last_scan']
        
        return {'total': total, 'online': online, 'offline': offline, 'not_scanned': not_scanned, 'last_scan': last_scan}


# Project functions

def create_project(proj_name):
    with get_db_connection() as conn:
        cur = conn.cursor()
        ts = datetime.now().isoformat()
        try:
            cur.execute('INSERT INTO projects (name, created_at) VALUES (?, ?)', (proj_name, ts))
            conn.commit()
            return {'success': True, 'id': cur.lastrowid}
        except sqlite3.IntegrityError:
            return {'success': False, 'error': 'Project with this name already exists'}


def get_all_projects():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM projects ORDER BY name')
        return [dict(r) for r in cur.fetchall()]


def get_project(proj_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM projects WHERE id = ?', (proj_id,))
        r = cur.fetchone()
        return dict(r) if r else None


def get_project_by_name(proj_name):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM projects WHERE name = ?', (proj_name,))
        r = cur.fetchone()
        return dict(r) if r else None


def delete_project(proj_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('UPDATE servers SET project_id = NULL WHERE project_id = ?', (proj_id,))
        cur.execute('DELETE FROM projects WHERE id = ?', (proj_id,))
        conn.commit()
        return cur.rowcount > 0


def rename_project(proj_id, new_name):
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute('UPDATE projects SET name = ? WHERE id = ?', (new_name, proj_id))
            conn.commit()
            return {'success': True}
        except sqlite3.IntegrityError:
            return {'success': False, 'error': 'Project with this name already exists'}


def get_servers_by_project(proj_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        if proj_id is None:
            cur.execute('SELECT * FROM servers WHERE project_id IS NULL ORDER BY id')
        else:
            cur.execute('SELECT * FROM servers WHERE project_id = ? ORDER BY id', (proj_id,))
        rows = cur.fetchall()
        result = []
        for r in rows:
            srv = dict(r)
            if srv.get('password'):
                srv['password'] = decrypt_password(srv['password'])
            result.append(srv)
        return result


def get_unassigned_servers():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM servers WHERE project_id IS NULL ORDER BY id')
        rows = cur.fetchall()
        result = []
        for r in rows:
            srv = dict(r)
            if srv.get('password'):
                srv['password'] = decrypt_password(srv['password'])
            result.append(srv)
        return result


def assign_servers_to_project(srv_ids, proj_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        ts = datetime.now().isoformat()
        for srv_id in srv_ids:
            cur.execute('UPDATE servers SET project_id = ?, updated_at = ? WHERE id = ?',
                       (proj_id, ts, srv_id))
        conn.commit()
        return {'success': True, 'updated': len(srv_ids)}


def get_all_projects_with_stats():
    projs = get_all_projects()
    result = []
    for p in projs:
        stats = get_server_stats(p['id'])
        p['stats'] = stats
        result.append(p)
    return {'projects': result, 'unassigned': get_server_stats_unassigned()}


def get_server_stats_unassigned():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) as total FROM servers WHERE project_id IS NULL')
        total = cur.fetchone()['total']
        cur.execute("SELECT COUNT(*) as online FROM servers WHERE status = 'Online' AND project_id IS NULL")
        online = cur.fetchone()['online']
        cur.execute("SELECT COUNT(*) as offline FROM servers WHERE status = 'Offline' AND project_id IS NULL")
        offline = cur.fetchone()['offline']
        cur.execute("SELECT COUNT(*) as not_scanned FROM servers WHERE status = 'Not Scanned' AND project_id IS NULL")
        not_scanned = cur.fetchone()['not_scanned']
        cur.execute('SELECT MAX(last_scan) as last_scan FROM servers WHERE project_id IS NULL')
        last_scan = cur.fetchone()['last_scan']
        return {'total': total, 'online': online, 'offline': offline, 'not_scanned': not_scanned, 'last_scan': last_scan}


# Initialize database on module import
init_db()

# Clear all data on startup - data is temporary, only for current session
# Data is used temporarily during scanning and Excel export, then cleared on exit
clear_all_data()

