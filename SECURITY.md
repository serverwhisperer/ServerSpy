# ServerScout - Security Documentation

## Table of Contents

1. [Overview](#overview)
2. [Encryption System](#encryption-system)
3. [Data Protection](#data-protection)
4. [Network Security](#network-security)
5. [Access Control](#access-control)
6. [Risk Analysis](#risk-analysis)
7. [Recommendations and Best Practices](#recommendations-and-best-practices)

---

## Overview

ServerScout is designed with production-ready security features. The system uses a multi-layered security approach to protect critical information such as root/domain admin passwords.

### Security Level: HIGH

**Core Security Principles:**

- Defense in Depth: Multi-layered protection
- Key Management: Secure key management (Windows DPAPI)
- Least Privilege: Minimum privilege principle
- Secure by Default: Secure default configuration
- Data Minimization: Temporary data storage

---

## Encryption System

### 1. Database Encryption

**Feature:** All passwords in the database are encrypted using AES-128 (Fernet) algorithm.

**Technical Details:**

- Algorithm: Industry-standard encryption (AES-128)
- Key Management: Protected with Windows DPAPI (Windows) or system-specific key (Linux/Mac)
- Format: Encrypted and encoded format

**Advantages:**

- Database file can be accessed but passwords cannot be read
- Each password is encrypted separately
- Industry-standard encryption (NIST approved)

### 2. Encryption Key Protection

**Windows Environment:**

- Key is protected with Windows DPAPI (Data Protection API)
- Key can only be decrypted by the same Windows user account
- Advantage: Key is linked to Windows user profile
- Security: Key file is stored in a secure location in user profile

**Linux/Mac Environment:**

- Key is encrypted with system-specific master key
- Master key is derived from user and system information
- Key file is readable only by owner (600 permissions)
- Security: Key is specific to system and user

### 3. Memory Security

**Feature:** Default credentials (default passwords) are also stored encrypted in memory.

**Technical Details:**

- Default credentials dictionary stores passwords encrypted
- Decrypted during use
- Memory is cleared when application closes

**Advantages:**

- Passwords cannot be read via process memory dump
- Only encrypted format exists in memory

---

## Data Protection

### 1. API Response Security

**Feature:** Passwords are never sent in API responses.

**Implementation:**

- All API endpoints use `sanitize_server_data()` function
- Password field is automatically removed from response
- Only `has_password` boolean flag is sent

**Affected Endpoints:**

- `GET /api/servers` - All servers
- `GET /api/servers/:id` - Single server
- `GET /api/projects/:id/servers` - Project servers
- `GET /api/credentials` - Default credentials

### 2. Database Access Control

**Feature:** Database file access control.

**Locations:**

- Development: Temporary database in application directory
- Production: Secure location in user profile

**Protection:**

- Database file is only written by the application
- Windows: User-based access control
- Linux: File permissions (600 - owner only)

### 3. Log Security

**Feature:** Passwords are never logged in log files.

**Implementation:**

- All log messages do not contain passwords
- Error messages do not show password information
- Log files: `%APPDATA%\ServerScout\logs\`

---

## Network Security

### 1. HTTPS Support

**Feature:** HTTPS is active by default - all connections are encrypted.

**Configuration:**

- HTTPS (Default): `https://127.0.0.1:5000` (self-signed certificate)
- HTTP (Optional): Can be disabled with `USE_HTTPS=false` environment variable
- Production: Use real SSL certificate (Let's Encrypt, corporate certificate)

**Security Features:**

- All API traffic is encrypted (HTTPS)
- Self-signed certificate is safe for localhost
- Electron automatically accepts self-signed certificate
- Can be bypassed in browser with "Advanced" > "Continue" (normal for localhost)

**Production Deployment:**

- Real SSL certificate should be used in production
- Self-signed certificate is only suitable for localhost/development
- See `app.py` file for SSL certificate configuration

### 2. Localhost Binding

**Feature:** Backend server runs on `localhost` by default.

**Configuration:**

- HTTP: `0.0.0.0:5000` (all interfaces)
- HTTPS: `127.0.0.1:5000` (localhost only, more secure)

**Security Note:**

- Application runs on localhost so network traffic is local only
- HTTPS provides extra security layer

### 3. CORS (Cross-Origin Resource Sharing)

**Feature:** CORS is active, but safe for localhost.

**Configuration:**

- `Flask-CORS` is active
- Localhost connections are allowed

**Production Recommendation:**

- Restrict CORS to trusted domains only
- Use HTTPS (now supported)

### 4. Scanning Protocols

**Windows (WinRM):**

- Port: 5985 (HTTP) or 5986 (HTTPS)
- Authentication: NTLM
- Security: Password is sent over network (WinRM protocol)

**Linux (SSH):**

- Port: 22
- Authentication: Username/Password
- Security: SSH protocol encrypts passwords (SSH encryption)

---

## Access Control

### 1. Application Access

**Current Status:**

- Anyone can access when application is opened
- No user authentication

**Recommendations:**

- Only trusted users should run the application
- Windows: User-based access control
- Restrict access to database file

### 2. Database Access

**Protection:**

- Database file contains encrypted passwords
- Key file is protected separately
- Both are linked to the same user account

**Risk:**

- If Windows user account is compromised, key can be decrypted
- Recommendation: Use strong Windows passwords

### 3. File Permissions

**Windows:**

- AppData folder is user-based
- Other users cannot access

**Linux:**

- Key file: `600` (owner read/write only)
- Database: `600` (owner read/write only)

---

## Risk Analysis

### High Risk Scenarios

**Database File Access**

- Description: Physical access to database file
- Impact: Passwords are encrypted, but can be decrypted with key
- Mitigation: Protect key file separately

**Windows User Account Compromise**

- Description: User account is hacked
- Impact: Key can be decrypted
- Mitigation: Strong Windows passwords, 2FA

**Memory Dump**

- Description: Process memory dump is taken
- Impact: Passwords are encrypted in memory, but can be decrypted
- Mitigation: Memory is cleared when application closes

**Network Sniffing**

- Description: Localhost traffic is monitored
- Impact: Password is sent over HTTP
- Mitigation: Use HTTPS in production

### Medium Risk Scenarios

**Log Files**

- Description: Access to log files
- Impact: Passwords are not logged
- Mitigation: Protect log files

**Excel Export**

- Description: Access to Excel files
- Impact: No passwords in Excel
- Mitigation: Store Excel files securely

**Backup Files**

- Description: Access to backups
- Impact: Database is encrypted
- Mitigation: Encrypt backups

### Low Risk Scenarios

**Frontend Access**

- Description: Access to web interface
- Impact: Runs on localhost
- Mitigation: Only trusted users

**API Access**

- Description: Access to API endpoints
- Impact: Password is not sent
- Mitigation: Localhost binding

---

## Recommendations and Best Practices

### 1. Usage Recommendations

**DO:**

- Only trusted, authorized users should run the application
- Use strong passwords on Windows user accounts
- Encrypt backups of database and key files
- Close the application when not in use
- Use HTTPS in production (optional)
- Regularly clean log files

**DON'T:**

- Run the application on shared computers
- Store database file on network share
- Copy key file to another location
- Manually write passwords to database
- Run the application on internet-exposed server

### 2. Production Deployment

**Default Configuration (HTTPS):**

```bash
# Electron (Recommended)
cd electron
npm start
# Automatically starts with HTTPS

# Python Backend (Development)
cd backend
python app.py
# HTTPS is active by default
```

**Switch to HTTP (Development Only):**

```bash
set USE_HTTPS=false
python backend/app.py
# http://127.0.0.1:5000
```

**Real SSL Certificate for Production:**

- Must use real SSL certificate in production
- Let's Encrypt or corporate certificate can be used
- See `app.py` file for SSL certificate configuration

**Note:** Must use real SSL certificate in production. Self-signed certificate is only suitable for localhost/development.

### 3. Backup Strategy

**IMPORTANT:** Data is temporary - database is cleared on each startup!

**Why Backup?**

- Database file can be corrupted (disk error, file corruption)
- Can be accidentally deleted
- Data loss can occur in case of system crash

**Is Backup Required?**

**NO!** Backup is not required because data is temporary:
- Database is cleared on each startup
- Data is only kept during session
- Data is deleted after Excel export

**If you want to save data:**

- Backup Excel export files (no passwords included)
- Scan results are stored in Excel
- No need for database backup (temporary data)

**Note:** Encryption key file is automatically managed (Windows DPAPI). Manual backup is not required.

### 4. Monitoring and Audit

**Recommendations:**

- Regularly check log files
- Add monitoring for suspicious activity
- Log user access (optional)
- Audit database access

### 5. Security Updates

**Recommendations:**

- Regularly update Python and libraries
- Keep `cryptography` library up to date
- Track security vulnerabilities
- Perform penetration testing (optional)

---

## Security Summary

### Strong Points

1. Database Encryption: All passwords encrypted with AES-128
2. Key Protection: Key protected with Windows DPAPI
3. Memory Security: Default credentials encrypted in memory
4. API Security: No password in responses
5. Industry Standard: NIST approved encryption algorithms

### Areas for Improvement

1. HTTPS: Production HTTPS support - COMPLETED
2. Authentication: User authentication can be added
3. Audit Logging: Detailed audit log can be added
4. Key Rotation: Key rotation mechanism can be added
5. 2FA: Two-factor authentication can be added
6. Production SSL: Real SSL certificate usage (Let's Encrypt, etc.)

---

## Technical Details

### Encryption Flow

1. User enters password (UI)
2. Frontend → Backend API (over HTTPS)
3. `encrypt_password()` function is called
4. Encryption with Fernet (AES-128)
5. Base64 encoding
6. Saved to database (encrypted format)
7. Decrypted with `decrypt_password()` during read
8. Password field removed from API response (`sanitize_server_data`)

### Key Management Principle

**Windows Environment:**

- Encryption key is protected with Windows DPAPI (Data Protection API)
- Key can only be decrypted by the same Windows user account
- Key file is stored in user profile
- Security: Key is linked to Windows user authentication

**Linux/Mac Environment:**

- Encryption key is encrypted with system-specific master key
- Master key is derived from user and system information
- Key file is readable only by owner (600 permissions)
- Security: Key is specific to system and user

**Note:** Detailed implementation information is not shared for security reasons.

### Security Layers

- Layer 1: HTTPS (Transport Security) - All traffic encrypted
- Layer 2: Database Encryption (Storage Security) - Passwords encrypted with AES-128
- Layer 3: Key Protection (Key Security) - Key protected with Windows DPAPI
- Layer 4: API Sanitization (Response Security) - No password in responses
- Layer 5: Memory Safety (Runtime Security) - Default creds encrypted in memory
- Layer 6: Temporary Data (Data Lifecycle) - Cleared on each startup

---

## Security Tests

### Test Scenarios

**1. Database File Access Test:**

- Even if database file is accessed, passwords are stored in encrypted format
- Passwords cannot be decrypted without encryption key
- Result: Passwords are protected even if database is compromised

**2. Key File Access Test:**

- Even if key file is copied to another system, it cannot be decrypted
- Windows DPAPI: Key is linked to user account
- Linux/Mac: Key is specific to system and user
- Result: Key file alone is not sufficient

**3. API Response Test:**

- Password field is not found in API responses
- Only `has_password` boolean flag is sent
- Result: API traffic is secure

**4. Memory Dump Test:**

- Even if process memory dump is taken, default credentials are stored in encrypted format
- Result: Passwords cannot be read via memory dump

## Support and Questions

For security-related questions:

- General Security: This documentation
- Key Management: `ENCRYPTION-KEY-EXPLANATION.md`
- Database Usage: `DATABASE-EXPLANATION.md`

**Note:** Detailed implementation code and security mechanisms are not shared for security reasons. Please contact project maintainers for security questions.

---

## Security Summary Table

- Database Encryption: Active - AES-128 (Fernet)
- Key Protection: Active - Windows DPAPI
- HTTPS: Default - Self-signed (localhost)
- API Sanitization: Active - No password in responses
- Memory Security: Active - Default creds encrypted
- Data Persistence: None - Cleared on each startup
- Log Security: Active - Passwords not logged
- Excel Export Security: Active - No passwords in export

---

**Last Update:** 2025-12-21  
**Security Level:** HIGH  
**Production Ready:** YES  
**HTTPS:** Default  
**Data Persistence:** Temporary (for security)
