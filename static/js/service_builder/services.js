/*
Service Builder Services JavaScript
Services management functionality
*/

// Services namespace
window.Services = {
    // Initialize services functionality
    init: function() {
        this.loadServiceStatuses();
        this.bindEvents();
    },
    
    // Bind event listeners
    bindEvents: function() {
        // Auto-refresh service statuses every 30 seconds, but only when page is visible
        this.statusInterval = setInterval(() => {
            if (!document.hidden) {
                this.loadServiceStatuses();
            }
        }, 30000);
        
        // Also refresh when page becomes visible
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.loadServiceStatuses();
            }
        });
    },
    
    // Load service statuses
    loadServiceStatuses: function() {
        const statusElements = document.querySelectorAll('[id^="status-"]');
        
        statusElements.forEach(element => {
            const serviceName = element.id.replace('status-', '');
            // Only check if not already checking
            if (!element.classList.contains('checking')) {
                this.getServiceStatus(serviceName);
            }
        });
    },
    
    // Get service status
    getServiceStatus: function(serviceName) {
        const statusElement = document.getElementById(`status-${serviceName}`);
        if (!statusElement) return;
        
        // Mark as checking
        statusElement.classList.add('checking');
        statusElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';
        
        ServiceBuilder.utils.apiRequest(`service-status/${serviceName}/`)
            .then(response => {
                this.updateServiceStatus(serviceName, response);
            })
            .catch(error => {
                console.error('Error getting service status:', error);
                this.updateServiceStatus(serviceName, { status: 'error', message: 'Status check failed' });
            })
            .finally(() => {
                // Remove checking class
                if (statusElement) {
                    statusElement.classList.remove('checking');
                }
            });
    },
    
    // Update service status display
    updateServiceStatus: function(serviceName, statusData) {
        const statusElement = document.getElementById(`status-${serviceName}`);
        if (!statusElement) return;
        
        const status = statusData.status;
        const message = statusData.message;
        
        // Update status badge
        statusElement.className = `status-badge status-${status}`;
        
        // Update icon and text
        const icon = statusElement.querySelector('i');
        const text = statusElement.querySelector('span') || statusElement;
        
        if (icon) {
            icon.className = this.getStatusIcon(status);
        }
        
        if (text && text.textContent) {
            text.textContent = message;
        } else {
            statusElement.innerHTML = `<i class="${this.getStatusIcon(status)}"></i> ${message}`;
        }
    },
    
    // Get status icon class
    getStatusIcon: function(status) {
        const icons = {
            'running': 'fas fa-check-circle',
            'stopped': 'fas fa-times-circle',
            'error': 'fas fa-exclamation-triangle',
            'unknown': 'fas fa-question-circle'
        };
        return icons[status] || 'fas fa-question-circle';
    }
};

// Global service control function
window.controlService = function(serviceName, action) {
    ServiceBuilder.utils.showLoading(document.querySelector(`[onclick*="${serviceName}"]`));
    
    ServiceBuilder.utils.apiRequest(`service/${serviceName}/control/${action}/`, {
        method: 'POST'
    })
    .then(response => {
        ServiceBuilder.utils.showNotification(`Service ${action} successful`, 'success');
        // Refresh status after a short delay
        setTimeout(() => {
            Services.getServiceStatus(serviceName);
        }, 2000);
    })
    .catch(error => {
        ServiceBuilder.utils.showNotification(`Service ${action} failed: ${error.message}`, 'error');
    })
    .finally(() => {
        ServiceBuilder.utils.hideLoading(document.querySelector(`[onclick*="${serviceName}"]`));
    });
};

// Global service delete function
window.deleteService = function(serviceName) {
    console.log('deleteService called for:', serviceName);
    
    // Show confirmation dialog
    if (!confirm(`Are you sure you want to delete the service "${serviceName}"?\n\nThis action will:\n- Stop the service\n- Remove it from systemd\n- Delete the service configuration\n\nThis action cannot be undone.`)) {
        return;
    }
    
    console.log('User confirmed deletion');
    
    // Find the delete button for this service
    const deleteButton = document.querySelector(`button[onclick*="deleteService('${serviceName}')"]`);
    if (deleteButton) {
        ServiceBuilder.utils.showLoading(deleteButton);
    }
    
    ServiceBuilder.utils.apiRequest(`delete-service/${serviceName}/`, {
        method: 'DELETE'
    })
    .then(response => {
        console.log('Delete response:', response);
        ServiceBuilder.utils.showNotification(`Service "${serviceName}" deleted successfully`, 'success');
        
        // Find and remove the service row from the table
        const deleteButton = document.querySelector(`button[onclick*="deleteService('${serviceName}')"]`);
        const serviceRow = deleteButton ? deleteButton.closest('tr') : null;
        if (serviceRow) {
            console.log('Removing service row');
            serviceRow.remove();
        } else {
            console.log('Service row not found, reloading page');
            location.reload();
        }
        
        // Check if table is empty and show empty state
        const tbody = document.querySelector('.services-table tbody');
        if (tbody && tbody.children.length === 0) {
            console.log('Table is empty, reloading page');
            location.reload(); // Reload to show empty state
        }
    })
    .catch(error => {
        console.error('Delete service error:', error);
        ServiceBuilder.utils.showNotification(`Failed to delete service: ${error.message}`, 'error');
    })
    .finally(() => {
        if (deleteButton) {
            ServiceBuilder.utils.hideLoading(deleteButton);
        }
    });
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    Services.init();
});

// Clean up intervals when page is unloaded
window.addEventListener('beforeunload', function() {
    if (Services.statusInterval) {
        clearInterval(Services.statusInterval);
    }
});