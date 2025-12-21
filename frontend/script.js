/**
 * ServerScout - Frontend JavaScript
 * Server Inventory Management Tool
 */

// Global state
let servers = [];
let filteredServers = [];
let projects = [];
let currentProjectId = null; // null = all projects
let sortColumn = 'hostname';
let sortDirection = 'asc';
let isLoading = false;
let confirmCallback = null;

// API Base URL
const API_BASE = '';

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    loadProjects();
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
        let endpoint = '/api/servers';
        
        if (currentProjectId !== null) {
            if (currentProjectId === 'unassigned') {
                endpoint = '/api/projects/unassigned/servers';
            } else {
                endpoint = `/api/projects/${currentProjectId}/servers`;
            }
        }
        
        const data = await apiCall(endpoint);
        if (data.success) {
            servers = data.servers || [];
            
            // Add project names to servers
            servers.forEach(server => {
                if (server.project_id) {
                    const project = projects.find(p => p.id === server.project_id);
                    server.project_name = project ? project.name : 'Unknown';
                } else {
                    server.project_name = '';
                }
            });
            
            filteredServers = [...servers];
            renderTable();
            updateEmptyState();
            updateProjectStats();
        } else {
            console.error('Failed to load servers:', data.error);
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

// ==================== PROJECT MANAGEMENT ====================

async function loadProjects() {
    try {
        const data = await apiCall('/api/projects');
        if (data.success) {
            projects = data.projects;
            updateProjectDropdowns();
        }
    } catch (error) {
        console.error('Error loading projects:', error);
    }
}

function updateProjectDropdowns() {
    const projectSelect = document.getElementById('projectSelect');
    const assignProjectSelect = document.getElementById('assignProjectSelect');
    
    if (projectSelect) {
        const currentValue = projectSelect.value;
        projectSelect.innerHTML = '<option value="">All Projects</option>';
        projectSelect.innerHTML += '<option value="unassigned">📁 Unassigned</option>';
        
        projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = `📂 ${project.name}`;
            projectSelect.appendChild(option);
        });
        
        // Restore selection
        if (currentValue) {
            projectSelect.value = currentValue;
        }
    }
    
    if (assignProjectSelect) {
        assignProjectSelect.innerHTML = '<option value="">(No Project)</option>';
        projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = project.name;
            assignProjectSelect.appendChild(option);
        });
    }
}

function onProjectChange() {
    const projectSelect = document.getElementById('projectSelect');
    const value = projectSelect ? projectSelect.value : '';
    
    if (value === '') {
        currentProjectId = null;
    } else if (value === 'unassigned') {
        currentProjectId = 'unassigned';
    } else {
        const parsed = parseInt(value);
        currentProjectId = isNaN(parsed) ? null : parsed;
    }
    
    loadServers();
    loadStats();
    updateProjectStats();
}

function updateProjectStats() {
    const projectStats = document.getElementById('projectServerCount');
    const projectSelect = document.getElementById('projectSelect');
    
    if (!projectStats) return;
    
    if (currentProjectId === null) {
        projectStats.textContent = `Total: ${servers.length} server${servers.length !== 1 ? 's' : ''}`;
    } else if (currentProjectId === 'unassigned') {
        projectStats.textContent = `Unassigned: ${servers.length} server${servers.length !== 1 ? 's' : ''}`;
    } else {
        const project = projects.find(p => p.id === currentProjectId);
        if (project) {
            projectStats.textContent = `${project.name}: ${servers.length} server${servers.length !== 1 ? 's' : ''}`;
        }
    }
}

function showNewProjectModal() {
    showModal('newProjectModal');
}

