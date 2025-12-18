"""
Scanner module for ServerScout
Handles Windows (WinRM) and Linux (SSH) server scanning
"""

import paramiko
import winrm
import socket
import json
from concurrent.futures import ThreadPoolExecutor, as_completed


class WindowsScanner:
    """Scanner for Windows servers using WinRM"""
    
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.session = None
    
    def connect(self):
        """Establish WinRM connection"""
        try:
            self.session = winrm.Session(
                f'http://{self.ip}:5985/wsman',
                auth=(self.username, self.password),
                transport='ntlm'
            )
            # Test connection
            result = self.session.run_ps('$env:COMPUTERNAME')
            if result.status_code != 0:
                raise Exception("Failed to connect via WinRM")
            return True
        except Exception as e:
            # Try HTTPS
            try:
                self.session = winrm.Session(
                    f'https://{self.ip}:5986/wsman',
                    auth=(self.username, self.password),
                    transport='ntlm',
                    server_cert_validation='ignore'
                )
                result = self.session.run_ps('$env:COMPUTERNAME')
                if result.status_code != 0:
                    raise Exception("Failed to connect via WinRM")
                return True
            except Exception as e2:
                raise Exception(f"WinRM connection failed: {str(e)} / {str(e2)}")
    
    def run_powershell(self, command):
        """Execute a PowerShell command and return output"""
        try:
            result = self.session.run_ps(command)
            if result.status_code == 0:
                return result.std_out.decode('utf-8', errors='ignore').strip()
            return None
        except Exception:
            return None
    
    def scan(self):
        """Perform full scan of Windows server"""
        data = {}
        
        # Computer Name
        data['hostname'] = self.run_powershell('$env:COMPUTERNAME')
        
        # Domain
        data['domain'] = self.run_powershell('(Get-WmiObject Win32_ComputerSystem).Domain')
        
        # Brand, Model, Serial
        system_info = self.run_powershell('''
            $p = Get-WmiObject Win32_ComputerSystemProduct
            @{Vendor=$p.Vendor; Name=$p.Name; Serial=$p.IdentifyingNumber} | ConvertTo-Json
        ''')
        if system_info:
            try:
                info = json.loads(system_info)
                data['brand'] = info.get('Vendor', '')
                data['model'] = info.get('Name', '')
                data['serial'] = info.get('Serial', '')
            except:
                pass
        
        # Motherboard
        mb_info = self.run_powershell('''
            $mb = Get-WmiObject Win32_BaseBoard
            "$($mb.Manufacturer) - $($mb.Product)"
        ''')
        data['motherboard'] = mb_info
        
        # CPU Info
        cpu_info = self.run_powershell('''
            $cpus = Get-WmiObject Win32_Processor
            $count = ($cpus | Measure-Object).Count
            $cores = ($cpus | Measure-Object -Property NumberOfCores -Sum).Sum
            $logical = ($cpus | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum
            $model = ($cpus | Select-Object -First 1).Name
            @{Count=$count; Cores=$cores; Logical=$logical; Model=$model} | ConvertTo-Json
        ''')
        if cpu_info:
            try:
                cpu = json.loads(cpu_info)
                data['cpu_count'] = cpu.get('Count', 0)
                data['cpu_cores'] = str(cpu.get('Cores', ''))
                data['cpu_logical_processors'] = str(cpu.get('Logical', ''))
                data['cpu_model'] = cpu.get('Model', '')
            except:
                pass
        
        # Physical Memory (RAM modules)
        ram_physical = self.run_powershell('''
            $ram = Get-WmiObject Win32_PhysicalMemory
            $modules = $ram | ForEach-Object { [math]::Round($_.Capacity / 1GB, 0) }
            $modules -join "GB + "
        ''')
        if ram_physical:
            data['ram_physical'] = ram_physical + "GB"
        
        # Logical Memory (Total RAM in MB)
        ram_logical = self.run_powershell('''
            $os = Get-WmiObject Win32_OperatingSystem
            [math]::Round($os.TotalVisibleMemorySize / 1024, 0)
        ''')
        if ram_logical:
            try:
                data['ram_logical'] = int(ram_logical)
            except:
                data['ram_logical'] = 0
        
        # Disk Info
        disk_info = self.run_powershell('''
            $disks = Get-WmiObject Win32_DiskDrive | Select Index, Size, Model
            $result = $disks | ForEach-Object {
                $sizeGB = [math]::Round($_.Size / 1GB, 0)
                "Disk $($_.Index): $($_.Model) - ${sizeGB}GB"
            }
            $result -join "; "
        ''')
        data['disk_info'] = disk_info
        
        # Network Info
        network_info = self.run_powershell('''
            $adapters = Get-WmiObject Win32_NetworkAdapterConfiguration | Where-Object { $_.IPEnabled -eq $true }
            $result = @()
            foreach ($a in $adapters) {
                $ip = if ($a.IPAddress) { $a.IPAddress[0] } else { "" }
                $subnet = if ($a.IPSubnet) { $a.IPSubnet[0] } else { "" }
                $gateway = if ($a.DefaultIPGateway) { $a.DefaultIPGateway[0] } else { "" }
                $mac = $a.MACAddress
                $result += @{IP=$ip; Subnet=$subnet; Gateway=$gateway; MAC=$mac}
            }
            $result | ConvertTo-Json
        ''')
        if network_info:
            try:
                networks = json.loads(network_info)
                if isinstance(networks, dict):
                    networks = [networks]
                if networks and len(networks) > 0:
                    primary = networks[0]
                    data['network_primary'] = f"IP: {primary.get('IP', '')} | Subnet: {primary.get('Subnet', '')} | Gateway: {primary.get('Gateway', '')} | MAC: {primary.get('MAC', '')}"
                    data['network_all'] = json.dumps(networks)
            except:
                pass
        
        # OS Version
        os_info = self.run_powershell('''
            $os = Get-WmiObject Win32_OperatingSystem
            @{Caption=$os.Caption; ServicePack=$os.CSDVersion} | ConvertTo-Json
        ''')
        if os_info:
            try:
                os_data = json.loads(os_info)
                data['os_version'] = os_data.get('Caption', '')
                data['service_pack'] = os_data.get('ServicePack', '') or 'N/A'
            except:
                pass
        
        data['status'] = 'Online'
        return data


