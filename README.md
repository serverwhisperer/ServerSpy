# 🔍 ServerScout

**Server Inventory Management Tool** - A modern Python web application for automated server scanning and Excel export.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![Electron](https://img.shields.io/badge/Electron-28-9feaf9.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- **🖥️ Server Management** - Add, edit, delete servers with IP, credentials, and OS type
- **📁 Bulk Import** - Import multiple servers from TXT files (IP + W/L for OS type)
- **🔄 Automated Scanning** - Collect hardware/software inventory from Windows (WinRM) and Linux (SSH) servers
- **⚡ Parallel Scanning** - Scan multiple servers simultaneously for faster results
- **🔍 Auto OS Detection** - Automatically detect Windows/Linux based on open ports (SSH/WinRM)
- **📊 Excel Export** - Generate professional Excel reports with 3 sheets (Summary, Inventory, Warnings)
- **🎨 Modern Web UI** - Clean, responsive dark theme interface with search, filter, and sort
- **💻 Desktop App** - Electron-based native desktop application
- **📦 Standalone Build** - Single installer with all dependencies bundled

## 📋 Data Collected

ServerScout collects comprehensive server inventory data:

| Category | Data Points |
|----------|-------------|
| **System** | Computer Name, IP Address, Domain |
| **Hardware** | Brand, Model, Serial Number, Motherboard |
| **CPU** | Count, Cores, Logical Processors, Model |
| **Memory** | Physical RAM Modules, Total Logical Memory |
| **Storage** | All Disks with Sizes |
| **Network** | IP, Subnet, Gateway, MAC (all adapters) |
| **OS** | Version, Service Pack |

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18+ (for Electron app)
- Windows: WinRM enabled on target servers
- Linux: SSH access to target servers

### Option 1: Run as Web App

```bash
# Clone the repository
git clone https://github.com/serverwhisperer/ServerSpy.git
cd ServerSpy

# Install dependencies
cd backend
pip install -r requirements.txt

# Run
python app.py
```

Or simply double-click `start.bat` (Windows)

### Option 2: Run as Desktop App (Electron)

```bash
cd electron
npm install
npm start
```

Or double-click `electron/start-electron.bat`

## 📦 Building Standalone Application

Build a complete installer that users can run without installing Python:

### Quick Build (Windows)

```bash
# Run from project root
build-all.bat
```

This will:
1. Install Python dependencies
2. Build Python backend with PyInstaller
3. Install Node.js dependencies
4. Build Electron app with installer

**Output files in `electron/dist/`:**
- `ServerScout Setup x.x.x.exe` - Windows Installer
- `ServerScout-Portable-x.x.x.exe` - Portable version (no installation needed)

### Manual Build Steps

**Step 1: Build Python Backend**
```bash
cd backend
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm serverscout.spec
```

**Step 2: Build Electron App**
```bash
cd electron
npm install
npm run build
```

## 📁 Project Structure

```
ServerScout/
├── backend/
│   ├── app.py              # Flask main application
│   ├── scanner.py          # Scanning logic (Windows + Linux)
│   ├── database.py         # In-memory data storage
│   ├── excel_export.py     # Excel generation
│   ├── serverscout.spec    # PyInstaller spec file
│   ├── requirements.txt    # Python dependencies
│   └── build-backend.bat   # Backend build script
├── electron/
│   ├── main.js             # Electron main process
│   ├── package.json        # Electron config & dependencies
│   ├── start-electron.bat  # Quick start script
│   └── dist/               # Build output (installers)
├── frontend/
│   ├── index.html          # Main page
│   ├── style.css           # Dark theme styling
│   ├── script.js           # Frontend logic
│   └── logo.png            # App logo
├── build-all.bat           # Full build script
├── start.bat               # Quick start (web)
└── README.md               # This file
```

## 🔧 Server Configuration

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

## 📥 Bulk Import Format

Import servers from a TXT file with this format:

```
192.168.1.10 W        # Windows server
192.168.1.20 L        # Linux server
server.domain.com W   # Hostname with OS type
192.168.1.30          # Auto-detect OS
```

- `W` = Windows
- `L` = Linux
- No letter = Auto-detect based on ports (22=SSH/Linux, 5985/5986=WinRM/Windows)

## 📊 Excel Export

The generated Excel file contains 3 sheets:

1. **Summary** - Total servers, online/offline counts, last scan time
2. **Inventory** - Complete server details in formatted table
3. **Warnings** - Servers with issues (offline, high disk usage, etc.)

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/servers` | Get all servers |
| POST | `/api/servers` | Add new server |
| DELETE | `/api/servers/:id` | Delete server |
| DELETE | `/api/servers/clear` | Clear all servers |
| POST | `/api/servers/bulk` | Bulk import |
| POST | `/api/scan/:id` | Scan single server |
| POST | `/api/scan-all` | Scan all servers |
| GET | `/api/export/excel` | Download Excel report |
| GET | `/api/stats` | Get server statistics |
| POST | `/api/credentials` | Set default credentials |
| GET | `/api/credentials` | Get saved credentials |

## 🛠️ Dependencies

### Python
- **Flask** - Web framework
- **Flask-CORS** - Cross-origin resource sharing
- **Paramiko** - SSH client for Linux scanning
- **PyWinRM** - WinRM client for Windows scanning
- **Pandas** - Data manipulation
- **OpenPyXL** - Excel file generation
- **PyInstaller** - Executable packaging

### Node.js
- **Electron** - Desktop app framework
- **electron-builder** - App packaging & installer creation

## 📜 License

MIT License - Feel free to use and modify.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

Made with ❤️ by [ServerWhisperer](https://github.com/serverwhisperer)