async function createProject(event) {
    event.preventDefault();
    
    const nameInput = document.getElementById('projectName');
    const name = nameInput.value.trim();
    
    if (!name) {
        showToast('Please enter project name', 'warning');
        return;
    }
    
    showLoading('Creating project...');
    
    try {
        const data = await apiCall('/api/projects', {
            method: 'POST',
            body: JSON.stringify({ name })
        });
        
        hideLoading();
        
        if (data.success) {
            showToast('Project created!', 'success');
            closeModal('newProjectModal');
            await loadProjects();
            
            // Select the new project after dropdown is updated
            setTimeout(() => {
                const projectSelect = document.getElementById('projectSelect');
                if (projectSelect && data.id) {
                    projectSelect.value = data.id;
                    onProjectChange();
                }
            }, 100);
        } else {
            showToast(data.error || 'Failed to create project', 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('An error occurred', 'error');
    }
}

function showManageProjectsModal() {
    loadProjectsList();
    showModal('manageProjectsModal');
}

async function loadProjectsList() {
    const container = document.getElementById('projectsList');
    if (!container) return;
    
    try {
        const data = await apiCall('/api/projects/with-stats');
        if (!data.success) return;
        
        const projectsData = data.data.projects;
        const unassigned = data.data.unassigned;
        
        if (projectsData.length === 0 && unassigned.total === 0) {
            container.innerHTML = `
                <div class="projects-empty">
                    <div class="projects-empty-icon">📂</div>
                    <p>No projects created yet</p>
                    <button class="btn btn-primary" onclick="closeModal('manageProjectsModal'); showNewProjectModal();">
                        ➕ Create First Project
                    </button>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        // Unassigned servers info
        if (unassigned.total > 0) {
            html += `
                <div class="project-item" style="border-left: 3px solid var(--warning);">
                    <div class="project-item-info">
                        <div class="project-item-name">📁 Unassigned Servers</div>
                        <div class="project-item-stats">
                            ${unassigned.total} server${unassigned.total !== 1 ? 's' : ''} | 
                            🟢 ${unassigned.online} | 
                            🔴 ${unassigned.offline} | 
                            🟡 ${unassigned.not_scanned}
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Projects
        projectsData.forEach(project => {
            const stats = project.stats;
            html += `
                <div class="project-item">
                    <div class="project-item-info">
                        <div class="project-item-name">📂 ${escapeHtml(project.name)}</div>
                        <div class="project-item-stats">
                            ${stats.total} server${stats.total !== 1 ? 's' : ''} | 
                            🟢 ${stats.online} | 
                            🔴 ${stats.offline} | 
                            🟡 ${stats.not_scanned}
                        </div>
                    </div>
                    <div class="project-item-actions">
                        <button class="action-btn" onclick="renameProjectPrompt(${project.id}, '${escapeHtml(project.name)}')" title="Rename">✏️</button>
                        <button class="action-btn delete" onclick="deleteProjectConfirm(${project.id}, '${escapeHtml(project.name)}')" title="Delete">🗑️</button>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading projects list:', error);
    }
}

function renameProjectPrompt(projectId, currentName) {
    const newName = prompt('New project name:', currentName);
    if (newName && newName.trim() && newName.trim() !== currentName) {
        renameProject(projectId, newName.trim());
    }
}

async function renameProject(projectId, newName) {
    try {
        const data = await apiCall(`/api/projects/${projectId}`, {
            method: 'PUT',
            body: JSON.stringify({ name: newName })
        });
        
        if (data.success) {
            showToast('Project renamed', 'success');
            await loadProjects();
            loadProjectsList();
        } else {
            showToast(data.error || 'Failed to rename project', 'error');
        }
    } catch (error) {
        showToast('An error occurred', 'error');
    }
}

function deleteProjectConfirm(projectId, projectName) {
    showConfirm(
        '🗑️ Delete Project',
        `Are you sure you want to delete project "${projectName}"?\n\nServers in this project will not be deleted, they will become "unassigned".`,
        'Yes, Delete',
        async (confirmed) => {
            if (!confirmed) return;
            
            try {
                const data = await apiCall(`/api/projects/${projectId}`, {
                    method: 'DELETE'
                });
                
                if (data.success) {
                    showToast('Project deleted', 'success');
                    
                    // If we were viewing this project, switch to all
                    if (currentProjectId === projectId) {
                        currentProjectId = null;
                        document.getElementById('projectSelect').value = '';
                    }
                    
                    await loadProjects();
                    loadProjectsList();
                    loadServers();
                } else {
                    showToast(data.error || 'Failed to delete', 'error');
                }
            } catch (error) {
                showToast('An error occurred', 'error');
            }
        }
    );
}

function showAssignProjectModal(serverId) {
    const server = servers.find(s => s.id === serverId);
    if (!server) return;
    
    document.getElementById('assignServerId').value = serverId;
    document.getElementById('assignServerInfo').textContent = `Server: ${server.ip} (${server.hostname || 'no hostname'})`;
    
    // Update dropdown
    updateProjectDropdowns();
    
    // Select current project if any
    const assignSelect = document.getElementById('assignProjectSelect');
    if (server.project_id) {
        assignSelect.value = server.project_id;
    } else {
        assignSelect.value = '';
    }
    
    showModal('assignProjectModal');
}

async function assignSelectedToProject(event) {
    event.preventDefault();
    
    const serverId = parseInt(document.getElementById('assignServerId').value);
    const projectId = document.getElementById('assignProjectSelect').value;
    
    showLoading('Assigning...');
    
    try {
        const data = await apiCall('/api/servers/assign', {
            method: 'POST',
            body: JSON.stringify({
                server_ids: [serverId],
                project_id: projectId ? parseInt(projectId) : null
            })
        });
        
        hideLoading();
        
        if (data.success) {
            showToast('Server assigned to project', 'success');
            closeModal('assignProjectModal');
            await loadServers();
        } else {
            showToast(data.error || 'Failed to assign', 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('An error occurred', 'error');
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
        showToast('Please enter username and password', 'warning');
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
            showToast(data.error || 'Failed to save', 'error');
        }
    } catch (error) {
        showToast('An error occurred', 'error');
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
            showToast(`${osType === 'windows' ? 'Windows' : 'Linux'} credentials cleared`, 'info');
        }
    } catch (error) {
        showToast('An error occurred', 'error');
    }
}

// ==================== SERVER MANAGEMENT ====================

async function addServer(event) {
    event.preventDefault();
    
    const ip = document.getElementById('serverIP').value.trim();
    const osType = document.getElementById('serverOS').value;
    const useCustom = document.getElementById('useCustomCreds').checked;
    
    if (!ip) {
        showToast('Please enter IP address', 'warning');
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
    
    // Assign to current project if a specific project is selected
    if (currentProjectId !== null && currentProjectId !== 'unassigned') {
        serverData.project_id = currentProjectId;
    }
    
    if (useCustom) {
        serverData.username = document.getElementById('serverUsername').value.trim();
        serverData.password = document.getElementById('serverPassword').value;
        
        if (!serverData.username || !serverData.password) {
            showToast('Please enter custom credentials', 'warning');
            return;
        }
    }
    
    showLoading('Adding server...');
    
    try {
        const data = await apiCall('/api/servers', {
            method: 'POST',
            body: JSON.stringify(serverData)
        });
        
        hideLoading();
        
        if (data.success) {
            let msg = 'Server added!';
            if (data.detected) {
                msg = `Server added! OS: ${data.os_type}`;
            }
            if (serverData.project_id) {
                const project = projects.find(p => p.id === serverData.project_id);
                if (project) {
                    msg += ` (Project: ${project.name})`;
                }
            }
            showToast(msg, 'success');
            closeModal('addServerModal');
            await loadServers();
            await loadStats();
        } else {
            showToast(data.error || 'Failed to add server', 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('An error occurred', 'error');
    }
}

function toggleCustomCreds() {
    const show = document.getElementById('useCustomCreds').checked;
    document.getElementById('customCredsSection').style.display = show ? 'block' : 'none';
}

function deleteServer(id) {
    const server = servers.find(s => s.id === id);
    const serverName = server ? (server.hostname || server.ip) : 'This server';
    
    showConfirm(
        '🗑️ Delete Server',
        `Are you sure you want to delete server "${serverName}"?`,
        'Yes, Delete',
        async (confirmed) => {
            if (!confirmed) return;
            
            showLoading('Siliniyor...');
            
            try {
                const data = await apiCall(`/api/servers/${id}`, {
                    method: 'DELETE'
                });
                
                hideLoading();
                
                if (data.success) {
                    showToast('Server deleted!', 'success');
                    await loadServers();
                    await loadStats();
                } else {
                    showToast(data.error || 'Failed to delete', 'error');
                }
            } catch (error) {
                hideLoading();
                showToast('An error occurred', 'error');
            }
        }
    );
}

function clearAllServers() {
    if (servers.length === 0) {
        showToast('No servers to delete', 'warning');
        return;
    }
    
    // Determine what we're clearing based on current project selection
    let title, message, endpoint;
    
    if (currentProjectId === null) {
        title = '⚠️ Delete All Servers';
        message = `Are you sure you want to delete ALL servers (${servers.length} server${servers.length !== 1 ? 's' : ''})?\n\nThis action cannot be undone!`;
        endpoint = '/api/servers/clear';
    } else if (currentProjectId === 'unassigned') {
        title = '⚠️ Delete Unassigned Servers';
        message = `Are you sure you want to delete unassigned servers (${servers.length} server${servers.length !== 1 ? 's' : ''})?\n\nThis action cannot be undone!`;
        endpoint = '/api/servers/clear?project_id=unassigned';
    } else {
        const project = projects.find(p => p.id === currentProjectId);
        const projectName = project ? project.name : 'Selected project';
        title = `⚠️ Delete "${projectName}" Servers`;
        message = `Are you sure you want to delete servers in project "${projectName}" (${servers.length} server${servers.length !== 1 ? 's' : ''})?\n\nThis action cannot be undone!`;
        endpoint = `/api/servers/clear?project_id=${currentProjectId}`;
    }
    
    showConfirm(
        title,
        message,
        'Yes, Delete',
        async (confirmed) => {
            if (!confirmed) return;
            
            showLoading('Deleting servers...');
            
            try {
                const data = await apiCall(endpoint, {
                    method: 'DELETE'
                });
                
                hideLoading();
                
                if (data.success) {
                    showToast(data.message || 'Servers deleted!', 'success');
                    await loadServers();
                    await loadStats();
                } else {
                    showToast(data.error || 'Failed to delete', 'error');
                }
            } catch (error) {
                hideLoading();
                showToast('An error occurred', 'error');
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
    
    // Get the project to assign (use current project if it's a specific project)
    let projectIdToAssign = null;
    if (currentProjectId !== null && currentProjectId !== 'unassigned') {
        projectIdToAssign = currentProjectId;
    }
    
    showLoading('Importing servers...');
    
    try {
        let response;
        if (hasFile) {
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            if (projectIdToAssign) {
                formData.append('project_id', projectIdToAssign);
            }
            response = await fetch(`${API_BASE}/api/servers/bulk`, {
                method: 'POST',
                body: formData
            });
        } else {
            const payload = { content: contentInput.value.trim() };
            if (projectIdToAssign) {
                payload.project_id = projectIdToAssign;
            }
            response = await fetch(`${API_BASE}/api/servers/bulk`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }
        
        const data = await response.json();
        
        hideLoading();
        
        if (data.success) {
            const result = data.result;
            let msg = `${result.success} server${result.success !== 1 ? 's' : ''} added.`;
            if (projectIdToAssign) {
                const project = projects.find(p => p.id === projectIdToAssign);
                if (project) {
                    msg += ` (Project: ${project.name})`;
                }
            }
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
            showToast(data.error || 'Import failed', 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('An error occurred', 'error');
    }
}

// ==================== SCANNING ====================

async function scanServer(id) {
    showLoading('Scanning...');
    
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
            showToast(data.error || 'Scan failed', 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('An error occurred', 'error');
    }
}

async function scanAllServers() {
    if (servers.length === 0) {
        showToast('No servers to scan', 'warning');
        return;
    }
    
    const btn = document.getElementById('btnScanAll');
    if (btn) btn.disabled = true;
    
    // Build endpoint with project filter
    let endpoint = '/api/scan-all';
    if (currentProjectId !== null) {
        if (currentProjectId === 'unassigned') {
            endpoint += '?project_id=unassigned';
        } else {
            endpoint += `?project_id=${currentProjectId}`;
        }
    }
    
    showLoading(`Scanning ${servers.length} server${servers.length > 1 ? 's' : ''}...`);
    
    try {
        const data = await apiCall(endpoint, {
            method: 'POST'
        });
        
        hideLoading();
        if (btn) btn.disabled = false;
        
        if (data.success) {
            let msg = `Scan completed: ${data.online} online, ${data.offline} offline`;
            if (data.skipped > 0) {
                msg += `, ${data.skipped} skipped (missing credentials)`;
            }
            showToast(msg, 'success');
            await loadServers();
            await loadStats();
        } else {
            showToast(data.error || 'Scan failed', 'error');
        }
    } catch (error) {
        hideLoading();
        if (btn) btn.disabled = false;
        showToast('An error occurred', 'error');
    }
}

// ==================== EXPORT ====================

function showExportModal() {
    // Update the current project name in export modal
    const exportCurrentName = document.getElementById('exportCurrentProjectName');
    if (exportCurrentName) {
        if (currentProjectId === null) {
            exportCurrentName.textContent = 'All servers (no filter)';
        } else if (currentProjectId === 'unassigned') {
            exportCurrentName.textContent = 'Unassigned servers';
        } else {
            const project = projects.find(p => p.id === currentProjectId);
            exportCurrentName.textContent = project ? project.name : 'Selected project';
        }
    }
    
    showModal('exportModal');
}

function exportCurrentProject() {
    closeModal('exportModal');
    
    if (servers.length === 0) {
        showToast('No servers to export', 'warning');
        return;
    }
    
    showLoading('Generating Excel report...');
    
    let endpoint = `${API_BASE}/api/export/excel`;
    
    if (currentProjectId !== null && currentProjectId !== 'unassigned') {
        endpoint = `${API_BASE}/api/export/excel/project/${currentProjectId}`;
    }
    
    const link = document.createElement('a');
    link.href = endpoint;
    link.download = '';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    setTimeout(() => {
        hideLoading();
        showToast('Excel raporu indirildi!', 'success');
    }, 1000);
}

function exportAllProjects() {
    closeModal('exportModal');
    
    showLoading('Generating Excel report for all projects...');
    
    const link = document.createElement('a');
    link.href = `${API_BASE}/api/export/excel/all-projects`;
    link.download = '';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    setTimeout(() => {
        hideLoading();
        showToast('All projects Excel report downloaded!', 'success');
    }, 1500);
}

// Keep old function for backward compatibility
function exportExcel() {
    showExportModal();
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
            <td>${renderProjectBadge(server.project_name)}</td>
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
                    <button class="action-btn" onclick="showAssignProjectModal(${server.id})" title="Assign to Project">📂</button>
                    <button class="action-btn" onclick="showSetCredsModal(${server.id})" title="Kimlik Bilgisi">🔑</button>
                    <button class="action-btn scan" onclick="scanServer(${server.id})" title="Tara">🔄</button>
                    <button class="action-btn delete" onclick="deleteServer(${server.id})" title="Sil">🗑️</button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function renderProjectBadge(projectName) {
    if (!projectName) {
        return '<span class="project-badge unassigned">Unassigned</span>';
    }
    return `<span class="project-badge">${escapeHtml(projectName)}</span>`;
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
                    <span class="detail-label">IP Address</span>
                    <span class="detail-value">${escapeHtml(server.ip)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Domain</span>
                    <span class="detail-value">${escapeHtml(server.domain || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Operating System</span>
                    <span class="detail-value">${escapeHtml(server.os_type)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">OS Version</span>
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
                    <span class="detail-label">Serial Number</span>
                    <span class="detail-value">${escapeHtml(server.serial || '-')}</span>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>⚡ CPU</h3>
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
                <h3>🧠 Bellek</h3>
                <div class="detail-row">
                    <span class="detail-label">Fiziksel RAM</span>
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

// ==================== SET CREDENTIALS MODAL ====================

function showSetCredsModal(serverId) {
    const server = servers.find(s => s.id === serverId);
    if (!server) return;
    
    const serverIdInput = document.getElementById('credServerId');
    const serverInfo = document.getElementById('credServerInfo');
    const usernameInput = document.getElementById('credUsername');
    const passwordInput = document.getElementById('credPassword');
    
    if (serverIdInput) serverIdInput.value = serverId;
    if (serverInfo) serverInfo.textContent = `Server: ${server.ip} (${server.os_type})`;
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
        showToast('Please enter username and password', 'warning');
        return;
    }
    
    showLoading('Saving...');
    
    try {
        const data = await apiCall(`/api/servers/${serverId}/credentials`, {
            method: 'PUT',
            body: JSON.stringify({ username, password })
        });
        
        hideLoading();
        
        if (data.success) {
            showToast('Credentials saved!', 'success');
            closeModal('setCredsModal');
            await loadServers();
        } else {
            showToast(data.error || 'Failed to save', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Error saving credentials:', error);
        showToast('An error occurred: ' + (error.message || 'Unknown error'), 'error');
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
    // Show info about which project servers will be added to
    const importInfo = document.querySelector('#importModal .import-info');
    if (importInfo && currentProjectId !== null && currentProjectId !== 'unassigned') {
        const project = projects.find(p => p.id === currentProjectId);
        if (project) {
            // Add project info if not already there
            let projectNote = importInfo.querySelector('.project-note');
            if (!projectNote) {
                projectNote = document.createElement('p');
                projectNote.className = 'project-note';
                projectNote.style.cssText = 'margin-top: 10px; padding: 8px; background: rgba(16, 185, 129, 0.1); border-radius: 6px; color: var(--accent-primary);';
                importInfo.appendChild(projectNote);
            }
            projectNote.innerHTML = `📂 Servers will be added to project <strong>"${escapeHtml(project.name)}"</strong>`;
        }
    } else {
        const projectNote = document.querySelector('#importModal .project-note');
        if (projectNote) {
            projectNote.remove();
        }
    }
    
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
    showToast('Data refreshed', 'info');
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

// ==================== REPORT COMPARISON ====================

function showCompareModal() {
    // Reset all forms
    document.querySelectorAll('#compareModal input[type="file"]').forEach(input => {
        input.value = '';
    });
    
    // Reset to first tab
    switchCompareTab('scan-hpsm');
    
    showModal('compareModal');
}

function switchCompareTab(tabId) {
    // Update tab buttons
    document.querySelectorAll('.compare-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.compare-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`tab-${tabId}`).classList.add('active');
}

async function compareReports(event, compareType) {
    event.preventDefault();
    
    let formData = new FormData();
    let endpoint = '';
    
    if (compareType === 'scan-hpsm') {
        const scanFile = document.getElementById('scanFile1').files[0];
        const hpsmFile = document.getElementById('hpsmFile1').files[0];
        
        if (!scanFile || !hpsmFile) {
            showToast('Please select both files', 'warning');
            return;
        }
        
        formData.append('scan_report', scanFile);
        formData.append('hpsm_report', hpsmFile);
        endpoint = '/api/compare/scan-hpsm';
        
    } else if (compareType === 'scan-zabbix') {
        const scanFile = document.getElementById('scanFile2').files[0];
        const zabbixFile = document.getElementById('zabbixFile1').files[0];
        
        if (!scanFile || !zabbixFile) {
            showToast('Please select both files', 'warning');
            return;
        }
        
        formData.append('scan_report', scanFile);
        formData.append('zabbix_report', zabbixFile);
        endpoint = '/api/compare/scan-zabbix';
        
    } else if (compareType === 'hpsm-zabbix') {
        const hpsmFile = document.getElementById('hpsmFile3').files[0];
        const zabbixFile = document.getElementById('zabbixFile3').files[0];
        
        if (!hpsmFile || !zabbixFile) {
            showToast('Please select both files', 'warning');
            return;
        }
        
        formData.append('hpsm_report', hpsmFile);
        formData.append('zabbix_report', zabbixFile);
        endpoint = '/api/compare/hpsm-zabbix';
        
    } else if (compareType === 'full') {
        const scanFile = document.getElementById('scanFile3').files[0];
        const hpsmFile = document.getElementById('hpsmFile2').files[0];
        const zabbixFile = document.getElementById('zabbixFile2').files[0];
        
        if (!scanFile || !hpsmFile || !zabbixFile) {
            showToast('Please select all three files', 'warning');
            return;
        }
        
        formData.append('scan_report', scanFile);
        formData.append('hpsm_report', hpsmFile);
        formData.append('zabbix_report', zabbixFile);
        endpoint = '/api/compare/full';
    }
    
    showLoading('Comparing reports...');
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        hideLoading();
        
        if (data.success) {
            closeModal('compareModal');
            showCompareResults(data.results, compareType);
        } else {
            showToast(data.error || 'Comparison failed', 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('Error: ' + error.message, 'error');
    }
}

function showCompareResults(results, compareType) {
    const content = document.getElementById('compareResultsContent');
    if (!content) return;
    
    let html = '';
    
    if (compareType === 'full') {
        // 3-way comparison results
        html = renderFullCompareResults(results);
    } else {
        // 2-way comparison results
        html = renderTwoWayCompareResults(results, compareType);
    }
    
    content.innerHTML = html;
    
    // Store results for download
    window.lastCompareResults = results;
    window.lastCompareType = compareType;
    
    showModal('compareResultsModal');
}

function renderTwoWayCompareResults(results, compareType) {
    let source1, source2, count1, count2, missingIn2, missingIn1;
    
    if (compareType === 'scan-hpsm') {
        source1 = 'Scan Report';
        source2 = 'HPSM';
        count1 = results.scan_count || 0;
        count2 = results.hpsm_count || 0;
        missingIn2 = results.missing_in_hpsm || [];
        missingIn1 = results.missing_in_scan || [];
    } else if (compareType === 'scan-zabbix') {
        source1 = 'Scan Report';
        source2 = 'Zabbix';
        count1 = results.scan_count || 0;
        count2 = results.zabbix_count || 0;
        missingIn2 = results.missing_in_zabbix || [];
        missingIn1 = results.missing_in_scan || [];
    } else if (compareType === 'hpsm-zabbix') {
        source1 = 'HPSM';
        source2 = 'Zabbix';
        count1 = results.hpsm_count || 0;
        count2 = results.zabbix_count || 0;
        missingIn2 = results.missing_in_zabbix || [];
        missingIn1 = results.missing_in_hpsm || [];
    }
    
    const matching = results.matching || [];
    
    return `
        <div class="compare-results">
            <div class="compare-summary">
                <div class="compare-stat info">
                    <div class="compare-stat-value">${count1}</div>
                    <div class="compare-stat-label">${source1}</div>
                </div>
                <div class="compare-stat info">
                    <div class="compare-stat-value">${count2}</div>
                    <div class="compare-stat-label">${source2}</div>
                </div>
                <div class="compare-stat success">
                    <div class="compare-stat-value">${matching.length}</div>
                    <div class="compare-stat-label">Matching</div>
                </div>
                <div class="compare-stat danger">
                    <div class="compare-stat-value">${missingIn2.length}</div>
                    <div class="compare-stat-label">Missing in ${source2}</div>
                </div>
                <div class="compare-stat warning">
                    <div class="compare-stat-value">${missingIn1.length}</div>
                    <div class="compare-stat-label">Missing in ${source1}</div>
                </div>
            </div>
            
            <div class="compare-section">
                <h4>❌ Missing in ${source2} (${missingIn2.length})</h4>
                <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 10px;">
                    These servers are in ${source1} but not in ${source2}
                </p>
                <div class="compare-list">
                    ${missingIn2.length > 0 
                        ? missingIn2.map(h => `<div class="compare-list-item">${escapeHtml(h)}</div>`).join('')
                        : '<div class="compare-list-empty">No missing records ✓</div>'
                    }
                </div>
            </div>
            
            <div class="compare-section">
                <h4>⚠️ Missing in ${source1} (${missingIn1.length})</h4>
                <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 10px;">
                    These servers are in ${source2} but not in ${source1}
                </p>
                <div class="compare-list">
                    ${missingIn1.length > 0 
                        ? missingIn1.map(h => `<div class="compare-list-item">${escapeHtml(h)}</div>`).join('')
                        : '<div class="compare-list-empty">No missing records ✓</div>'
                    }
                </div>
            </div>
            
            <div class="compare-actions">
                <button class="btn btn-secondary" onclick="closeModal('compareResultsModal')">Close</button>
                <button class="btn btn-info" onclick="downloadCompareReport()">📥 Download Report</button>
            </div>
        </div>
    `;
}

function renderFullCompareResults(results) {
    const inAll3 = results.in_all_three || [];
    const inScanHpsm = results.in_scan_and_hpsm_only || [];
    const inScanZabbix = results.in_scan_and_zabbix_only || [];
    const inHpsmZabbix = results.in_hpsm_and_zabbix_only || [];
    const onlyInScan = results.only_in_scan || [];
    const onlyInHpsm = results.only_in_hpsm || [];
    const onlyInZabbix = results.only_in_zabbix || [];
    
    return `
        <div class="compare-results">
            <div class="compare-summary">
                <div class="compare-stat info">
                    <div class="compare-stat-value">${results.scan_count || 0}</div>
                    <div class="compare-stat-label">Scan Report</div>
                </div>
                <div class="compare-stat info">
                    <div class="compare-stat-value">${results.hpsm_count || 0}</div>
                    <div class="compare-stat-label">HPSM</div>
                </div>
                <div class="compare-stat info">
                    <div class="compare-stat-value">${results.zabbix_count || 0}</div>
                    <div class="compare-stat-label">Zabbix</div>
                </div>
                <div class="compare-stat success">
                    <div class="compare-stat-value">${inAll3.length}</div>
                    <div class="compare-stat-label">✓ Verified (All 3)</div>
                </div>
            </div>
            
            <div class="compare-section" style="border-left: 4px solid var(--success);">
                <h4>✅ Verified - In All 3 Systems (${inAll3.length})</h4>
                <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 10px;">
                    These servers are confirmed in Scan, HPSM, and Zabbix
                </p>
                <div class="compare-list">
                    ${inAll3.length > 0 
                        ? inAll3.slice(0, 50).map(h => `<div class="compare-list-item">${escapeHtml(h)}</div>`).join('') + (inAll3.length > 50 ? `<div class="compare-list-item">... and ${inAll3.length - 50} more</div>` : '')
                        : '<div class="compare-list-empty">No records found in all 3 systems</div>'
                    }
                </div>
            </div>
            
            <div class="compare-grid">
                <div class="compare-section" style="border-left: 4px solid var(--warning);">
                    <h4>⚠️ In Scan + HPSM only (${inScanHpsm.length})</h4>
                    <p style="font-size: 11px; color: var(--text-muted);">Missing from Zabbix</p>
                    <div class="compare-list">
                        ${inScanHpsm.length > 0 
                            ? inScanHpsm.map(h => `<div class="compare-list-item">${escapeHtml(h)}</div>`).join('')
                            : '<div class="compare-list-empty">None</div>'
                        }
                    </div>
                </div>
                
                <div class="compare-section" style="border-left: 4px solid var(--warning);">
                    <h4>⚠️ In Scan + Zabbix only (${inScanZabbix.length})</h4>
                    <p style="font-size: 11px; color: var(--text-muted);">Missing from HPSM</p>
                    <div class="compare-list">
                        ${inScanZabbix.length > 0 
                            ? inScanZabbix.map(h => `<div class="compare-list-item">${escapeHtml(h)}</div>`).join('')
                            : '<div class="compare-list-empty">None</div>'
                        }
                    </div>
                </div>
                
                <div class="compare-section" style="border-left: 4px solid var(--warning);">
                    <h4>⚠️ In HPSM + Zabbix only (${inHpsmZabbix.length})</h4>
                    <p style="font-size: 11px; color: var(--text-muted);">Missing from Scan</p>
                    <div class="compare-list">
                        ${inHpsmZabbix.length > 0 
                            ? inHpsmZabbix.map(h => `<div class="compare-list-item">${escapeHtml(h)}</div>`).join('')
                            : '<div class="compare-list-empty">None</div>'
                        }
                    </div>
                </div>
            </div>
            
            <div class="compare-grid">
                <div class="compare-section" style="border-left: 4px solid var(--danger);">
                    <h4>❌ Only in Scan (${onlyInScan.length})</h4>
                    <p style="font-size: 11px; color: var(--text-muted);">Review needed</p>
                    <div class="compare-list">
                        ${onlyInScan.length > 0 
                            ? onlyInScan.map(h => `<div class="compare-list-item">${escapeHtml(h)}</div>`).join('')
                            : '<div class="compare-list-empty">None</div>'
                        }
                    </div>
                </div>
                
                <div class="compare-section" style="border-left: 4px solid var(--danger);">
                    <h4>❌ Only in HPSM (${onlyInHpsm.length})</h4>
                    <p style="font-size: 11px; color: var(--text-muted);">Review needed</p>
                    <div class="compare-list">
                        ${onlyInHpsm.length > 0 
                            ? onlyInHpsm.map(h => `<div class="compare-list-item">${escapeHtml(h)}</div>`).join('')
                            : '<div class="compare-list-empty">None</div>'
                        }
                    </div>
                </div>
                
                <div class="compare-section" style="border-left: 4px solid var(--danger);">
                    <h4>❌ Only in Zabbix (${onlyInZabbix.length})</h4>
                    <p style="font-size: 11px; color: var(--text-muted);">Review needed</p>
                    <div class="compare-list">
                        ${onlyInZabbix.length > 0 
                            ? onlyInZabbix.map(h => `<div class="compare-list-item">${escapeHtml(h)}</div>`).join('')
                            : '<div class="compare-list-empty">None</div>'
                        }
                    </div>
                </div>
            </div>
            
            <div class="compare-actions">
                <button class="btn btn-secondary" onclick="closeModal('compareResultsModal')">Close</button>
                <button class="btn btn-info" onclick="downloadCompareReport()">📥 Download Report</button>
            </div>
        </div>
    `;
}

async function downloadCompareReport() {
    if (!window.lastCompareResults) {
        showToast('No report to download', 'warning');
        return;
    }
    
    showLoading('Generating report...');
    
    try {
        const response = await fetch(`${API_BASE}/api/compare/download`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...window.lastCompareResults,
                compare_type: window.lastCompareType
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `comparison_report_${new Date().toISOString().slice(0,10)}.xlsx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            hideLoading();
            showToast('Report downloaded!', 'success');
        } else {
            hideLoading();
            showToast('Download failed', 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('Error occurred', 'error');
    }
}
