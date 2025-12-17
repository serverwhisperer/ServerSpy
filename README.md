# 🔍 ServerScout

**Server Inventory Management Tool** - A modern Python web application for automated server scanning and Excel export.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- **🖥️ Server Management** - Add, edit, delete servers with IP, credentials, and OS type
- **📁 Bulk Import** - Import multiple servers from CSV files
- **🔄 Automated Scanning** - Collect hardware/software inventory from Windows (WinRM) and Linux (SSH) servers
- **⚡ Parallel Scanning** - Scan multiple servers simultaneously for faster results
- **📊 Excel Export** - Generate professional Excel reports with 3 sheets (Summary, Inventory, Warnings)
- **🎨 Modern Web UI** - Clean, responsive interface with search, filter, and sort capabilities
- **💾 SQLite Database** - Lightweight, portable data storage

## 📋 Data Collected

ServerScout collects the same data as legacy VBScript inventory systems:

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
- Windows: WinRM enabled on target servers
- Linux: SSH access to target servers

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/serverwhisperer/ServerSpy.git
   cd ServerSpy
   ```

2. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```
   
   Or simply double-click `start.bat` (Windows)

4. **Open in browser:**
   Navigate to `http://localhost:5000`

## 📁 Project Structure

```
ServerScout/
├── backend/
│   ├── app.py              # Flask main application
│   ├── scanner.py          # Scanning logic (Windows + Linux)
│   ├── database.py         # SQLite operations
│   ├── excel_export.py     # Excel generation
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main page
│   ├── style.css           # Styling
│   └── script.js           # Frontend logic
├── data/
│   └── inventory.db        # SQLite database (auto-created)
├── exports/                # Excel export folder
├── build.bat               # PyInstaller build script
├── start.bat               # Quick start script
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

## 📊 Excel Export Format

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
| POST | `/api/servers/bulk` | Bulk import from CSV |
| POST | `/api/scan/:id` | Scan single server |
| POST | `/api/scan-all` | Scan all servers |
| GET | `/api/export/excel` | Download Excel report |
| GET | `/api/stats` | Get server statistics |

## 📝 CSV Import Format

```csv
ip,username,password,os_type
192.168.1.10,Administrator,password123,Windows
192.168.1.20,root,secretpass,Linux
```

## 🏗️ Building Executable

To create a standalone executable:

```bash
# Run build script
build.bat

# Output will be in: backend/dist/ServerScout/
```

## 🛠️ Dependencies

- **Flask** - Web framework
- **Flask-CORS** - Cross-origin resource sharing
- **Paramiko** - SSH client for Linux scanning
- **PyWinRM** - WinRM client for Windows scanning
- **Pandas** - Data manipulation
- **OpenPyXL** - Excel file generation
- **PyInstaller** - Executable packaging

## 📜 License

MIT License - Feel free to use and modify.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

Made with ❤️ by ServerWhisperer
