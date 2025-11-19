// Files Tab - Dosya tree yapısı

// Global değişkenler - sadece bir kez tanımla
if (typeof currentPath === 'undefined') {
    var currentPath = '/';
}
if (typeof fileTree === 'undefined') {
    var fileTree = {};
}

function loadFiles() {
    console.log('Loading files for container:', currentContainerId);
    
    const filesTree = document.getElementById('filesTree');
    const currentPathElement = document.getElementById('currentPath');
    
    filesTree.innerHTML = '<div class="loading">Loading files...</div>';
    currentPathElement.textContent = currentPath;
    
    fetch(`/docker-manager/api/container/${currentContainerId}/files/?path=${encodeURIComponent(currentPath)}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayFiles(data.files);
        } else {
            showFilesError(data.message);
        }
    })
    .catch(error => {
        showFilesError('Files yüklenirken hata oluştu: ' + error.message);
    });
}

function displayFiles(files) {
    const container = document.getElementById('filesTree');
    
    if (!files || files.length === 0) {
        container.innerHTML = '<div class="no-files">No files found</div>';
        return;
    }
    
    // Dosyaları türüne göre sırala (klasörler önce)
    const sortedFiles = files.sort((a, b) => {
        if (a.type === 'directory' && b.type !== 'directory') return -1;
        if (a.type !== 'directory' && b.type === 'directory') return 1;
        return a.name.localeCompare(b.name);
    });
    
    const filesHTML = sortedFiles.map(file => {
        const icon = getFileIcon(file);
        const size = file.size ? formatFileSize(file.size) : '';
        const permissions = file.permissions || '';
        
        return `
            <div class="file-item" onclick="handleFileClick('${file.name}', '${file.type}')">
                <div class="file-icon">${icon}</div>
                <div class="file-name">${escapeHtml(file.name)}</div>
                <div class="file-size">${size}</div>
                <div class="file-permissions">${permissions}</div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = filesHTML;
}

function getFileIcon(file) {
    if (file.type === 'directory') {
        return '<i class="fas fa-folder" style="color: #ffa500;"></i>';
    } else if (file.name.endsWith('.js')) {
        return '<i class="fas fa-file-code" style="color: #f7df1e;"></i>';
    } else if (file.name.endsWith('.html')) {
        return '<i class="fas fa-file-code" style="color: #e34c26;"></i>';
    } else if (file.name.endsWith('.css')) {
        return '<i class="fas fa-file-code" style="color: #1572b6;"></i>';
    } else if (file.name.endsWith('.py')) {
        return '<i class="fas fa-file-code" style="color: #3776ab;"></i>';
    } else if (file.name.endsWith('.json')) {
        return '<i class="fas fa-file-code" style="color: #000000;"></i>';
    } else if (file.name.endsWith('.txt') || file.name.endsWith('.md')) {
        return '<i class="fas fa-file-alt" style="color: #6c757d;"></i>';
    } else if (file.name.endsWith('.jpg') || file.name.endsWith('.jpeg') || file.name.endsWith('.png') || file.name.endsWith('.gif')) {
        return '<i class="fas fa-file-image" style="color: #28a745;"></i>';
    } else {
        return '<i class="fas fa-file" style="color: #6c757d;"></i>';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function handleFileClick(name, type) {
    if (type === 'directory') {
        // Klasöre gir
        if (currentPath === '/') {
            currentPath = '/' + name;
        } else {
            currentPath = currentPath + '/' + name;
        }
        loadFiles();
    } else {
        // Dosya içeriğini göster
        showFileContent(name);
    }
}

function showFileContent(filename) {
    const fullPath = currentPath === '/' ? '/' + filename : currentPath + '/' + filename;
    
    fetch(`/docker-manager/api/container/${currentContainerId}/files/content/?path=${encodeURIComponent(fullPath)}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayFileContent(filename, data.content);
        } else {
            showNotification('File content could not be loaded: ' + data.message);
        }
    })
    .catch(error => {
        showNotification('File content error: ' + error.message);
    });
}

function displayFileContent(filename, content) {
    // Modal veya yeni tab açarak dosya içeriğini göster
    const modal = document.createElement('div');
    modal.className = 'file-modal';
    modal.innerHTML = `
        <div class="file-modal-content">
            <div class="file-modal-header">
                <h3>${escapeHtml(filename)}</h3>
                <button onclick="closeFileModal()" class="close-btn">&times;</button>
            </div>
            <div class="file-modal-body">
                <pre class="file-content">${escapeHtml(content)}</pre>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function closeFileModal() {
    const modal = document.querySelector('.file-modal');
    if (modal) {
        modal.remove();
    }
}

function refreshFiles() {
    loadFiles();
}

function showFilesError(message) {
    const container = document.getElementById('filesTree');
    container.innerHTML = `<div class="error">Error: ${escapeHtml(message)}</div>`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Files için CSS ekle
const style = document.createElement('style');
style.textContent = `
    .file-item {
        display: flex;
        align-items: center;
        padding: 8px 12px;
        border-radius: 4px;
        cursor: pointer;
        transition: background 0.2s ease;
        border-bottom: 1px solid #f0f0f0;
    }
    
    .file-item:hover {
        background: #f8f9fa;
    }
    
    .file-icon {
        margin-right: 12px;
        width: 20px;
        text-align: center;
    }
    
    .file-name {
        flex: 1;
        font-family: monospace;
        font-size: 14px;
        color: #1a202c;
    }
    
    .file-size {
        color: #718096;
        font-size: 12px;
        margin-left: 8px;
        min-width: 60px;
        text-align: right;
    }
    
    .file-permissions {
        color: #718096;
        font-size: 12px;
        margin-left: 8px;
        min-width: 80px;
        font-family: monospace;
    }
    
    .loading {
        text-align: center;
        padding: 40px;
        color: #718096;
    }
    
    .no-files {
        text-align: center;
        padding: 40px;
        color: #718096;
        font-style: italic;
    }
    
    .error {
        color: #dc3545;
        padding: 20px;
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 4px;
    }
    
    .file-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .file-modal-content {
        background: white;
        border-radius: 8px;
        width: 80%;
        height: 80%;
        display: flex;
        flex-direction: column;
    }
    
    .file-modal-header {
        padding: 16px 20px;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .file-modal-body {
        flex: 1;
        overflow: auto;
        padding: 20px;
    }
    
    .file-content {
        background: #f8f9fa;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 16px;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.4;
        white-space: pre-wrap;
        overflow-x: auto;
    }
    
    .close-btn {
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: #718096;
    }
`;
document.head.appendChild(style);
