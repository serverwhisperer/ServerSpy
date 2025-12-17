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

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    init_db, add_server, get_all_servers, get_server,
    delete_server, update_server_scan_data, update_server_status,
    bulk_add_servers, get_server_stats
)
from scanner import scan_server, scan_all_servers
from excel_export import generate_excel_report

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')
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
            return jsonify({'success': True, 'server': server})
        return jsonify({'success': False, 'error': 'Server not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/servers', methods=['POST'])
def api_add_server():
    """Add a new server"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['ip', 'username', 'password', 'os_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        result = add_server(
            data['ip'],
            data['username'],
            data['password'],
            data['os_type']
        )
        
        if result['success']:
            return jsonify({'success': True, 'id': result['id']})
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


@app.route('/api/servers/bulk', methods=['POST'])
def api_bulk_import():
    """Bulk import servers from CSV"""
    try:
        if 'file' not in request.files:
            # Try JSON data
            data = request.get_json()
            if data and 'servers' in data:
                result = bulk_add_servers(data['servers'])
                return jsonify({'success': True, 'result': result})
            return jsonify({'success': False, 'error': 'No file or data provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Read CSV
        stream = io.StringIO(file.stream.read().decode('utf-8'))
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
        servers = get_all_servers()
        if not servers:
            return jsonify({'success': True, 'results': [], 'message': 'No servers to scan'})
        
        # Perform parallel scan
        results = scan_all_servers(servers)
        
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
            'offline': sum(1 for r in results if r.get('status') == 'Offline')
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
    # Open browser in separate thread
    threading.Timer(1.5, open_browser).start()
    
    print("\n" + "="*50)
    print("  ServerScout - Server Inventory Management")
    print("="*50)
    print("\n  Starting server at http://localhost:5000")
    print("  Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)

