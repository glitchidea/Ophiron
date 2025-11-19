// Docker Images - JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeImages();
});

function initializeImages() {
    console.log('Initializing Docker Images...');
    
    // Search functionality
    setupSearchFunctionality();
    
    // Filter functionality
    setupFilterFunctionality();
    
    // Select all functionality
    setupSelectAllFunctionality();
    
    // Action buttons
    setupActionButtons();
    
    // Build functionality
    setupBuildFunctionality();
}

function setupSearchFunctionality() {
    const searchInput = document.getElementById('imageSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            filterImages(searchTerm);
        });
    }
}

function setupFilterFunctionality() {
    const danglingOnlyCheckbox = document.getElementById('danglingOnly');
    if (danglingOnlyCheckbox) {
        danglingOnlyCheckbox.addEventListener('change', function() {
            filterImages();
        });
    }
}

function setupSelectAllFunctionality() {
    const selectAllCheckbox = document.getElementById('selectAllImages');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const imageCheckboxes = document.querySelectorAll('.image-checkbox');
            imageCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }
}

function setupActionButtons() {
    // Action buttons are handled by onclick events in HTML
}

function filterImages(searchTerm = '') {
    const danglingOnly = document.getElementById('danglingOnly').checked;
    const rows = document.querySelectorAll('#imagesTableBody tr');
    let visibleCount = 0;
    
    rows.forEach(row => {
        const nameCell = row.querySelector('.image-name');
        const tagCell = row.querySelector('.image-tag');
        
        if (!nameCell) return;
        
        const name = nameCell.textContent.toLowerCase();
        const tag = tagCell ? tagCell.textContent.toLowerCase() : '';
        
        const matchesSearch = searchTerm === '' || 
            name.includes(searchTerm) || 
            tag.includes(searchTerm);
        
        const matchesFilter = !danglingOnly || tag === '<none>' || tag === '';
        
        if (matchesSearch && matchesFilter) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    updateItemCount(visibleCount);
}

function updateItemCount(count) {
    const itemsCountElement = document.querySelector('.items-count');
    if (itemsCountElement) {
        itemsCountElement.textContent = `Showing ${count} items`;
    }
}

// Image Actions
function runImage(imageId) {
    console.log('Running image:', imageId);
    
    // Actions kısmından çağrıldığında imageId parametresi ile çalış
    if (imageId) {
        // Image bilgilerini al
        const imageRow = document.querySelector(`[data-image-id="${imageId}"]`);
        if (imageRow) {
            const imageName = imageRow.querySelector('.image-name').textContent;
            const imageTag = imageRow.querySelector('.image-tag').textContent;
            const imageSize = imageRow.querySelector('.image-size').textContent;
            
            const selectedImage = {
                id: imageId,
                fullName: `${imageName}:${imageTag}`,
                name: imageName,
                tag: imageTag,
                size: imageSize
            };
            
            console.log('Running selected image:', selectedImage);
            
            // Run popup'ını seçili image ile aç
            showRunImageModalWithImage(selectedImage);
        } else {
            showNotification('Image not found', 'error');
        }
    } else {
        // Üstten çağrıldığında seçili image kontrolü yap
        const selectedImages = getSelectedImages();
        if (selectedImages.length === 0) {
            showNotification('Please select an image to run', 'warning');
            return;
        }
        
        if (selectedImages.length > 1) {
            showNotification('Please select only one image to run', 'warning');
            return;
        }
        
        const selectedImage = selectedImages[0];
        console.log('Running selected image:', selectedImage);
        
        // Run popup'ını seçili image ile aç
        showRunImageModalWithImage(selectedImage);
    }
}

function deleteImage(imageId) {
    console.log('Deleting image:', imageId);
    
    // Actions kısmından çağrıldığında imageId parametresi ile çalış
    if (imageId) {
        // Image bilgilerini al
        const imageRow = document.querySelector(`[data-image-id="${imageId}"]`);
        if (imageRow) {
            const imageName = imageRow.querySelector('.image-name').textContent;
            const imageTag = imageRow.querySelector('.image-tag').textContent;
            const imageSize = imageRow.querySelector('.image-size').textContent;
            
            const selectedImage = {
                id: imageId,
                fullName: `${imageName}:${imageTag}`,
                name: imageName,
                tag: imageTag,
                size: imageSize
            };
            
            console.log('Removing selected image:', selectedImage);
            
            // Remove popup'ını seçili image ile aç
            showRemoveModalWithImage(selectedImage);
        } else {
            showNotification('Image not found', 'error');
        }
    } else {
        // Üstten çağrıldığında seçili image kontrolü yap
        const selectedImages = getSelectedImages();
        if (selectedImages.length === 0) {
            showNotification('Please select an image to remove', 'warning');
            return;
        }
        
        if (selectedImages.length > 1) {
            showNotification('Please select only one image to remove', 'warning');
            return;
        }
        
        const selectedImage = selectedImages[0];
        console.log('Removing selected image:', selectedImage);
        
        // Remove popup'ını seçili image ile aç
        showRemoveModalWithImage(selectedImage);
    }
}

function pullImage() {
    console.log('Pulling image...');
    
    // Üstten açılan popup - boş form
    showPullModal();
}

function buildImage() {
    console.log('Building image...');
    
    // Üstten açılan popup - boş form
    showBuildModal();
}

function getSelectedImages() {
    const checkboxes = document.querySelectorAll('.image-checkbox:checked');
    const selectedImages = [];
    
    checkboxes.forEach(checkbox => {
        const imageId = checkbox.dataset.imageId;
        const row = checkbox.closest('tr');
        const imageName = row.querySelector('.image-name').textContent;
        const imageTag = row.querySelector('.image-tag').textContent;
        
        selectedImages.push({
            id: imageId,
            name: imageName,
            tag: imageTag,
            fullName: imageTag !== '<none>' ? `${imageName}:${imageTag}` : imageName
        });
    });
    
    return selectedImages;
}

function showRunImageModal(imageId) {
    // Create modal for run options - boş popup
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>
                    <i class="fas fa-play"></i>
                    Run Image
                </h3>
                <button class="close-btn">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label for="imageName">Image Name:</label>
                    <input type="text" id="imageName" placeholder="Enter image name (e.g., nginx:latest)">
                </div>
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
                <button class="btn btn-primary" onclick="runImageWithOptions()">
                    <i class="fas fa-play"></i>
                    Run Container
                </button>
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

function showRunImageModalWithImage(selectedImage) {
    console.log('Showing run modal with image:', selectedImage);
    
    // Create modal for run options with selected image
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>
                    <i class="fas fa-play"></i>
                    Run Image
                </h3>
                <button class="close-btn">&times;</button>
            </div>
            <div class="modal-body">
                <div class="selected-image-info">
                    <div class="image-preview">
                        <div class="image-icon">
                            <i class="fas fa-image"></i>
                        </div>
                        <div class="image-details">
                            <div class="image-name">${selectedImage.fullName}</div>
                            <div class="image-id">${selectedImage.id}</div>
                        </div>
                    </div>
                </div>
                
                <form id="runForm">
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
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeRunModal()">Cancel</button>
                <button class="btn btn-primary" onclick="runImageWithOptions('${selectedImage.id}')">
                    <i class="fas fa-play"></i>
                    Run Container
                </button>
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
        closeRunModal();
    });
    
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeRunModal();
        }
    });
}

