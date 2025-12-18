/**
 * ServerScout - Frontend JavaScript
 * Server Inventory Management Tool
 */

// Global state
let servers = [];
let filteredServers = [];
let sortColumn = 'hostname';
let sortDirection = 'asc';

// API Base URL
const API_BASE = '';

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    loadServers();
    loadStats();
});

// ==================== API CALLS ====================

async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API Error:', error);
        showToast('Connection error. Please check if the server is running.', 'error');
        throw error;
    }
}

async function loadServers() {
    try {
        const data = await apiCall('/api/servers');
        if (data.success) {
            servers = data.servers;
            filteredServers = [...servers];
            renderTable();
            updateEmptyState();
        } else {
            showToast('Failed to load servers', 'error');
        }
    } catch (error) {
        console.error('Error loading servers:', error);
    }
}

async function loadStats() {
    try {
        const data = await apiCall('/api/stats');
        if (data.success) {
            document.getElementById('statTotal').textContent = data.stats.total;
            document.getElementById('statOnline').textContent = data.stats.online;
            document.getElementById('statOffline').textContent = data.stats.offline;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// ==================== SERVER MANAGEMENT ====================

async function addServer(event) {
    event.preventDefault();
    
    const serverData = {
        ip: document.getElementById('serverIP').value.trim(),
        username: document.getElementById('serverUsername').value.trim(),
        password: document.getElementById('serverPassword').value,
        os_type: document.getElementById('serverOS').value
    };
    
    showLoading('Adding server...');
    
    try {
        const data = await apiCall('/api/servers', {
            method: 'POST',
            body: JSON.stringify(serverData)
        });
        
        if (data.success) {
            showToast('Server added successfully!', 'success');
            closeModal('addServerModal');
            document.getElementById('addServerForm').reset();
            await loadServers();
            await loadStats();
        } else {
            showToast(data.error || 'Failed to add server', 'error');
        }
    } catch (error) {
        showToast('Error adding server', 'error');
    } finally {
        hideLoading();
    }
}

async function deleteServer(id) {
    if (!confirm('Are you sure you want to delete this server?')) {
        return;
    }
    
    showLoading('Deleting server...');
    
    try {
        const data = await apiCall(`/api/servers/${id}`, {
            method: 'DELETE'
        });
        
        if (data.success) {
            showToast('Server deleted successfully!', 'success');
            await loadServers();
            await loadStats();
        } else {
            showToast(data.error || 'Failed to delete server', 'error');
        }
    } catch (error) {
        showToast('Error deleting server', 'error');
    } finally {
        hideLoading();
    }
}

async function bulkImport(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showToast('Please select a CSV file', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    showLoading('Importing servers...');
    
    try {
        const response = await fetch(`${API_BASE}/api/servers/bulk`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        if (data.success) {
            const result = data.result;
            showToast(`Imported ${result.success} servers. ${result.failed} failed.`, 
                result.failed > 0 ? 'warning' : 'success');
            closeModal('bulkImportModal');
            document.getElementById('bulkImportForm').reset();
            await loadServers();
            await loadStats();
        } else {
            showToast(data.error || 'Failed to import servers', 'error');
        }
    } catch (error) {
        showToast('Error importing servers', 'error');
    } finally {
        hideLoading();
    }
}

// ==================== SCANNING ====================

async function scanServer(id) {
    showLoading('Scanning server...');
    
    try {
        const data = await apiCall(`/api/scan/${id}`, {
            method: 'POST'
        });
        
        if (data.success) {
            const status = data.result.status;
            showToast(`Scan complete: ${status}`, status === 'Online' ? 'success' : 'warning');
            await loadServers();
            await loadStats();
        } else {
            showToast(data.error || 'Scan failed', 'error');
        }
    } catch (error) {
        showToast('Error scanning server', 'error');
    } finally {
        hideLoading();
    }
}

async function scanAllServers() {
    if (servers.length === 0) {
        showToast('No servers to scan', 'warning');
        return;
    }
    
    const btn = document.getElementById('btnScanAll');
    btn.disabled = true;
    showLoading(`Scanning ${servers.length} servers...`);
    
    try {
        const data = await apiCall('/api/scan-all', {
            method: 'POST'
        });
        
        if (data.success) {
            showToast(`Scan complete: ${data.online} online, ${data.offline} offline`, 'success');
            await loadServers();
            await loadStats();
        } else {
            showToast(data.error || 'Scan failed', 'error');
        }
    } catch (error) {
        showToast('Error scanning servers', 'error');
    } finally {
        hideLoading();
        btn.disabled = false;
    }
}

// ==================== EXPORT ====================

function exportExcel() {
    if (servers.length === 0) {
        showToast('No servers to export', 'warning');
        return;
    }
    
    showLoading('Generating Excel report...');
    
    // Create a download link
    const link = document.createElement('a');
    link.href = `${API_BASE}/api/export/excel`;
    link.download = '';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    setTimeout(() => {
        hideLoading();
        showToast('Excel report downloaded!', 'success');
    }, 1000);
}

// ==================== TABLE RENDERING ====================

function renderTable() {
    const tbody = document.getElementById('serverTableBody');
    tbody.innerHTML = '';
    
    filteredServers.forEach(server => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${escapeHtml(server.hostname || '-')}</td>
            <td class="ip-address">${escapeHtml(server.ip)}</td>
            <td>${renderOSBadge(server.os_type)}</td>
            <td>${escapeHtml(server.brand || '-')}</td>
            <td>${escapeHtml(server.model || '-')}</td>
            <td>${renderCPUInfo(server)}</td>
            <td>${formatRAM(server.ram_logical)}</td>
            <td>${truncateText(server.disk_info, 30) || '-'}</td>
            <td>${renderStatusBadge(server.status)}</td>
            <td>${formatDate(server.last_scan)}</td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn" onclick="showServerDetails(${server.id})" title="View Details">👁️</button>
                    <button class="action-btn scan" onclick="scanServer(${server.id})" title="Scan">🔄</button>
                    <button class="action-btn delete" onclick="deleteServer(${server.id})" title="Delete">🗑️</button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function renderOSBadge(osType) {
    const os = (osType || '').toLowerCase();
    if (os === 'windows') {
        return '<span class="os-badge windows">🪟 Windows</span>';
    } else if (os === 'linux') {
        return '<span class="os-badge linux">🐧 Linux</span>';
    }
    return `<span class="os-badge">${escapeHtml(osType || 'Unknown')}</span>`;
}

function renderStatusBadge(status) {
    const statusClass = (status || 'not-scanned').toLowerCase().replace(' ', '-');
    let icon = '⚪';
    if (status === 'Online') icon = '🟢';
    else if (status === 'Offline') icon = '🔴';
    else icon = '🟡';
    
    return `<span class="status-badge ${statusClass}">
        <span class="status-dot"></span>
        ${escapeHtml(status || 'Not Scanned')}
    </span>`;
}

function renderCPUInfo(server) {
    if (!server.cpu_count && !server.cpu_cores) return '-';
    const cores = server.cpu_cores || '?';
    const logical = server.cpu_logical_processors || '?';
    return `${cores}C/${logical}T`;
}

// ==================== FILTERING & SORTING ====================

function filterServers() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const osFilter = document.getElementById('filterOS').value;
    const statusFilter = document.getElementById('filterStatus').value;
    
    filteredServers = servers.filter(server => {
        // Search filter
        const matchesSearch = !searchTerm || 
            (server.hostname && server.hostname.toLowerCase().includes(searchTerm)) ||
            (server.ip && server.ip.toLowerCase().includes(searchTerm));
        
        // OS filter
        const matchesOS = !osFilter || server.os_type === osFilter;
        
        // Status filter
        const matchesStatus = !statusFilter || server.status === statusFilter;
        
        return matchesSearch && matchesOS && matchesStatus;
    });
    
    renderTable();
    updateEmptyState();
}

function sortTable(column) {
    if (sortColumn === column) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortColumn = column;
        sortDirection = 'asc';
    }
    
    filteredServers.sort((a, b) => {
        let valA = a[column] || '';
        let valB = b[column] || '';
        
        if (typeof valA === 'string') {
            valA = valA.toLowerCase();
            valB = valB.toLowerCase();
        }
        
        if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
        if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
        return 0;
    });
    
    renderTable();
}

// ==================== SERVER DETAILS ====================

async function showServerDetails(id) {
    const server = servers.find(s => s.id === id);
    if (!server) return;
    
    const content = document.getElementById('serverDetailsContent');
    content.innerHTML = `
        <div class="server-details">
            <div class="detail-section">
                <h3>📋 General Information</h3>
                <div class="detail-row">
                    <span class="detail-label">Hostname</span>
                    <span class="detail-value">${escapeHtml(server.hostname || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">IP Address</span>
                    <span class="detail-value">${escapeHtml(server.ip)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Domain</span>
                    <span class="detail-value">${escapeHtml(server.domain || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">OS Type</span>
                    <span class="detail-value">${escapeHtml(server.os_type)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">OS Version</span>
                    <span class="detail-value">${escapeHtml(server.os_version || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Service Pack</span>
                    <span class="detail-value">${escapeHtml(server.service_pack || '-')}</span>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>🏭 Hardware</h3>
                <div class="detail-row">
                    <span class="detail-label">Brand</span>
                    <span class="detail-value">${escapeHtml(server.brand || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Model</span>
                    <span class="detail-value">${escapeHtml(server.model || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Serial Number</span>
                    <span class="detail-value">${escapeHtml(server.serial || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Motherboard</span>
                    <span class="detail-value">${escapeHtml(server.motherboard || '-')}</span>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>⚡ CPU</h3>
                <div class="detail-row">
                    <span class="detail-label">CPU Count</span>
                    <span class="detail-value">${server.cpu_count || '-'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Cores</span>
                    <span class="detail-value">${escapeHtml(server.cpu_cores || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Logical Processors</span>
                    <span class="detail-value">${escapeHtml(server.cpu_logical_processors || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Model</span>
                    <span class="detail-value">${escapeHtml(server.cpu_model || '-')}</span>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>🧠 Memory</h3>
                <div class="detail-row">
                    <span class="detail-label">Physical RAM</span>
                    <span class="detail-value">${escapeHtml(server.ram_physical || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Total RAM</span>
                    <span class="detail-value">${formatRAM(server.ram_logical)}</span>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>💾 Storage</h3>
                <div class="detail-row">
                    <span class="detail-label">Disk Info</span>
                    <span class="detail-value">${escapeHtml(server.disk_info || '-')}</span>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>🌐 Network</h3>
                <div class="detail-row">
                    <span class="detail-label">Primary Network</span>
                    <span class="detail-value">${escapeHtml(server.network_primary || '-')}</span>
                </div>
            </div>
        </div>
    `;
    
    showModal('serverDetailsModal');
}

// ==================== MODAL HELPERS ====================

function closeAllModals() {
    document.querySelectorAll('.modal.show').forEach(modal => {
        modal.classList.remove('show');
    });
    document.body.style.overflow = '';
}

function showModal(modalId) {
    // Close any open modals first
    closeAllModals();
    
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Focus first input in modal after a brief delay
        setTimeout(() => {
            const firstInput = modal.querySelector('input:not([type="file"]), select');
            if (firstInput) {
                firstInput.focus();
            }
        }, 100);
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        
        // Reset any forms in the modal
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }
    }
    
    // Only restore body overflow if no modals are open
    if (!document.querySelector('.modal.show')) {
        document.body.style.overflow = '';
    }
}

function showAddServerModal() {
    // Reset form before showing
    const form = document.getElementById('addServerForm');
    if (form) form.reset();
    
    showModal('addServerModal');
}

function showBulkImportModal() {
    // Reset form before showing
    const form = document.getElementById('bulkImportForm');
    if (form) form.reset();
    
    showModal('bulkImportModal');
}

// Close modal when clicking outside (on backdrop)
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal') && e.target.classList.contains('show')) {
        closeModal(e.target.id);
    }
});

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            closeModal(openModal.id);
        }
    }
});

// ==================== LOADING ====================

function showLoading(text = 'Loading...') {
    document.getElementById('loadingText').textContent = text;
    document.getElementById('loadingOverlay').classList.add('show');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('show');
}

// ==================== TOAST NOTIFICATIONS ====================

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    else if (type === 'error') icon = '❌';
    else if (type === 'warning') icon = '⚠️';
    
    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-message">${escapeHtml(message)}</span>
    `;
    
    container.appendChild(toast);
    
    // Remove toast after 4 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ==================== UTILITY FUNCTIONS ====================

function refreshServers() {
    loadServers();
    loadStats();
    showToast('Data refreshed', 'info');
}

function updateEmptyState() {
    const emptyState = document.getElementById('emptyState');
    const table = document.getElementById('serverTable');
    
    if (filteredServers.length === 0) {
        emptyState.style.display = 'flex';
        table.style.display = 'none';
    } else {
        emptyState.style.display = 'none';
        table.style.display = 'table';
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatRAM(ramMB) {
    if (!ramMB) return '-';
    const gb = Math.round(ramMB / 1024);
    return `${gb} GB`;
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
        const date = new Date(dateStr);
        return date.toLocaleString('tr-TR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dateStr;
    }
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

