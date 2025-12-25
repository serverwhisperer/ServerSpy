# Config stuff
import os
import sys

def get_appdata_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.getenv('APPDATA'), 'ServerScout')
    return None

def get_data_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(get_appdata_path(), 'data')
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

def get_logs_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(get_appdata_path(), 'logs')
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')

# Server settings
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000
USE_HTTPS = os.environ.get('USE_HTTPS', 'true').lower() != 'false'

# DB
DB_NAME = 'inventory.db'

# Encryption
ENCRYPTION_KEY_FILE = '.encryption_key'

# Scanning
SCAN_WORKERS = {'small': 10, 'medium': 20, 'large': 30, 'xlarge': 50}
SSH_TIMEOUT = 30
WINRM_TIMEOUT = 30
PORT_CHECK_TIMEOUT = 3

def get_frontend_path():
    # Try env var first (Electron sets this)
    fe_path = os.environ.get('FRONTEND_PATH')
    if fe_path and os.path.exists(fe_path):
        return os.path.abspath(fe_path)
    
    # Get the project root directory (parent of backend directory)
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(backend_dir)
    fe_path = os.path.join(project_root, 'frontend')
    
    # Make it absolute
    fe_path = os.path.abspath(fe_path)
    
    if getattr(sys, 'frozen', False):
        # In packaged mode, frontend is in resources
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        res_dir = os.path.dirname(exe_dir)
        alt = os.path.join(res_dir, 'frontend')
        if os.path.exists(alt):
            return os.path.abspath(alt)
    
    return fe_path