function closeRunModal() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}

function runImageWithOptions(imageId = null) {
    const imageName = document.getElementById('imageName') ? document.getElementById('imageName').value : null;
    const containerName = document.getElementById('containerName').value;
    const ports = document.getElementById('ports').value;
    const envVars = document.getElementById('envVars').value;
    
    // Image ID veya Image Name kontrolü
    const finalImageId = imageId || imageName;
    if (!finalImageId) {
        showNotification('Please enter an image name', 'error');
        return;
    }
    
    const options = {
        image: finalImageId,
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
            closeRunModal();
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

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Copied to clipboard', 'success');
    }, function(err) {
        console.error('Could not copy text: ', err);
        showNotification('Failed to copy to clipboard', 'error');
    });
}

// Build functionality
function setupBuildFunctionality() {
    console.log('Build functionality setup complete');
}

// Build modal functions
function showBuildModal() {
    console.log('showBuildModal called from images.js');
    const modal = document.getElementById('buildModal');
    console.log('Modal element found:', modal);
    if (modal) {
        console.log('Adding show class to modal');
        modal.classList.add('show');
        modal.style.display = 'flex';
        console.log('Modal should be visible now');
    } else {
        console.error('buildModal element not found!');
        // Try to create the modal dynamically
        console.log('Attempting to create modal dynamically...');
        createBuildModalFromImages();
    }
}

