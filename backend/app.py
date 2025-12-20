# ServerScout - Flask backend

import os
import sys
import csv
import io
import webbrowser
import threading
import logging
from datetime import datetime
import pandas as pd
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    import sys
    
    if getattr(sys, 'frozen', False):
        log_dir = os.path.join(os.getenv('APPDATA'), 'ServerScout', 'logs')
    else:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'serverscout_{datetime.now().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler(sys.stdout)]
    )
    
    return log_file

# Initialize logging
try:
    log_file_path = setup_logging()
    logging.info(f"Logging initialized. Log file: {log_file_path}")
except Exception as e:
    # Fallback if logging fails
    print(f"Warning: Could not setup logging: {e}")

from database import (
    init_db, add_server, get_all_servers, get_server,
    delete_server, update_server_scan_data, update_server_status,
    bulk_add_servers, get_server_stats, clear_all_servers, clear_all_data,
    clear_servers_by_project, clear_unassigned_servers,
    # Project functions
    create_project, get_all_projects, get_project, delete_project,
    rename_project, get_servers_by_project, get_unassigned_servers,
    assign_servers_to_project, get_all_projects_with_stats, get_server_stats_unassigned
)
from scanner import scan_server, scan_all_servers, detect_os_type
from excel_export import generate_excel_report, generate_project_excel_report, generate_all_projects_excel_report
from encryption import encrypt_password, decrypt_password, sanitize_server_data
from validation import validate_ip, validate_username, validate_password, validate_project_name, validate_os_type

# Import configuration
from config import get_frontend_path, SERVER_HOST, SERVER_PORT, USE_HTTPS

# Get frontend path from config
FRONTEND_DIR = get_frontend_path()
logging.info(f"Using frontend directory: {FRONTEND_DIR} (exists: {os.path.exists(FRONTEND_DIR)})")

# Initialize Flask app
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

# Initialize database
try:
    logging.info("Initializing database...")
    init_db()
    logging.info("Database initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize database: {e}", exc_info=True)
    # Don't crash - try to continue
    print(f"ERROR: Database initialization failed: {e}")


# ==================== HEALTH CHECK ====================



# Static files

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)


# Default creds storage (in memory, encrypted)
default_credentials = {
    'windows': {'username': '', 'password_encrypted': ''},
    'linux': {'username': '', 'password_encrypted': ''}
}


