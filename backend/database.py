"""
Database module for ServerScout
In-memory storage with credential management
"""

from datetime import datetime

# In-memory storage
_servers = []
_next_id = 1

# Default credentials
_credentials = {
    'windows': {
        'username': '',
        'password': ''
    },
    'linux': {
        'username': '',
        'password': ''
    }
}


def _get_next_id():
    """Get next available ID"""
    global _next_id
    current_id = _next_id
    _next_id += 1
    return current_id


def init_db():
    """Initialize (reset) the in-memory storage"""
    global _servers, _next_id
    _servers = []
    _next_id = 1


# ==================== CREDENTIALS ====================

def set_credentials(os_type, username, password):
    """Set default credentials for an OS type"""
    global _credentials
    os_key = os_type.lower()
    if os_key in _credentials:
        _credentials[os_key]['username'] = username
        _credentials[os_key]['password'] = password
        return True
    return False


def get_credentials(os_type):
    """Get default credentials for an OS type"""
    os_key = os_type.lower()
    return _credentials.get(os_key, {'username': '', 'password': ''})


def get_all_credentials():
    """Get all default credentials"""
    return _credentials.copy()


# ==================== SERVERS ====================

def add_server(ip, os_type, username=None, password=None, use_custom=False):
    """Add a new server"""
    global _servers
    
    # Check if IP already exists
    for server in _servers:
        if server['ip'] == ip:
            return {'success': False, 'error': 'Server with this IP already exists'}
    
    now = datetime.now().isoformat()
    server = {
        'id': _get_next_id(),
        'ip': ip,
        'username': username or '',  # Only store if custom
        'password': password or '',  # Only store if custom
        'os_type': os_type,
        'use_custom_creds': use_custom,  # True = use stored creds, False = use default at scan time
        'hostname': None,
        'domain': None,
        'brand': None,
        'model': None,
        'serial': None,
        'motherboard': None,
        'cpu_count': None,
        'cpu_cores': None,
        'cpu_logical_processors': None,
        'cpu_model': None,
        'ram_physical': None,
        'ram_logical': None,
        'disk_info': None,
        'network_primary': None,
        'network_all': None,
        'os_version': None,
        'service_pack': None,
        'status': 'Not Scanned',
        'last_scan': None,
        'created_at': now,
        'updated_at': now
    }
    _servers.append(server)
    return {'success': True, 'id': server['id']}


def get_all_servers():
    """Get all servers (without passwords in response)"""
    result = []
    for server in _servers:
        s = server.copy()
        # Don't expose password in API response
        s['password'] = '***' if s['password'] else ''
        result.append(s)
    return result


def get_server(server_id):
    """Get a single server by ID (with credentials for scanning)"""
    for server in _servers:
        if server['id'] == server_id:
            return server.copy()
    return None


def get_server_by_ip(ip):
    """Get a single server by IP"""
    for server in _servers:
        if server['ip'] == ip:
            return server.copy()
    return None


def delete_server(server_id):
    """Delete a server"""
    global _servers
    for i, server in enumerate(_servers):
        if server['id'] == server_id:
            _servers.pop(i)
            return True
    return False


def update_server_credentials(server_id, username, password):
    """Update credentials for a specific server"""
    global _servers
    for server in _servers:
        if server['id'] == server_id:
            server['username'] = username
            server['password'] = password
            server['use_custom_creds'] = True
            return True
    return False


def update_server_scan_data(server_id, scan_data):
    """Update server with scan results"""
    global _servers
    now = datetime.now().isoformat()
    
    for server in _servers:
        if server['id'] == server_id:
            server['hostname'] = scan_data.get('hostname')
            server['domain'] = scan_data.get('domain')
            server['brand'] = scan_data.get('brand')
            server['model'] = scan_data.get('model')
            server['serial'] = scan_data.get('serial')
            server['motherboard'] = scan_data.get('motherboard')
            server['cpu_count'] = scan_data.get('cpu_count')
            server['cpu_cores'] = scan_data.get('cpu_cores')
            server['cpu_logical_processors'] = scan_data.get('cpu_logical_processors')
            server['cpu_model'] = scan_data.get('cpu_model')
            server['ram_physical'] = scan_data.get('ram_physical')
            server['ram_logical'] = scan_data.get('ram_logical')
            server['disk_info'] = scan_data.get('disk_info')
            server['network_primary'] = scan_data.get('network_primary')
            server['network_all'] = scan_data.get('network_all')
            server['os_version'] = scan_data.get('os_version')
            server['service_pack'] = scan_data.get('service_pack')
            server['status'] = scan_data.get('status', 'Online')
            server['last_scan'] = now
            server['updated_at'] = now
            return True
    return False


def update_server_status(server_id, status):
    """Update only the status of a server"""
    global _servers
    now = datetime.now().isoformat()
    
    for server in _servers:
        if server['id'] == server_id:
            server['status'] = status
            server['last_scan'] = now
            server['updated_at'] = now
            return True
    return False


def bulk_add_servers_from_txt(content, auto_detect_fn=None):
    """
    Add multiple servers from TXT content
    Format: IP/HOSTNAME [OSTYPE]
    OSTYPE: W = Windows, L = Linux (optional - auto-detected if not provided)
    """
    results = {'success': 0, 'failed': 0, 'errors': [], 'detected': 0}
    
    lines = content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = line.split()
        if len(parts) < 1:
            continue
        
        ip = parts[0].strip()
        os_type = None
        
        # Check if OS type is provided
        if len(parts) >= 2:
            os_code = parts[1].strip().upper()
            if os_code == 'W':
                os_type = 'Windows'
            elif os_code == 'L':
                os_type = 'Linux'
            # If not W or L, ignore and auto-detect
        
        # Auto-detect if OS type not provided
        if os_type is None and auto_detect_fn:
            os_type = auto_detect_fn(ip)
            if os_type:
                results['detected'] += 1
        
        # Default to Windows if still unknown
        if os_type is None:
            os_type = 'Windows'
        
        # use_custom=False means use default credentials at scan time
        result = add_server(ip, os_type, use_custom=False)
        if result['success']:
            results['success'] += 1
        else:
            results['failed'] += 1
            results['errors'].append({'line': line, 'error': result['error']})
    
    return results


def bulk_add_servers(servers_list):
    """Add multiple servers from a list (legacy CSV support)"""
    results = {'success': 0, 'failed': 0, 'errors': []}
    for server in servers_list:
        has_custom_creds = bool(server.get('username') and server.get('password'))
        result = add_server(
            server.get('ip'),
            server.get('os_type', 'Windows'),
            server.get('username'),
            server.get('password'),
            use_custom=has_custom_creds
        )
        if result['success']:
            results['success'] += 1
        else:
            results['failed'] += 1
            results['errors'].append({'ip': server.get('ip'), 'error': result['error']})
    return results


def get_server_stats():
    """Get statistics about servers"""
    total = len(_servers)
    online = sum(1 for s in _servers if s['status'] == 'Online')
    offline = sum(1 for s in _servers if s['status'] == 'Offline')
    not_scanned = sum(1 for s in _servers if s['status'] == 'Not Scanned')
    
    last_scan = None
    for server in _servers:
        if server['last_scan']:
            if last_scan is None or server['last_scan'] > last_scan:
                last_scan = server['last_scan']
    
    return {
        'total': total,
        'online': online,
        'offline': offline,
        'not_scanned': not_scanned,
        'last_scan': last_scan
    }


def clear_all_servers():
    """Clear all servers from memory"""
    global _servers, _next_id
    _servers = []
    _next_id = 1