function createBuildModalFromImages() {
    console.log('Creating build modal from images.js...');
    // Check if modal already exists
    if (document.getElementById('buildModal')) {
        console.log('Modal already exists, showing it...');
        showBuildModal();
        return;
    }
    
    // Create modal HTML
    const modalHTML = `
        <div class="modal" id="buildModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Create New Build</h3>
                    <button class="modal-close" onclick="hideBuildModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <form id="buildForm">
                        <div class="form-group">
                            <label for="dockerfilePath">Dockerfile Path</label>
                            <input type="text" id="dockerfilePath" name="dockerfile_path" class="form-control" 
                                   placeholder="/path/to/Dockerfile" required>
                            <small class="form-text">Absolute path to the directory containing Dockerfile</small>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="imageName">Image Name</label>
                                <input type="text" id="imageName" name="image_name" class="form-control" 
                                       placeholder="my-app" required>
                            </div>
                            <div class="form-group">
                                <label for="imageTag">Tag</label>
                                <input type="text" id="imageTag" name="tag" class="form-control" 
                                       placeholder="latest" value="latest">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="buildArgs">Build Arguments (JSON)</label>
                            <textarea id="buildArgs" name="build_args" class="form-control" rows="3" 
                                      placeholder='{"NODE_ENV": "production", "PORT": "3000"}'></textarea>
                            <small class="form-text">Optional build arguments in JSON format</small>
                        </div>
                        
                        <div class="form-group">
                            <label class="checkbox-label">
                                <input type="checkbox" id="noCache" name="no_cache">
                                <span class="checkmark"></span>
                                No Cache
                            </label>
                            <small class="form-text">Build without using cache</small>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="hideBuildModal()">Cancel</button>
                    <button class="btn btn-primary" onclick="startBuild()">
                        <i class="fas fa-play"></i>
                        Start Build
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    console.log('Modal created and added to DOM');
    
    // Show the modal
    const newModal = document.getElementById('buildModal');
    if (newModal) {
        console.log('Showing newly created modal...');
        newModal.classList.add('show');
        newModal.style.display = 'flex';
    }
}

function hideBuildModal() {
    console.log('hideBuildModal called from images.js');
    const modal = document.getElementById('buildModal');
    console.log('Modal element found for hiding:', modal);
    if (modal) {
        console.log('Hiding modal...');
        modal.classList.remove('show');
        modal.style.display = 'none';
        console.log('Modal hidden');
    } else {
        console.error('buildModal element not found for hiding!');
    }
}

function showGitBuildModal() {
    const modal = document.getElementById('gitBuildModal');
    if (modal) {
        modal.classList.add('show');
        modal.style.display = 'flex';
    }
}

function hideGitBuildModal() {
    const modal = document.getElementById('gitBuildModal');
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
    }
}

// Build execution functions
function startBuild() {
    console.log('startBuild called from images.js');
    const form = document.getElementById('buildForm');
    console.log('Build form found:', form);
    
    if (!form) {
        console.error('Build form not found!');
        showNotification('Build form not found', 'error');
        return;
    }

    const formData = new FormData(form);
    const buildData = {
        dockerfile_path: formData.get('dockerfile_path'),
        image_name: formData.get('image_name'),
        tag: formData.get('tag') || 'latest',
        build_args: parseBuildArgs(formData.get('build_args')),
        no_cache: formData.get('no_cache') === 'on'
    };

    console.log('Build data:', buildData);

    if (!buildData.dockerfile_path || !buildData.image_name) {
        console.log('Missing required fields');
        showNotification('Please fill in all required fields', 'error');
        return;
    }

    console.log('Starting build process...');
    hideBuildModal();
    showBuildProgress();
    executeBuild(buildData);
}

function startGitBuild() {
    const form = document.getElementById('gitBuildForm');
    if (!form) return;

    const formData = new FormData(form);
    const buildData = {
        git_url: formData.get('git_url'),
        image_name: formData.get('image_name'),
        tag: formData.get('tag') || 'latest',
        dockerfile_path: formData.get('dockerfile_path') || 'Dockerfile',
        build_args: parseBuildArgs(formData.get('build_args'))
    };

    if (!buildData.git_url || !buildData.image_name) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }

    hideGitBuildModal();
    showBuildProgress();
    executeGitBuild(buildData);
}

function parseBuildArgs(argsStr) {
    if (!argsStr || argsStr.trim() === '') return {};
    
    try {
        return JSON.parse(argsStr);
    } catch (e) {
        console.warn('Invalid build args JSON:', e);
        return {};
    }
}

function executeBuild(buildData) {
    fetch('/docker-manager/api/build/image/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(buildData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            hideBuildProgress();
            setTimeout(() => location.reload(), 2000);
        } else {
            showNotification(data.message, 'error');
            hideBuildProgress();
        }
    })
    .catch(error => {
        console.error('Build error:', error);
        showNotification('Build failed: ' + error.message, 'error');
        hideBuildProgress();
    });
}

function executeGitBuild(buildData) {
    fetch('/docker-manager/api/build/git/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(buildData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            hideBuildProgress();
            setTimeout(() => location.reload(), 2000);
        } else {
            showNotification(data.message, 'error');
            hideBuildProgress();
        }
    })
    .catch(error => {
        console.error('Git build error:', error);
        showNotification('Git build failed: ' + error.message, 'error');
        hideBuildProgress();
    });
}

function showBuildProgress() {
    const modal = document.getElementById('buildProgressModal');
    if (modal) {
        modal.classList.add('show');
        modal.style.display = 'flex';
        
        const progressFill = document.getElementById('buildProgressFill');
        const progressText = document.getElementById('buildProgressText');
        const progressLogs = document.getElementById('buildProgressLogs');
        
        if (progressFill) progressFill.style.width = '0%';
        if (progressText) progressText.textContent = 'Preparing build...';
        if (progressLogs) progressLogs.textContent = '';
    }
}

function hideBuildProgress() {
    const modal = document.getElementById('buildProgressModal');
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
    }
}

function cancelBuild() {
    hideBuildProgress();
}

function pruneImages() {
    if (!confirm('Are you sure you want to prune unused images?\n\nThis will remove dangling images and free up disk space.')) {
        return;
    }

    showNotification('Pruning images...', 'info');
    
    fetch('/docker-manager/api/build/prune/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 2000);
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Prune error:', error);
        showNotification('Failed to prune images', 'error');
    });
}

function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

// Image action functions
function showImageLogs(imageId) {
    const modal = document.getElementById('imageLogsModal');
    const content = document.getElementById('imageLogsContent');
    
    if (modal && content) {
        modal.classList.add('show');
        modal.style.display = 'flex';
        content.textContent = 'Loading logs...';
        
        fetch(`/docker-manager/api/image/${imageId}/logs/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    content.textContent = data.logs || 'No logs available';
                } else {
                    content.textContent = 'Error: ' + data.message;
                }
            })
            .catch(error => {
                content.textContent = 'Error loading logs: ' + error.message;
            });
    }
}

