# ServerScout

Server Inventory Management Tool - A modern desktop application for automated server scanning and Excel export.

Desktop Application - Runs as Electron desktop app, no browser needed.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- Server Management - Add, edit, delete servers with IP, credentials, and OS type
- Bulk Import - Import multiple servers from CSV files
- Automated Scanning - Collect hardware/software inventory from Windows (WinRM) and Linux (SSH) servers
- Parallel Scanning - Scan multiple servers simultaneously for faster results
- Excel Export - Generate professional Excel reports with 3 sheets (Summary, Inventory, Warnings)
- Modern Web UI - Clean, responsive interface with search, filter, and sort capabilities
- Temporary Data Storage - Data is cleared on each startup (session-based)
- HTTPS by Default - All connections encrypted with self-signed certificate
- Desktop App - Electron-based, no browser required

## Data Collected

ServerScout collects the same data as legacy VBScript inventory systems:

- System: Computer Name, IP Address, Domain
- Hardware: Brand, Model, Serial Number, Motherboard
- CPU: Count, Cores, Logical Processors, Model
- Memory: Physical RAM Modules, Total Logical Memory
- Storage: All Disks with Sizes
- Network: IP, Subnet, Gateway, MAC (all adapters)
- OS: Version, Service Pack

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Windows: WinRM enabled on target servers
- Linux: SSH access to target servers

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/serverwhisperer/ServerSpy.git
   cd ServerSpy
   ```

2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Run as Desktop App (Recommended):
   ```bash
   cd electron
   npm install
   npm start
   ```
   
   Or simply double-click `start.bat` (Windows)
   
   Note: Runs as desktop application (Electron), HTTPS enabled by default, self-signed certificate warning is automatically handled, no browser needed.

4. Run as Web App (Development):
   ```bash
   cd backend
   python app.py
   ```
   
   Then open `https://localhost:5000` in browser
   
   Note: Browser will show security warning for self-signed certificate - click "Advanced" > "Continue" (this is normal for localhost)

## Project Structure

```
ServerScout/
├── backend/                 # Python Flask Backend
│   ├── app.py              # Main Flask application (API routes)
│   ├── config.py           # Configuration settings
│   ├── database.py         # SQLite database operations
│   ├── encryption.py       # Password encryption (AES-128)
│   ├── scanner.py          # Server scanning (Windows/Linux)
│   ├── excel_export.py      # Excel report generation
│   └── requirements.txt    # Python dependencies
├── frontend/               # Web Frontend
│   ├── index.html          # Main HTML page
│   ├── style.css           # Styling
│   └── script.js           # JavaScript logic
├── electron/               # Electron Desktop App
│   ├── main.js             # Electron main process
│   ├── package.json        # Node.js dependencies
│   └── icon.ico            # Application icon
├── data/                   # Database files (gitignore)
│   └── inventory.db        # SQLite database (temporary)
├── logs/                   # Log files (gitignore)
├── build-all.bat           # Build script (all versions)
├── start.bat               # Quick start script
└── README.md               # This file
```

See [PROJECT-STRUCTURE.md](PROJECT-STRUCTURE.md) for detailed architecture documentation.

## Security Features

ServerScout implements enterprise-grade security for protecting sensitive credentials:

- Password Encryption: All passwords encrypted with AES-128 (Fernet) - Industry standard
- Key Protection: Encryption keys protected with Windows DPAPI (Windows) or system-derived keys (Linux/Mac)
- HTTPS by Default: All connections encrypted with self-signed certificate (localhost)
- API Security: Passwords never sent in API responses - automatic sanitization
- Memory Safety: Default credentials stored encrypted in memory
- Temporary Data: Database cleared on each startup - no persistent storage
- Secure Logging: Passwords never logged - secure error handling

Security Level: HIGH

See [SECURITY.md](SECURITY.md) for comprehensive security documentation.

## Server Configuration

### Windows (WinRM)

Enable WinRM on target Windows servers:

```powershell
# Run as Administrator
winrm quickconfig
winrm set winrm/config/service/auth @{Basic="true"}
winrm set winrm/config/service @{AllowUnencrypted="true"}
```

### Linux (SSH)

Ensure SSH is enabled and the user has appropriate permissions:

