"""
ServerScout - Server Inventory Management Tool
Main Flask application
"""

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

# Setup logging
def setup_logging():
    """Setup logging to file"""
    import sys
    
    # Determine log directory
    if getattr(sys, 'frozen', False):
        # Packaged mode - use AppData
        log_dir = os.path.join(os.getenv('APPDATA'), 'ServerScout', 'logs')
    else:
        # Development mode - use project directory
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Log file path
    log_file = os.path.join(log_dir, f'serverscout_{datetime.now().strftime("%Y%m%d")}.log')
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)  # Also print to console
        ]
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

# Determine frontend path
# In packaged mode, Electron passes FRONTEND_PATH via environment variable
FRONTEND_DIR = os.environ.get('FRONTEND_PATH')
if not FRONTEND_DIR or not os.path.exists(FRONTEND_DIR):
    # Fallback to relative path (works in development)
    FRONTEND_DIR = '../frontend'
    if getattr(sys, 'frozen', False):
        # In packaged mode, try to find frontend relative to exe location
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        resources_dir = os.path.dirname(exe_dir)
        alt_frontend = os.path.join(resources_dir, 'frontend')
        if os.path.exists(alt_frontend):
            FRONTEND_DIR = alt_frontend
        else:
            logging.warning(f"Frontend path not found. FRONTEND_PATH env: {os.environ.get('FRONTEND_PATH')}, exe_dir: {exe_dir}, trying: {alt_frontend}")

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



# ==================== STATIC FILES ====================

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(app.static_folder, filename)


# ==================== CREDENTIALS STORAGE ====================
# In-memory storage for default credentials (cleared on restart)
default_credentials = {
    'windows': {'username': '', 'password': ''},
    'linux': {'username': '', 'password': ''}
}


