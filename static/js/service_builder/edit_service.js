/*
Service Builder Edit Service JavaScript
Edit service page functionality
*/

// Edit Service namespace
window.EditService = {
    serviceName: null,
    
    // Initialize edit service functionality
    init: function() {
        this.serviceName = this.getServiceNameFromUrl();
        this.bindEvents();
        this.loadServiceData();
    },
    
    // Get service name from URL
    getServiceNameFromUrl: function() {
        const path = window.location.pathname;
        const matches = path.match(/\/service\/([^\/]+)\/edit\//);
        return matches ? matches[1] : null;
    },
    
    // Bind event listeners
    bindEvents: function() {
        const form = document.getElementById('editServiceForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveServiceChanges();
            });
        }
    },
    
    // Load service data
    loadServiceData: function() {
        if (!this.serviceName) return;
        
        // The form is already populated by Django template
        // We just need to set up any additional functionality
        this.setupFormValidation();
    },
    
    // Setup form validation
    setupFormValidation: function() {
        const form = document.getElementById('editServiceForm');
        const requiredFields = ['applicationPath', 'user'];
        
        requiredFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.addEventListener('blur', () => {
                    this.validateField(field);
                });
            }
        });
    },
    
    // Validate individual field
    validateField: function(field) {
        const value = field.value.trim();
        const isValid = value.length > 0;
        
        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
        }
        
        return isValid;
    },
    
    // Validate entire form
    validateForm: function() {
        const requiredFields = [
            { id: 'applicationPath', name: 'Application Path' },
            { id: 'user', name: 'User' }
        ];
        
        let isValid = true;
        const errors = [];
        
        requiredFields.forEach(field => {
            const element = document.getElementById(field.id);
            if (!element || !element.value.trim()) {
                isValid = false;
                errors.push(`${field.name} is required`);
                if (element) {
                    element.classList.add('is-invalid');
                }
            } else {
                if (element) {
                    element.classList.remove('is-invalid');
                    element.classList.add('is-valid');
                }
            }
        });
        
        if (!isValid) {
            ServiceBuilder.utils.showNotification(`Please fix the following errors:\n${errors.join('\n')}`, 'error');
        }
        
        return isValid;
    },
    
    // Save service changes
    saveServiceChanges: function() {
        if (!this.validateForm()) {
            return;
        }
        
        const serviceData = {
            description: document.getElementById('description').value,
            service_type: document.getElementById('serviceType').value,
            application_path: document.getElementById('applicationPath').value,
            interpreter: document.getElementById('interpreter').value,
            user: document.getElementById('user').value,
            working_directory: document.getElementById('workingDirectory').value,
            port: document.getElementById('port').value ? parseInt(document.getElementById('port').value) : null,
            host: document.getElementById('host').value,
            restart_policy: document.getElementById('restartPolicy').value,
            environment_vars: document.getElementById('environmentVars').value
        };
        
        ServiceBuilder.utils.showLoading(document.querySelector('#editServiceForm button[type="submit"]'));
        
        ServiceBuilder.utils.apiRequest(`update-service/${this.serviceName}/`, {
            method: 'PUT',
            body: JSON.stringify(serviceData)
        })
        .then(response => {
            ServiceBuilder.utils.showNotification(`Service "${this.serviceName}" updated successfully`, 'success');
            // Redirect to service detail page after successful update
            setTimeout(() => {
                window.location.href = `/service-builder/service/${this.serviceName}/`;
            }, 1500);
        })
        .catch(error => {
            ServiceBuilder.utils.showNotification(`Failed to update service: ${error.message}`, 'error');
        })
        .finally(() => {
            ServiceBuilder.utils.hideLoading(document.querySelector('#editServiceForm button[type="submit"]'));
        });
    }
};

// Global cancel edit function
window.cancelEdit = function() {
    if (confirm('Are you sure you want to cancel? Any unsaved changes will be lost.')) {
        const serviceName = EditService.serviceName;
        if (serviceName) {
            window.location.href = `/service-builder/service/${serviceName}/`;
        } else {
            window.location.href = '/service-builder/services/';
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    EditService.init();
});