```bash
# For hardware info (dmidecode), user needs sudo access
# Add to /etc/sudoers:
username ALL=(ALL) NOPASSWD: /usr/sbin/dmidecode
```

## Excel Export Format

The generated Excel file contains 3 sheets:

1. Summary - Total servers, online/offline counts, last scan time
2. Inventory - Complete server details in formatted table
3. Warnings - Servers with issues (offline, high disk usage, etc.)

## API Endpoints

### Server Management

- GET `/api/servers` - Get all servers (filtered by project)
- POST `/api/servers` - Add new server
- GET `/api/servers/:id` - Get single server
- DELETE `/api/servers/:id` - Delete server
- PUT `/api/servers/:id/credentials` - Update server credentials
- POST `/api/servers/bulk` - Bulk import from CSV/TXT

### Scanning

- POST `/api/scan/:id` - Scan single server
- POST `/api/scan-all` - Scan all servers (or filtered by project)

### Projects

- GET `/api/projects` - Get all projects
- POST `/api/projects` - Create new project
- GET `/api/projects/:id/servers` - Get servers in project
- PUT `/api/projects/:id` - Rename project
- DELETE `/api/projects/:id` - Delete project

### Export & Stats

- GET `/api/export/excel` - Download Excel report (all servers)
- GET `/api/export/excel/project/:id` - Download Excel report (project)
- GET `/api/export/excel/all-projects` - Download Excel report (all projects)
- GET `/api/stats` - Get server statistics

## CSV Import Format

```csv
ip,username,password,os_type
192.168.1.10,Administrator,password123,Windows
192.168.1.20,root,secretpass,Linux
```

## Electron Desktop App (Primary Method)

ServerScout is designed to run as a desktop application using Electron. This is the recommended way to use the application.

### Prerequisites

- Node.js 18+ (download from https://nodejs.org)
- Python dependencies already installed

### Run as Desktop App

```bash
cd electron
npm install
npm start
```

Or simply double-click `start.bat` (Windows)

Features:
- Native desktop experience
- HTTPS enabled by default
- Self-signed certificate automatically accepted
- No browser needed
- Automatic backend server management

### Build Electron Installer

```bash
cd electron
npm run build
```

Output will be in `electron/dist/`
- Portable: `ServerScout-Portable-*.exe` (no installation needed)
- Installer: `ServerScout-Setup-*.exe` (with installer)

## Building PyInstaller Executable

To create a standalone executable (without Electron):

```bash
# Run build script
build.bat

# Output will be in: backend/dist/ServerScout/
```

## Dependencies

### Backend (Python)

- Flask (3.0+) - Web framework
- Flask-CORS (4.0+) - Cross-origin resource sharing
- Paramiko (3.4+) - SSH client for Linux scanning
- PyWinRM (0.4.3+) - WinRM client for Windows scanning
- Pandas (2.2+) - Data manipulation
- OpenPyXL (3.1+) - Excel file generation
- Cryptography (41.0+) - Password encryption (AES-128)
- PyWin32 (306+) - Windows DPAPI support (Windows only)

### Frontend

- Electron (28.0+) - Desktop application framework
- Node.js (18+) - Runtime for Electron

Install all dependencies:

```bash
cd backend
pip install -r requirements.txt

cd ../electron
npm install
```

## Documentation

Comprehensive documentation available:

- [SECURITY.md](SECURITY.md) - Complete security documentation
- [PROJECT-STRUCTURE.md](PROJECT-STRUCTURE.md) - Architecture and code organization
- [DATABASE-EXPLANATION.md](DATABASE-EXPLANATION.md) - Database usage and purpose
- [ENCRYPTION-KEY-EXPLANATION.md](ENCRYPTION-KEY-EXPLANATION.md) - Encryption key management
- [HTTPS-SETUP.md](HTTPS-SETUP.md) - HTTPS configuration guide
- [BUILD.md](BUILD.md) - Build instructions
- [QUICK-START.md](QUICK-START.md) - Quick start guide
- [CHANGELOG.md](CHANGELOG.md) - Version history

## License

MIT License - Feel free to use and modify.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Important Notes

- Build files are NOT included in repository (too large for GitHub)
- Users can build executables using `build-all.bat`
- See [BUILD.md](BUILD.md) for build instructions
- Build outputs are in `.gitignore`

---

Made with ❤️ by ServerWhisperer