class LinuxScanner:
    """Scanner for Linux servers using SSH"""
    
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.client = None
    
    def connect(self):
        """Establish SSH connection"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                self.ip,
                username=self.username,
                password=self.password,
                timeout=30
            )
            return True
        except Exception as e:
            raise Exception(f"SSH connection failed: {str(e)}")
    
    def run_command(self, command):
        """Execute a command and return output"""
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=30)
            return stdout.read().decode('utf-8', errors='ignore').strip()
        except Exception:
            return None
    
    def close(self):
        """Close SSH connection"""
        if self.client:
            self.client.close()
    
    def scan(self):
        """Perform full scan of Linux server"""
        data = {}
        
        # Hostname - try multiple methods
        hostname = self.run_command('hostname 2>/dev/null')
        if not hostname:
            hostname = self.run_command('cat /etc/hostname 2>/dev/null')
        if not hostname:
            hostname = self.run_command('uname -n 2>/dev/null')
        if not hostname:
            hostname = self.run_command('hostnamectl --static 2>/dev/null')
        data['hostname'] = hostname.strip() if hostname else self.ip
        
        # Domain
        domain = self.run_command('dnsdomainname 2>/dev/null')
        if not domain:
            domain = self.run_command('hostname -d 2>/dev/null')
        if not domain:
            domain = self.run_command('cat /etc/resolv.conf 2>/dev/null | grep "^search" | awk \'{print $2}\'')
        data['domain'] = domain.strip() if domain else 'N/A'
        
        # Brand/Model/Serial (requires root/sudo for dmidecode)
        data['brand'] = self.run_command('sudo dmidecode -s system-manufacturer 2>/dev/null') or 'N/A'
        data['model'] = self.run_command('sudo dmidecode -s system-product-name 2>/dev/null') or 'N/A'
        data['serial'] = self.run_command('sudo dmidecode -s system-serial-number 2>/dev/null') or 'N/A'
        
        # Motherboard
        mb_manufacturer = self.run_command('sudo dmidecode -s baseboard-manufacturer 2>/dev/null') or ''
        mb_product = self.run_command('sudo dmidecode -s baseboard-product-name 2>/dev/null') or ''
        data['motherboard'] = f"{mb_manufacturer} - {mb_product}".strip(' -') or 'N/A'
        
        # CPU Info
        cpu_count = self.run_command('grep -c "^processor" /proc/cpuinfo 2>/dev/null')
        try:
            data['cpu_count'] = int(cpu_count) if cpu_count else 0
        except:
            data['cpu_count'] = 0
        
        cores = self.run_command('lscpu 2>/dev/null | grep "Core(s) per socket" | awk \'{print $4}\'')
        sockets = self.run_command('lscpu 2>/dev/null | grep "Socket(s)" | awk \'{print $2}\'')
        try:
            total_cores = int(cores or 0) * int(sockets or 1)
            data['cpu_cores'] = str(total_cores)
        except:
            data['cpu_cores'] = cores or 'N/A'
        
        logical = self.run_command('nproc 2>/dev/null')
        data['cpu_logical_processors'] = logical or 'N/A'
        
        cpu_model = self.run_command('lscpu 2>/dev/null | grep "Model name" | cut -d: -f2')
        data['cpu_model'] = cpu_model.strip() if cpu_model else 'N/A'
        
        # Physical Memory (RAM modules)
        ram_modules = self.run_command('sudo dmidecode -t memory 2>/dev/null | grep "Size:" | grep -v "No Module" | awk \'{print $2 $3}\'')
        if ram_modules:
            modules_list = [m for m in ram_modules.split('\n') if m and 'No' not in m]
            data['ram_physical'] = ' + '.join(modules_list) if modules_list else 'N/A'
        else:
            data['ram_physical'] = 'N/A'
        
        # Logical Memory (Total RAM in MB)
        ram_total = self.run_command('free -m 2>/dev/null | grep Mem | awk \'{print $2}\'')
        try:
            data['ram_logical'] = int(ram_total) if ram_total else 0
        except:
            data['ram_logical'] = 0
        
        # Disk Info
        disk_info = self.run_command('lsblk -d -o NAME,SIZE,MODEL 2>/dev/null | grep -v "loop" | tail -n +2')
        if disk_info:
            disks = []
            for line in disk_info.split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        size = parts[1]
                        model = ' '.join(parts[2:]) if len(parts) > 2 else ''
                        disks.append(f"{name}: {model} - {size}".strip(' -'))
            data['disk_info'] = '; '.join(disks) if disks else 'N/A'
        else:
            data['disk_info'] = 'N/A'
        
        # Network Info
        ip_info = self.run_command('ip -4 addr show 2>/dev/null | grep "inet " | grep -v "127.0.0.1"')
        gateway = self.run_command('ip route 2>/dev/null | grep default | awk \'{print $3}\'')
        mac_info = self.run_command('ip link show 2>/dev/null | grep "link/ether" | awk \'{print $2}\'')
        
        if ip_info:
            lines = ip_info.strip().split('\n')
            networks = []
            macs = mac_info.split('\n') if mac_info else []
            
            for i, line in enumerate(lines):
                parts = line.strip().split()
                if len(parts) >= 2:
                    ip_subnet = parts[1].split('/')
                    ip = ip_subnet[0]
                    subnet = ip_subnet[1] if len(ip_subnet) > 1 else ''
                    mac = macs[i] if i < len(macs) else ''
                    networks.append({
                        'IP': ip,
                        'Subnet': subnet,
                        'Gateway': gateway or '',
                        'MAC': mac
                    })
            
            if networks:
                primary = networks[0]
                data['network_primary'] = f"IP: {primary['IP']} | Subnet: {primary['Subnet']} | Gateway: {primary['Gateway']} | MAC: {primary['MAC']}"
                data['network_all'] = json.dumps(networks)
        else:
            data['network_primary'] = 'N/A'
            data['network_all'] = '[]'
        
        # OS Version
        os_version = self.run_command('cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d= -f2 | tr -d \'"\'')
        if not os_version:
            os_version = self.run_command('cat /etc/redhat-release 2>/dev/null')
        data['os_version'] = os_version or 'N/A'
        data['service_pack'] = 'N/A'  # Linux doesn't have service packs
        
        data['status'] = 'Online'
        return data


def check_port(ip, port, timeout=3):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False


def scan_server(server):
    """
    Scan a single server based on OS type
    
    Args:
        server: dict with keys: id, ip, username, password, os_type
    
    Returns:
        dict with scan results or error status
    """
    ip = server['ip']
    username = server['username']
    password = server['password']
    os_type = server['os_type'].lower()
    
    try:
        if os_type == 'windows':
            # Check if WinRM ports are accessible
            if not check_port(ip, 5985) and not check_port(ip, 5986):
                return {
                    'id': server['id'],
                    'status': 'Offline',
                    'error': 'WinRM ports (5985/5986) not accessible'
                }
            
            scanner = WindowsScanner(ip, username, password)
            scanner.connect()
            result = scanner.scan()
            result['id'] = server['id']
            return result
            
        elif os_type == 'linux':
            # Check if SSH port is accessible
            if not check_port(ip, 22):
                return {
                    'id': server['id'],
                    'status': 'Offline',
                    'error': 'SSH port (22) not accessible'
                }
            
            scanner = LinuxScanner(ip, username, password)
            scanner.connect()
            result = scanner.scan()
            scanner.close()
            result['id'] = server['id']
            return result
            
        else:
            return {
                'id': server['id'],
                'status': 'Offline',
                'error': f'Unknown OS type: {os_type}'
            }
            
    except Exception as e:
        return {
            'id': server['id'],
            'status': 'Offline',
            'error': str(e)
        }


def scan_all_servers(servers, max_workers=10):
    """
    Scan multiple servers in parallel
    
    Args:
        servers: list of server dicts
        max_workers: number of parallel workers
    
    Returns:
        list of scan results
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_server = {
            executor.submit(scan_server, server): server
            for server in servers
        }
        
        for future in as_completed(future_to_server):
            server = future_to_server[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    'id': server['id'],
                    'ip': server['ip'],
                    'status': 'Offline',
                    'error': str(e)
                })
    
    return results

