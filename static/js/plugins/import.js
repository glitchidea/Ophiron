// Plugin Import JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializePluginImport();
});

function initializePluginImport() {
    const importBtn = document.getElementById('import-plugin-btn');
    const importModal = document.getElementById('plugin-import-modal');
    const closeBtn = document.getElementById('import-modal-close');
    const cancelBtn = document.getElementById('cancel-import-btn');
    const closeAfterImportBtn = document.getElementById('close-import-modal-btn');
    const validateBtn = document.getElementById('validate-plugin-btn');
    const confirmImportBtn = document.getElementById('confirm-import-btn');
    const backBtn = document.getElementById('back-to-step1-btn');
    const folderInput = document.getElementById('plugin-folder-input');
    const selectFolderBtn = document.getElementById('select-folder-btn');
    const selectedFolderName = document.getElementById('selected-folder-name');
    
    if (!importBtn || !importModal) return;
    
    let selectedFiles = [];
    let selectedFolderPath = '';
    
    // Open modal
    importBtn.addEventListener('click', function() {
        showImportModal();
    });
    
    // Close modal
    if (closeBtn) {
        closeBtn.addEventListener('click', hideImportModal);
    }
    
    if (cancelBtn) {
        cancelBtn.addEventListener('click', hideImportModal);
    }
    
    if (closeAfterImportBtn) {
        closeAfterImportBtn.addEventListener('click', function() {
            hideImportModal();
            // Reload page to show new plugin
            window.location.reload();
        });
    }
    
    // Overlay click
    const overlay = importModal.querySelector('.modal-overlay');
    if (overlay) {
        overlay.addEventListener('click', hideImportModal);
    }
    
    // ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && importModal.classList.contains('show')) {
            hideImportModal();
        }
    });
    
    // Select folder button
    if (selectFolderBtn && folderInput) {
        selectFolderBtn.addEventListener('click', function() {
            folderInput.click();
        });
        
        folderInput.addEventListener('change', function(e) {
            const files = Array.from(e.target.files);
            if (files.length === 0) {
                selectedFiles = [];
                selectedFolderPath = '';
                selectedFolderName.textContent = '';
                validateBtn.disabled = true;
                return;
            }
            
            selectedFiles = files;
            
            // Get folder name from first file's path
            const firstFile = files[0];
            const pathParts = firstFile.webkitRelativePath.split('/');
            if (pathParts.length > 0) {
                selectedFolderPath = pathParts[0];
                selectedFolderName.textContent = selectedFolderPath;
                validateBtn.disabled = false;
            }
        });
    }
    
    // Validate plugin
    if (validateBtn) {
        validateBtn.addEventListener('click', function() {
            if (selectedFiles.length === 0) {
                alert('Please select a plugin folder');
                return;
            }
            validatePluginFromFiles(selectedFiles);
        });
    }
    
    // Confirm import
    if (confirmImportBtn) {
        confirmImportBtn.addEventListener('click', function() {
            if (selectedFiles.length === 0) {
                alert('Please select a plugin folder');
                return;
            }
            importPluginFromFiles(selectedFiles);
        });
    }
    
    // Back to step 1
    if (backBtn) {
        backBtn.addEventListener('click', function() {
            showStep(1);
        });
    }
}

function showImportModal() {
    const modal = document.getElementById('plugin-import-modal');
    if (!modal) return;
    
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
    showStep(1);
    
    // Clear previous data
    const folderInput = document.getElementById('plugin-folder-input');
    const selectedFolderName = document.getElementById('selected-folder-name');
    const validateBtn = document.getElementById('validate-plugin-btn');
    
    if (folderInput) {
        folderInput.value = '';
    }
    if (selectedFolderName) {
        selectedFolderName.textContent = '';
    }
    if (validateBtn) {
        validateBtn.disabled = true;
    }
    
    const preview = document.getElementById('plugin-preview');
    if (preview) {
        preview.innerHTML = '';
    }
    
    // Reset selected files
    if (typeof selectedFiles !== 'undefined') {
        selectedFiles = [];
    }
}

function hideImportModal() {
    const modal = document.getElementById('plugin-import-modal');
    if (!modal) return;
    
    modal.classList.remove('show');
    document.body.style.overflow = '';
}

function showStep(step) {
    // Hide all steps
    for (let i = 1; i <= 3; i++) {
        const stepEl = document.getElementById(`import-step-${i}`);
        if (stepEl) {
            stepEl.style.display = 'none';
        }
    }
    
    // Show requested step
    const stepEl = document.getElementById(`import-step-${step}`);
    if (stepEl) {
        stepEl.style.display = 'block';
    }
}

function validatePluginFromFiles(files) {
    const validateBtn = document.getElementById('validate-plugin-btn');
    const preview = document.getElementById('plugin-preview');
    
    if (!preview) return;
    
    // Show loading
    validateBtn.disabled = true;
    validateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Validating...';
    
    preview.innerHTML = `
        <div class="import-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Uploading and validating plugin...</p>
        </div>
    `;
    
    // Create FormData to upload files
    const formData = new FormData();
    Array.from(files).forEach((file, index) => {
        formData.append(`file_${index}`, file);
        // Preserve relative path
        formData.append(`path_${index}`, file.webkitRelativePath || file.name);
    });
    formData.append('file_count', files.length);
    
    fetch('/plugins/import/validate/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        validateBtn.disabled = false;
        validateBtn.innerHTML = '<i class="fas fa-check"></i> Validate Plugin';
        
        if (data.success && data.preview) {
            displayPluginPreview(data.preview);
            showStep(2);
        } else {
            preview.innerHTML = `
                <div class="plugin-preview-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <div>
                        <strong>Validation Failed</strong>
                        <p>${data.error || 'Unknown error'}</p>
                    </div>
                </div>
            `;
        }
    })
    .catch(error => {
        validateBtn.disabled = false;
        validateBtn.innerHTML = '<i class="fas fa-check"></i> Validate Plugin';
        
        preview.innerHTML = `
            <div class="plugin-preview-error">
                <i class="fas fa-exclamation-triangle"></i>
                <div>
                    <strong>Error</strong>
                    <p>${error.message || 'Failed to validate plugin'}</p>
                </div>
            </div>
        `;
    });
}

