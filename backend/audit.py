# Audit logging for security events
# Tracks important security-related operations

import os
import sys
import json
import logging
from datetime import datetime
from config import get_data_path

AUDIT_LOG_DIR = os.path.join(get_data_path(), 'audit')
AUDIT_LOG_FILE = os.path.join(AUDIT_LOG_DIR, f'audit_{datetime.now().strftime("%Y%m%d")}.log')


def ensure_audit_dir():
    """Ensure audit log directory exists"""
    try:
        os.makedirs(AUDIT_LOG_DIR, exist_ok=True)
        # Unix permissions: owner only
        if hasattr(os, 'chmod'):
            os.chmod(AUDIT_LOG_DIR, 0o700)
    except Exception as e:
        logging.error(f"Failed to create audit directory: {e}")


def get_user_info():
    """Get current user information for audit logs"""
    try:
        import getpass
        username = getpass.getuser()
    except:
        username = "unknown"
    
    try:
        import socket
        hostname = socket.gethostname()
    except:
        hostname = "unknown"
    
    return username, hostname


def audit_log(event_type, action, details=None, ip_address=None, success=True):
    """
    Log a security audit event
    
    Args:
        event_type: Type of event (e.g., 'AUTH', 'DATA_ACCESS', 'DATA_MODIFY', 'KEY_ROTATION')
        action: Specific action (e.g., 'LOGIN', 'ADD_SERVER', 'DELETE_SERVER', 'KEY_ROTATED')
        details: Additional details (dict)
        ip_address: Client IP address if available
        success: Whether the action was successful
    """
    try:
        ensure_audit_dir()
        
        username, hostname = get_user_info()
        timestamp = datetime.now().isoformat()
        
        audit_entry = {
            'timestamp': timestamp,
            'event_type': event_type,
            'action': action,
            'user': username,
            'hostname': hostname,
            'ip_address': ip_address or 'N/A',
            'success': success,
            'details': details or {}
        }
        
        # Write to audit log file
        with open(AUDIT_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry, ensure_ascii=False) + '\n')
        
        # Also log to main logger at INFO level
        status = "SUCCESS" if success else "FAILED"
        log_msg = f"[AUDIT] {status} | {event_type} | {action} | User: {username} | IP: {ip_address or 'N/A'}"
        if details:
            log_msg += f" | Details: {json.dumps(details, ensure_ascii=False)}"
        logging.info(log_msg)
        
    except Exception as e:
        # Don't fail if audit logging fails, but log the error
        logging.error(f"Audit logging failed: {e}", exc_info=True)


def get_client_ip(request):
    """Extract client IP from Flask request"""
    if request is None:
        return None
    
    # Try to get real IP (in case of proxy)
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


# Convenience functions for common audit events

def audit_server_add(ip_address, server_id, request=None, success=True):
    """Audit server addition"""
    client_ip = get_client_ip(request) if request else None
    audit_log(
        event_type='DATA_MODIFY',
        action='ADD_SERVER',
        details={'server_ip': ip_address, 'server_id': server_id},
        ip_address=client_ip,
        success=success
    )


def audit_server_delete(server_id, server_ip=None, request=None, success=True):
    """Audit server deletion"""
    client_ip = get_client_ip(request) if request else None
    audit_log(
        event_type='DATA_MODIFY',
        action='DELETE_SERVER',
        details={'server_id': server_id, 'server_ip': server_ip},
        ip_address=client_ip,
        success=success
    )


def audit_server_clear(request=None, project_id=None, count=0, success=True):
    """Audit server clearing"""
    client_ip = get_client_ip(request) if request else None
    details = {'count': count}
    if project_id:
        details['project_id'] = project_id
    audit_log(
        event_type='DATA_MODIFY',
        action='CLEAR_SERVERS',
        details=details,
        ip_address=client_ip,
        success=success
    )


def audit_password_access(server_id, server_ip=None, request=None):
    """Audit password access (decryption)"""
    client_ip = get_client_ip(request) if request else None
    audit_log(
        event_type='DATA_ACCESS',
        action='PASSWORD_ACCESS',
        details={'server_id': server_id, 'server_ip': server_ip},
        ip_address=client_ip,
        success=True
    )


def audit_credential_update(server_id, server_ip=None, request=None, success=True):
    """Audit credential update"""
    client_ip = get_client_ip(request) if request else None
    audit_log(
        event_type='DATA_MODIFY',
        action='UPDATE_CREDENTIALS',
        details={'server_id': server_id, 'server_ip': server_ip},
        ip_address=client_ip,
        success=success
    )


def audit_key_rotation(old_key_id=None, new_key_id=None, servers_updated=0, success=True):
    """Audit key rotation"""
    audit_log(
        event_type='KEY_ROTATION',
        action='ROTATE_ENCRYPTION_KEY',
        details={
            'old_key_id': old_key_id,
            'new_key_id': new_key_id,
            'servers_updated': servers_updated
        },
        success=success
    )


def audit_export(excel_file=None, project_id=None, request=None, success=True):
    """Audit Excel export"""
    client_ip = get_client_ip(request) if request else None
    details = {}
    if excel_file:
        details['file'] = excel_file
    if project_id:
        details['project_id'] = project_id
    audit_log(
        event_type='DATA_ACCESS',
        action='EXPORT_DATA',
        details=details,
        ip_address=client_ip,
        success=success
    )


def audit_scan_start(server_id, server_ip=None, request=None):
    """Audit scan start"""
    client_ip = get_client_ip(request) if request else None
    audit_log(
        event_type='OPERATION',
        action='SCAN_START',
        details={'server_id': server_id, 'server_ip': server_ip},
        ip_address=client_ip,
        success=True
    )


def audit_scan_complete(server_id, server_ip=None, success=True):
    """Audit scan completion"""
    audit_log(
        event_type='OPERATION',
        action='SCAN_COMPLETE',
        details={'server_id': server_id, 'server_ip': server_ip},
        success=success
    )


def audit_project_create(project_id, project_name, request=None, success=True):
    """Audit project creation"""
    client_ip = get_client_ip(request) if request else None
    audit_log(
        event_type='DATA_MODIFY',
        action='CREATE_PROJECT',
        details={'project_id': project_id, 'project_name': project_name},
        ip_address=client_ip,
        success=success
    )


def audit_project_delete(project_id, project_name=None, request=None, success=True):
    """Audit project deletion"""
    client_ip = get_client_ip(request) if request else None
    audit_log(
        event_type='DATA_MODIFY',
        action='DELETE_PROJECT',
        details={'project_id': project_id, 'project_name': project_name},
        ip_address=client_ip,
        success=success
    )



