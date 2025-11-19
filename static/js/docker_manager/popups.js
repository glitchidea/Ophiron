// Docker Manager Popups - JavaScript

// Global variables
let buildModal = null;
let pullModal = null;
let removeModal = null;
let buildProgressModal = null;
let pullProgressModal = null;
let removeProgressModal = null;
let currentBuildProcess = null;
let currentPullProcess = null;
let currentRemoveProcess = null;

// Initialize popups
document.addEventListener('DOMContentLoaded', function() {
    initializePopups();
});

function initializePopups() {
    console.log('Initializing Docker Manager Popups...');
    
    // Create modal elements
    createBuildModal();
    createPullModal();
    createRemoveModal();
    
    // Setup event listeners
    setupEventListeners();
}

function createBuildModal() {
    // Check if build modal already exists
    if (document.getElementById('buildModal')) return;
    
    // Create build modal HTML
    const buildModalHTML = `
        <!-- Build Image Popup -->
        <div class="modal-overlay" id="buildModal">
            <div class="modal-content build-modal">
                <div class="modal-header">
                    <h3>
                        <i class="fas fa-hammer"></i>
                        Build Image
                    </h3>
                    <button class="close-btn" onclick="closeBuildModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="buildForm">
                        <div class="form-group">
                            <label for="buildDockerfile">Dockerfile Path:</label>
                            <input type="text" id="buildDockerfile" placeholder="e.g., ./Dockerfile" required>
                            <small class="form-help">Path to your Dockerfile</small>
                        </div>
                        
                        <div class="form-group">
                            <label for="buildImageName">Image Name:</label>
                            <input type="text" id="buildImageName" placeholder="e.g., myapp:latest" required>
                            <small class="form-help">Name and tag for your image</small>
                        </div>
                        
                        <div class="form-group">
                            <label for="buildContext">Build Context:</label>
                            <input type="text" id="buildContext" placeholder="e.g., ." value=".">
                            <small class="form-help">Build context directory (default: current directory)</small>
                        </div>
                        
                        <div class="form-group">
                            <label for="buildArgs">Build Arguments:</label>
                            <textarea id="buildArgs" placeholder="Enter build arguments (one per line)&#10;e.g.,&#10;VERSION=1.0&#10;ENV=production"></textarea>
                            <small class="form-help">Build arguments in KEY=VALUE format</small>
                        </div>
                        
                        <div class="form-group">
                            <label for="buildOptions">Build Options:</label>
                            <div class="checkbox-group">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="buildNoCache" name="buildOptions" value="no-cache">
                                    <span class="checkmark"></span>
                                    No cache
                                </label>
                                <label class="checkbox-label">
                                    <input type="checkbox" id="buildPull" name="buildOptions" value="pull">
                                    <span class="checkmark"></span>
                                    Always pull base images
                                </label>
                                <label class="checkbox-label">
                                    <input type="checkbox" id="buildSquash" name="buildOptions" value="squash">
                                    <span class="checkmark"></span>
                                    Squash layers
                                </label>
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeBuildModal()">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="startBuild()">
                        <i class="fas fa-hammer"></i>
                        Start Build
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', buildModalHTML);
    buildModal = document.getElementById('buildModal');
}

function createPullModal() {
    // Check if pull modal already exists
    if (document.getElementById('pullModal')) return;
    
    // Create pull modal HTML
    const pullModalHTML = `
        <!-- Pull Image Popup -->
        <div class="modal-overlay" id="pullModal">
            <div class="modal-content pull-modal">
                <div class="modal-header">
                    <h3>
                        <i class="fas fa-download"></i>
                        Pull Image
                    </h3>
                    <button class="close-btn" onclick="closePullModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="pullForm">
                        <div class="form-group">
                            <label for="pullImageName">Image Name:</label>
                            <input type="text" id="pullImageName" placeholder="e.g., nginx:latest" required>
                            <small class="form-help">Docker Hub image name and tag</small>
                        </div>
                        
                        <div class="form-group">
                            <label for="pullRegistry">Registry:</label>
                            <select id="pullRegistry">
                                <option value="docker.io">Docker Hub (docker.io)</option>
                                <option value="ghcr.io">GitHub Container Registry</option>
                                <option value="quay.io">Quay.io</option>
                                <option value="custom">Custom Registry</option>
                            </select>
                        </div>
                        
                        <div class="form-group" id="customRegistryGroup" style="display: none;">
                            <label for="customRegistry">Custom Registry URL:</label>
                            <input type="text" id="customRegistry" placeholder="e.g., registry.example.com">
                        </div>
                        
                        <div class="form-group">
                            <label for="pullAuth">Authentication:</label>
                            <div class="auth-group">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="pullUseAuth">
                                    <span class="checkmark"></span>
                                    Use authentication
                                </label>
                            </div>
                        </div>
                        
                        <div class="auth-fields" id="authFields" style="display: none;">
                            <div class="form-group">
                                <label for="pullUsername">Username:</label>
                                <input type="text" id="pullUsername" placeholder="Registry username">
                            </div>
                            <div class="form-group">
                                <label for="pullPassword">Password/Token:</label>
                                <input type="password" id="pullPassword" placeholder="Registry password or token">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="pullOptions">Pull Options:</label>
                            <div class="checkbox-group">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="pullAllTags" name="pullOptions" value="all-tags">
                                    <span class="checkmark"></span>
                                    Pull all tags
                                </label>
                                <label class="checkbox-label">
                                    <input type="checkbox" id="pullQuiet" name="pullOptions" value="quiet">
                                    <span class="checkmark"></span>
                                    Quiet mode
                                </label>
                                <label class="checkbox-label">
                                    <input type="checkbox" id="pullDisableContentTrust" name="pullOptions" value="disable-content-trust">
                                    <span class="checkmark"></span>
                                    Disable content trust
                                </label>
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closePullModal()">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="startPull()">
                        <i class="fas fa-download"></i>
                        Start Pull
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', pullModalHTML);
    pullModal = document.getElementById('pullModal');
}

