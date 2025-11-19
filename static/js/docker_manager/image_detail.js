// Image Detail - JavaScript

// Global variables
let currentImageId = null;
let currentTab = 'overview';

document.addEventListener('DOMContentLoaded', function() {
    initializeImageDetail();
});

function initializeImageDetail() {
    console.log('Initializing Image Detail...');
    
    // Get image ID from URL
    const pathParts = window.location.pathname.split('/');
    currentImageId = pathParts[pathParts.length - 2];
    
    console.log('Current Image ID:', currentImageId);
    
    // Setup tab functionality
    setupTabFunctionality();
    
    // Load initial data
    loadImageDetails();
}

function setupTabFunctionality() {
    const navTabs = document.querySelectorAll('.nav-tab');
    
    navTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    console.log('Switching to tab:', tabName);
    
    // Update active tab
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update active content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-content`).classList.add('active');
    
    currentTab = tabName;
    
    // Load tab-specific data
    loadTabData(tabName);
}

function loadTabData(tabName) {
    switch(tabName) {
        case 'overview':
            loadOverviewData();
            break;
        case 'layers':
            loadLayersData();
            break;
        case 'history':
            loadHistoryData();
            break;
        case 'logs':
            loadImageLogs(currentImageId);
            break;
        case 'inspect':
            loadInspectData();
            break;
        default:
            console.warn('Unknown tab:', tabName);
    }
}

function loadImageDetails() {
    console.log('Loading image details...');
    
    // Load overview data by default
    loadOverviewData();
}

function loadOverviewData() {
    console.log('Loading overview data...');
    
    // Load basic info
    loadBasicInfo();
    
    // Load labels
    loadLabels();
    
    // Load environment variables
    loadEnvironmentVariables();
    
    // Load exposed ports
    loadExposedPorts();
}

function loadBasicInfo() {
    fetch(`/docker-manager/api/image/${currentImageId}/inspect/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log('Basic info response:', data);
        if (data.success) {
            const inspect = data.inspect;
            
            // Update architecture
            const archElement = document.getElementById('architecture');
            if (archElement) {
                archElement.textContent = inspect.Architecture || 'Unknown';
            }
            
            // Update OS
            const osElement = document.getElementById('os');
            if (osElement) {
                osElement.textContent = inspect.Os || 'Unknown';
            }
        }
    })
    .catch(error => {
        console.error('Basic info load error:', error);
    });
}

function loadLabels() {
    fetch(`/docker-manager/api/image/${currentImageId}/inspect/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log('Labels response:', data);
        if (data.success) {
            displayLabels(data.inspect.Config?.Labels || {});
        } else {
            showEmptyState('labelsList', 'No labels found');
        }
    })
    .catch(error => {
        console.error('Labels load error:', error);
        showEmptyState('labelsList', 'Error loading labels');
    });
}

function displayLabels(labels) {
    const labelsList = document.getElementById('labelsList');
    if (!labelsList) return;
    
    if (Object.keys(labels).length === 0) {
        showEmptyState('labelsList', 'No labels found');
        return;
    }
    
    let labelsHTML = '';
    Object.entries(labels).forEach(([key, value]) => {
        labelsHTML += `
            <div class="label-item">
                <span class="label-key">${escapeHtml(key)}</span>
                <span class="label-value">${escapeHtml(value)}</span>
            </div>
        `;
    });
    
    labelsList.innerHTML = labelsHTML;
}

function loadEnvironmentVariables() {
    fetch(`/docker-manager/api/image/${currentImageId}/inspect/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log('Environment variables response:', data);
        if (data.success) {
            displayEnvironmentVariables(data.inspect.Config?.Env || []);
        } else {
            showEmptyState('envVarsList', 'No environment variables found');
        }
    })
    .catch(error => {
        console.error('Environment variables load error:', error);
        showEmptyState('envVarsList', 'Error loading environment variables');
    });
}

