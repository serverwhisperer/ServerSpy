# Input validation utilities
# Security: Validate all user inputs to prevent injection attacks

import re
import ipaddress
import logging

# IP address validation patterns
IPV4_PATTERN = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
IPV6_PATTERN = re.compile(r'^([0-9a-fA-F]{0,4}:){7}[0-9a-fA-F]{0,4}$')

# Username validation: alphanumeric, underscore, dash, dot, @ (for domain users)
# Max length: 256 characters (Windows limit)
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.@]{1,256}$')

# Password validation: allow most characters, max length reasonable
# Max length: 512 characters (reasonable limit)
PASSWORD_MAX_LENGTH = 512

# Project name validation: alphanumeric, spaces, dash, underscore
PROJECT_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s_\-]{1,100}$')


def validate_ip(ip_str):
    """
    Validate IP address (IPv4 or IPv6)
    Returns: (is_valid, error_message)
    """
    if not ip_str or not isinstance(ip_str, str):
        return False, "IP address is required"
    
    ip_str = ip_str.strip()
    
    # Check basic format
    if not ip_str:
        return False, "IP address cannot be empty"
    
    # Try IPv4
    try:
        ipaddress.IPv4Address(ip_str)
        return True, None
    except:
        pass
    
    # Try IPv6
    try:
        ipaddress.IPv6Address(ip_str)
        return True, None
    except:
        pass
    
    # Try hostname (for localhost, etc.)
    if ip_str.lower() in ['localhost', '127.0.0.1', '::1']:
        return True, None
    
    return False, "Invalid IP address format"


def validate_username(username):
    """
    Validate username
    Returns: (is_valid, error_message)
    """
    if username is None:
        return True, None  # Username is optional
    
    if not isinstance(username, str):
        return False, "Username must be a string"
    
    username = username.strip()
    
    # Empty username is OK (will use defaults)
    if not username or username == 'pending':
        return True, None
    
    # Check length
    if len(username) > 256:
        return False, "Username too long (max 256 characters)"
    
    # Check pattern
    if not USERNAME_PATTERN.match(username):
        return False, "Username contains invalid characters"
    
    return True, None


def validate_password(password):
    """
    Validate password
    Returns: (is_valid, error_message)
    """
    if password is None:
        return True, None  # Password is optional
    
    if not isinstance(password, str):
        return False, "Password must be a string"
    
    # Empty password is OK (will use defaults)
    if not password or password == 'pending':
        return True, None
    
    # Check length
    if len(password) > PASSWORD_MAX_LENGTH:
        return False, f"Password too long (max {PASSWORD_MAX_LENGTH} characters)"
    
    return True, None


def validate_project_name(name):
    """
    Validate project name
    Returns: (is_valid, error_message)
    """
    if not name or not isinstance(name, str):
        return False, "Project name is required"
    
    name = name.strip()
    
    if not name:
        return False, "Project name cannot be empty"
    
    if len(name) > 100:
        return False, "Project name too long (max 100 characters)"
    
    if not PROJECT_NAME_PATTERN.match(name):
        return False, "Project name contains invalid characters"
    
    return True, None


def validate_os_type(os_type):
    """
    Validate OS type
    Returns: (is_valid, error_message)
    """
    if not os_type:
        return True, None  # Optional, will auto-detect
    
    if not isinstance(os_type, str):
        return False, "OS type must be a string"
    
    os_type = os_type.strip().lower()
    
    if os_type not in ['windows', 'linux']:
        return False, "OS type must be 'Windows' or 'Linux'"
    
    return True, None


def sanitize_string(value, max_length=None):
    """
    Sanitize string input (remove control characters, trim)
    Returns: sanitized string or None
    """
    if value is None:
        return None
    
    if not isinstance(value, str):
        return None
    
    # Remove control characters (except newline, tab)
    sanitized = ''.join(c for c in value if ord(c) >= 32 or c in '\n\t')
    
    # Trim
    sanitized = sanitized.strip()
    
    # Check length
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized if sanitized else None



