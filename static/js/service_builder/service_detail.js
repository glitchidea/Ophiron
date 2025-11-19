/*
Service Builder Service Detail JavaScript
Service detail page functionality
*/

// Service Detail namespace
window.ServiceDetail = {
    serviceName: null,
    
    // Initialize service detail functionality
    init: function() {
        this.serviceName = this.getServiceNameFromUrl();
        this.loadServiceStatus();
        this.loadServiceLogs();
        this.bindEvents();
        this.initTabs();
    },
    
    // Get service name from URL
    getServiceNameFromUrl: function() {
        const path = window.location.pathname;
        const matches = path.match(/\/service\/([^\/]+)\//);
        return matches ? matches[1] : null;
    },
    
    // Bind event listeners
    bindEvents: function() {
        // Auto-refresh status every 30 seconds, but only when page is visible
        this.statusInterval = setInterval(() => {
            if (!document.hidden) {
                this.loadServiceStatus();
            }
        }, 30000);
        
        // Also refresh when page becomes visible
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.loadServiceStatus();
            }
        });
    },
    
    // Initialize tabs
    initTabs: function() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabPanes = document.querySelectorAll('.tab-pane');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.dataset.tab;
                
                // Remove active class from all buttons and panes
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabPanes.forEach(pane => pane.classList.remove('active'));
                
                // Add active class to clicked button and corresponding pane
                button.classList.add('active');
                document.getElementById(tabName).classList.add('active');
                
                // Load content for specific tabs
                if (tabName === 'logs') {
                    this.loadServiceLogs();
                }
            });
        });
    },
    
    // Load service status
    loadServiceStatus: function() {
        if (!this.serviceName) return;
        
        const statusElement = document.getElementById('serviceStatus');
        const messageElement = document.getElementById('serviceStatusMessage');
        
        // Show loading state
        if (statusElement) {
            statusElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';
        }
        if (messageElement) {
            messageElement.textContent = 'Checking service status...';
        }
        
        ServiceBuilder.utils.apiRequest(`service-status/${this.serviceName}/`)
            .then(response => {
                this.updateServiceStatus(response);
            })
            .catch(error => {
                console.error('Error loading service status:', error);
                this.updateServiceStatus({ status: 'error', message: 'Status check failed' });
            });
    },
    
    // Update service status display
    updateServiceStatus: function(statusData) {
        const statusElement = document.getElementById('serviceStatus');
        const messageElement = document.getElementById('serviceStatusMessage');
        
        if (statusElement) {
            statusElement.textContent = statusData.status || 'Unknown';
        }
        
        if (messageElement) {
            messageElement.textContent = statusData.message || 'Status unknown';
        }
    },
    
    // Load service logs
    loadServiceLogs: function() {
        if (!this.serviceName) return;
        
        const logsContainer = document.getElementById('logsContainer');
        if (!logsContainer) return;
        
        // Show loading state
        logsContainer.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-border text-primary"></div>
                <p>Loading logs...</p>
            </div>
        `;
        
        ServiceBuilder.utils.apiRequest(`service-logs/${this.serviceName}/`)
            .then(response => {
                this.displayServiceLogs(response.logs);
            })
            .catch(error => {
                console.error('Error loading service logs:', error);
                logsContainer.innerHTML = `
                    <div class="error-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Failed to load logs: ${error.message}</p>
                    </div>
                `;
            });
    },
    
    // Display service logs
    displayServiceLogs: function(logs) {
        const logsContainer = document.getElementById('logsContainer');
        if (!logsContainer) return;
        
        if (logs.length === 0) {
            logsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-alt"></i>
                    <p>No logs available for this service</p>
                </div>
            `;
            return;
        }
        
        const logsHtml = logs.map(log => `
            <div class="log-entry log-${log.status}">
                <div class="log-header">
                    <span class="log-action">${log.action}</span>
                    <span class="log-status status-${log.status}">
                        <i class="fas fa-${log.status === 'success' ? 'check-circle' : log.status === 'error' ? 'times-circle' : 'info-circle'}"></i>
                        ${log.status}
                    </span>
                    <span class="log-time">${new Date(log.created_at).toLocaleString()}</span>
                </div>
                <div class="log-message">${log.message}</div>
                <div class="log-meta">
                    <span class="log-user">User: ${log.user}</span>
                </div>
            </div>
        `).join('');
        
        logsContainer.innerHTML = `
            <div class="logs-list">
                ${logsHtml}
            </div>
        `;
    }
};

// Global service control function
window.controlService = function(serviceName, action) {
    ServiceBuilder.utils.showNotification(`Performing ${action} on service...`, 'info');
    
    ServiceBuilder.utils.apiRequest(`service/${serviceName}/control/${action}/`, {
        method: 'POST'
    })
    .then(response => {
        ServiceBuilder.utils.showNotification(`Service ${action} successful`, 'success');
        // Refresh status and logs
        setTimeout(() => {
            ServiceDetail.loadServiceStatus();
            ServiceDetail.loadServiceLogs();
        }, 2000);
    })
    .catch(error => {
        ServiceBuilder.utils.showNotification(`Service ${action} failed: ${error.message}`, 'error');
    });
};

// Global refresh logs function
window.refreshLogs = function() {
    ServiceDetail.loadServiceLogs();
};


// Global service delete function
window.deleteService = function(serviceName) {
    // Show confirmation dialog
    if (!confirm(`Are you sure you want to delete the service "${serviceName}"?\n\nThis action will:\n- Stop the service\n- Remove it from systemd\n- Delete the service configuration\n\nThis action cannot be undone.`)) {
        return;
    }
    
    ServiceBuilder.utils.showNotification(`Deleting service "${serviceName}"...`, 'info');
    
    ServiceBuilder.utils.apiRequest(`delete-service/${serviceName}/`, {
        method: 'DELETE'
    })
    .then(response => {
        ServiceBuilder.utils.showNotification(`Service "${serviceName}" deleted successfully`, 'success');
        // Redirect to services list after successful deletion
        setTimeout(() => {
            window.location.href = '/service-builder/services/';
        }, 2000);
    })
    .catch(error => {
        ServiceBuilder.utils.showNotification(`Failed to delete service: ${error.message}`, 'error');
    });
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    ServiceDetail.init();
});

// Clean up intervals when page is unloaded
window.addEventListener('beforeunload', function() {
    if (ServiceDetail.statusInterval) {
        clearInterval(ServiceDetail.statusInterval);
    }
});
