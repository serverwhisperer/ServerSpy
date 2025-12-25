# ServerScout - Security Documentation

## Quick Summary

ServerScout implements enterprise-grade security for protecting sensitive server credentials. All passwords are encrypted using AES-128 (Fernet) and stored securely. The encryption key is protected with Windows DPAPI on Windows systems, or system-specific keys on Linux/Mac. Passwords are never sent in API responses, never logged, and the database is cleared on each application startup for maximum security.

**Security Level:** HIGH  
**Production Ready:** YES  
**HTTPS:** Enabled by default  
**Data Persistence:** Temporary (cleared on startup)

---

## Table of Contents

1. [Overview](#overview)
2. [Encryption System](#encryption-system)
3. [Data Protection](#data-protection)
4. [Network Security](#network-security)
5. [Access Control](#access-control)
6. [Risk Analysis](#risk-analysis)
7. [Best Practices](#best-practices)

---

## Overview

ServerScout uses a multi-layered security approach to protect critical information such as root/domain admin passwords.

**Core Security Principles:**

- Defense in Depth: Multi-layered protection
- Key Management: Secure key management (Windows DPAPI)
- Least Privilege: Minimum privilege principle
- Secure by Default: Secure default configuration
- Data Minimization: Temporary data storage

---

## Encryption System

### Database Encryption

All passwords in the database are encrypted using AES-128 (Fernet) algorithm. The encryption key is protected with Windows DPAPI on Windows systems, or system-specific master keys on Linux/Mac.

**Key Points:**

- Industry-standard encryption (NIST approved)
- Each password encrypted separately
- Database file can be accessed but passwords cannot be read without the key

### Key Protection

**Windows:** Key protected with Windows DPAPI, can only be decrypted by the same Windows user account.

**Linux/Mac:** Key encrypted with system-specific master key derived from user and system information. Key file has 600 permissions (owner only).

### Memory Security

Default credentials are stored encrypted in memory. Passwords cannot be read via process memory dump.

---

## Data Protection

### API Response Security

Passwords are never sent in API responses. All endpoints use `sanitize_server_data()` function which automatically removes password fields. Only `has_password` boolean flag is sent.

**Affected Endpoints:** All server and credential endpoints.

### Database Access Control

Database file is stored in user profile (Windows) or application directory (Linux). File permissions restrict access to owner only.

### Log Security

Passwords are never logged. All log messages and error messages exclude password information.

---

## Network Security

### HTTPS Support

HTTPS is active by default. All connections are encrypted with self-signed certificate for localhost. For production, use real SSL certificate (Let's Encrypt, corporate certificate).

**Configuration:**

- Default: `https://127.0.0.1:5000`
- HTTP (dev only): Set `USE_HTTPS=false` environment variable

### Localhost Binding

Backend server runs on `localhost` by default. Network traffic is local only, providing additional security layer.

### CORS

CORS is active but safe for localhost. For production, restrict CORS to trusted domains only.

### Scanning Protocols

**Windows (WinRM):** Port 5985/5986, NTLM authentication  
**Linux (SSH):** Port 22, SSH encryption

---

## Access Control

### Application Access

No built-in user authentication. Application relies on Windows user-based access control. Only trusted users should run the application.

### Database Access

Database file contains encrypted passwords. Key file is protected separately. Both are linked to the same user account. If Windows user account is compromised, key can be decrypted - use strong Windows passwords.

### File Permissions

**Windows:** AppData folder is user-based, other users cannot access.  
**Linux:** Key file and database have 600 permissions (owner read/write only).

---

## Risk Analysis

### High Risk Scenarios

- **Database File Access:** Passwords encrypted but can be decrypted with key. Mitigation: Protect key file separately.
- **Windows User Account Compromise:** Key can be decrypted. Mitigation: Strong Windows passwords, 2FA.
- **Memory Dump:** Passwords encrypted in memory but can be decrypted. Mitigation: Memory cleared on application close.
- **Network Sniffing:** Password sent over HTTP. Mitigation: Use HTTPS in production.

### Medium Risk Scenarios

- **Log Files:** Passwords not logged. Mitigation: Protect log files.
- **Excel Export:** No passwords in Excel. Mitigation: Store Excel files securely.
- **Backup Files:** Database encrypted. Mitigation: Encrypt backups.

### Low Risk Scenarios

- **Frontend Access:** Runs on localhost. Mitigation: Only trusted users.
- **API Access:** Password not sent. Mitigation: Localhost binding.

---

## Best Practices

### Usage Recommendations

**DO:**

- Only trusted, authorized users should run the application
- Use strong passwords on Windows user accounts
- Close the application when not in use
- Use HTTPS in production
- Regularly clean log files

**DON'T:**

- Run on shared computers
- Store database file on network share
- Copy key file to another location
- Run on internet-exposed server

### Production Deployment

**Default (HTTPS):**

```bash
cd electron
npm start
```

**Real SSL Certificate:**

For production, use real SSL certificate (Let's Encrypt, corporate certificate). See `app.py` for configuration.

### Backup Strategy

**IMPORTANT:** Data is temporary - database cleared on each startup!

Backup is not required because data is temporary. If you want to save data, backup Excel export files (no passwords included).

### Security Updates

- Regularly update Python and libraries
- Keep `cryptography` library up to date
- Track security vulnerabilities

---

## Security Summary

**Active Features:**

- Database Encryption: AES-128 (Fernet)
- Key Protection: Windows DPAPI
- HTTPS: Default (self-signed for localhost)
- API Sanitization: No password in responses
- Memory Security: Default creds encrypted
- Log Security: Passwords not logged
- Excel Export Security: No passwords in export

**Areas for Future Improvement:**

- User authentication
- Audit logging
- Key rotation
- Two-factor authentication

---

## Support

For security-related questions:

- General Security: This documentation
- Key Management: `ENCRYPTION-KEY-EXPLANATION.md`
- Database Usage: `DATABASE-EXPLANATION.md`

**Note:** Detailed implementation code is not shared for security reasons. Contact project maintainers for security questions.

---

**Last Update:** 2025-12-21  
**Security Level:** HIGH  
**Production Ready:** YES