@app.route('/api/credentials', methods=['GET'])
def api_get_credentials():
    try:
        return jsonify({
            'success': True,
            'credentials': {
                'windows': {
                    'username': default_credentials['windows']['username'],
                    'has_password': bool(default_credentials['windows']['password_encrypted'])
                },
                'linux': {
                    'username': default_credentials['linux']['username'],
                    'has_password': bool(default_credentials['linux']['password_encrypted'])
                }
            }
        })
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/credentials', methods=['POST'])
def api_save_credentials():
    try:
        data = request.get_json()
        os_t = data.get('os_type', '').lower()
        user = data.get('username', '')
        pwd = data.get('password', '')
        
        if os_t not in ['windows', 'linux']:
            return jsonify({'success': False, 'error': 'Invalid OS type'}), 400
        
        default_credentials[os_t]['username'] = user
        default_credentials[os_t]['password_encrypted'] = encrypt_password(pwd)
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/servers/<int:srv_id>/credentials', methods=['PUT'])
def api_update_server_credentials(srv_id):
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        
        user = data.get('username', '').strip()
        pwd = data.get('password', '')
        
        # Validate username
        is_valid, error_msg = validate_username(user)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        if not user:
            return jsonify({'success': False, 'error': 'Username is required'}), 400
        
        # Validate password
        if pwd is None:
            pwd = ''
        is_valid, error_msg = validate_password(pwd)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        srv = get_server(srv_id)
        if not srv:
            return jsonify({'success': False, 'error': 'Server not found'}), 404
        
        from database import update_server_credentials
        ok = update_server_credentials(srv_id, user, pwd)
        
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Update failed'}), 500
    except Exception as e:
        logging.error(f"Error updating credentials: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


# Server API

@app.route('/api/servers', methods=['GET'])
def api_get_servers():
    try:
        project_id = request.args.get('project_id')
        
        if project_id is not None:
            if project_id == 'unassigned':
                servers = get_unassigned_servers()
            else:
                servers = get_servers_by_project(int(project_id))
        else:
            servers = get_all_servers()
        
        # Remove passwords from response
        servers = sanitize_server_data(servers)
        
        return jsonify({'success': True, 'servers': servers})
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/servers/<int:srv_id>', methods=['GET'])
def api_get_server(srv_id):
    try:
        srv = get_server(srv_id)
        if srv:
            srv = sanitize_server_data(srv)
            return jsonify({'success': True, 'server': srv})
        return jsonify({'success': False, 'error': 'Server not found'}), 404
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/servers', methods=['POST'])
def api_add_server():
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request data'}), 400
        
        # Validate IP
        if not data.get('ip'):
            return jsonify({'success': False, 'error': 'Missing required field: ip'}), 400
        
        ip_addr = data['ip'].strip()
        is_valid, error_msg = validate_ip(ip_addr)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Validate username
        user = data.get('username', '').strip()
        is_valid, error_msg = validate_username(user)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Validate password
        pwd = data.get('password', '')
        is_valid, error_msg = validate_password(pwd)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Use defaults if needed
        if data.get('use_default', False) or (not user and not pwd):
            user = user or 'pending'
            pwd = pwd or 'pending'
        
        # Validate OS type
        os_t = data.get('os_type', '').strip()
        is_valid, error_msg = validate_os_type(os_t)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        auto_detected = False
        if not os_t or data.get('auto_detect', False):
            os_t = detect_os_type(ip_addr)
            auto_detected = True
        
        proj_id = data.get('project_id')
        if proj_id is not None:
            try:
                proj_id = int(proj_id)
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': 'Invalid project_id'}), 400
        
        res = add_server(ip_addr, user, pwd, os_t, proj_id)
        
        if res['success']:
            resp = {'success': True, 'id': res['id']}
            if auto_detected:
                resp['detected'] = True
                resp['os_type'] = os_t
            return jsonify(resp)
        return jsonify({'success': False, 'error': res.get('error', 'Failed to add server')}), 400
        
    except Exception as e:
        logging.error(f"Error adding server: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/servers/<int:srv_id>', methods=['DELETE'])
def api_delete_server(srv_id):
    try:
        if delete_server(srv_id):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Server not found'}), 404
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/servers/clear', methods=['DELETE'])
def api_clear_servers():
    try:
        proj_id = request.args.get('project_id')
        
        if proj_id is None:
            cnt = clear_all_servers()
            msg = 'All servers deleted'
        elif proj_id == 'unassigned':
            cnt = clear_unassigned_servers()
            msg = 'Unassigned servers deleted'
        else:
            cnt = clear_servers_by_project(int(proj_id))
            msg = 'Project servers deleted'
        
        return jsonify({'success': True, 'deleted': cnt, 'message': msg})
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/servers/bulk', methods=['POST'])
def api_bulk_import():
    try:
        proj_id = None
        
        if 'file' not in request.files:
            # Try JSON
            data = request.get_json()
            if data and 'servers' in data:
                proj_id = data.get('project_id')
                res = bulk_add_servers(data['servers'], proj_id)
                return jsonify({'success': True, 'result': res})
            elif data and 'content' in data:
                proj_id = data.get('project_id')
                srv_list = parse_server_list_content(data['content'])
                res = bulk_add_servers(srv_list, proj_id)
                return jsonify({'success': True, 'result': res})
            return jsonify({'success': False, 'error': 'No file or data provided'}), 400
        
        f = request.files['file']
        if f.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        proj_id = request.form.get('project_id')
        if proj_id:
            proj_id = int(proj_id)
        
        content = f.stream.read().decode('utf-8')
        fname = f.filename.lower()
        
        if fname.endswith('.csv'):
            # CSV
            stream = io.StringIO(content)
            reader = csv.DictReader(stream)
            srv_list = [{
                'ip': row.get('ip', '').strip(),
                'username': row.get('username', '').strip(),
                'password': row.get('password', '').strip(),
                'os_type': row.get('os_type', 'Windows').strip()
            } for row in reader]
        else:
            # TXT
            srv_list = parse_server_list_content(content)
        
        res = bulk_add_servers(srv_list, proj_id)
        return jsonify({'success': True, 'result': res})
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


def parse_server_list_content(content, auto_detect=True):
    # Parse IP list from text
    srv_list = []
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = line.split()
        ip_addr = parts[0].strip()
        os_t = None
        
        if len(parts) > 1:
            hint = parts[1].upper()
            if hint in ['L', 'LINUX']:
                os_t = 'Linux'
            elif hint in ['W', 'WINDOWS']:
                os_t = 'Windows'
        
        if os_t is None:
            if auto_detect:
                os_t = detect_os_type(ip_addr)
            else:
                os_t = 'Windows'
        
        srv_list.append({'ip': ip_addr, 'username': '', 'password': '', 'os_type': os_t})
    
    return srv_list


# Project API

@app.route('/api/projects', methods=['GET'])
def api_get_projects():
    try:
        projs = get_all_projects()
        return jsonify({'success': True, 'projects': projs})
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/projects/with-stats', methods=['GET'])
def api_get_projects_with_stats():
    try:
        data = get_all_projects_with_stats()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/projects', methods=['POST'])
def api_create_project():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'success': False, 'error': 'Project name is required'}), 400
        res = create_project(name)
        if res['success']:
            return jsonify({'success': True, 'id': res['id']})
        return jsonify({'success': False, 'error': res['error']}), 400
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/projects/<int:proj_id>', methods=['GET'])
def api_get_project(proj_id):
    try:
        proj = get_project(proj_id)
        if proj:
            return jsonify({'success': True, 'project': proj})
        return jsonify({'success': False, 'error': 'Project not found'}), 404
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/projects/<int:proj_id>', methods=['PUT'])
def api_rename_project(proj_id):
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        
        name = data.get('name', '').strip()
        
        # Validate project name
        is_valid, error_msg = validate_project_name(name)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        if not name:
            return jsonify({'success': False, 'error': 'Project name is required'}), 400
        
        res = rename_project(proj_id, name)
        if res['success']:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': res['error']}), 400
    except Exception as e:
        logging.error(f"Error renaming project: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/projects/<int:proj_id>', methods=['DELETE'])
def api_delete_project(proj_id):
    try:
        if delete_project(proj_id):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Project not found'}), 404
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/projects/<int:proj_id>/servers', methods=['GET'])
def api_get_project_servers(proj_id):
    try:
        srv_list = get_servers_by_project(proj_id)
        stats = get_server_stats(proj_id)
        srv_list = sanitize_server_data(srv_list)
        return jsonify({'success': True, 'servers': srv_list, 'stats': stats})
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/projects/unassigned/servers', methods=['GET'])
def api_get_unassigned_servers():
    try:
        srv_list = get_unassigned_servers()
        stats = get_server_stats_unassigned()
        srv_list = sanitize_server_data(srv_list)
        return jsonify({'success': True, 'servers': srv_list, 'stats': stats})
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/servers/assign', methods=['POST'])
def api_assign_servers():
    try:
        data = request.get_json()
        srv_ids = data.get('server_ids', [])
        proj_id = data.get('project_id')
        if not srv_ids:
            return jsonify({'success': False, 'error': 'No servers specified'}), 400
        res = assign_servers_to_project(srv_ids, proj_id)
        return jsonify({'success': True, 'result': res})
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


# Scanning API

def get_server_with_credentials(srv):
    # Fill in default creds if server doesn't have them
    srv_copy = dict(srv)
    os_t = srv_copy.get('os_type', 'Windows').lower()
    
    if not srv_copy.get('username') or not srv_copy.get('password'):
        key = 'windows' if os_t == 'windows' else 'linux'
        enc_pwd = default_credentials[key].get('password_encrypted', '')
        if default_credentials[key]['username'] and enc_pwd:
            srv_copy['username'] = default_credentials[key]['username']
            srv_copy['password'] = decrypt_password(enc_pwd)
        else:
            return None
    
    return srv_copy

@app.route('/api/scan/<int:srv_id>', methods=['POST'])
def api_scan_server(srv_id):
    try:
        srv = get_server(srv_id)
        if not srv:
            return jsonify({'success': False, 'error': 'Server not found'}), 404
        
        srv_creds = get_server_with_credentials(srv)
        if not srv_creds:
            return jsonify({'success': False, 'error': 'No credentials found. Please set server or default credentials.'}), 400
        
        res = scan_server(srv_creds)
        
        if res.get('status') == 'Online':
            update_server_scan_data(srv_id, res)
        else:
            update_server_status(srv_id, 'Offline')
        
        return jsonify({'success': True, 'result': res})
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/scan-all', methods=['POST'])
def api_scan_all():
    try:
        # Get project filter from query or body
        proj_id = request.args.get('project_id')
        if not proj_id and request.is_json:
            data = request.get_json()
            proj_id = data.get('project_id') if data else None
        
        if proj_id == 'unassigned':
            proj_id = 'unassigned'
        elif proj_id:
            try:
                proj_id = int(proj_id)
            except (ValueError, TypeError):
                proj_id = None
        
        # Get servers to scan
        if proj_id is not None:
            if proj_id == 'unassigned':
                servers = get_unassigned_servers()
            else:
                servers = get_servers_by_project(int(proj_id))
        else:
            servers = get_all_servers()
        
        if not servers:
            return jsonify({'success': True, 'results': [], 'message': 'No servers to scan'})
        
        # Get servers ready for scanning
        to_scan = []
        skipped = 0
        
        for srv in servers:
            srv_with_creds = get_server_with_credentials(srv)
            if srv_with_creds:
                to_scan.append(srv_with_creds)
            else:
                skipped += 1
        
        if not to_scan:
            return jsonify({'success': True, 'results': [], 'message': 'No servers to scan (missing credentials)', 'skipped': skipped})
        
        # Adjust workers based on count
        cnt = len(to_scan)
        if cnt <= 10:
            workers = 10
        elif cnt <= 50:
            workers = 20
        elif cnt <= 100:
            workers = 30
        else:
            workers = 50
        
        results = scan_all_servers(to_scan, max_workers=workers)
        
        # Save results to DB
        for res in results:
            srv_id = res.get('id')
            if srv_id:
                if res.get('status') == 'Online':
                    update_server_scan_data(srv_id, res)
                else:
                    update_server_status(srv_id, 'Offline')
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results),
            'online': sum(1 for r in results if r.get('status') == 'Online'),
            'offline': sum(1 for r in results if r.get('status') == 'Offline'),
            'skipped': skipped
        })
        
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


