// Docker Volumes - JavaScript

// Global variables
let volumes = [];
let filteredVolumes = [];

// Initialize volumes page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Docker Volumes...');
    initializeVolumes();
});

function initializeVolumes() {
    // Setup event listeners
    setupEventListeners();
    
    // Initialize search
    initializeSearch();
    
    // Initialize select all
    initializeSelectAll();
}

function setupEventListeners() {
    // Search functionality
    const searchInput = document.getElementById('volumeSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterVolumes();
        });
    }
    
    // Dangling filter
    const danglingFilter = document.getElementById('danglingOnly');
    if (danglingFilter) {
        danglingFilter.addEventListener('change', function() {
            filterVolumes();
        });
    }
    
    // Select all functionality
    const selectAllCheckbox = document.getElementById('selectAllVolumes');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            toggleSelectAll(this.checked);
        });
    }
}

function initializeSearch() {
    // Get all volume rows
    const volumeRows = document.querySelectorAll('#volumesTableBody tr[data-volume-name]');
    volumes = Array.from(volumeRows).map(row => {
        const name = row.dataset.volumeName;
        const nameElement = row.querySelector('.volume-name');
        const driverElement = row.querySelector('.volume-driver');
        const sizeElement = row.querySelector('.volume-size');
        const createdElement = row.querySelector('.created-col');
        
        return {
            name: name,
            displayName: nameElement ? nameElement.textContent : name,
            driver: driverElement ? driverElement.textContent : '',
            size: sizeElement ? sizeElement.textContent : '',
            created: createdElement ? createdElement.textContent : '',
            element: row
        };
    });
    
    filteredVolumes = [...volumes];
    console.log('Initialized volumes:', volumes.length);
}

function initializeSelectAll() {
    const selectAllCheckbox = document.getElementById('selectAllVolumes');
    const volumeCheckboxes = document.querySelectorAll('.volume-checkbox');
    
    if (selectAllCheckbox && volumeCheckboxes.length > 0) {
        selectAllCheckbox.addEventListener('change', function() {
            volumeCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }
}

function filterVolumes() {
    const searchTerm = document.getElementById('volumeSearch').value.toLowerCase();
    const showDangling = document.getElementById('danglingOnly').checked;
    
    filteredVolumes = volumes.filter(volume => {
        const matchesSearch = volume.displayName.toLowerCase().includes(searchTerm);
        const isDangling = volume.name.length > 20; // Simple dangling detection
        const matchesFilter = showDangling ? isDangling : !isDangling;
        
        return matchesSearch && matchesFilter;
    });
    
    // Update table display
    volumes.forEach(volume => {
        const isVisible = filteredVolumes.includes(volume);
        volume.element.style.display = isVisible ? '' : 'none';
    });
    
    // Update item count
    updateItemCount(filteredVolumes.length);
}

function updateItemCount(count) {
    const itemsCountElement = document.querySelector('.items-count');
    if (itemsCountElement) {
        itemsCountElement.textContent = `Showing ${count} items`;
    }
}

function toggleSelectAll(checked) {
    const volumeCheckboxes = document.querySelectorAll('.volume-checkbox');
    volumeCheckboxes.forEach(checkbox => {
        checkbox.checked = checked;
    });
}

// Volume Actions
function inspectVolume(volumeName) {
    console.log('Inspecting volume:', volumeName);
    
    // Show loading
    showNotification('Loading volume details...', 'info');
    
    // Fetch volume details
    fetch(`/docker-manager/api/volume/${volumeName}/inspect/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showVolumeDetailModal(volumeName, data.inspect);
        } else {
            showNotification('Failed to inspect volume: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Inspect volume error:', error);
        showNotification('Error inspecting volume: ' + error.message, 'error');
    });
}

function deleteVolume(volumeName) {
    console.log('Deleting volume:', volumeName);
    
    if (confirm(`Are you sure you want to delete volume "${volumeName}"? This action cannot be undone.`)) {
        // Show loading
        showNotification('Deleting volume...', 'info');
        
        // Delete volume
        fetch(`/docker-manager/api/volume/${volumeName}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Volume deleted successfully', 'success');
                // Remove row from table
                const row = document.querySelector(`[data-volume-name="${volumeName}"]`);
                if (row) {
                    row.remove();
                }
                updateItemCount(document.querySelectorAll('#volumesTableBody tr:not([style*="display: none"])').length);
            } else {
                showNotification('Failed to delete volume: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Delete volume error:', error);
            showNotification('Error deleting volume: ' + error.message, 'error');
        });
    }
}

function showCreateVolumeModal() {
    console.log('Showing create volume modal...');
    
    const modal = document.getElementById('createVolumeModal');
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Focus on volume name input
        setTimeout(() => {
            const volumeNameInput = document.getElementById('volumeName');
            if (volumeNameInput) {
                volumeNameInput.focus();
            }
        }, 300);
    }
}

