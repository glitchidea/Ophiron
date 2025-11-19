/*
Service Builder Create Service JavaScript
Specific functionality for service creation form
*/

// Create Service namespace
window.CreateService = {
    // Configuration
    config: {
        formId: 'serviceForm',
        modalId: 'serviceModal',
        validationModalId: 'validationModal'
    },
    
    // Initialize create service functionality
    init: function() {
        this.bindEvents();
        this.initializeForm();
    },
    
    // Bind event listeners
    bindEvents: function() {
        const form = document.getElementById(this.config.formId);
        if (form) {
            form.addEventListener('submit', this.handleFormSubmit.bind(this));
        }
        
        // Service type change handler
        const serviceTypeInputs = document.querySelectorAll('input[name="service_type"]');
        serviceTypeInputs.forEach(input => {
            input.addEventListener('change', this.handleServiceTypeChange.bind(this));
        });
        
        // Application path change handler
        const appPathInput = document.getElementById('application_path');
        if (appPathInput) {
            appPathInput.addEventListener('change', this.handleApplicationPathChange.bind(this));
        }
        
        // Validate button
        const validateBtn = document.getElementById('validateBtn');
        if (validateBtn) {
            validateBtn.addEventListener('click', this.handleValidateConfiguration.bind(this));
        }
    },
    
    // Initialize form
    initializeForm: function() {
        // Set default working directory based on application path
        const appPathInput = document.getElementById('application_path');
        const workingDirInput = document.getElementById('working_directory');
        
        if (appPathInput && workingDirInput) {
            appPathInput.addEventListener('input', function() {
                if (this.value && !workingDirInput.value) {
                    const path = this.value.trim();
                    if (path) {
                        const dir = path.substring(0, path.lastIndexOf('/'));
                        workingDirInput.value = dir;
                    }
                }
            });
        }
        
        // Show default service type settings (Normal Application)
        const normalSettings = document.getElementById('normalSettings');
        if (normalSettings) {
            normalSettings.style.display = 'block';
        }
    },
    
    // Handle service type change
    handleServiceTypeChange: function(event) {
        const serviceType = event.target.value;
        const webSettings = document.getElementById('webSettings');
        const backgroundSettings = document.getElementById('backgroundSettings');
        const normalSettings = document.getElementById('normalSettings');
        
        // Hide all service-specific settings first
        if (webSettings) webSettings.style.display = 'none';
        if (backgroundSettings) backgroundSettings.style.display = 'none';
        if (normalSettings) normalSettings.style.display = 'none';
        
        // Show settings based on service type
        if (serviceType === 'web') {
            if (webSettings) {
                webSettings.style.display = 'block';
                // Auto-suggest port for web applications
                const portInput = document.getElementById('port');
                if (portInput && !portInput.value) {
                    portInput.value = '8080';
                }
            }
        } else if (serviceType === 'background') {
            if (backgroundSettings) {
                backgroundSettings.style.display = 'block';
            }
        } else if (serviceType === 'normal') {
            if (normalSettings) {
                normalSettings.style.display = 'block';
            }
        }
        
        // Update form validation based on service type
        this.updateFormValidation(serviceType);
    },
    
    // Update form validation based on service type
    updateFormValidation: function(serviceType) {
        const portInput = document.getElementById('port');
        const hostInput = document.getElementById('host');
        
        if (serviceType === 'web') {
            // Make port and host required for web applications
            if (portInput) {
                portInput.required = true;
                portInput.setAttribute('data-required', 'true');
            }
            if (hostInput) {
                hostInput.required = true;
                hostInput.setAttribute('data-required', 'true');
            }
        } else {
            // Make port and host optional for other service types
            if (portInput) {
                portInput.required = false;
                portInput.removeAttribute('data-required');
            }
            if (hostInput) {
                hostInput.required = false;
                hostInput.removeAttribute('data-required');
            }
        }
    },
    
    // Handle application path change
    handleApplicationPathChange: function(event) {
        const appPath = event.target.value.trim();
        
        if (appPath && appPath.endsWith('.py')) {
            // Auto-suggest Python interpreter
            const interpreterInput = document.getElementById('interpreter');
            if (interpreterInput && !interpreterInput.value) {
                interpreterInput.value = '/usr/bin/python3';
            }
            
            // Analyze Python file for configuration
            this.analyzePythonFile(appPath);
        }
    },
    
    // Analyze Python file
    analyzePythonFile: function(filePath) {
        ServiceBuilder.utils.apiRequest('analyze-python/', {
            method: 'POST',
            body: JSON.stringify({ file_path: filePath })
        })
        .then(response => {
            if (response.port) {
                this.showPortSuggestion(response.port);
            }
            
            if (response.host) {
                const hostSelect = document.getElementById('host');
                if (hostSelect) {
                    hostSelect.value = response.host;
                }
            }
        })
        .catch(error => {
            console.log('Python analysis failed:', error);
        });
    },
    
    // Show port suggestion
    showPortSuggestion: function(port) {
        const portInput = document.getElementById('port');
        if (portInput && !portInput.value) {
            const confirmMessage = `
                <div class="alert alert-info">
                    <strong>Port Detected!</strong><br>
                    This application is configured to run on port ${port}.<br>
                    <div class="mt-2">
                        <button type="button" class="btn btn-sm btn-success me-2" 
                                onclick="CreateService.useDetectedPort(${port})">
                            Use This Port
                        </button>
                        <button type="button" class="btn btn-sm btn-secondary" 
                                onclick="CreateService.useCustomPort()">
                            Use Different Port
                        </button>
                    </div>
                </div>
            `;
            
            // Insert suggestion above the form
            const form = document.getElementById(this.config.formId);
            form.insertAdjacentHTML('afterbegin', confirmMessage);
        }
    },
    
    // Use detected port
    useDetectedPort: function(port) {
        const portInput = document.getElementById('port');
        if (portInput) {
            portInput.value = port;
            // Trigger validation
            portInput.dispatchEvent(new Event('input'));
        }
        // Remove suggestion
        const alert = document.querySelector('.alert-info');
        if (alert) {
            alert.remove();
        }
    },
    
    // Use custom port
    useCustomPort: function() {
        const portInput = document.getElementById('port');
        if (portInput) {
            portInput.value = '';
            portInput.focus();
        }
        // Remove suggestion
        const alert = document.querySelector('.alert-info');
        if (alert) {
            alert.remove();
        }
    },
    
    // Handle form submission
    handleFormSubmit: function(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Show modal
        this.showServiceModal('Creating service, please wait...');
        
        // Submit form
        this.submitService(data);
    },
    
    // Submit service
    submitService: function(data) {
        ServiceBuilder.utils.apiRequest('create-service/', {
            method: 'POST',
            body: JSON.stringify(data)
        })
        .then(response => {
            this.showServiceModal(`
                <div class="service-status">
                    <div class="service-status-icon success">
                        <i class="fas fa-check-circle"></i>
                    </div>
                    <h3 class="service-status-title">Service Created Successfully!</h3>
                    <p class="service-status-message">${response.message}</p>
                    <div class="service-status-actions">
                        <a href="/service-builder/services/" class="btn btn-primary">
                            <i class="fas fa-list"></i>
                            View Services
                        </a>
                        <a href="/service-builder/services/${data.name}/" class="btn btn-outline">
                            <i class="fas fa-eye"></i>
                            View Details
                        </a>
                    </div>
                </div>
            `);
            
            // Auto redirect after 3 seconds
            setTimeout(() => {
                window.location.href = '/service-builder/services/';
            }, 3000);
        })
        .catch(error => {
            this.showServiceModal(`
                <div class="service-status">
                    <div class="service-status-icon error">
                        <i class="fas fa-times-circle"></i>
                    </div>
                    <h3 class="service-status-title">Service Creation Failed</h3>
                    <p class="service-status-message">${error.message}</p>
                    <div class="service-status-actions">
                        <button type="button" class="btn btn-primary" onclick="CreateService.hideServiceModal()">
                            <i class="fas fa-edit"></i>
                            Try Again
                        </button>
                    </div>
                </div>
            `);
        });
    },
    
    // Handle validate configuration
    handleValidateConfiguration: function() {
        const form = document.getElementById(this.config.formId);
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Show validation modal
        this.showValidationModal('Validating configuration...');
        
        // Validate configuration
        this.validateConfiguration(data);
    },
    
    // Validate configuration
    validateConfiguration: function(data) {
        const validationItems = [];
        
        // Validate application path
        if (!data.application_path) {
            validationItems.push({
                type: 'error',
                title: 'Application Path',
                message: 'Application path is required'
            });
        } else {
            validationItems.push({
                type: 'success',
                title: 'Application Path',
                message: 'Application path is valid'
            });
        }
        
        // Validate service name
        if (!data.name) {
            validationItems.push({
                type: 'error',
                title: 'Service Name',
                message: 'Service name is required'
            });
        } else if (!/^[a-z0-9-_]+$/.test(data.name)) {
            validationItems.push({
                type: 'error',
                title: 'Service Name',
                message: 'Service name can only contain lowercase letters, numbers, hyphens, and underscores'
            });
        } else {
            validationItems.push({
                type: 'success',
                title: 'Service Name',
                message: 'Service name is valid'
            });
        }
        
        // Validate user
        if (!data.user) {
            validationItems.push({
                type: 'error',
                title: 'User',
                message: 'User is required'
            });
        } else {
            validationItems.push({
                type: 'success',
                title: 'User',
                message: `Service will run as user: ${data.user}`
            });
        }
        
        // Validate port for web applications
        if (data.service_type === 'web' && data.port) {
            const port = parseInt(data.port);
            if (port < 1 || port > 65535) {
                validationItems.push({
                    type: 'error',
                    title: 'Port',
                    message: 'Port must be between 1 and 65535'
                });
            } else {
                validationItems.push({
                    type: 'success',
                    title: 'Port',
                    message: `Web application will run on port ${port}`
                });
            }
        }
        
        // Show validation results
        this.showValidationResults(validationItems);
    },
    
    // Show validation results
    showValidationResults: function(items) {
        const resultsHtml = `
            <div class="validation-results">
                ${items.map(item => `
                    <div class="validation-item ${item.type}">
                        <div class="validation-icon ${item.type}">
                            <i class="fas fa-${item.type === 'success' ? 'check' : item.type === 'error' ? 'times' : 'info'}"></i>
                        </div>
                        <div class="validation-content">
                            <h4 class="validation-title">${item.title}</h4>
                            <p class="validation-message">${item.message}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        this.showValidationModal(resultsHtml);
    },
    
    // Show service modal
    showServiceModal: function(content) {
        const modal = document.getElementById(this.config.modalId);
        if (modal) {
            const modalBody = modal.querySelector('.modal-body');
            if (modalBody) {
                modalBody.innerHTML = content;
            }
            ServiceBuilder.utils.showModal(this.config.modalId);
        }
    },
    
    // Hide service modal
    hideServiceModal: function() {
        ServiceBuilder.utils.hideModal(this.config.modalId);
    },
    
    // Show validation modal
    showValidationModal: function(content) {
        const modal = document.getElementById(this.config.validationModalId);
        if (modal) {
            const modalBody = modal.querySelector('.modal-body');
            if (modalBody) {
                modalBody.innerHTML = content;
            }
            ServiceBuilder.utils.showModal(this.config.validationModalId);
        }
    },
    
    // Hide validation modal
    hideValidationModal: function() {
        ServiceBuilder.utils.hideModal(this.config.validationModalId);
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    CreateService.init();
});