function hideImageLogs() {
    const modal = document.getElementById('imageLogsModal');
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
    }
}

function refreshImageLogs() {
    const content = document.getElementById('imageLogsContent');
    if (content) {
        content.textContent = 'Refreshing logs...';
        // Get image ID from current context or pass it as parameter
        const imageId = getCurrentImageId();
        if (imageId) {
            showImageLogs(imageId);
        }
    }
}

function inspectImage(imageId) {
    const modal = document.getElementById('imageInspectModal');
    const content = document.getElementById('imageInspectContent');
    
    if (modal && content) {
        modal.classList.add('show');
        modal.style.display = 'flex';
        content.textContent = 'Loading inspect data...';
        
        fetch(`/docker-manager/api/image/${imageId}/inspect/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    content.textContent = JSON.stringify(data.inspect, null, 2);
                } else {
                    content.textContent = 'Error: ' + data.message;
                }
            })
            .catch(error => {
                content.textContent = 'Error loading inspect data: ' + error.message;
            });
    }
}

function hideImageInspect() {
    const modal = document.getElementById('imageInspectModal');
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
    }
}

function showImageHistory(imageId) {
    const modal = document.getElementById('imageHistoryModal');
    const content = document.getElementById('imageHistoryContent');
    
    if (modal && content) {
        modal.classList.add('show');
        modal.style.display = 'flex';
        content.textContent = 'Loading history...';
        
        fetch(`/docker-manager/api/image/${imageId}/history/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    content.textContent = JSON.stringify(data.history, null, 2);
                } else {
                    content.textContent = 'Error: ' + data.message;
                }
            })
            .catch(error => {
                content.textContent = 'Error loading history: ' + error.message;
            });
    }
}

