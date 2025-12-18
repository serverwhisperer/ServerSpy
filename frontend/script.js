/**
 * ServerScout - Frontend JavaScript
 * Server Inventory Management Tool
 */

// Global state
let servers = [];
let filteredServers = [];
let sortColumn = 'hostname';
let sortDirection = 'asc';
let isLoading = false;
let confirmCallback = null;

// API Base URL
const API_BASE = '';

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    loadServers();
    loadStats();
    loadCredentials();
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
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
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

async function loadCredentials() {
    try {
        const data = await apiCall('/api/credentials');
        if (data.success) {
            const creds = data.credentials;
            if (creds.windows) {
                document.getElementById('winUsername').value = creds.windows.username || '';
                document.getElementById('winCredStatus').textContent = creds.windows.has_password ? '✓ Kayıtlı' : '';
            }
            if (creds.linux) {
                document.getElementById('linuxUsername').value = creds.linux.username || '';
                document.getElementById('linuxCredStatus').textContent = creds.linux.has_password ? '✓ Kayıtlı' : '';
            }
        }
    } catch (error) {
        console.error('Error loading credentials:', error);
    }
}

// ==================== CUSTOM CONFIRM MODAL ====================

function showConfirm(title, message, yesText, callback) {
    confirmCallback = callback;
    
    document.getElementById('confirmTitle').textContent = title;
    document.getElementById('confirmMessage').textContent = message;
    document.getElementById('confirmYesBtn').textContent = yesText;
    
    const modal = document.getElementById('confirmModal');
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function handleConfirm(result) {
    const modal = document.getElementById('confirmModal');
    modal.classList.remove('show');
    document.body.style.overflow = '';
    
    if (confirmCallback) {
        const cb = confirmCallback;
        confirmCallback = null;
        
        // Small delay to ensure modal is fully closed
        setTimeout(() => {
            cb(result);
        }, 100);
    }
}

// ==================== CREDENTIALS ====================

async function saveCredentials(osType) {
    let username, password, statusEl;
    
    if (osType === 'windows') {
        username = document.getElementById('winUsername').value.trim();
        password = document.getElementById('winPassword').value;
        statusEl = document.getElementById('winCredStatus');
    } else {
        username = document.getElementById('linuxUsername').value.trim();
        password = document.getElementById('linuxPassword').value;
        statusEl = document.getElementById('linuxCredStatus');
    }
    
    if (!username || !password) {
        showToast('Kullanıcı adı ve şifre giriniz', 'warning');
        return;
    }
    
    try {
        const data = await apiCall('/api/credentials', {
            method: 'POST',
            body: JSON.stringify({ os_type: osType, username, password })
        });
        
        if (data.success) {
            statusEl.textContent = '✓ Kayıtlı';
            if (osType === 'windows') {
                document.getElementById('winPassword').value = '';
            } else {
                document.getElementById('linuxPassword').value = '';
            }
            showToast(`${osType === 'windows' ? 'Windows' : 'Linux'} bilgileri kaydedildi!`, 'success');
        } else {
            showToast(data.error || 'Kayıt başarısız', 'error');
        }
    } catch (error) {
        showToast('Hata oluştu', 'error');
    }
}

async function clearCredentials(osType) {
    try {
        const data = await apiCall('/api/credentials', {
            method: 'POST',
            body: JSON.stringify({ os_type: osType, username: '', password: '' })
        });
        
        if (data.success) {
            if (osType === 'windows') {
                document.getElementById('winUsername').value = '';
                document.getElementById('winPassword').value = '';
                document.getElementById('winCredStatus').textContent = '';
            } else {
                document.getElementById('linuxUsername').value = '';
                document.getElementById('linuxPassword').value = '';
                document.getElementById('linuxCredStatus').textContent = '';
            }
            showToast(`${osType === 'windows' ? 'Windows' : 'Linux'} bilgileri temizlendi`, 'info');
        }
    } catch (error) {
        showToast('Hata oluştu', 'error');
    }
}

// ==================== SERVER MANAGEMENT ====================

async function addServer(event) {
    event.preventDefault();
    
    const ip = document.getElementById('serverIP').value.trim();
    const osType = document.getElementById('serverOS').value;
    const useCustom = document.getElementById('useCustomCreds').checked;
    
    if (!ip) {
        showToast('IP adresi giriniz', 'warning');
        return;
    }
    
    const serverData = {
        ip: ip,
        use_default: !useCustom,
        auto_detect: !osType
    };
    
    if (osType) {
        serverData.os_type = osType;
    }
    
    if (useCustom) {
        serverData.username = document.getElementById('serverUsername').value.trim();
        serverData.password = document.getElementById('serverPassword').value;
        
        if (!serverData.username || !serverData.password) {
            showToast('Özel kimlik bilgisi giriniz', 'warning');
            return;
        }
    }
    
    showLoading('Sunucu ekleniyor...');
    
    try {
        const data = await apiCall('/api/servers', {
            method: 'POST',
            body: JSON.stringify(serverData)
        });
        
        hideLoading();
        
        if (data.success) {
            let msg = 'Sunucu eklendi!';
            if (data.detected) {
                msg = `Sunucu eklendi! OS: ${data.os_type}`;
            }
            showToast(msg, 'success');
            closeModal('addServerModal');
            await loadServers();
            await loadStats();
        } else {
            showToast(data.error || 'Ekleme başarısız', 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('Hata oluştu', 'error');
    }
}

function toggleCustomCreds() {
    const show = document.getElementById('useCustomCreds').checked;
    document.getElementById('customCredsSection').style.display = show ? 'block' : 'none';
}

function deleteServer(id) {
    const server = servers.find(s => s.id === id);
    const serverName = server ? (server.hostname || server.ip) : 'Bu sunucu';
    
    showConfirm(
        '🗑️ Sunucu Sil',
        `"${serverName}" sunucusunu silmek istediğinize emin misiniz?`,
        'Evet, Sil',
        async (confirmed) => {
            if (!confirmed) return;
            
            showLoading('Siliniyor...');
            
            try {
                const data = await apiCall(`/api/servers/${id}`, {
                    method: 'DELETE'
                });
                
                hideLoading();
                
                if (data.success) {
                    showToast('Sunucu silindi!', 'success');
                    await loadServers();
                    await loadStats();
                } else {
                    showToast(data.error || 'Silme başarısız', 'error');
                }
            } catch (error) {
                hideLoading();
                showToast('Hata oluştu', 'error');
            }
        }
    );
}

function clearAllServers() {
    if (servers.length === 0) {
        showToast('Silinecek sunucu yok', 'warning');
        return;
    }
    
    showConfirm(
        '⚠️ Tümünü Sil',
        `Tüm sunucuları (${servers.length} adet) silmek istediğinize emin misiniz?\n\nBu işlem geri alınamaz!`,
        'Evet, Tümünü Sil',
        async (confirmed) => {
            if (!confirmed) return;
            
            showLoading('Tüm sunucular siliniyor...');
            
            try {
                const data = await apiCall('/api/servers/clear', {
                    method: 'DELETE'
                });
                
                hideLoading();
                
                if (data.success) {
                    showToast('Tüm sunucular silindi!', 'success');
                    await loadServers();
                    await loadStats();
                } else {
                    showToast(data.error || 'Silme başarısız', 'error');
                }
            } catch (error) {
                hideLoading();
                showToast('Hata oluştu', 'error');
            }
        }
    );
}

async function importServers(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('importFile');
    const contentInput = document.getElementById('importContent');
    
    let hasFile = fileInput && fileInput.files && fileInput.files.length > 0;
    let hasContent = contentInput && contentInput.value && contentInput.value.trim();
    
    if (!hasFile && !hasContent) {
        showToast('Dosya seçin veya içerik yapıştırın', 'warning');
        return;
    }
    
    showLoading('Sunucular import ediliyor...');
    
    try {
        let response;
        if (hasFile) {
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            response = await fetch(`${API_BASE}/api/servers/bulk`, {
                method: 'POST',
                body: formData
            });
        } else {
            response = await fetch(`${API_BASE}/api/servers/bulk`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: contentInput.value.trim() })
            });
        }
        
        const data = await response.json();
        
        hideLoading();
        
        if (data.success) {
            const result = data.result;
            let msg = `${result.success} sunucu eklendi.`;
            if (result.detected > 0) {
                msg += ` (${result.detected} otomatik tespit)`;
            }
            if (result.failed > 0) {
                msg += ` ${result.failed} başarısız.`;
            }
            showToast(msg, result.failed > 0 ? 'warning' : 'success');
            closeModal('importModal');
            await loadServers();
            await loadStats();
        } else {
            showToast(data.error || 'Import başarısız', 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('Hata oluştu', 'error');
    }
}

// ==================== SCANNING ====================

async function scanServer(id) {
    showLoading('Taranıyor...');
    
    try {
        const data = await apiCall(`/api/scan/${id}`, {
            method: 'POST'
        });
        
        hideLoading();
        
        if (data.success) {
            const status = data.result.status;
            showToast(`Tarama tamamlandı: ${status}`, status === 'Online' ? 'success' : 'warning');
            await loadServers();
            await loadStats();
        } else {
            showToast(data.error || 'Tarama başarısız', 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('Hata oluştu', 'error');
    }
}

async function scanAllServers() {
    if (servers.length === 0) {
        showToast('Taranacak sunucu yok', 'warning');
        return;
    }
    
    const btn = document.getElementById('btnScanAll');
    if (btn) btn.disabled = true;
    showLoading(`${servers.length} sunucu taranıyor...`);
    
    try {
        const data = await apiCall('/api/scan-all', {
            method: 'POST'
        });
        
        hideLoading();
        if (btn) btn.disabled = false;
        
        if (data.success) {
            let msg = `Tarama tamamlandı: ${data.online} çevrimiçi, ${data.offline} çevrimdışı`;
            if (data.skipped > 0) {
                msg += `, ${data.skipped} atlandı (kimlik bilgisi yok)`;
            }
            showToast(msg, 'success');
            await loadServers();
            await loadStats();
        } else {
            showToast(data.error || 'Tarama başarısız', 'error');
        }
    } catch (error) {
        hideLoading();
        if (btn) btn.disabled = false;
        showToast('Hata oluştu', 'error');
    }
}

// ==================== EXPORT ====================

function exportExcel() {
    if (servers.length === 0) {
        showToast('Export edilecek sunucu yok', 'warning');
        return;
    }
    
    showLoading('Excel raporu oluşturuluyor...');
    
    const link = document.createElement('a');
    link.href = `${API_BASE}/api/export/excel`;
    link.download = '';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    setTimeout(() => {
        hideLoading();
        showToast('Excel raporu indirildi!', 'success');
    }, 1000);
}

// ==================== TABLE RENDERING ====================

function renderTable() {
    const tbody = document.getElementById('serverTableBody');
    if (!tbody) return;
    
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
                    <button class="action-btn" onclick="showServerDetails(${server.id})" title="Detaylar">👁️</button>
                    <button class="action-btn" onclick="showSetCredsModal(${server.id})" title="Kimlik Bilgisi">🔑</button>
                    <button class="action-btn scan" onclick="scanServer(${server.id})" title="Tara">🔄</button>
                    <button class="action-btn delete" onclick="deleteServer(${server.id})" title="Sil">🗑️</button>
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
    const searchInput = document.getElementById('searchInput');
    const filterOS = document.getElementById('filterOS');
    const filterStatus = document.getElementById('filterStatus');
    
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const osFilter = filterOS ? filterOS.value : '';
    const statusFilter = filterStatus ? filterStatus.value : '';
    
    filteredServers = servers.filter(server => {
        const matchesSearch = !searchTerm || 
            (server.hostname && server.hostname.toLowerCase().includes(searchTerm)) ||
            (server.ip && server.ip.toLowerCase().includes(searchTerm));
        const matchesOS = !osFilter || server.os_type === osFilter;
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

function showServerDetails(id) {
    const server = servers.find(s => s.id === id);
    if (!server) return;
    
    const content = document.getElementById('serverDetailsContent');
    if (!content) return;
    
    content.innerHTML = `
        <div class="server-details">
            <div class="detail-section">
                <h3>📋 Genel Bilgiler</h3>
                <div class="detail-row">
                    <span class="detail-label">Hostname</span>
                    <span class="detail-value">${escapeHtml(server.hostname || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">IP Adresi</span>
                    <span class="detail-value">${escapeHtml(server.ip)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Domain</span>
                    <span class="detail-value">${escapeHtml(server.domain || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">İşletim Sistemi</span>
                    <span class="detail-value">${escapeHtml(server.os_type)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">OS Versiyonu</span>
                    <span class="detail-value">${escapeHtml(server.os_version || '-')}</span>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>🏭 Donanım</h3>
                <div class="detail-row">
                    <span class="detail-label">Marka</span>
                    <span class="detail-value">${escapeHtml(server.brand || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Model</span>
                    <span class="detail-value">${escapeHtml(server.model || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Seri No</span>
                    <span class="detail-value">${escapeHtml(server.serial || '-')}</span>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>⚡ İşlemci</h3>
                <div class="detail-row">
                    <span class="detail-label">Çekirdek</span>
                    <span class="detail-value">${escapeHtml(server.cpu_cores || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Mantıksal İşlemci</span>
                    <span class="detail-value">${escapeHtml(server.cpu_logical_processors || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Model</span>
                    <span class="detail-value">${escapeHtml(server.cpu_model || '-')}</span>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>🧠 Bellek</h3>
                <div class="detail-row">
                    <span class="detail-label">Fiziksel RAM</span>
                    <span class="detail-value">${escapeHtml(server.ram_physical || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Toplam RAM</span>
                    <span class="detail-value">${formatRAM(server.ram_logical)}</span>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>💾 Depolama</h3>
                <div class="detail-row">
                    <span class="detail-label">Disk Bilgisi</span>
                    <span class="detail-value">${escapeHtml(server.disk_info || '-')}</span>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>🌐 Ağ</h3>
                <div class="detail-row">
                    <span class="detail-label">Birincil Ağ</span>
                    <span class="detail-value">${escapeHtml(server.network_primary || '-')}</span>
                </div>
            </div>
        </div>
    `;
    
    showModal('serverDetailsModal');
}

// ==================== SET CREDENTIALS MODAL ====================

function showSetCredsModal(serverId) {
    const server = servers.find(s => s.id === serverId);
    if (!server) return;
    
    const serverIdInput = document.getElementById('credServerId');
    const serverInfo = document.getElementById('credServerInfo');
    const usernameInput = document.getElementById('credUsername');
    const passwordInput = document.getElementById('credPassword');
    
    if (serverIdInput) serverIdInput.value = serverId;
    if (serverInfo) serverInfo.textContent = `Sunucu: ${server.ip} (${server.os_type})`;
    if (usernameInput) usernameInput.value = '';
    if (passwordInput) passwordInput.value = '';
    
    showModal('setCredsModal');
}

async function saveServerCredentials(event) {
    event.preventDefault();
    
    const serverId = document.getElementById('credServerId').value;
    const username = document.getElementById('credUsername').value.trim();
    const password = document.getElementById('credPassword').value;
    
    if (!username || !password) {
        showToast('Kullanıcı adı ve şifre giriniz', 'warning');
        return;
    }
    
    showLoading('Kaydediliyor...');
    
    try {
        const data = await apiCall(`/api/servers/${serverId}/credentials`, {
            method: 'PUT',
            body: JSON.stringify({ username, password })
        });
        
        hideLoading();
        
        if (data.success) {
            showToast('Kimlik bilgileri kaydedildi!', 'success');
            closeModal('setCredsModal');
            await loadServers();
        } else {
            showToast(data.error || 'Kayıt başarısız', 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('Hata oluştu', 'error');
    }
}

// ==================== MODAL HELPERS ====================

function showModal(modalId) {
    // Don't open modal if confirm is showing
    if (document.getElementById('confirmModal').classList.contains('show')) {
        return;
    }
    
    hideLoading();
    
    // Close other modals except confirm
    document.querySelectorAll('.modal.show').forEach(modal => {
        if (modal.id !== 'confirmModal') {
            modal.classList.remove('show');
        }
    });
    
    const modal = document.getElementById(modalId);
    if (modal) {
        const form = modal.querySelector('form');
        if (form) form.reset();
        
        if (modalId === 'addServerModal') {
            const customSection = document.getElementById('customCredsSection');
            if (customSection) customSection.style.display = 'none';
        }
        
        if (modalId === 'importModal') {
            const textarea = document.getElementById('importContent');
            if (textarea) textarea.value = '';
        }
        
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        setTimeout(() => {
            const firstInput = modal.querySelector('input:not([type="file"]):not([type="hidden"]):not([type="checkbox"]), select, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        }, 150);
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
    }
    
    const hasOpenModal = document.querySelector('.modal.show');
    if (!hasOpenModal) {
        document.body.style.overflow = '';
    }
}

function showImportModal() {
    showModal('importModal');
}

function showAddServerModal() {
    showModal('addServerModal');
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal') && e.target.classList.contains('show')) {
        if (e.target.id === 'confirmModal') {
            // Don't close confirm modal by clicking outside
            return;
        }
        closeModal(e.target.id);
    }
});

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const confirmModal = document.getElementById('confirmModal');
        if (confirmModal && confirmModal.classList.contains('show')) {
            handleConfirm(false);
            return;
        }
        
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            closeModal(openModal.id);
        }
    }
});

// ==================== LOADING ====================

function showLoading(text = 'Yükleniyor...') {
    if (isLoading) return;
    isLoading = true;
    
    const overlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    
    if (loadingText) loadingText.textContent = text;
    if (overlay) overlay.classList.add('show');
}

function hideLoading() {
    isLoading = false;
    
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.remove('show');
}

// ==================== TOAST NOTIFICATIONS ====================

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
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
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ==================== UTILITY FUNCTIONS ====================

function refreshServers() {
    loadServers();
    loadStats();
    showToast('Veriler yenilendi', 'info');
}

function updateEmptyState() {
    const emptyState = document.getElementById('emptyState');
    const table = document.getElementById('serverTable');
    
    if (!emptyState || !table) return;
    
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