function displayEnvironmentVariables(envVars) {
    const envVarsList = document.getElementById('envVarsList');
    if (!envVarsList) return;
    
    if (envVars.length === 0) {
        showEmptyState('envVarsList', 'No environment variables found');
        return;
    }
    
    let envHTML = '';
    envVars.forEach(envVar => {
        const [key, value] = envVar.split('=', 2);
        envHTML += `
            <div class="env-item">
                <span class="env-key">${escapeHtml(key)}</span>
                <span class="env-value">${escapeHtml(value || '')}</span>
            </div>
        `;
    });
    
    envVarsList.innerHTML = envHTML;
}

function loadExposedPorts() {
    fetch(`/docker-manager/api/image/${currentImageId}/inspect/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log('Exposed ports response:', data);
        if (data.success) {
            displayExposedPorts(data.inspect.Config?.ExposedPorts || {});
        } else {
            showEmptyState('exposedPortsList', 'No exposed ports found');
        }
    })
    .catch(error => {
        console.error('Exposed ports load error:', error);
        showEmptyState('exposedPortsList', 'Error loading exposed ports');
    });
}

function displayExposedPorts(ports) {
    const exposedPortsList = document.getElementById('exposedPortsList');
    if (!exposedPortsList) return;
    
    if (Object.keys(ports).length === 0) {
        showEmptyState('exposedPortsList', 'No exposed ports found');
        return;
    }
    
    let portsHTML = '';
    Object.entries(ports).forEach(([port, protocol]) => {
        portsHTML += `
            <div class="port-item">
                <span class="port-number">${escapeHtml(port)}</span>
                <span class="port-protocol">${escapeHtml(protocol || 'tcp')}</span>
            </div>
        `;
    });
    
    exposedPortsList.innerHTML = portsHTML;
}

function loadLayersData() {
    console.log('Loading layers data...');
    
    fetch(`/docker-manager/api/image/${currentImageId}/history/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log('Layers response:', data);
        if (data.success) {
            displayLayers(data.history);
        } else {
            showEmptyState('layersList', 'No layers found');
        }
    })
    .catch(error => {
        console.error('Layers load error:', error);
        showEmptyState('layersList', 'Error loading layers');
    });
}

function displayLayers(history) {
    const layersList = document.getElementById('layersList');
    const layersCount = document.getElementById('layersCount');
    
    if (!layersList) return;
    
    if (!history || history.length === 0) {
        showEmptyState('layersList', 'No layers found');
        return;
    }
    
    if (layersCount) {
        layersCount.textContent = `${history.length} layers`;
    }
    
    let layersHTML = '';
    history.forEach((layer, index) => {
        const size = formatBytes(layer.Size || 0);
        const command = layer.CreatedBy || 'No command';
        const id = layer.Id || `layer-${index}`;
        
        layersHTML += `
            <div class="layer-item">
                <span class="layer-id">${id.substring(0, 12)}</span>
                <span class="layer-command">${escapeHtml(command)}</span>
                <span class="layer-size">${size}</span>
            </div>
        `;
    });
    
    layersList.innerHTML = layersHTML;
}

function loadHistoryData() {
    console.log('Loading history data...');
    
    fetch(`/docker-manager/api/image/${currentImageId}/history/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log('History response:', data);
        if (data.success) {
            displayHistory(data.history);
        } else {
            showEmptyState('historyList', 'No history found');
        }
    })
    .catch(error => {
        console.error('History load error:', error);
        showEmptyState('historyList', 'Error loading history');
    });
}

function displayHistory(history) {
    const historyList = document.getElementById('historyList');
    if (!historyList) return;
    
    if (!history || history.length === 0) {
        showEmptyState('historyList', 'No history found');
        return;
    }
    
    let historyHTML = '';
    history.forEach((item, index) => {
        const size = formatBytes(item.Size || 0);
        const command = item.CreatedBy || 'No command';
        const created = formatDate(item.Created);
        
        historyHTML += `
            <div class="history-item">
                <span class="history-created">${created}</span>
                <span class="history-command">${escapeHtml(command)}</span>
                <span class="history-size">${size}</span>
            </div>
        `;
    });
    
    historyList.innerHTML = historyHTML;
}

function loadInspectData() {
    console.log('Loading inspect data...');
    
    fetch(`/docker-manager/api/image/${currentImageId}/inspect/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log('Inspect response:', data);
        if (data.success) {
            displayInspectData(data.inspect);
        } else {
            showEmptyState('inspectData', 'Error loading inspect data');
        }
    })
    .catch(error => {
        console.error('Inspect load error:', error);
        showEmptyState('inspectData', 'Error loading inspect data');
    });
}