@app.route('/api/credentials', methods=['GET'])
def api_get_credentials():
    """Get stored default credentials (passwords hidden)"""
    try:
        return jsonify({
            'success': True,
            'credentials': {
                'windows': {
                    'username': default_credentials['windows']['username'],
                    'has_password': bool(default_credentials['windows']['password'])
                },
                'linux': {
                    'username': default_credentials['linux']['username'],
                    'has_password': bool(default_credentials['linux']['password'])
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/credentials', methods=['POST'])
def api_save_credentials():
    """Save default credentials for Windows or Linux"""
    try:
        data = request.get_json()
        os_type = data.get('os_type', '').lower()
        username = data.get('username', '')
        password = data.get('password', '')
        
        if os_type not in ['windows', 'linux']:
            return jsonify({'success': False, 'error': 'Invalid OS type'}), 400
        
        default_credentials[os_type]['username'] = username
        default_credentials[os_type]['password'] = password
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/servers/<int:server_id>/credentials', methods=['PUT'])
def api_update_server_credentials(server_id):
    """Update credentials for a specific server"""
    try:
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        
        server = get_server(server_id)
        if not server:
            return jsonify({'success': False, 'error': 'Server not found'}), 404
        
        # Update server credentials in database
        from database import update_server_credentials
        result = update_server_credentials(server_id, username, password)
        
        if result:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Update failed'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== SERVER MANAGEMENT API ====================

@app.route('/api/servers', methods=['GET'])
def api_get_servers():
    """Get all servers, optionally filtered by project"""
    try:
        project_id = request.args.get('project_id')
        
        if project_id is not None:
            if project_id == 'unassigned':
                servers = get_unassigned_servers()
            else:
                servers = get_servers_by_project(int(project_id))
        else:
            servers = get_all_servers()
        
        return jsonify({'success': True, 'servers': servers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/servers/<int:server_id>', methods=['GET'])
def api_get_server(server_id):
    """Get a single server by ID"""
    try:
        server = get_server(server_id)
        if server:
            return jsonify({'success': True, 'server': server})
        return jsonify({'success': False, 'error': 'Server not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/servers', methods=['POST'])
def api_add_server():
    """Add a new server"""
    try:
        data = request.get_json()
        
        # IP is always required
        if not data.get('ip'):
            return jsonify({'success': False, 'error': 'Missing required field: ip'}), 400
        
        ip = data['ip'].strip()
        
        # Get credentials - use defaults if not provided
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # If using default credentials, get them from stored credentials
        if data.get('use_default', False) or (not username and not password):
            # Will be filled during scan from default credentials
            username = username or 'pending'
            password = password or 'pending'
        
        # Auto-detect OS type if not provided
        os_type = data.get('os_type', '').strip()
        detected = False
        
        if not os_type or data.get('auto_detect', False):
            os_type = detect_os_type(ip)
            detected = True
        
        # Get optional project_id
        project_id = data.get('project_id')
        
        result = add_server(
            ip,
            username,
            password,
            os_type,
            project_id
        )
        
        if result['success']:
            response = {'success': True, 'id': result['id']}
            if detected:
                response['detected'] = True
                response['os_type'] = os_type
            return jsonify(response)
        return jsonify({'success': False, 'error': result['error']}), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/servers/<int:server_id>', methods=['DELETE'])
def api_delete_server(server_id):
    """Delete a server"""
    try:
        if delete_server(server_id):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Server not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/servers/clear', methods=['DELETE'])
def api_clear_servers():
    """Delete servers - optionally filtered by project"""
    try:
        project_id = request.args.get('project_id')
        
        if project_id is None:
            # No filter - delete all
            count = clear_all_servers()
            message = 'Tüm sunucular silindi'
        elif project_id == 'unassigned':
            # Delete unassigned servers
            count = clear_unassigned_servers()
            message = 'Atanmamış sunucular silindi'
        else:
            # Delete servers in specific project
            count = clear_servers_by_project(int(project_id))
            message = 'Projedeki sunucular silindi'
        
        return jsonify({'success': True, 'deleted': count, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/servers/bulk', methods=['POST'])
def api_bulk_import():
    """Bulk import servers from TXT, CSV or JSON"""
    try:
        project_id = None
        
        if 'file' not in request.files:
            # Try JSON data
            data = request.get_json()
            if data and 'servers' in data:
                project_id = data.get('project_id')
                result = bulk_add_servers(data['servers'], project_id)
                return jsonify({'success': True, 'result': result})
            elif data and 'content' in data:
                # Handle text content (from textarea)
                project_id = data.get('project_id')
                content = data['content']
                servers = parse_server_list_content(content)
                result = bulk_add_servers(servers, project_id)
                return jsonify({'success': True, 'result': result})
            return jsonify({'success': False, 'error': 'No file or data provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Get project_id from form data
        project_id = request.form.get('project_id')
        if project_id:
            project_id = int(project_id)
        
        # Read file content
        content = file.stream.read().decode('utf-8')
        filename = file.filename.lower()
        
        # Determine file type and parse accordingly
        if filename.endswith('.csv'):
            # CSV format with headers
            stream = io.StringIO(content)
            reader = csv.DictReader(stream)
            
            servers = []
            for row in reader:
                servers.append({
                    'ip': row.get('ip', '').strip(),
                    'username': row.get('username', '').strip(),
                    'password': row.get('password', '').strip(),
                    'os_type': row.get('os_type', 'Windows').strip()
                })
        else:
            # TXT format - one IP per line with optional OS hint
            servers = parse_server_list_content(content)
        
        result = bulk_add_servers(servers, project_id)
        return jsonify({'success': True, 'result': result})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def parse_server_list_content(content, auto_detect=True):
    """Parse server list from text content"""
    servers = []
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = line.split()
        ip = parts[0].strip()
        os_type = None
        
        if len(parts) > 1:
            os_hint = parts[1].upper()
            if os_hint in ['L', 'LINUX']:
                os_type = 'Linux'
            elif os_hint in ['W', 'WINDOWS']:
                os_type = 'Windows'
        
        # Auto-detect if OS type not specified
        if os_type is None:
            if auto_detect:
                os_type = detect_os_type(ip)
            else:
                os_type = 'Windows'  # Default fallback
        
        servers.append({
            'ip': ip,
            'username': '',  # Will use default credentials
            'password': '',
            'os_type': os_type
        })
    
    return servers


# ==================== PROJECT MANAGEMENT API ====================

@app.route('/api/projects', methods=['GET'])
def api_get_projects():
    """Get all projects"""
    try:
        projects = get_all_projects()
        return jsonify({'success': True, 'projects': projects})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/projects/with-stats', methods=['GET'])
def api_get_projects_with_stats():
    """Get all projects with their statistics"""
    try:
        data = get_all_projects_with_stats()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/projects', methods=['POST'])
def api_create_project():
    """Create a new project"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': 'Project name is required'}), 400
        
        result = create_project(name)
        
        if result['success']:
            return jsonify({'success': True, 'id': result['id']})
        return jsonify({'success': False, 'error': result['error']}), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>', methods=['GET'])
def api_get_project(project_id):
    """Get a single project by ID"""
    try:
        project = get_project(project_id)
        if project:
            return jsonify({'success': True, 'project': project})
        return jsonify({'success': False, 'error': 'Project not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def api_rename_project(project_id):
    """Rename a project"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': 'Project name is required'}), 400
        
        result = rename_project(project_id, name)
        
        if result['success']:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': result['error']}), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def api_delete_project(project_id):
    """Delete a project"""
    try:
        if delete_project(project_id):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Project not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/servers', methods=['GET'])
def api_get_project_servers(project_id):
    """Get all servers for a project"""
    try:
        servers = get_servers_by_project(project_id)
        stats = get_server_stats(project_id)
        return jsonify({'success': True, 'servers': servers, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/projects/unassigned/servers', methods=['GET'])
def api_get_unassigned_servers():
    """Get all servers without a project"""
    try:
        servers = get_unassigned_servers()
        stats = get_server_stats_unassigned()
        return jsonify({'success': True, 'servers': servers, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/servers/assign', methods=['POST'])
def api_assign_servers():
    """Assign servers to a project"""
    try:
        data = request.get_json()
        server_ids = data.get('server_ids', [])
        project_id = data.get('project_id')  # None means unassign
        
        if not server_ids:
            return jsonify({'success': False, 'error': 'No servers specified'}), 400
        
        result = assign_servers_to_project(server_ids, project_id)
        return jsonify({'success': True, 'result': result})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== SCANNING API ====================

@app.route('/api/scan/<int:server_id>', methods=['POST'])
def get_server_with_credentials(server):
    """Get server with credentials - use defaults if empty"""
    server_copy = dict(server)
    os_type = server_copy.get('os_type', 'Windows').lower()
    
    # Use default credentials if server has no credentials
    if not server_copy.get('username') or not server_copy.get('password'):
        cred_key = 'windows' if os_type == 'windows' else 'linux'
        
        if default_credentials[cred_key]['username'] and default_credentials[cred_key]['password']:
            server_copy['username'] = default_credentials[cred_key]['username']
            server_copy['password'] = default_credentials[cred_key]['password']
        else:
            # No credentials available
            return None
    
    return server_copy


def api_scan_server(server_id):
    """Scan a single server"""
    try:
        server = get_server(server_id)
        if not server:
            return jsonify({'success': False, 'error': 'Server not found'}), 404
        
        # Get server with credentials
        server_with_creds = get_server_with_credentials(server)
        if not server_with_creds:
            return jsonify({
                'success': False, 
                'error': 'Kimlik bilgisi bulunamadı. Lütfen sunucu veya varsayılan kimlik bilgilerini girin.'
            }), 400
        
        # Perform scan
        result = scan_server(server_with_creds)
        
        # Update database
        if result.get('status') == 'Online':
            update_server_scan_data(server_id, result)
        else:
            update_server_status(server_id, 'Offline')
        
        return jsonify({'success': True, 'result': result})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scan-all', methods=['POST'])
def api_scan_all():
    """Scan all servers in parallel"""
    try:
        servers = get_all_servers()
        if not servers:
            return jsonify({'success': True, 'results': [], 'message': 'No servers to scan'})
        
        # Prepare servers with credentials
        servers_to_scan = []
        skipped = 0
        
        for server in servers:
            server_with_creds = get_server_with_credentials(server)
            if server_with_creds:
                servers_to_scan.append(server_with_creds)
            else:
                skipped += 1
        
        if not servers_to_scan:
            return jsonify({
                'success': True, 
                'results': [], 
                'message': 'Taranacak sunucu yok (kimlik bilgisi eksik)',
                'skipped': skipped
            })
        
        # Perform parallel scan
        results = scan_all_servers(servers_to_scan)
        
        # Update database for each result
        for result in results:
            server_id = result.get('id')
            if server_id:
                if result.get('status') == 'Online':
                    update_server_scan_data(server_id, result)
                else:
                    update_server_status(server_id, 'Offline')
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results),
            'online': sum(1 for r in results if r.get('status') == 'Online'),
            'offline': sum(1 for r in results if r.get('status') == 'Offline'),
            'skipped': skipped
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== EXPORT API ====================

@app.route('/api/export/excel', methods=['GET'])
def api_export_excel():
    """Generate and download Excel report (all servers)"""
    try:
        servers = get_all_servers()
        stats = get_server_stats()
        
        filepath = generate_excel_report(servers, stats)
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export/excel/project/<int:project_id>', methods=['GET'])
def api_export_project_excel(project_id):
    """Generate and download Excel report for a single project"""
    try:
        project = get_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        servers = get_servers_by_project(project_id)
        stats = get_server_stats(project_id)
        
        filepath = generate_project_excel_report(project['name'], servers, stats)
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export/excel/all-projects', methods=['GET'])
def api_export_all_projects_excel():
    """Generate and download Excel report with all projects (each project as separate sheet)"""
    try:
        projects = get_all_projects()
        
        # Build projects data with servers and stats
        projects_data = []
        for project in projects:
            servers = get_servers_by_project(project['id'])
            stats = get_server_stats(project['id'])
            projects_data.append({
                'name': project['name'],
                'servers': servers,
                'stats': stats
            })
        
        # Also include unassigned servers
        unassigned_servers = get_unassigned_servers()
        unassigned_stats = get_server_stats_unassigned()
        
        filepath = generate_all_projects_excel_report(projects_data, unassigned_servers, unassigned_stats)
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== STATS API ====================

# ==================== REPORT COMPARISON API ====================

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
        return jsonify({'success': False, 'error': str(e)}), 500


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
        return jsonify({'success': False, 'error': str(e)}), 500


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
        return jsonify({'success': False, 'error': str(e)}), 500


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
        return jsonify({'success': False, 'error': str(e)}), 500


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
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== STATS API ====================

@app.route('/api/stats', methods=['GET'])
def api_get_stats():
    """Get server statistics"""
    try:
        stats = get_server_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== MAIN ====================

def open_browser():
    """Open browser after a short delay"""
    webbrowser.open('http://localhost:5000')


if __name__ == '__main__':
    print("\n" + "="*50)
    print("  ServerScout - Server Inventory Management")
    print("="*50)
    print("\n  Starting server at http://localhost:5000")
    print("  Press Ctrl+C to stop\n")
    
    # Only open browser if NOT running under Electron
    if not os.environ.get('ELECTRON_RUN'):
        threading.Timer(1.5, open_browser).start()
    
    app.run(host='0.0.0.0', port=5000, debug=False)