# Export API

@app.route('/api/export/excel', methods=['GET'])
def api_export_excel():
    try:
        srv_list = get_all_servers()
        stats = get_server_stats()
        filepath = generate_excel_report(srv_list, stats)
        return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath),
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/export/excel/project/<int:proj_id>', methods=['GET'])
def api_export_project_excel(proj_id):
    try:
        proj = get_project(proj_id)
        if not proj:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        srv_list = get_servers_by_project(proj_id)
        stats = get_server_stats(proj_id)
        filepath = generate_project_excel_report(proj['name'], srv_list, stats)
        return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath),
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/export/excel/all-projects', methods=['GET'])
def api_export_all_projects_excel():
    try:
        projs = get_all_projects()
        proj_data = []
        for p in projs:
            srv_list = get_servers_by_project(p['id'])
            stats = get_server_stats(p['id'])
            proj_data.append({'name': p['name'], 'servers': srv_list, 'stats': stats})
        unassigned_srv = get_unassigned_servers()
        unassigned_stats = get_server_stats_unassigned()
        filepath = generate_all_projects_excel_report(proj_data, unassigned_srv, unassigned_stats)
        return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath),
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


# Stats API

# Report comparison

def read_scan_hostnames(file):
    """Read hostnames from scan report Excel file"""
    hostnames = set()
    df_dict = pd.read_excel(file, sheet_name=None)
    for sheet_name, df in df_dict.items():
        if sheet_name.lower() not in ['summary', 'warnings', 'özet', 'uyarılar']:
            if 'Hostname' in df.columns:
                values = df['Hostname'].dropna().astype(str).str.strip().str.upper()
                hostnames.update(h for h in values if h and h != '-' and h != 'NAN' and h != '')
    return hostnames