function displayInspectData(inspect) {
    const inspectData = document.getElementById('inspectData');
    if (!inspectData) return;
    
    inspectData.textContent = JSON.stringify(inspect, null, 2);
}

function copyInspectData() {
    const inspectData = document.getElementById('inspectData');
    if (inspectData) {
        navigator.clipboard.writeText(inspectData.textContent).then(function() {
            showNotification('Inspect data copied to clipboard', 'success');
        }, function(err) {
            console.error('Could not copy text: ', err);
            showNotification('Failed to copy to clipboard', 'error');
        });
    }
}

// Image Actions
function runImage(imageId) {
    console.log('Running image:', imageId);
    
    // Show modal for run options
    showRunImageModal(imageId);
}

function deleteImage(imageId) {
    console.log('Deleting image:', imageId);
    
    if (confirm('Are you sure you want to delete this image? This action cannot be undone.')) {
        fetch(`/docker-manager/api/image/${imageId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Image deleted successfully', 'success');
                // Redirect to images page
                setTimeout(() => {
                    window.location.href = '/docker-manager/images/';
                }, 1000);
            } else {
                showNotification('Failed to delete image: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Delete image error:', error);
            showNotification('Error deleting image: ' + error.message, 'error');
        });
    }
}

function showRunImageModal(imageId) {
    // Create modal for run options
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Run Image</h3>
                <button class="close-btn">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label for="containerName">Container Name:</label>
                    <input type="text" id="containerName" placeholder="Enter container name">
                </div>
                <div class="form-group">
                    <label for="ports">Ports (e.g., 8080:80):</label>
                    <input type="text" id="ports" placeholder="Enter port mapping">
                </div>
                <div class="form-group">
                    <label for="envVars">Environment Variables:</label>
                    <textarea id="envVars" placeholder="Enter environment variables (one per line)"></textarea>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn btn-primary" onclick="runImageWithOptions('${imageId}')">Run</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close modal handlers
    modal.querySelector('.close-btn').addEventListener('click', closeModal);
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
}

function runImageWithOptions(imageId) {
    const containerName = document.getElementById('containerName').value;
    const ports = document.getElementById('ports').value;
    const envVars = document.getElementById('envVars').value;
    
    const options = {
        image: imageId,
        name: containerName,
        ports: ports,
        env: envVars.split('\n').filter(line => line.trim())
    };
    
    fetch('/docker-manager/api/image/run/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(options)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Container started successfully', 'success');
            closeModal();
            // Redirect to containers page
            setTimeout(() => {
                window.location.href = '/docker-manager/';
            }, 1000);
        } else {
            showNotification('Failed to start container: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Run image error:', error);
        showNotification('Error starting container: ' + error.message, 'error');
    });
}

function closeModal() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) {
        modal.remove();
    }
}

// Utility functions
function showEmptyState(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-info-circle"></i>
                <p>${message}</p>
            </div>
        `;
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Copied to clipboard', 'success');
    }, function(err) {
        console.error('Could not copy text: ', err);
        showNotification('Failed to copy to clipboard', 'error');
    });
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleString();
    } catch (e) {
        return 'Unknown';
    }
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Logs functionality
function showImageLogs(imageId) {
    console.log('Showing logs for image:', imageId);
    
    // Switch to logs tab
    switchTab('logs');
    
    // Load logs data
    loadImageLogs(imageId);
}

function loadImageLogs(imageId) {
    const logsData = document.getElementById('logsData');
    if (!logsData) return;
    
    logsData.textContent = 'Loading logs...';
    
    fetch(`/docker-manager/api/image/${imageId}/logs/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                logsData.textContent = data.logs || 'No logs available';
            } else {
                logsData.textContent = 'Error: ' + data.message;
            }
        })
        .catch(error => {
            console.error('Error loading logs:', error);
            logsData.textContent = 'Error loading logs: ' + error.message;
        });
}

function refreshImageLogs() {
    if (currentImageId) {
        loadImageLogs(currentImageId);
    }
}
