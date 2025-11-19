// Container Detail - Ana JavaScript dosyası

// Global değişkenler - sadece bir kez tanımla
if (typeof currentContainerId === 'undefined') {
    var currentContainerId = '';
}
if (typeof currentTab === 'undefined') {
    var currentTab = 'logs';
}
if (typeof logsInterval === 'undefined') {
    var logsInterval = null;
}
if (typeof statsInterval === 'undefined') {
    var statsInterval = null;
}

// Ensure jsTranslations is available
if (typeof window.jsTranslations === 'undefined') {
    window.jsTranslations = {};
}

document.addEventListener('DOMContentLoaded', function() {
    initializeContainerDetail();
});

function initializeContainerDetail() {
    // Container ID'yi URL'den al
    const pathParts = window.location.pathname.split('/');
    currentContainerId = pathParts[pathParts.length - 2]; // URL: /container/{id}/detail/
    
    // Tab navigation'ı ayarla
    setupTabNavigation();
    
    // İlk tab'ı yükle
    loadTab('logs');
}

function setupTabNavigation() {
    const tabs = document.querySelectorAll('.nav-tab');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Tüm tab'ları gizle
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Tüm nav tab'ları deaktif et
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Seçilen tab'ı aktif et
    document.getElementById(`${tabName}-content`).classList.add('active');
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    currentTab = tabName;
    
    // Tab'a özel yükleme
    loadTab(tabName);
}

function loadTab(tabName) {
    switch(tabName) {
        case 'logs':
            loadLogs();
            break;
        case 'inspect':
            loadInspect();
            break;
        case 'mounts':
            loadMounts();
            break;
        case 'files':
            loadFiles();
            break;
        case 'stats':
            loadStats();
            break;
    }
}

// Container işlemleri
function stopContainer(containerId) {
    if (!containerId || containerId === 'null' || containerId === 'undefined') {
        console.error('Invalid containerId for stopContainer:', containerId);
        showNotification((window.jsTranslations['Error'] || 'Error') + ': ' + (window.jsTranslations['Container ID not found'] || 'Container ID not found'));
        return;
    }
    const confirmMsg = (window.jsTranslations['Stop container'] || 'Stop container') + ' ' + containerId + '?';
    if (confirm(confirmMsg)) {
        const startingMsg = (window.jsTranslations['Stopping container'] || 'Stopping container') + ' ' + containerId + '...';
        showNotification(startingMsg);
        
        fetch(`/docker-manager/api/container/${containerId}/stop/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const successMsg = (window.jsTranslations['Container stopped'] || 'Container stopped') + ' ' + containerId;
                showNotification(successMsg);
                setTimeout(() => location.reload(), 1000);
            } else {
                const errorMsg = (window.jsTranslations['Error'] || 'Error') + ': ' + data.message;
                showNotification(errorMsg);
            }
        })
        .catch(error => {
            const errorMsg = (window.jsTranslations['Error'] || 'Error') + ': ' + error.message;
            showNotification(errorMsg);
        });
    }
}

function startContainer(containerId) {
    if (!containerId || containerId === 'null' || containerId === 'undefined') {
        console.error('Invalid containerId for startContainer:', containerId);
        showNotification((window.jsTranslations['Error'] || 'Error') + ': ' + (window.jsTranslations['Container ID not found'] || 'Container ID not found'));
        return;
    }
    const startingMsg = (window.jsTranslations['Starting container'] || 'Starting container') + ' ' + containerId + '...';
    showNotification(startingMsg);
    
    fetch(`/docker-manager/api/container/${containerId}/start/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const successMsg = (window.jsTranslations['Container started'] || 'Container started') + ' ' + containerId;
            showNotification(successMsg);
            setTimeout(() => location.reload(), 1000);
        } else {
            const errorMsg = (window.jsTranslations['Error'] || 'Error') + ': ' + data.message;
            showNotification(errorMsg);
        }
    })
    .catch(error => {
        const errorMsg = (window.jsTranslations['Error'] || 'Error') + ': ' + error.message;
        showNotification(errorMsg);
    });
}