function createRemoveModal() {
    // Check if remove modal already exists
    if (document.getElementById('removeModal')) return;
    
    // Create remove modal HTML
    const removeModalHTML = `
        <!-- Remove Image Popup -->
        <div class="modal-overlay" id="removeModal">
            <div class="modal-content remove-modal">
                <div class="modal-header">
                    <h3>
                        <i class="fas fa-trash"></i>
                        Remove Image
                    </h3>
                    <button class="close-btn" onclick="closeRemoveModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="remove-warning">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span>This action cannot be undone!</span>
                    </div>
                    
                    <div class="selected-image-info">
                        <div class="image-preview">
                            <div class="image-icon">
                                <i class="fas fa-image"></i>
                            </div>
                            <div class="image-details">
                                <div class="image-name" id="removeImageName">Image Name</div>
                                <div class="image-id" id="removeImageId">Image ID</div>
                                <div class="image-size" id="removeImageSize">Size</div>
                            </div>
                        </div>
                    </div>
                    
                    <form id="removeForm">
                        <div class="form-group">
                            <label for="removeOptions">Remove Options:</label>
                            <div class="checkbox-group">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="removeForce" name="removeOptions" value="force">
                                    <span class="checkmark"></span>
                                    Force removal (remove even if used by containers)
                                </label>
                                <label class="checkbox-label">
                                    <input type="checkbox" id="removeNoPrune" name="removeOptions" value="no-prune">
                                    <span class="checkmark"></span>
                                    Don't delete untagged parent images
                                </label>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="removeReason">Reason for removal (optional):</label>
                            <select id="removeReason">
                                <option value="">Select a reason...</option>
                                <option value="no-longer-needed">No longer needed</option>
                                <option value="outdated">Outdated version</option>
                                <option value="security">Security concerns</option>
                                <option value="cleanup">System cleanup</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                        
                        <div class="form-group" id="customReasonGroup" style="display: none;">
                            <label for="customReason">Custom reason:</label>
                            <input type="text" id="customReason" placeholder="Enter custom reason...">
                        </div>
                        
                        <div class="form-group">
                            <label for="removeConfirmation">Type the image name to confirm:</label>
                            <input type="text" id="removeConfirmation" placeholder="Type image name here..." required>
                            <small class="form-help">This helps prevent accidental deletions</small>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeRemoveModal()">Cancel</button>
                    <button type="button" class="btn btn-danger" onclick="confirmRemoveImage()" id="removeConfirmBtn" disabled>
                        <i class="fas fa-trash"></i>
                        Remove Image
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', removeModalHTML);
    removeModal = document.getElementById('removeModal');
}

function setupEventListeners() {
    // Registry selection change
    const pullRegistry = document.getElementById('pullRegistry');
    if (pullRegistry) {
        pullRegistry.addEventListener('change', function() {
            const customGroup = document.getElementById('customRegistryGroup');
            if (this.value === 'custom') {
                customGroup.style.display = 'block';
            } else {
                customGroup.style.display = 'none';
            }
        });
    }
    
    // Authentication checkbox
    const pullUseAuth = document.getElementById('pullUseAuth');
    if (pullUseAuth) {
        pullUseAuth.addEventListener('change', function() {
            const authFields = document.getElementById('authFields');
            if (this.checked) {
                authFields.style.display = 'block';
            } else {
                authFields.style.display = 'none';
            }
        });
    }
    
    // Remove reason selection
    const removeReason = document.getElementById('removeReason');
    if (removeReason) {
        removeReason.addEventListener('change', function() {
            const customGroup = document.getElementById('customReasonGroup');
            if (this.value === 'other') {
                customGroup.style.display = 'block';
            } else {
                customGroup.style.display = 'none';
            }
        });
    }
    
    // Remove confirmation input
    const removeConfirmation = document.getElementById('removeConfirmation');
    if (removeConfirmation) {
        removeConfirmation.addEventListener('input', function() {
            const confirmBtn = document.getElementById('removeConfirmBtn');
            const expectedName = this.dataset.expectedName || '';
            if (this.value === expectedName) {
                confirmBtn.disabled = false;
            } else {
                confirmBtn.disabled = true;
            }
        });
    }
    
    // Modal overlay clicks
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal-overlay')) {
            if (e.target.id === 'buildModal') {
                closeBuildModal();
            } else if (e.target.id === 'pullModal') {
                closePullModal();
            } else if (e.target.id === 'removeModal') {
                closeRemoveModal();
            }
        }
    });
}

// Build Modal Functions
function showBuildModal() {
    console.log('Showing build modal from popups.js...');
    if (buildModal) {
        console.log('Using existing buildModal from popups.js');
        buildModal.classList.add('show');
        document.body.style.overflow = 'hidden';
    } else {
        console.log('buildModal not found in popups.js, trying to find in DOM...');
        const modal = document.getElementById('buildModal');
        if (modal) {
            console.log('Found buildModal in DOM, using it...');
            modal.classList.add('show');
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        } else {
            console.error('buildModal not found anywhere!');
        }
    }
}

function showBuildModalWithImage(selectedImage) {
    console.log('Showing build modal with image:', selectedImage);
    
    // Build modal'ı oluştur veya güncelle
    if (!buildModal) {
        createBuildModal();
    }
    
    // Seçili image bilgilerini form'a doldur
    if (selectedImage) {
        const buildImageName = document.getElementById('buildImageName');
        if (buildImageName) {
            buildImageName.value = selectedImage.fullName;
        }
        
        // Base image olarak seçili image'ı göster
        const baseImageInfo = document.createElement('div');
        baseImageInfo.className = 'base-image-info';
        baseImageInfo.innerHTML = `
            <div class="form-group">
                <label>Base Image:</label>
                <div class="base-image-display">
                    <span class="base-image-name">${selectedImage.fullName}</span>
                    <span class="base-image-id">(${selectedImage.id})</span>
                </div>
            </div>
        `;
        
        // Base image info'yu form'un başına ekle
        const form = document.getElementById('buildForm');
        if (form && !form.querySelector('.base-image-info')) {
            form.insertBefore(baseImageInfo, form.firstChild);
        }
    }
    
    buildModal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeBuildModal() {
    console.log('Closing build modal...');
    if (buildModal) {
        buildModal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

function startBuild() {
    console.log('Starting build...');
    
    const dockerfile = document.getElementById('buildDockerfile').value;
    const imageName = document.getElementById('buildImageName').value;
    const context = document.getElementById('buildContext').value;
    const args = document.getElementById('buildArgs').value;
    
    if (!dockerfile || !imageName) {
        showNotification('Please fill in required fields', 'error');
        return;
    }
    
    // Get build options
    const options = [];
    const buildOptions = document.querySelectorAll('input[name="buildOptions"]:checked');
    buildOptions.forEach(option => {
        options.push(option.value);
    });
    
    // Parse build arguments
    const buildArgs = {};
    if (args.trim()) {
        args.split('\n').forEach(line => {
            const trimmed = line.trim();
            if (trimmed && trimmed.includes('=')) {
                const [key, value] = trimmed.split('=', 2);
                buildArgs[key.trim()] = value.trim();
            }
        });
    }
    
    // Close build modal
    closeBuildModal();
    
    // Show progress modal
    showBuildProgressModal();
    
    // Start build process
    fetch('/docker-manager/api/image/build/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            dockerfile: dockerfile,
            image: imageName,
            context: context,
            args: buildArgs,
            options: options
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateBuildProgress(100, 'Build completed successfully!');
            setTimeout(() => {
                closeBuildProgressModal();
                showNotification('Image built successfully', 'success');
                // Refresh images page
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }, 2000);
        } else {
            updateBuildProgress(0, 'Build failed: ' + data.message);
            setTimeout(() => {
                closeBuildProgressModal();
                showNotification('Build failed: ' + data.message, 'error');
            }, 3000);
        }
    })
    .catch(error => {
        console.error('Build error:', error);
        updateBuildProgress(0, 'Build error: ' + error.message);
        setTimeout(() => {
            closeBuildProgressModal();
            showNotification('Build error: ' + error.message, 'error');
        }, 3000);
    });
}

function showBuildProgressModal() {
    // Create progress modal if it doesn't exist
    if (!document.getElementById('buildProgressModal')) {
        const progressModalHTML = `
            <div class="modal-overlay" id="buildProgressModal">
                <div class="modal-content progress-modal">
                    <div class="modal-header">
                        <h3>
                            <i class="fas fa-cog fa-spin"></i>
                            Building Image
                        </h3>
                    </div>
                    <div class="modal-body">
                        <div class="progress-container">
                            <div class="progress-bar">
                                <div class="progress-fill" id="buildProgress"></div>
                            </div>
                            <div class="progress-text" id="buildProgressText">Preparing build...</div>
                        </div>
                        <div class="build-logs" id="buildLogs">
                            <div class="log-line">Starting build process...</div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-danger" onclick="cancelBuild()">
                            <i class="fas fa-times"></i>
                            Cancel Build
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', progressModalHTML);
    }
    
    buildProgressModal = document.getElementById('buildProgressModal');
    buildProgressModal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeBuildProgressModal() {
    if (buildProgressModal) {
        buildProgressModal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

function updateBuildProgress(percent, text) {
    const progressBar = document.getElementById('buildProgress');
    const progressText = document.getElementById('buildProgressText');
    
    if (progressBar) {
        progressBar.style.width = percent + '%';
    }
    if (progressText) {
        progressText.textContent = text;
    }
}

function cancelBuild() {
    console.log('Cancelling build...');
    closeBuildProgressModal();
    showNotification('Build cancelled', 'warning');
}

// Pull Modal Functions
function showPullModal() {
    console.log('Showing pull modal...');
    if (pullModal) {
        pullModal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
}

function showPullModalWithImage(selectedImage) {
    console.log('Showing pull modal with image:', selectedImage);
    
    // Pull modal'ı oluştur veya güncelle
    if (!pullModal) {
        createPullModal();
    }
    
    // Seçili image bilgilerini form'a doldur
    if (selectedImage) {
        const pullImageName = document.getElementById('pullImageName');
        if (pullImageName) {
            pullImageName.value = selectedImage.fullName;
        }
        
        // Base image olarak seçili image'ı göster
        const baseImageInfo = document.createElement('div');
        baseImageInfo.className = 'base-image-info';
        baseImageInfo.innerHTML = `
            <div class="form-group">
                <label>Current Image:</label>
                <div class="base-image-display">
                    <span class="base-image-name">${selectedImage.fullName}</span>
                    <span class="base-image-id">(${selectedImage.id})</span>
                </div>
            </div>
        `;
        
        // Base image info'yu form'un başına ekle
        const form = document.getElementById('pullForm');
        if (form && !form.querySelector('.base-image-info')) {
            form.insertBefore(baseImageInfo, form.firstChild);
        }
    }
    
    pullModal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closePullModal() {
    console.log('Closing pull modal...');
    if (pullModal) {
        pullModal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

function startPull() {
    console.log('Starting pull...');
    
    const imageName = document.getElementById('pullImageName').value;
    const registry = document.getElementById('pullRegistry').value;
    const customRegistry = document.getElementById('customRegistry').value;
    const useAuth = document.getElementById('pullUseAuth').checked;
    const username = document.getElementById('pullUsername').value;
    const password = document.getElementById('pullPassword').value;
    
    if (!imageName) {
        showNotification('Please enter image name', 'error');
        return;
    }
    
    // Get pull options
    const options = [];
    const pullOptions = document.querySelectorAll('input[name="pullOptions"]:checked');
    pullOptions.forEach(option => {
        options.push(option.value);
    });
    
    // Build full image name
    let fullImageName = imageName;
    if (registry === 'custom' && customRegistry) {
        fullImageName = customRegistry + '/' + imageName;
    } else if (registry !== 'docker.io') {
        fullImageName = registry + '/' + imageName;
    }
    
    // Close pull modal
    closePullModal();
    
    // Show progress modal
    showPullProgressModal();
    
    // Start pull process
    fetch('/docker-manager/api/image/pull/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            image: fullImageName,
            auth: useAuth ? { username: username, password: password } : null,
            options: options
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updatePullProgress(100, 'Pull completed successfully!');
            setTimeout(() => {
                closePullProgressModal();
                showNotification('Image pulled successfully', 'success');
                // Refresh images page
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }, 2000);
        } else {
            updatePullProgress(0, 'Pull failed: ' + data.message);
            setTimeout(() => {
                closePullProgressModal();
                showNotification('Pull failed: ' + data.message, 'error');
            }, 3000);
        }
    })
    .catch(error => {
        console.error('Pull error:', error);
        updatePullProgress(0, 'Pull error: ' + error.message);
        setTimeout(() => {
            closePullProgressModal();
            showNotification('Pull error: ' + error.message, 'error');
        }, 3000);
    });
}

function showPullProgressModal() {
    // Create progress modal if it doesn't exist
    if (!document.getElementById('pullProgressModal')) {
        const progressModalHTML = `
            <div class="modal-overlay" id="pullProgressModal">
                <div class="modal-content progress-modal">
                    <div class="modal-header">
                        <h3>
                            <i class="fas fa-download fa-spin"></i>
                            Pulling Image
                        </h3>
                    </div>
                    <div class="modal-body">
                        <div class="progress-container">
                            <div class="progress-bar">
                                <div class="progress-fill" id="pullProgress"></div>
                            </div>
                            <div class="progress-text" id="pullProgressText">Preparing pull...</div>
                        </div>
                        <div class="pull-logs" id="pullLogs">
                            <div class="log-line">Starting pull process...</div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-danger" onclick="cancelPull()">
                            <i class="fas fa-times"></i>
                            Cancel Pull
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', progressModalHTML);
    }
    
    pullProgressModal = document.getElementById('pullProgressModal');
    pullProgressModal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closePullProgressModal() {
    if (pullProgressModal) {
        pullProgressModal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

function updatePullProgress(percent, text) {
    const progressBar = document.getElementById('pullProgress');
    const progressText = document.getElementById('pullProgressText');
    
    if (progressBar) {
        progressBar.style.width = percent + '%';
    }
    if (progressText) {
        progressText.textContent = text;
    }
}

function cancelPull() {
    console.log('Cancelling pull...');
    closePullProgressModal();
    showNotification('Pull cancelled', 'warning');
}

// Remove Modal Functions
function showRemoveModal() {
    console.log('Showing remove modal...');
    if (removeModal) {
        removeModal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
}

function showRemoveModalWithImage(selectedImage) {
    console.log('Showing remove modal with image:', selectedImage);
    
    // Remove modal'ı oluştur veya güncelle
    if (!removeModal) {
        createRemoveModal();
    }
    
    // Seçili image bilgilerini form'a doldur
    if (selectedImage) {
        document.getElementById('removeImageName').textContent = selectedImage.fullName;
        document.getElementById('removeImageId').textContent = selectedImage.id;
        document.getElementById('removeImageSize').textContent = selectedImage.size || 'Unknown';
        
        // Confirmation input için expected name
        const confirmationInput = document.getElementById('removeConfirmation');
        if (confirmationInput) {
            confirmationInput.dataset.expectedName = selectedImage.fullName;
            confirmationInput.value = '';
        }
        
        // Remove button'ı disable et
        const removeBtn = document.getElementById('removeConfirmBtn');
        if (removeBtn) {
            removeBtn.disabled = true;
        }
    }
    
    removeModal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeRemoveModal() {
    console.log('Closing remove modal...');
    if (removeModal) {
        removeModal.classList.remove('show');
        document.body.style.overflow = '';
        
        // Form'u temizle
        const form = document.getElementById('removeForm');
        if (form) {
            form.reset();
        }
        
        // Custom reason group'u gizle
        const customGroup = document.getElementById('customReasonGroup');
        if (customGroup) {
            customGroup.style.display = 'none';
        }
    }
}

function confirmRemoveImage() {
    console.log('Confirming image removal...');
    
    const selectedImages = getSelectedImages();
    if (selectedImages.length === 0) {
        showNotification('No image selected', 'error');
        return;
    }
    
    const selectedImage = selectedImages[0];
    const confirmation = document.getElementById('removeConfirmation').value;
    const expectedName = document.getElementById('removeConfirmation').dataset.expectedName;
    
    if (confirmation !== expectedName) {
        showNotification('Image name confirmation does not match', 'error');
        return;
    }
    
    // Get remove options
    const options = [];
    const removeOptions = document.querySelectorAll('input[name="removeOptions"]:checked');
    removeOptions.forEach(option => {
        options.push(option.value);
    });
    
    // Get reason
    const reason = document.getElementById('removeReason').value;
    const customReason = document.getElementById('customReason').value;
    const finalReason = reason === 'other' ? customReason : reason;
    
    // Close remove modal
    closeRemoveModal();
    
    // Show progress modal
    showRemoveProgressModal();
    
    // Start remove process
    fetch(`/docker-manager/api/image/${selectedImage.id}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            options: options,
            reason: finalReason
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateRemoveProgress(100, 'Image removed successfully!');
            setTimeout(() => {
                closeRemoveProgressModal();
                showNotification('Image removed successfully', 'success');
                // Refresh images page
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }, 2000);
        } else {
            updateRemoveProgress(0, 'Remove failed: ' + data.message);
            setTimeout(() => {
                closeRemoveProgressModal();
                showNotification('Remove failed: ' + data.message, 'error');
            }, 3000);
        }
    })
    .catch(error => {
        console.error('Remove error:', error);
        updateRemoveProgress(0, 'Remove error: ' + error.message);
        setTimeout(() => {
            closeRemoveProgressModal();
            showNotification('Remove error: ' + error.message, 'error');
        }, 3000);
    });
}

function showRemoveProgressModal() {
    // Create progress modal if it doesn't exist
    if (!document.getElementById('removeProgressModal')) {
        const progressModalHTML = `
            <div class="modal-overlay" id="removeProgressModal">
                <div class="modal-content progress-modal">
                    <div class="modal-header">
                        <h3>
                            <i class="fas fa-trash fa-spin"></i>
                            Removing Image
                        </h3>
                    </div>
                    <div class="modal-body">
                        <div class="progress-container">
                            <div class="progress-bar">
                                <div class="progress-fill" id="removeProgress"></div>
                            </div>
                            <div class="progress-text" id="removeProgressText">Preparing removal...</div>
                        </div>
                        <div class="remove-logs" id="removeLogs">
                            <div class="log-line">Starting removal process...</div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-danger" onclick="cancelRemove()">
                            <i class="fas fa-times"></i>
                            Cancel Removal
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', progressModalHTML);
    }
    
    removeProgressModal = document.getElementById('removeProgressModal');
    removeProgressModal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeRemoveProgressModal() {
    if (removeProgressModal) {
        removeProgressModal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

function updateRemoveProgress(percent, text) {
    const progressBar = document.getElementById('removeProgress');
    const progressText = document.getElementById('removeProgressText');
    
    if (progressBar) {
        progressBar.style.width = percent + '%';
    }
    if (progressText) {
        progressText.textContent = text;
    }
}

function cancelRemove() {
    console.log('Cancelling remove...');
    closeRemoveProgressModal();
    showNotification('Remove cancelled', 'warning');
}

// Notification function
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
