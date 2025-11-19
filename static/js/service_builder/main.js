/*
Service Builder Main JavaScript
Core functionality and utilities
*/

// Service Builder namespace
window.ServiceBuilder = {
    // Configuration
    config: {
        apiBaseUrl: '/service-builder/api/',
        csrfToken: document.querySelector('[name=csrfmiddlewaretoken]')?.value,
        debounceDelay: 300
    },
    
    // Utilities
    utils: {
        // Debounce function
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Show loading state
        showLoading: function(element) {
            if (element) {
                element.classList.add('loading');
                element.disabled = true;
            }
        },
        
        // Hide loading state
        hideLoading: function(element) {
            if (element) {
                element.classList.remove('loading');
                element.disabled = false;
            }
        },
        
        // Show validation message
        showValidation: function(element, message, type = 'error') {
            const validationElement = document.getElementById(element.id + 'Validation') || 
                                    element.parentNode.querySelector('.validation-message');
            
            if (validationElement) {
                validationElement.textContent = message;
                validationElement.className = `validation-message ${type}`;
                validationElement.style.display = 'block';
            }
        },
        
        // Hide validation message
        hideValidation: function(element) {
            const validationElement = document.getElementById(element.id + 'Validation') || 
                                    element.parentNode.querySelector('.validation-message');
            
            if (validationElement) {
                validationElement.style.display = 'none';
            }
        },
        
        // Make API request
        apiRequest: async function(url, options = {}) {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': ServiceBuilder.config.csrfToken
                }
            };
            
            const mergedOptions = { ...defaultOptions, ...options };
            
            try {
                const response = await fetch(ServiceBuilder.config.apiBaseUrl + url, mergedOptions);
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'API request failed');
                }
                
                return data;
            } catch (error) {
                console.error('API request failed:', error);
                throw error;
            }
        },
        
        // Show modal
        showModal: function(modalId, content = null) {
            const modal = document.getElementById(modalId);
            if (modal) {
                if (content) {
                    const modalBody = modal.querySelector('.modal-body');
                    if (modalBody) {
                        modalBody.innerHTML = content;
                    }
                }
                modal.classList.add('show');
                modal.style.display = 'flex';
            }
        },
        
        // Hide modal
        hideModal: function(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.remove('show');
                setTimeout(() => {
                    modal.style.display = 'none';
                }, 300);
            }
        },
        
        // Show notification
        showNotification: function(message, type = 'info') {
            // Create notification element
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.innerHTML = `
                <div class="notification-content">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'times-circle' : 'info-circle'}"></i>
                    <span>${message}</span>
                </div>
            `;
            
            // Add to page
            document.body.appendChild(notification);
            
            // Show notification
            setTimeout(() => {
                notification.classList.add('show');
            }, 100);
            
            // Auto remove
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => {
                    document.body.removeChild(notification);
                }, 300);
            }, 3000);
        }
    },
    
    // Form handlers
    forms: {
        // Initialize form validation
        initValidation: function() {
            const forms = document.querySelectorAll('form[data-validate]');
            forms.forEach(form => {
                form.addEventListener('submit', ServiceBuilder.forms.handleSubmit);
            });
        },
        
        // Handle form submission
        handleSubmit: function(event) {
            event.preventDefault();
            
            const form = event.target;
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            
            // Validate form
            if (ServiceBuilder.forms.validateForm(form)) {
                ServiceBuilder.forms.submitForm(form, data);
            }
        },
        
        // Validate form
        validateForm: function(form) {
            let isValid = true;
            const requiredFields = form.querySelectorAll('[required]');
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    ServiceBuilder.utils.showValidation(field, 'This field is required', 'error');
                    isValid = false;
                } else {
                    ServiceBuilder.utils.hideValidation(field);
                }
            });
            
            return isValid;
        },
        
        // Submit form
        submitForm: function(form, data) {
            const submitBtn = form.querySelector('[type="submit"]');
            ServiceBuilder.utils.showLoading(submitBtn);
            
            // Make API request
            ServiceBuilder.utils.apiRequest('create-service/', {
                method: 'POST',
                body: JSON.stringify(data)
            })
            .then(response => {
                ServiceBuilder.utils.showNotification('Service created successfully!', 'success');
                // Redirect or show success modal
                setTimeout(() => {
                    window.location.href = '/service-builder/services/';
                }, 1500);
            })
            .catch(error => {
                ServiceBuilder.utils.showNotification(error.message, 'error');
            })
            .finally(() => {
                ServiceBuilder.utils.hideLoading(submitBtn);
            });
        }
    },
    
    // Service type handlers
    serviceTypes: {
        // Initialize service type selection
        init: function() {
            const serviceTypeInputs = document.querySelectorAll('input[name="service_type"]');
            const webSettings = document.getElementById('webSettings');
            
            serviceTypeInputs.forEach(input => {
                input.addEventListener('change', function() {
                    if (this.value === 'web') {
                        webSettings.style.display = 'block';
                    } else {
                        webSettings.style.display = 'none';
                    }
                });
            });
        }
    },
    
    // Path validation
    pathValidation: {
        // Initialize path validation
        init: function() {
            const pathInput = document.getElementById('application_path');
            if (pathInput) {
                const debouncedValidate = ServiceBuilder.utils.debounce(
                    ServiceBuilder.pathValidation.validate,
                    ServiceBuilder.config.debounceDelay
                );
                
                pathInput.addEventListener('input', debouncedValidate);
            }
        },
        
        // Validate application path
        validate: function(event) {
            const pathInput = event.target;
            const path = pathInput.value.trim();
            
            if (path.length < 3) {
                ServiceBuilder.utils.hideValidation(pathInput);
                return;
            }
            
            ServiceBuilder.utils.apiRequest('validate-path/', {
                method: 'POST',
                body: JSON.stringify({
                    app_path: path,
                    app_type: document.querySelector('input[name="service_type"]:checked')?.value || 'normal'
                })
            })
            .then(response => {
                if (response.valid) {
                    ServiceBuilder.utils.showValidation(pathInput, response.message, 'success');
                } else {
                    ServiceBuilder.utils.showValidation(pathInput, response.message, 'error');
                }
            })
            .catch(error => {
                ServiceBuilder.utils.showValidation(pathInput, 'Validation failed', 'error');
            });
        }
    },
    
    // Port validation
    portValidation: {
        // Initialize port validation
        init: function() {
            const portInput = document.getElementById('port');
            if (portInput) {
                const debouncedValidate = ServiceBuilder.utils.debounce(
                    ServiceBuilder.portValidation.validate,
                    ServiceBuilder.config.debounceDelay
                );
                
                portInput.addEventListener('input', debouncedValidate);
            }
        },
        
        // Validate port
        validate: function(event) {
            const portInput = event.target;
            const port = parseInt(portInput.value);
            
            if (!port || port < 1 || port > 65535) {
                ServiceBuilder.utils.showValidation(portInput, 'Port must be between 1 and 65535', 'error');
                return;
            }
            
            ServiceBuilder.utils.apiRequest(`check-port/${port}/`)
            .then(response => {
                if (response.available) {
                    ServiceBuilder.utils.showValidation(portInput, 'Port is available', 'success');
                } else {
                    ServiceBuilder.utils.showValidation(portInput, 'Port is already in use', 'error');
                }
            })
            .catch(error => {
                ServiceBuilder.utils.showValidation(portInput, 'Port check failed', 'error');
            });
        }
    },
    
    // Initialize all components
    init: function() {
        // Initialize form validation
        ServiceBuilder.forms.initValidation();
        
        // Initialize service type selection
        ServiceBuilder.serviceTypes.init();
        
        // Initialize path validation
        ServiceBuilder.pathValidation.init();
        
        // Initialize port validation
        ServiceBuilder.portValidation.init();
        
        // Initialize other components
        ServiceBuilder.initOtherComponents();
    },
    
    // Initialize other components
    initOtherComponents: function() {
        // Add any other component initialization here
        console.log('Service Builder initialized');
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    ServiceBuilder.init();
});

// Add notification styles
const notificationStyles = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--bg-primary);
        border: 1px solid var(--border-light);
        border-radius: var(--radius-md);
        box-shadow: 0 4px 12px var(--shadow-medium);
        padding: 16px 20px;
        z-index: 1060;
        transform: translateX(100%);
        transition: transform var(--transition-normal);
        max-width: 400px;
    }
    
    .notification.show {
        transform: translateX(0);
    }
    
    .notification-success {
        border-left: 4px solid var(--accent-green);
    }
    
    .notification-error {
        border-left: 4px solid var(--accent-red);
    }
    
    .notification-info {
        border-left: 4px solid var(--accent-blue);
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .notification-content i {
        font-size: 16px;
    }
    
    .notification-success .notification-content i {
        color: var(--accent-green);
    }
    
    .notification-error .notification-content i {
        color: var(--accent-red);
    }
    
    .notification-info .notification-content i {
        color: var(--accent-blue);
    }
`;

// Add styles to head
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);
