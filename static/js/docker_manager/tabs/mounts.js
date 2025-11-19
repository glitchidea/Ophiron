// Mounts Tab - Bind mounts bilgileri

function loadMounts() {
    console.log('Loading mounts for container:', currentContainerId);
    
    const mountsList = document.getElementById('mountsList');
    mountsList.innerHTML = '<div class="loading">Loading mount information...</div>';
    
    fetch(`/docker-manager/api/container/${currentContainerId}/mounts/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayMounts(data.mounts);
        } else {
            showMountsError(data.message);
        }
    })
    .catch(error => {
        showMountsError('Mounts yüklenirken hata oluştu: ' + error.message);
    });
}

function displayMounts(mounts) {
    const container = document.getElementById('mountsList');
    
    if (!mounts || mounts.length === 0) {
        container.innerHTML = '<div class="no-mounts">No bind mounts found</div>';
        return;
    }
    
    const mountsHTML = mounts.map(mount => {
        return `
            <div class="mount-item">
                <div class="mount-header">
                    <span class="mount-type">${mount.Type || 'bind'}</span>
                    <span class="mount-mode">${mount.Mode || 'rw'}</span>
                </div>
                <div class="mount-source">
                    <i class="fas fa-folder"></i>
                    ${escapeHtml(mount.Source || 'N/A')}
                </div>
                <div class="mount-destination">
                    <i class="fas fa-arrow-right"></i>
                    ${escapeHtml(mount.Destination || 'N/A')}
                </div>
                ${mount.Propagation ? `<div class="mount-propagation">Propagation: ${mount.Propagation}</div>` : ''}
                ${mount.RW !== undefined ? `<div class="mount-rw">Read/Write: ${mount.RW ? 'Yes' : 'No'}</div>` : ''}
            </div>
        `;
    }).join('');
    
    container.innerHTML = mountsHTML;
}

function showMountsError(message) {
    const container = document.getElementById('mountsList');
    container.innerHTML = `<div class="error">Error: ${escapeHtml(message)}</div>`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Mounts için CSS ekle
const style = document.createElement('style');
style.textContent = `
    .mount-item {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .mount-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    
    .mount-type {
        background: #007bff;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
    }
    
    .mount-mode {
        background: #28a745;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
    }
    
    .mount-source {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        color: #1a202c;
        margin-bottom: 8px;
        font-family: monospace;
        font-size: 14px;
    }
    
    .mount-destination {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #718096;
        font-family: monospace;
        font-size: 14px;
        margin-bottom: 8px;
    }
    
    .mount-propagation,
    .mount-rw {
        font-size: 12px;
        color: #718096;
        margin-top: 4px;
    }
    
    .loading {
        text-align: center;
        padding: 40px;
        color: #718096;
    }
    
    .no-mounts {
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
`;
document.head.appendChild(style);