function restartContainer(containerId) {
    if (!containerId || containerId === 'null' || containerId === 'undefined') {
        console.error('Invalid containerId for restartContainer:', containerId);
        showNotification((window.jsTranslations['Error'] || 'Error') + ': ' + (window.jsTranslations['Container ID not found'] || 'Container ID not found'));
        return;
    }
    const confirmMsg = (window.jsTranslations['Restart container'] || 'Restart container') + ' ' + containerId + '?';
    if (confirm(confirmMsg)) {
        const restartingMsg = (window.jsTranslations['Restarting container'] || 'Restarting container') + ' ' + containerId + '...';
        showNotification(restartingMsg);
        
        fetch(`/docker-manager/api/container/${containerId}/restart/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const successMsg = (window.jsTranslations['Container restarted'] || 'Container restarted') + ' ' + containerId;
                showNotification(successMsg);
                setTimeout(() => location.reload(), 1000);
            } else {
                const errorMsg = (window.jsTranslations['Error'] || 'Error') + ': ' + data.message;
                showNotification(errorMsg);
            }
        })
        .catch(error => {
            const errorMsg = (window.jsTranslations['Error'] || 'Error') + ': ' + error.message;
            showNotification(errorMsg);
        });
    }
}

function deleteContainer(containerId) {
    if (!containerId || containerId === 'null' || containerId === 'undefined') {
        console.error('Invalid containerId for deleteContainer:', containerId);
        showNotification((window.jsTranslations['Error'] || 'Error') + ': ' + (window.jsTranslations['Container ID not found'] || 'Container ID not found'));
        return;
    }
    const confirmMsg = (window.jsTranslations['Delete container'] || 'Delete container') + ' ' + containerId + '? ' + (window.jsTranslations['This action cannot be undone'] || 'This action cannot be undone') + '.';
    if (confirm(confirmMsg)) {
        const deletingMsg = (window.jsTranslations['Deleting container'] || 'Deleting container') + ' ' + containerId + '...';
        showNotification(deletingMsg);
        
        fetch(`/docker-manager/api/container/${containerId}/remove/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const successMsg = (window.jsTranslations['Container deleted'] || 'Container deleted') + ' ' + containerId;
                showNotification(successMsg);
                setTimeout(() => window.location.href = '/docker-manager/', 1000);
            } else {
                const errorMsg = (window.jsTranslations['Error'] || 'Error') + ': ' + data.message;
                showNotification(errorMsg);
            }
        })
        .catch(error => {
            const errorMsg = (window.jsTranslations['Error'] || 'Error') + ': ' + error.message;
            showNotification(errorMsg);
        });
    }
}

// Navigation
function goBack() {
    window.location.href = '/docker-manager/';
}


// Utility functions
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        const successMsg = window.jsTranslations['Copied to clipboard'] || 'Copied to clipboard';
        showNotification(successMsg);
    }).catch(err => {
        console.error('Failed to copy: ', err);
        const errorMsg = window.jsTranslations['Failed to copy'] || 'Failed to copy';
        showNotification(errorMsg);
    });
}

function showNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #007acc;
        color: white;
        padding: 12px 20px;
        border-radius: 4px;
        z-index: 1000;
        font-size: 14px;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Tab yükleme fonksiyonları (modüller tarafından override edilecek)
function loadLogs() {
    // logs.js tarafından override edilecek
}

function loadInspect() {
    // inspect.js tarafından override edilecek
}

function loadMounts() {
    // mounts.js tarafından override edilecek
}

function loadTerminal() {
    // terminal.js tarafından override edilecek
}

function loadFiles() {
    // files.js tarafından override edilecek
}

function loadStats() {
    // stats.js tarafından override edilecek
}
