/**
 * Service Details - JavaScript Module
 * Handles service details, control, and deletion
 */

(function() {
    'use strict';
    
    let currentService = null;
    let detailsModal, controlModal, deleteModal;
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
    function initialize() {
        // Get modal elements
        detailsModal = document.getElementById('serviceDetailsModal');
        controlModal = document.getElementById('serviceControlModal');
        deleteModal = document.getElementById('serviceDeleteModal');
        
        // Initialize event listeners
        initializeEventListeners();
        
        console.log('Service Details module initialized successfully');
    }
    
    function initializeEventListeners() {
        // Control modal buttons
        if (controlModal) {
            controlModal.querySelectorAll('[data-action]').forEach(button => {
                button.addEventListener('click', function() {
                    const action = this.dataset.action;
                    performServiceAction(action);
                });
            });
        }
        
        // Delete confirmation
        const confirmDeleteCheckbox = document.getElementById('confirmDelete');
        const confirmDeleteBtn = document.getElementById('confirmDeleteService');
        
        if (confirmDeleteCheckbox && confirmDeleteBtn) {
            confirmDeleteCheckbox.addEventListener('change', function() {
                confirmDeleteBtn.disabled = !this.checked;
            });
            
            confirmDeleteBtn.addEventListener('click', function() {
                if (confirmDeleteCheckbox.checked) {
                    performServiceDelete();
                }
            });
        }
        
        // Modal close handlers
        setupModalCloseHandlers();
    }
    
    function setupModalCloseHandlers() {
        const modals = [detailsModal, controlModal, deleteModal];
        
        modals.forEach(modal => {
            if (modal) {
                const closeBtn = modal.querySelector('.modal-close');
                if (closeBtn) {
                    closeBtn.addEventListener('click', () => closeModal(modal));
                }
                
                // Close on backdrop click
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        closeModal(modal);
                    }
                });
            }
        });
    }
    
    function openDetails(serviceName) {
        currentService = serviceName;
        
        if (!detailsModal) {
            console.error('Service details modal not found');
            return;
        }
        
        // Show loading state
        const modalBody = detailsModal.querySelector('.modal-body');
        if (modalBody) {
            modalBody.innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Loading service details...</span>
                </div>
            `;
        }
        
        // Update title
        const title = detailsModal.querySelector('.modal-title span');
        if (title) {
            title.textContent = `Service Details: ${serviceName}`;
        }
        
        // Show modal
        showModal(detailsModal);
        
        // Load service details
        loadServiceDetails(serviceName);
    }
    
    function loadServiceDetails(serviceName) {
        fetch(`/service-monitoring/api/service/${serviceName}/details/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderServiceDetails(data.service);
                } else {
                    showError('Failed to load service details: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error loading service details:', error);
                showError('Failed to load service details: ' + error.message);
            });
    }
    
    function renderServiceDetails(service) {
        const modalBody = detailsModal.querySelector('.modal-body');
        if (!modalBody) return;
        
        const statusClass = service.status === 'active' ? 'active' : 'inactive';
        const statusText = service.status === 'active' ? 'Active' : 'Inactive';
        
        modalBody.innerHTML = `
            <div class="service-details">
                <!-- Service Overview -->
                <div class="details-section">
                    <h4>Service Overview</h4>
                    <div class="details-grid">
                        <div class="detail-item">
                            <label>Name:</label>
                            <span>${service.name}</span>
                        </div>
                        <div class="detail-item">
                            <label>Status:</label>
                            <span class="status-badge ${statusClass}">${statusText}</span>
                        </div>
                        <div class="detail-item">
                            <label>Description:</label>
                            <span>${service.description || 'No description'}</span>
                        </div>
                        <div class="detail-item">
                            <label>Loaded:</label>
                            <span>${service.loaded ? 'Yes' : 'No'}</span>
                        </div>
                        <div class="detail-item">
                            <label>Enabled:</label>
                            <span>${service.enabled ? 'Yes' : 'No'}</span>
                        </div>
                        <div class="detail-item">
                            <label>Uptime:</label>
                            <span>${service.uptime || 'N/A'}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Resource Usage -->
                <div class="details-section">
                    <h4>Resource Usage</h4>
                    <div class="details-grid">
                        <div class="detail-item">
                            <label>Memory Usage:</label>
                            <span>${service.memory_usage || '0'}%</span>
                        </div>
                        <div class="detail-item">
                            <label>CPU Usage:</label>
                            <span>${service.cpu_usage || '0'}%</span>
                        </div>
                        <div class="detail-item">
                            <label>PID:</label>
                            <span>${service.pid || 'N/A'}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Dependencies -->
                ${service.dependencies && service.dependencies.length > 0 ? `
                <div class="details-section">
                    <h4>Dependencies</h4>
                    <div class="dependencies-list">
                        ${service.dependencies.map(dep => `<span class="dependency-item">${dep}</span>`).join('')}
                    </div>
                </div>
                ` : ''}
                
                <!-- Unit File -->
                ${service.unit_file ? `
                <div class="details-section">
                    <h4>Unit File</h4>
                    <div class="unit-file-content">
                        <pre>${service.unit_file}</pre>
                    </div>
                </div>
                ` : ''}
                
                <!-- Recent Logs -->
                ${service.logs && service.logs.length > 0 ? `
                <div class="details-section">
                    <h4>Recent Logs</h4>
                    <div class="logs-content">
                        <pre>${service.logs.slice(0, 10).join('\n')}</pre>
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }
    
    function openControl(serviceName) {
        currentService = serviceName;
        
        if (!controlModal) {
            console.error('Service control modal not found');
            return;
        }
        
        // Update service info
        const serviceNameEl = controlModal.querySelector('#controlServiceName');
        const serviceStatusEl = controlModal.querySelector('#controlServiceStatus');
        
        if (serviceNameEl) serviceNameEl.textContent = serviceName;
        if (serviceStatusEl) {
            // Get current status
            fetch(`/service-monitoring/api/service/${serviceName}/details/`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const statusClass = data.service.status === 'active' ? 'active' : 'inactive';
                        const statusText = data.service.status === 'active' ? 'Active' : 'Inactive';
                        serviceStatusEl.innerHTML = `<span class="status-badge ${statusClass}">${statusText}</span>`;
                    }
                });
        }
        
        // Clear previous result
        const resultEl = controlModal.querySelector('#controlResult');
        if (resultEl) {
            resultEl.style.display = 'none';
        }
        
        showModal(controlModal);
    }
    
    function performServiceAction(action) {
        if (!currentService) return;
        
        // Show loading state
        const resultEl = controlModal.querySelector('#controlResult');
        if (resultEl) {
            resultEl.style.display = 'block';
            resultEl.innerHTML = `
                <div class="result-message">
                    <i class="fas fa-spinner fa-spin"></i>
                    Performing ${action}...
                </div>
            `;
        }
        
        // Disable all control buttons
        controlModal.querySelectorAll('[data-action]').forEach(btn => {
            btn.disabled = true;
        });
        
        fetch(`/service-monitoring/api/service/${currentService}/control/${action}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess(data.message);
                // Refresh service list after successful action
                if (window.ServiceMonitor) {
                    window.ServiceMonitor.loadServices();
                }
            } else {
                showError(data.message || 'Action failed');
            }
        })
        .catch(error => {
            console.error('Error performing service action:', error);
            showError('Action failed: ' + error.message);
        })
        .finally(() => {
            // Re-enable control buttons
            controlModal.querySelectorAll('[data-action]').forEach(btn => {
                btn.disabled = false;
            });
        });
    }
    
    function openDelete(serviceName) {
        currentService = serviceName;
        
        if (!deleteModal) {
            console.error('Service delete modal not found');
            return;
        }
        
        // Update service name
        const serviceNameEl = deleteModal.querySelector('#deleteServiceName');
        if (serviceNameEl) {
            serviceNameEl.textContent = serviceName;
        }
        
        // Reset checkbox
        const confirmCheckbox = deleteModal.querySelector('#confirmDelete');
        if (confirmCheckbox) {
            confirmCheckbox.checked = false;
        }
        
        showModal(deleteModal);
    }
    
    function performServiceDelete() {
        if (!currentService) return;
        
        // Show loading state
        const confirmBtn = deleteModal.querySelector('#confirmDeleteService');
        if (confirmBtn) {
            const originalContent = confirmBtn.innerHTML;
            confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
            confirmBtn.disabled = true;
        }
        
        fetch(`/service-monitoring/api/service/${currentService}/delete/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess(data.message);
                closeModal(deleteModal);
                // Refresh service list
                if (window.ServiceMonitor) {
                    window.ServiceMonitor.loadServices();
                }
            } else {
                showError(data.message || 'Delete failed');
            }
        })
        .catch(error => {
            console.error('Error deleting service:', error);
            showError('Delete failed: ' + error.message);
        })
        .finally(() => {
            // Reset button
            const confirmBtn = deleteModal.querySelector('#confirmDeleteService');
            if (confirmBtn) {
                confirmBtn.innerHTML = '<i class="fas fa-trash"></i> Delete Service';
                confirmBtn.disabled = false;
            }
        });
    }
    
    function showModal(modal) {
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }
    
    function closeModal(modal) {
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    function showSuccess(message) {
        const resultEl = controlModal.querySelector('#controlResult');
        if (resultEl) {
            resultEl.style.display = 'block';
            resultEl.innerHTML = `
                <div class="result-message success">
                    <i class="fas fa-check-circle"></i>
                    ${message}
                </div>
            `;
        }
    }
    
    function showError(message) {
        const resultEl = controlModal.querySelector('#controlResult');
        if (resultEl) {
            resultEl.style.display = 'block';
            resultEl.innerHTML = `
                <div class="result-message error">
                    <i class="fas fa-exclamation-circle"></i>
                    ${message}
                </div>
            `;
        }
    }
    
    function getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    // Public API
    window.ServiceDetails = {
        openDetails: openDetails,
        openControl: openControl,
        openDelete: openDelete
    };
    
})();