function hideImageHistory() {
    const modal = document.getElementById('imageHistoryModal');
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
    }
}

function deleteImage(imageId) {
    if (!confirm('Are you sure you want to delete this image?\n\nThis action cannot be undone.')) {
        return;
    }
    
    showNotification('Deleting image...', 'info');
    
    fetch(`/docker-manager/api/image/${imageId}/delete/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 2000);
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Delete error:', error);
        showNotification('Failed to delete image', 'error');
    });
}

function copyInspectData() {
    const content = document.getElementById('imageInspectContent');
    if (content) {
        copyToClipboard(content.textContent);
    }
}

function copyHistoryData() {
    const content = document.getElementById('imageHistoryContent');
    if (content) {
        copyToClipboard(content.textContent);
    }
}

function getCurrentImageId() {
    // This function should return the current image ID being viewed
    // For now, we'll need to track this in a global variable or get it from the context
    return window.currentImageId || null;
}

// Nested/Grouped Image View Functions
function toggleImageContainers(imageId) {
    const containerRows = document.querySelectorAll(`tr.container-row[data-parent-image="${imageId}"]`);
    const expandBtn = document.querySelector(`tr.image-row[data-image-id="${imageId}"] .expand-btn`);
    const imageCard = document.querySelector(`tr.image-row[data-image-id="${imageId}"]`);
    
    containerRows.forEach(row => {
        if (row.style.display === 'none') {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
    
    if (expandBtn) {
        const icon = expandBtn.querySelector('i');
        if (icon.classList.contains('fa-chevron-right')) {
            icon.classList.remove('fa-chevron-right');
            icon.classList.add('fa-chevron-down');
            expandBtn.classList.add('expanded');
        } else {
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-right');
            expandBtn.classList.remove('expanded');
        }
    }
    
    if (imageCard) {
        if (imageCard.classList.contains('expanded')) {
            imageCard.classList.remove('expanded');
        } else {
            imageCard.classList.add('expanded');
        }
    }
}

function showContainerLogs(containerId) {
    console.log('Showing logs for container:', containerId);
    // Implement container logs functionality
    showNotification('Container logs feature coming soon', 'info');
}

function stopContainer(containerId) {
    if (!confirm('Are you sure you want to stop this container?')) {
        return;
    }
    
    showNotification('Stopping container...', 'info');
    
    fetch(`/docker-manager/api/container/${containerId}/stop/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 2000);
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Stop container error:', error);
        showNotification('Failed to stop container', 'error');
    });
}
