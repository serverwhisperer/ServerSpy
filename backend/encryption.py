# Password encryption stuff
# Uses Fernet (AES-128) for encrypting passwords in DB
# Key is protected with Windows DPAPI on Windows

import os
import sys
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Check if we can use Windows DPAPI
HAS_WIN32CRYPT = False
try:
    if sys.platform == 'win32':
        import win32crypt
        HAS_WIN32CRYPT = True
except:
    pass

# Cache the key so we don't load it every time
_key = None
_fernet = None


def get_key_file_path():
    # Figure out where to store the key file
    if getattr(sys, 'frozen', False):
        appdata_path = os.path.join(os.getenv('APPDATA'), 'ServerScout', 'data')
    else:
        appdata_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    
    os.makedirs(appdata_path, exist_ok=True)
    return os.path.join(appdata_path, '.encryption_key')


def generate_key():
    return Fernet.generate_key()


def get_or_create_encryption_key():
    # Get the key, create if needed
    global _key
    
    if _key is not None:
        return _key
    
    key_path = get_key_file_path()
    
    # Load existing key if it exists
    if os.path.exists(key_path):
        try:
            with open(key_path, 'rb') as f:
                enc_key = f.read()
            
            if HAS_WIN32CRYPT:
                try:
                    # Windows DPAPI decrypt
                    _key = win32crypt.CryptUnprotectData(enc_key, None, None, None, 0)[1]
                except Exception as e:
                    logging.error(f"DPAPI decrypt failed: {e}")
                    _key = generate_key()
                    save_encryption_key(_key)
            else:
                # Linux/Mac - use master key
                master = _get_master_key()
                if master:
                    try:
                        f = Fernet(master)
                        _key = f.decrypt(enc_key)
                    except:
                        _key = generate_key()
                        save_encryption_key(_key)
                else:
                    _key = enc_key  # fallback
            
            return _key
        except Exception as e:
            logging.error(f"Key load error: {e}")
    
    # New key needed
    _key = generate_key()
    save_encryption_key(_key)
    return _key


def _get_master_key():
    # For non-Windows: create master key from system info
    # Security: Use environment variable if available, otherwise derive from system
    try:
        import getpass
        import socket
        import hashlib
        
        # Check for environment variable first (more secure)
        env_key = os.getenv('SERVERSCOUT_MASTER_KEY')
        if env_key:
            # Use provided key as base
            key_base = env_key.encode()
        else:
            # Derive from system info (username + hostname + app identifier)
            # Security: Multiple factors make it harder to predict
            sys_info = f"{getpass.getuser()}{socket.gethostname()}"
            # Add application-specific component (hashed to avoid hardcoding)
            app_id = hashlib.sha256(b"ServerScout").hexdigest()[:16]
            key_base = f"{sys_info}{app_id}".encode()
        
        # Use username+hostname as salt
        salt_str = f"{getpass.getuser()}{socket.gethostname()}"
        salt = salt_str.encode()
        
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        key_bytes = kdf.derive(key_base)
        return base64.urlsafe_b64encode(key_bytes)
    except:
        return None


def save_encryption_key(key):
    key_path = get_key_file_path()
    
    try:
        if HAS_WIN32CRYPT:
            # Windows: use DPAPI
            enc_key = win32crypt.CryptProtectData(key, "ServerScout Encryption Key", None, None, None, 0)
        else:
            # Linux/Mac: encrypt with master key
            master = _get_master_key()
            if master:
                f = Fernet(master)
                enc_key = f.encrypt(key)
            else:
                enc_key = key  # fallback
        
        with open(key_path, 'wb') as f:
            f.write(enc_key)
        
        # Unix file permissions
        if hasattr(os, 'chmod'):
            os.chmod(key_path, 0o600)
        
        logging.info(f"Key saved: {key_path}")
    except Exception as e:
        logging.error(f"Save key failed: {e}")
        raise


def get_fernet():
    global _fernet
    
    if _fernet is None:
        k = get_or_create_encryption_key()
        _fernet = Fernet(k)
    
    return _fernet


def encrypt_password(pwd):
    # Encrypt password before storing in DB
    if not pwd or pwd == '' or pwd == 'pending':
        return ''
    
    try:
        if isinstance(pwd, str):
            pwd = pwd.encode('utf-8')
        
        f = get_fernet()
        enc = f.encrypt(pwd)
        return base64.urlsafe_b64encode(enc).decode('utf-8')
    except Exception as e:
        logging.error(f"Encrypt error: {e}")
        return ''  # Don't break if encryption fails


def decrypt_password(enc_pwd):
    # Decrypt password from DB
    if not enc_pwd or enc_pwd == '':
        return ''
    
    try:
        enc_bytes = base64.urlsafe_b64decode(enc_pwd.encode('utf-8'))
        f = get_fernet()
        dec = f.decrypt(enc_bytes)
        return dec.decode('utf-8')
    except Exception as e:
        logging.error(f"Decrypt error: {e}")
        return ''


def sanitize_server_data(data):
    # Remove passwords from API responses
    if isinstance(data, list):
        return [sanitize_server_data(item) for item in data]
    
    if isinstance(data, dict):
        result = dict(data)
        if 'password' in result:
            del result['password']
        return result
    
    return data

