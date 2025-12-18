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
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

# Determine if we're running as a PyInstaller bundle
def get_base_path():
    """Get the base path for resources - handles both dev and PyInstaller bundle"""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

# Add backend directory to path
sys.path.insert(0, get_base_path())

from database import (
    init_db, add_server, get_all_servers, get_server,
    delete_server, update_server_scan_data, update_server_status,
    bulk_add_servers, bulk_add_servers_from_txt, get_server_stats,
    set_credentials, get_credentials, get_all_credentials,
    update_server_credentials, clear_all_servers
)
from scanner import scan_server, scan_all_servers, detect_os_type
from excel_export import generate_excel_report

# Determine frontend folder path
def get_frontend_path():
    """Get the correct frontend folder path"""
    if getattr(sys, 'frozen', False):
        # PyInstaller bundle - frontend is bundled with exe
        return os.path.join(sys._MEIPASS, 'frontend')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend')

# Initialize Flask app
FRONTEND_PATH = get_frontend_path()
app = Flask(__name__, static_folder=FRONTEND_PATH, static_url_path='')
CORS(app)

# Initialize database
init_db()


# ==================== STATIC FILES ====================

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(app.static_folder, filename)


# ==================== CREDENTIALS API ====================

@app.route('/api/credentials', methods=['GET'])
def api_get_credentials():
    """Get all default credentials (without passwords)"""
    try:
        creds = get_all_credentials()
        # Hide passwords
        safe_creds = {}
        for os_type, cred in creds.items():
            safe_creds[os_type] = {
                'username': cred['username'],
                'has_password': bool(cred['password'])
            }
        return jsonify({'success': True, 'credentials': safe_creds})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/credentials', methods=['POST'])
def api_set_credentials():
    """Set default credentials for an OS type"""
    try:
        data = request.get_json()
        os_type = data.get('os_type', '').lower()
        username = data.get('username', '')
        password = data.get('password', '')
        
        if os_type not in ['windows', 'linux']:
            return jsonify({'success': False, 'error': 'Invalid OS type. Use windows or linux'}), 400
        
        set_credentials(os_type, username, password)
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== SERVER MANAGEMENT API ====================

@app.route('/api/servers', methods=['GET'])
def api_get_servers():
    """Get all servers"""
    try:
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
            # Hide password
            server['password'] = '***' if server['password'] else ''
            return jsonify({'success': True, 'server': server})
        return jsonify({'success': False, 'error': 'Server not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/servers', methods=['POST'])
def api_add_server():
    """Add a new server"""
    try:
        data = request.get_json()
        
        ip = data.get('ip', '').strip()
        os_type = data.get('os_type', '')
        username = data.get('username', '')
        password = data.get('password', '')
        use_custom = not data.get('use_default', True)  # use_default=True means use_custom=False
        auto_detect = data.get('auto_detect', False)
        
        if not ip:
            return jsonify({'success': False, 'error': 'IP address is required'}), 400
        
        # Auto-detect OS if requested or not provided
        detected = False
        if auto_detect or not os_type:
            detected_os = detect_os_type(ip)
            if detected_os:
                os_type = detected_os
                detected = True
            elif not os_type:
                os_type = 'Windows'  # Default fallback
        
        result = add_server(ip, os_type, username, password, use_custom)
        
        if result['success']:
            return jsonify({'success': True, 'id': result['id'], 'os_type': os_type, 'detected': detected})
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


@app.route('/api/servers/<int:server_id>/credentials', methods=['PUT'])
def api_update_server_credentials(server_id):
    """Update credentials for a specific server"""
    try:
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        
        if update_server_credentials(server_id, username, password):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Server not found'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/servers/clear', methods=['DELETE'])
def api_clear_servers():
    """Clear all servers"""
    try:
        clear_all_servers()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/servers/bulk', methods=['POST'])
def api_bulk_import():
    """Bulk import servers from TXT or CSV file"""
    try:
        if 'file' not in request.files:
            # Try JSON data
            data = request.get_json()
            if data and 'servers' in data:
                result = bulk_add_servers(data['servers'])
                return jsonify({'success': True, 'result': result})
            if data and 'content' in data:
                # TXT content directly - with auto-detection
                result = bulk_add_servers_from_txt(data['content'], auto_detect_fn=detect_os_type)
                return jsonify({'success': True, 'result': result})
            return jsonify({'success': False, 'error': 'No file or data provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        content = file.stream.read().decode('utf-8')
        
        # Detect file type
        if file.filename.endswith('.csv'):
            # CSV format
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
            
            result = bulk_add_servers(servers)
        else:
            # TXT format: IP [OSTYPE] - with auto-detection
            result = bulk_add_servers_from_txt(content, auto_detect_fn=detect_os_type)
        
        return jsonify({'success': True, 'result': result})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== SCANNING API ====================

@app.route('/api/scan/<int:server_id>', methods=['POST'])
def api_scan_server(server_id):
    """Scan a single server"""
    try:
        server = get_server(server_id)
        if not server:
            return jsonify({'success': False, 'error': 'Server not found'}), 404
        
        # Get credentials at scan time
        if server.get('use_custom_creds') and server.get('username') and server.get('password'):
            # Use custom credentials stored with server
            username = server['username']
            password = server['password']
        else:
            # Use default credentials for this OS type
            creds = get_credentials(server['os_type'])
            username = creds['username']
            password = creds['password']
        
        if not username or not password:
            os_type = server['os_type']
            return jsonify({
                'success': False, 
                'error': f'No credentials set. Please enter {os_type} credentials at the top of the page.'
            }), 400
        
        # Apply credentials to server object for scanning
        server['username'] = username
        server['password'] = password
        
        # Perform scan
        result = scan_server(server)
        
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
        servers_list = get_all_servers()
        if not servers_list:
            return jsonify({'success': True, 'results': [], 'message': 'No servers to scan'})
        
        # Get default credentials once
        windows_creds = get_credentials('windows')
        linux_creds = get_credentials('linux')
        
        # Apply credentials to each server at scan time
        servers_to_scan = []
        skipped = 0
        
        for server in servers_list:
            # Get full server data including password
            full_server = get_server(server['id'])
            if not full_server:
                continue
            
            # Determine which credentials to use
            if full_server.get('use_custom_creds') and full_server.get('username') and full_server.get('password'):
                # Use custom credentials
                username = full_server['username']
                password = full_server['password']
            else:
                # Use default credentials based on OS type
                if full_server['os_type'].lower() == 'windows':
                    username = windows_creds['username']
                    password = windows_creds['password']
                else:
                    username = linux_creds['username']
                    password = linux_creds['password']
            
            if username and password:
                full_server['username'] = username
                full_server['password'] = password
                servers_to_scan.append(full_server)
            else:
                skipped += 1
        
        # Perform parallel scan
        results = scan_all_servers(servers_to_scan) if servers_to_scan else []
        
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
    """Generate and download Excel report"""
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