function displayPluginPreview(preview) {
    const previewEl = document.getElementById('plugin-preview');
    if (!previewEl) return;
    
    // Get display name (support i18n)
    const displayName = typeof preview.display_name === 'object' 
        ? (preview.display_name.en || preview.display_name.tr || preview.name)
        : (preview.display_name || preview.name);
    
    // Get description (support i18n)
    const description = typeof preview.description === 'object'
        ? (preview.description.en || preview.description.tr || 'No description available.')
        : (preview.description || 'No description available.');
    
    // Get author name
    const authorName = typeof preview.author === 'object'
        ? (preview.author.name || 'Unknown')
        : (preview.author || 'Unknown');
    
    // Features
    const features = [];
    if (preview.has_go_binary) features.push({ icon: 'fas fa-code', text: 'Go Binary' });
    if (preview.has_settings) features.push({ icon: 'fas fa-cog', text: 'Settings' });
    if (preview.has_scheduled_tasks) features.push({ icon: 'fas fa-clock', text: 'Scheduled Tasks' });
    if (preview.supported_languages && preview.supported_languages.length > 0) {
        features.push({ icon: 'fas fa-language', text: `${preview.supported_languages.length} Languages` });
    }
    
    let warningHtml = '';
    if (preview.name_conflict) {
        warningHtml = `
            <div class="plugin-preview-warning">
                <i class="fas fa-exclamation-triangle"></i>
                <div>
                    <strong>Warning: Plugin name conflict</strong>
                    <p>A plugin with the name "${preview.name}" already exists in the system. Importing will overwrite the existing plugin.</p>
                </div>
            </div>
        `;
    }
    
    previewEl.innerHTML = `
        <div class="plugin-preview">
            <div class="plugin-preview-header">
                <div class="plugin-preview-icon">
                    <i class="${preview.icon || 'fas fa-cube'}"></i>
                </div>
                <div class="plugin-preview-info">
                    <h4>${escapeHtml(displayName)}</h4>
                    <p>${escapeHtml(description)}</p>
                </div>
                <span class="plugin-preview-badge ${preview.name_conflict ? 'warning' : 'success'}">
                    ${preview.name_conflict ? '⚠ Conflict' : '✓ Valid'}
                </span>
            </div>
            
            <div class="plugin-preview-details">
                <div class="preview-detail-item">
                    <span class="preview-detail-label">Name</span>
                    <span class="preview-detail-value">${escapeHtml(preview.name)}</span>
                </div>
                <div class="preview-detail-item">
                    <span class="preview-detail-label">Version</span>
                    <span class="preview-detail-value">${escapeHtml(preview.version || 'N/A')}</span>
                </div>
                <div class="preview-detail-item">
                    <span class="preview-detail-label">Author</span>
                    <span class="preview-detail-value">${escapeHtml(authorName)}</span>
                </div>
                <div class="preview-detail-item">
                    <span class="preview-detail-label">Category</span>
                    <span class="preview-detail-value">${escapeHtml(preview.category || 'other')}</span>
                </div>
                ${preview.route ? `
                <div class="preview-detail-item">
                    <span class="preview-detail-label">Route</span>
                    <span class="preview-detail-value">/${escapeHtml(preview.route)}</span>
                </div>
                ` : ''}
            </div>
            
            ${features.length > 0 ? `
                <div class="plugin-preview-features">
                    ${features.map(f => `
                        <span class="feature-badge">
                            <i class="${f.icon}"></i>
                            ${f.text}
                        </span>
                    `).join('')}
                </div>
            ` : ''}
            
            ${warningHtml}
        </div>
    `;
}

function importPluginFromFiles(files) {
    const confirmBtn = document.getElementById('confirm-import-btn');
    const resultEl = document.getElementById('import-result');
    
    if (!resultEl) return;
    
    // Show loading
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Importing...';
    
    resultEl.innerHTML = `
        <div class="import-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Importing plugin...</p>
        </div>
    `;
    
    showStep(3);
    
    // Files are already uploaded during validation and stored in session
    // Just send an empty POST request - backend will use session temp_dir
    const formData = new FormData();
    
    fetch('/plugins/import/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = '<i class="fas fa-check"></i> Import Plugin';
        
        if (data.success) {
            resultEl.innerHTML = `
                <div class="import-result success">
                    <i class="fas fa-check-circle"></i>
                    <h3>Plugin Imported Successfully!</h3>
                    <p>${data.message || 'Plugin has been imported and is now available in your system.'}</p>
                    <p style="margin-top: 12px; font-size: 13px; color: #6b7280;">
                        The page will reload automatically after closing this dialog.
                    </p>
                </div>
            `;
        } else {
            resultEl.innerHTML = `
                <div class="import-result error">
                    <i class="fas fa-times-circle"></i>
                    <h3>Import Failed</h3>
                    <p>${data.error || 'Unknown error occurred'}</p>
                </div>
            `;
        }
    })
    .catch(error => {
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = '<i class="fas fa-check"></i> Import Plugin';
        
        resultEl.innerHTML = `
            <div class="import-result error">
                <i class="fas fa-times-circle"></i>
                <h3>Import Failed</h3>
                <p>${error.message || 'Failed to import plugin'}</p>
            </div>
        `;
    });
}

function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

