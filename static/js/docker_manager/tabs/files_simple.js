// Files Tab - Basit versiyon

// Global değişkenler - navigasyon için
if (typeof pathHistory === 'undefined') {
    var pathHistory = ['/'];
}
if (typeof currentPathIndex === 'undefined') {
    var currentPathIndex = 0;
}

// Ensure jsTranslations is available
if (typeof window.jsTranslations === 'undefined') {
    window.jsTranslations = {};
}

function loadFiles() {
    console.log('Loading files...');
    
    const filesTree = document.getElementById('filesTree');
    const currentPathElement = document.getElementById('currentPath');
    
    if (!filesTree) {
        console.error('filesTree element not found');
        return;
    }
    
    const loadingMsg = window.jsTranslations['Loading files...'] || 'Loading files...';
    filesTree.innerHTML = '<div class="loading">' + loadingMsg + '</div>';
    
    // Container ID'yi URL'den al
    const pathParts = window.location.pathname.split('/');
    let containerId = pathParts[pathParts.length - 2];
    if (!containerId || containerId === 'null' || containerId === 'undefined') {
        const metaEl = document.getElementById('containerIdMeta');
        if (metaEl && metaEl.content) {
            containerId = metaEl.content;
        }
    }
    
    if (!containerId) {
        const errorMsg = window.jsTranslations['Container ID not found'] || 'Container ID not found';
        filesTree.innerHTML = '<div class="error">' + errorMsg + '</div>';
        return;
    }
    
    console.log('Fetching files for container:', containerId);
    
    fetch(`/docker-manager/api/container/${containerId}/files/?path=/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log('Files response:', data);
        if (data.success) {
            displayFiles(data.files, data.path);
        } else {
            const errorMsg = (window.jsTranslations['Error'] || 'Error') + ': ' + data.message;
            filesTree.innerHTML = '<div class="error">' + errorMsg + '</div>';
        }
    })
    .catch(error => {
        console.error('Files error:', error);
        const errorMsg = (window.jsTranslations['Error'] || 'Error') + ': ' + error.message;
        filesTree.innerHTML = '<div class="error">' + errorMsg + '</div>';
    });
}

function displayFiles(files, currentPath) {
    const filesTree = document.getElementById('filesTree');
    const currentPathElement = document.getElementById('currentPath');
    
    console.log('Displaying files, count:', files ? files.length : 0);
    
    if (currentPathElement) {
        currentPathElement.textContent = currentPath;
    }
    
    if (!files || files.length === 0) {
        filesTree.innerHTML = '<div class="no-files">No files found</div>';
        return;
    }
    
    let filesHTML = '<div class="files-list">';
    
    files.forEach((file, index) => {
        const icon = file.type === 'directory' ? '📁' : '📄';
        const size = file.size || '0';
        const permissions = file.permissions || '';
        const owner = file.owner || '';
        const group = file.group || '';
        
        filesHTML += `
            <div class="file-item" data-path="${file.path}" data-type="${file.type}">
                <div class="file-icon">${icon}</div>
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-details">
                        <span class="file-size">${size}</span>
                        <span class="file-permissions">${permissions}</span>
                        <span class="file-owner">${owner}:${group}</span>
                    </div>
                </div>
            </div>
        `;
    });
    
    filesHTML += '</div>';
    filesTree.innerHTML = filesHTML;
    
    // Click event listeners
    document.querySelectorAll('.file-item').forEach(item => {
        item.addEventListener('click', function() {
            const path = this.dataset.path;
            const type = this.dataset.type;
            
            console.log('Clicked:', path, type);
            
            if (type === 'directory') {
                loadDirectory(path);
            } else {
                loadFile(path);
            }
        });
    });
    
    console.log('Files displayed successfully');
}

function loadDirectory(path) {
    console.log('Loading directory:', path);
    
    const filesTree = document.getElementById('filesTree');
    const currentPathElement = document.getElementById('currentPath');
    
    filesTree.innerHTML = '<div class="loading">Loading directory...</div>';
    
    const pathParts = window.location.pathname.split('/');
    let containerId = pathParts[pathParts.length - 2];
    if (!containerId || containerId === 'null' || containerId === 'undefined') {
        const metaEl = document.getElementById('containerIdMeta');
        if (metaEl && metaEl.content) {
            containerId = metaEl.content;
        }
    }
    
    fetch(`/docker-manager/api/container/${containerId}/files/?path=${encodeURIComponent(path)}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log('Directory response:', data);
        if (data.success) {
            displayFiles(data.files, data.path);
            addToHistory(data.path);
        } else {
            filesTree.innerHTML = `<div class="error">Error: ${data.message}</div>`;
        }
    })
    .catch(error => {
        console.error('Directory load error:', error);
        filesTree.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    });
}

function loadFile(path) {
    console.log('Loading file:', path);
    
    const pathParts = window.location.pathname.split('/');
    let containerId = pathParts[pathParts.length - 2];
    if (!containerId || containerId === 'null' || containerId === 'undefined') {
        const metaEl = document.getElementById('containerIdMeta');
        if (metaEl && metaEl.content) {
            containerId = metaEl.content;
        }
    }
    
    fetch(`/docker-manager/api/container/${containerId}/files/content/?path=${encodeURIComponent(path)}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayFileContent(data.content, path);
        } else {
            alert(`Error: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('File load error:', error);
        alert(`Error: ${error.message}`);
    });
}

function displayFileContent(content, path) {
    const modal = document.createElement('div');
    modal.className = 'file-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>File: ${path}</h3>
                <button class="close-btn">&times;</button>
            </div>
            <div class="modal-body">
                <pre>${escapeHtml(content)}</pre>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close button
    modal.querySelector('.close-btn').addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    // Close on backdrop click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Navigasyon fonksiyonları
function goBackInFiles() {
    if (currentPathIndex > 0) {
        currentPathIndex--;
        const path = pathHistory[currentPathIndex];
        loadDirectory(path);
        updateNavigationButtons();
    }
}

function goUp() {
    const currentPath = document.getElementById('currentPath').textContent;
    const parentPath = currentPath.substring(0, currentPath.lastIndexOf('/'));
    if (parentPath === '') {
        loadDirectory('/');
    } else {
        loadDirectory(parentPath);
    }
}

function updateNavigationButtons() {
    const backBtn = document.getElementById('backBtn');
    if (backBtn) {
        backBtn.disabled = currentPathIndex <= 0;
    }
}

function addToHistory(path) {
    // Mevcut path'i history'ye ekle
    if (pathHistory[currentPathIndex] !== path) {
        // Yeni path'i ekle ve index'i güncelle
        pathHistory = pathHistory.slice(0, currentPathIndex + 1);
        pathHistory.push(path);
        currentPathIndex = pathHistory.length - 1;
    }
    updateNavigationButtons();
}