function closeCreateVolumeModal() {
    const modal = document.getElementById('createVolumeModal');
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

function createVolume() {
    console.log('Creating volume...');
    
    const volumeName = document.getElementById('volumeName').value;
    const volumeDriver = document.getElementById('volumeDriver').value;
    const volumeLabels = document.getElementById('volumeLabels').value;
    const volumeOptions = document.getElementById('volumeOptions').value;
    
    // Parse labels
    const labels = {};
    if (volumeLabels) {
        volumeLabels.split('\n').forEach(line => {
            if (line.trim() && line.includes('=')) {
                const [key, value] = line.split('=', 2);
                labels[key.trim()] = value.trim();
            }
        });
    }
    
    // Parse options
    const options = {};
    if (volumeOptions) {
        volumeOptions.split('\n').forEach(line => {
            if (line.trim() && line.includes('=')) {
                const [key, value] = line.split('=', 2);
                options[key.trim()] = value.trim();
            }
        });
    }
    
    const volumeData = {
        name: volumeName || null,
        driver: volumeDriver,
        labels: labels,
        options: options
    };
    
    // Show loading
    showNotification('Creating volume...', 'info');
    
    // Create volume
    fetch('/docker-manager/api/volume/create/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(volumeData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Volume created successfully', 'success');
            closeCreateVolumeModal();
            // Refresh page
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification('Failed to create volume: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Create volume error:', error);
        showNotification('Error creating volume: ' + error.message, 'error');
    });
}

function pruneVolumes() {
    console.log('Pruning volumes...');
    
    if (confirm('Are you sure you want to prune unused volumes? This will delete all unused volumes.')) {
        // Show loading
        showNotification('Pruning volumes...', 'info');
        
        // Prune volumes
        fetch('/docker-manager/api/volume/prune/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(`Pruned ${data.pruned_count || 0} volumes`, 'success');
                // Refresh page
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showNotification('Failed to prune volumes: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Prune volumes error:', error);
            showNotification('Error pruning volumes: ' + error.message, 'error');
        });
    }
}

function showVolumeDetailModal(volumeName, inspectData) {
    console.log('Showing volume detail modal:', volumeName);
    
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content volume-detail-modal">
            <div class="modal-header">
                <h3>
                    <i class="fas fa-database"></i>
                    Volume Details: ${volumeName}
                </h3>
                <button class="close-btn">&times;</button>
            </div>
            <div class="modal-body volume-detail-content">
                <div class="volume-detail-section">
                    <h4>Basic Information</h4>
                    <pre>${JSON.stringify({
                        Name: inspectData.Name || 'N/A',
                        Driver: inspectData.Driver || 'N/A',
                        Mountpoint: inspectData.Mountpoint || 'N/A',
                        CreatedAt: inspectData.CreatedAt || 'N/A'
                    }, null, 2)}</pre>
                </div>
                
                <div class="volume-detail-section">
                    <h4>Labels</h4>
                    <pre>${JSON.stringify(inspectData.Labels || {}, null, 2)}</pre>
                </div>
                
                <div class="volume-detail-section">
                    <h4>Options</h4>
                    <pre>${JSON.stringify(inspectData.Options || {}, null, 2)}</pre>
                </div>
                
                <div class="volume-detail-section">
                    <h4>Full Inspect Data</h4>
                    <pre>${JSON.stringify(inspectData, null, 2)}</pre>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Show modal
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
    
    // Close modal handlers
    modal.querySelector('.close-btn').addEventListener('click', function() {
        closeVolumeDetailModal();
    });
    
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeVolumeDetailModal();
        }
    });

    // Close on ESC key
    function escListener(ev) {
        if (ev.key === 'Escape') {
            closeVolumeDetailModal();
        }
    }
    document.addEventListener('keydown', escListener);
    // Clean up ESC listener on close
    const originalClose = closeVolumeDetailModal;
    window.closeVolumeDetailModal = function() {
        document.removeEventListener('keydown', escListener);
        originalClose();
    };
}

function closeVolumeDetailModal() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}

// Notification function
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Utility functions
function getSelectedVolumes() {
    const checkboxes = document.querySelectorAll('.volume-checkbox:checked');
    const selectedVolumes = [];
    
    checkboxes.forEach(checkbox => {
        const volumeName = checkbox.dataset.volumeName;
        const row = document.querySelector(`[data-volume-name="${volumeName}"]`);
        
        if (row) {
            const nameElement = row.querySelector('.volume-name');
            const driverElement = row.querySelector('.volume-driver');
            const sizeElement = row.querySelector('.volume-size');
            
            selectedVolumes.push({
                name: volumeName,
                displayName: nameElement ? nameElement.textContent : volumeName,
                driver: driverElement ? driverElement.textContent : '',
                size: sizeElement ? sizeElement.textContent : ''
            });
        }
    });
    
    return selectedVolumes;
}

// Export functions for global access
window.inspectVolume = inspectVolume;
window.deleteVolume = deleteVolume;
window.showCreateVolumeModal = showCreateVolumeModal;
window.closeCreateVolumeModal = closeCreateVolumeModal;
window.createVolume = createVolume;
window.pruneVolumes = pruneVolumes;
window.showVolumeDetailModal = showVolumeDetailModal;
window.closeVolumeDetailModal = closeVolumeDetailModal;