def read_hpsm_hostnames(file):
    """Read hostnames from HPSM report Excel file"""
    hostnames = set()
    df = pd.read_excel(file)
    
    # Find SERIAL_NO_ column
    serial_col = None
    for col in df.columns:
        col_upper = col.upper().strip()
        if 'SERIAL_NO' in col_upper or col_upper == 'SERIAL_NO_':
            serial_col = col
            break
    
    if serial_col is None:
        for col in df.columns:
            col_upper = col.upper().strip()
            if 'HOSTNAME' in col_upper or col_upper == 'HOST' or 'SERVER' in col_upper:
                serial_col = col
                break
    
    if serial_col:
        values = df[serial_col].dropna().astype(str).str.strip().str.upper()
        hostnames.update(h for h in values if h and h != '-' and h != 'NAN' and h != '')
    
    return hostnames


def read_zabbix_hostnames(file):
    """Read hostnames from Zabbix report Excel file"""
    hostnames = set()
    df = pd.read_excel(file)
    
    # Find Host column
    host_col = None
    for col in df.columns:
        col_upper = col.upper().strip()
        if col_upper == 'HOST' or col_upper == 'HOSTNAME' or col_upper == 'NAME':
            host_col = col
            break
    
    if host_col is None:
        # Use first column as fallback
        host_col = df.columns[0]
    
    if host_col:
        values = df[host_col].dropna().astype(str).str.strip().str.upper()
        hostnames.update(h for h in values if h and h != '-' and h != 'NAN' and h != '')
    
    return hostnames


@app.route('/api/compare/scan-hpsm', methods=['POST'])
def api_compare_scan_hpsm():
    """Compare hostnames between scan report and HPSM report"""
    try:
        if 'scan_report' not in request.files or 'hpsm_report' not in request.files:
            return jsonify({'success': False, 'error': 'Both files are required'}), 400
        
        scan_file = request.files['scan_report']
        hpsm_file = request.files['hpsm_report']
        
        try:
            scan_hostnames = read_scan_hostnames(scan_file)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Cannot read Scan report: {str(e)}'}), 400
        
        try:
            hpsm_hostnames = read_hpsm_hostnames(hpsm_file)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Cannot read HPSM report: {str(e)}'}), 400
        
        if not hpsm_hostnames:
            return jsonify({'success': False, 'error': 'No hostnames found in HPSM report. Check SERIAL_NO_ column.'}), 400
        
        # Compare
        matching = scan_hostnames.intersection(hpsm_hostnames)
        missing_in_hpsm = scan_hostnames - hpsm_hostnames
        missing_in_scan = hpsm_hostnames - scan_hostnames
        
        results = {
            'scan_count': len(scan_hostnames),
            'hpsm_count': len(hpsm_hostnames),
            'matching': sorted(list(matching)),
            'missing_in_hpsm': sorted(list(missing_in_hpsm)),
            'missing_in_scan': sorted(list(missing_in_scan))
        }
        
        return jsonify({'success': True, 'results': results})
        
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/compare/scan-zabbix', methods=['POST'])
def api_compare_scan_zabbix():
    """Compare hostnames between scan report and Zabbix report"""
    try:
        if 'scan_report' not in request.files or 'zabbix_report' not in request.files:
            return jsonify({'success': False, 'error': 'Both files are required'}), 400
        
        scan_file = request.files['scan_report']
        zabbix_file = request.files['zabbix_report']
        
        try:
            scan_hostnames = read_scan_hostnames(scan_file)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Cannot read Scan report: {str(e)}'}), 400
        
        try:
            zabbix_hostnames = read_zabbix_hostnames(zabbix_file)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Cannot read Zabbix report: {str(e)}'}), 400
        
        if not zabbix_hostnames:
            return jsonify({'success': False, 'error': 'No hostnames found in Zabbix report. Check Host column.'}), 400
        
        # Compare
        matching = scan_hostnames.intersection(zabbix_hostnames)
        missing_in_zabbix = scan_hostnames - zabbix_hostnames
        missing_in_scan = zabbix_hostnames - scan_hostnames
        
        results = {
            'scan_count': len(scan_hostnames),
            'zabbix_count': len(zabbix_hostnames),
            'matching': sorted(list(matching)),
            'missing_in_zabbix': sorted(list(missing_in_zabbix)),
            'missing_in_scan': sorted(list(missing_in_scan))
        }
        
        return jsonify({'success': True, 'results': results})
        
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/compare/hpsm-zabbix', methods=['POST'])
def api_compare_hpsm_zabbix():
    """Compare hostnames between HPSM report and Zabbix report"""
    try:
        if 'hpsm_report' not in request.files or 'zabbix_report' not in request.files:
            return jsonify({'success': False, 'error': 'Both files are required'}), 400
        
        hpsm_file = request.files['hpsm_report']
        zabbix_file = request.files['zabbix_report']
        
        try:
            hpsm_hostnames = read_hpsm_hostnames(hpsm_file)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Cannot read HPSM report: {str(e)}'}), 400
        
        try:
            zabbix_hostnames = read_zabbix_hostnames(zabbix_file)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Cannot read Zabbix report: {str(e)}'}), 400
        
        if not hpsm_hostnames:
            return jsonify({'success': False, 'error': 'No hostnames found in HPSM report. Check SERIAL_NO_ column.'}), 400
        
        if not zabbix_hostnames:
            return jsonify({'success': False, 'error': 'No hostnames found in Zabbix report. Check Host column.'}), 400
        
        # Compare
        matching = hpsm_hostnames.intersection(zabbix_hostnames)
        missing_in_zabbix = hpsm_hostnames - zabbix_hostnames  # In HPSM but not in Zabbix
        missing_in_hpsm = zabbix_hostnames - hpsm_hostnames    # In Zabbix but not in HPSM
        
        results = {
            'hpsm_count': len(hpsm_hostnames),
            'zabbix_count': len(zabbix_hostnames),
            'matching': sorted(list(matching)),
            'missing_in_zabbix': sorted(list(missing_in_zabbix)),
            'missing_in_hpsm': sorted(list(missing_in_hpsm))
        }
        
        return jsonify({'success': True, 'results': results})
        
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/compare/full', methods=['POST'])
def api_compare_full():
    """Full 3-way comparison between Scan, HPSM, and Zabbix"""
    try:
        if 'scan_report' not in request.files or 'hpsm_report' not in request.files or 'zabbix_report' not in request.files:
            return jsonify({'success': False, 'error': 'All three files are required'}), 400
        
        scan_file = request.files['scan_report']
        hpsm_file = request.files['hpsm_report']
        zabbix_file = request.files['zabbix_report']
        
        try:
            scan_hostnames = read_scan_hostnames(scan_file)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Cannot read Scan report: {str(e)}'}), 400
        
        try:
            hpsm_hostnames = read_hpsm_hostnames(hpsm_file)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Cannot read HPSM report: {str(e)}'}), 400
        
        try:
            zabbix_hostnames = read_zabbix_hostnames(zabbix_file)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Cannot read Zabbix report: {str(e)}'}), 400
        
        # 3-way comparison
        in_all_three = scan_hostnames & hpsm_hostnames & zabbix_hostnames
        
        in_scan_and_hpsm = scan_hostnames & hpsm_hostnames
        in_scan_and_zabbix = scan_hostnames & zabbix_hostnames
        in_hpsm_and_zabbix = hpsm_hostnames & zabbix_hostnames
        
        in_scan_and_hpsm_only = in_scan_and_hpsm - zabbix_hostnames
        in_scan_and_zabbix_only = in_scan_and_zabbix - hpsm_hostnames
        in_hpsm_and_zabbix_only = in_hpsm_and_zabbix - scan_hostnames
        
        only_in_scan = scan_hostnames - hpsm_hostnames - zabbix_hostnames
        only_in_hpsm = hpsm_hostnames - scan_hostnames - zabbix_hostnames
        only_in_zabbix = zabbix_hostnames - scan_hostnames - hpsm_hostnames
        
        results = {
            'scan_count': len(scan_hostnames),
            'hpsm_count': len(hpsm_hostnames),
            'zabbix_count': len(zabbix_hostnames),
            'in_all_three': sorted(list(in_all_three)),
            'in_scan_and_hpsm_only': sorted(list(in_scan_and_hpsm_only)),
            'in_scan_and_zabbix_only': sorted(list(in_scan_and_zabbix_only)),
            'in_hpsm_and_zabbix_only': sorted(list(in_hpsm_and_zabbix_only)),
            'only_in_scan': sorted(list(only_in_scan)),
            'only_in_hpsm': sorted(list(only_in_hpsm)),
            'only_in_zabbix': sorted(list(only_in_zabbix))
        }
        
        return jsonify({'success': True, 'results': results})
        
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/compare/download', methods=['POST'])
def api_download_compare_report():
    """Generate and download comparison report as Excel"""
    try:
        data = request.get_json()
        
        from excel_export import generate_comparison_report, generate_full_comparison_report
        
        compare_type = data.get('compare_type', 'scan-hpsm')
        
        if compare_type == 'full':
            filepath = generate_full_comparison_report(data)
        else:
            filepath = generate_comparison_report(data, compare_type)
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/api/stats', methods=['GET'])
def api_get_stats():
    try:
        stats = get_server_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# Main

def open_browser():
    webbrowser.open('https://localhost:5000')


if __name__ == '__main__':
    protocol = 'https' if USE_HTTPS else 'http'
    
    print("\n" + "="*50)
    print("  ServerScout - Server Inventory Management")
    print("="*50)
    print(f"\n  Starting server at {protocol}://{SERVER_HOST}:{SERVER_PORT}")
    if USE_HTTPS:
        print("  [HTTPS] Secure connection enabled")
    print("  Press Ctrl+C to stop\n")
    
    if not os.environ.get('ELECTRON_RUN'):
        threading.Timer(1.5, open_browser).start()
    
    try:
        if USE_HTTPS:
            app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False, ssl_context='adhoc')
        else:
            app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False)
    except Exception as e:
        logging.error(f"Failed to start server: {e}")
        print(f"\n[ERROR] Failed to start server: {e}")
        sys.exit(1)

