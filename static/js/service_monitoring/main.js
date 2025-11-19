// Service Monitoring Main JavaScript

class ServiceMonitoring {
    constructor() {
        this.services = [];
        this.categories = [];
        this.currentFilters = {
            category: '',
            status: '',
            search: ''
        };
        
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadServices();
        this.setupAutoRefresh();
        this.checkLiveModeStatus();
    }

    bindEvents() {
        // Refresh button
        document.getElementById('refreshServicesBtn').addEventListener('click', () => {
            this.loadServices();
        });


        // Filters
        document.getElementById('categoryFilter').addEventListener('change', (e) => {
            this.currentFilters.category = e.target.value;
            this.filterServices();
        });

        document.getElementById('statusFilter').addEventListener('change', (e) => {
            this.currentFilters.status = e.target.value;
            this.filterServices();
        });

        document.getElementById('searchInput').addEventListener('input', (e) => {
            this.currentFilters.search = e.target.value.toLowerCase();
            this.filterServices();
        });

    }

    async loadServices() {
        try {
            this.showLoading();
            
            const response = await fetch('/service-monitoring/api/services/');
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.services = data.services;
            this.categories = data.categories;
            
            this.updateStats(data);
            this.populateCategoryFilter();
            this.renderServices();
            
        } catch (error) {
            console.error('Error loading services:', error);
            this.showError((window.jsTranslations?.error_loading_services || 'Error loading services') + ': ' + error.message);
        }
    }

    updateStats(data) {
        const totalServices = data.total_services;
        const activeServices = this.services.filter(s => s.status === 'active').length;
        const inactiveServices = totalServices - activeServices;

        document.getElementById('totalServices').textContent = totalServices;
        document.getElementById('activeServices').textContent = activeServices;
        document.getElementById('inactiveServices').textContent = inactiveServices;
    }

    populateCategoryFilter() {
        const categoryFilter = document.getElementById('categoryFilter');
        categoryFilter.innerHTML = `<option value="">${window.jsTranslations?.all_categories || 'All Categories'}</option>`;
        
        this.categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categoryFilter.appendChild(option);
        });
    }

    filterServices() {
        const filteredServices = this.services.filter(service => {
            const matchesCategory = !this.currentFilters.category || 
                service.category === this.currentFilters.category;
            
            const matchesStatus = !this.currentFilters.status || 
                service.status === this.currentFilters.status;
            
            const matchesSearch = !this.currentFilters.search || 
                service.name.toLowerCase().includes(this.currentFilters.search) ||
                (service.description && service.description.toLowerCase().includes(this.currentFilters.search));
            
            return matchesCategory && matchesStatus && matchesSearch;
        });
        
        this.renderServices(filteredServices);
    }

    renderServices(services = this.services) {
        const tbody = document.getElementById('servicesTableBody');
        
        if (services.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="empty-state">
                        <i class="fas fa-search"></i>
                        <h3>${window.jsTranslations?.no_services_found || 'No services found'}</h3>
                        <p>${window.jsTranslations?.try_adjusting_filters || 'Try adjusting your filters or search terms'}</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = services.map(service => `
            <tr>
                <td>
                    <div class="service-name">
                        <strong>${service.name}</strong>
                        ${service.type ? `<span class="service-type">${service.type}</span>` : ''}
                    </div>
                </td>
                <td>
                    <span class="service-status ${service.status}">
                        <i class="fas fa-${service.status === 'active' ? 'play' : 'pause'}"></i>
                        ${service.status}
                    </span>
                </td>
                <td>
                    <span class="service-category">${service.category || (window.jsTranslations?.other || 'Other')}</span>
                </td>
                <td>
                    <div class="service-description">
                        ${service.description || (window.jsTranslations?.no_description_available || 'No description available')}
                    </div>
                </td>
                <td>
                    <div class="service-actions">
                        ${this.getActionButtons(service)}
                    </div>
                </td>
            </tr>
        `).join('');
        
        this.bindServiceActions();
    }

    getActionButtons(service) {
        const buttons = [];
        
        if (service.status === 'active') {
            buttons.push(`<button class="action-btn stop" data-service="${service.name}" data-action="stop">
                <i class="fas fa-stop"></i> ${window.jsTranslations?.stop || 'Stop'}
            </button>`);
            buttons.push(`<button class="action-btn restart" data-service="${service.name}" data-action="restart">
                <i class="fas fa-redo"></i> ${window.jsTranslations?.restart || 'Restart'}
            </button>`);
        } else {
            buttons.push(`<button class="action-btn start" data-service="${service.name}" data-action="start">
                <i class="fas fa-play"></i> ${window.jsTranslations?.start || 'Start'}
            </button>`);
        }
        
        buttons.push(`<button class="action-btn details" data-service="${service.name}">
            <i class="fas fa-info"></i> ${window.jsTranslations?.view_details || 'Details'}
        </button>`);
        
        buttons.push(`<button class="action-btn logs" data-service="${service.name}">
            <i class="fas fa-file-alt"></i> ${window.jsTranslations?.view_logs || 'Logs'}
        </button>`);
        
        return buttons.join('');
    }

    bindServiceActions() {
        document.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const serviceName = e.target.closest('button').dataset.service;
                const action = e.target.closest('button').dataset.action;
                
                if (action) {
                    this.controlService(serviceName, action);
                } else if (e.target.closest('button').classList.contains('details')) {
                    this.showServiceDetails(serviceName);
                } else if (e.target.closest('button').classList.contains('logs')) {
                    this.showServiceLogs(serviceName);
                }
            });
        });
    }

    async controlService(serviceName, action) {
        try {
            const response = await fetch(`/service-monitoring/api/control/${action}/${serviceName}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(data.message);
                this.loadServices(); // Refresh the list
            } else {
                this.showError(data.message);
            }
            
        } catch (error) {
            console.error('Error controlling service:', error);
            this.showError((window.jsTranslations?.operation_failed || 'Operation failed') + ': ' + error.message);
        }
    }

    async showServiceDetails(serviceName) {
        try {
            const response = await fetch(`/service-monitoring/api/details/${serviceName}/`);
            const data = await response.json();
            
            if (data.success) {
                this.displayServiceDetails(data.details);
            } else {
                this.showError(data.message);
            }
            
        } catch (error) {
            console.error('Error loading service details:', error);
            this.showError((window.jsTranslations?.error_loading_services || 'Error loading services') + ': ' + error.message);
        }
    }

    displayServiceDetails(details) {
        const modal = document.getElementById('serviceDetailsModal');
        const content = document.getElementById('serviceDetailsContent');
        
        document.getElementById('modalServiceName').textContent = `${details.name} - ${window.jsTranslations?.details || 'Details'}`;
        
        content.innerHTML = `
            <div class="service-details">
                <div class="detail-group">
                    <div class="detail-label">${window.jsTranslations?.status || 'Status'}</div>
                    <div class="detail-value">
                        <span class="service-status ${details.status}">
                            <i class="fas fa-${details.status === 'active' ? 'play' : 'pause'}"></i>
                            ${details.status}
                        </span>
                    </div>
                </div>
                
                <div class="detail-group">
                    <div class="detail-label">${window.jsTranslations?.description || 'Description'}</div>
                    <div class="detail-value">${details.description || (window.jsTranslations?.no_description_available || 'No description available')}</div>
                </div>
                
                <div class="detail-group">
                    <div class="detail-label">${window.jsTranslations?.enabled || 'Enabled'}</div>
                    <div class="detail-value">${details.enabled ? (window.jsTranslations?.yes || 'Yes') : (window.jsTranslations?.no || 'No')}</div>
                </div>
                
                <div class="detail-group">
                    <div class="detail-label">${window.jsTranslations?.active || 'Active'}</div>
                    <div class="detail-value">${details.active ? (window.jsTranslations?.yes || 'Yes') : (window.jsTranslations?.no || 'No')}</div>
                </div>
                
                ${details.pid ? `
                <div class="detail-group">
                    <div class="detail-label">${window.jsTranslations?.pid || 'PID'}</div>
                    <div class="detail-value">${details.pid}</div>
                </div>
                ` : ''}
                
                ${details.uptime ? `
                <div class="detail-group">
                    <div class="detail-label">${window.jsTranslations?.uptime || 'Uptime'}</div>
                    <div class="detail-value">${details.uptime}</div>
                </div>
                ` : ''}
                
                ${details.memory_usage ? `
                <div class="detail-group">
                    <div class="detail-label">${window.jsTranslations?.memory_usage || 'Memory Usage'}</div>
                    <div class="detail-value">${details.memory_usage}%</div>
                </div>
                ` : ''}
                
                ${details.cpu_usage ? `
                <div class="detail-group">
                    <div class="detail-label">${window.jsTranslations?.cpu_usage || 'CPU Usage'}</div>
                    <div class="detail-value">${details.cpu_usage}%</div>
                </div>
                ` : ''}
            </div>
        `;
        
        modal.style.display = 'flex';
    }

    async showServiceLogs(serviceName) {
        try {
            const response = await fetch(`/service-monitoring/api/logs/${serviceName}/?lines=50`);
            const data = await response.json();
            
            if (data.success) {
                this.displayServiceLogs(serviceName, data.logs);
            } else {
                this.showError(data.message);
            }
            
        } catch (error) {
            console.error('Error loading service logs:', error);
            this.showError((window.jsTranslations?.error_loading_services || 'Error loading services') + ': ' + error.message);
        }
    }

    displayServiceLogs(serviceName, logs) {
        const modal = document.getElementById('serviceLogsModal');
        const content = document.getElementById('serviceLogsContent');
        
        document.getElementById('modalLogsServiceName').textContent = `${serviceName} - ${window.jsTranslations?.logs || 'Logs'}`;
        
        content.innerHTML = `
            <div class="logs-container">
                ${logs.length > 0 ? logs.map(log => `
                    <div class="log-entry ${this.getLogLevel(log)}">${this.escapeHtml(log)}</div>
                `).join('') : `<div class="log-entry">${window.jsTranslations?.no_logs_available || 'No logs available'}</div>`}
            </div>
        `;
        
        modal.style.display = 'flex';
    }

    getLogLevel(log) {
        const logLower = log.toLowerCase();
        if (logLower.includes('error') || logLower.includes('failed')) return 'error';
        if (logLower.includes('warning') || logLower.includes('warn')) return 'warning';
        if (logLower.includes('info')) return 'info';
        return '';
    }


    showLoading() {
        const tbody = document.getElementById('servicesTableBody');
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="loading-cell">
                    <i class="fas fa-spinner fa-spin"></i>
                    ${window.jsTranslations?.loading_services || 'Loading services...'}
                </td>
            </tr>
        `;
    }

    showError(message) {
        // Create a better notification system
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        // Create a better notification system
        this.showNotification(message, 'success');
    }

    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
                <span>${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    closeModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || '';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    setupAutoRefresh() {
        // Auto-refresh every 30 seconds
        setInterval(() => {
            this.loadServices();
        }, 30000);
        
        // Check live mode status every 5 seconds
        setInterval(() => {
            this.checkLiveModeStatus();
        }, 5000);
    }
    
    checkLiveModeStatus() {
        // Check live mode status and update indicator
        fetch('/service-monitoring/api/live-mode/status/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.updateLiveIndicator(data.live_mode_enabled);
                } else {
                    this.updateLiveIndicator(false);
                }
            })
            .catch(error => {
                console.error('Error checking live mode status:', error);
                this.updateLiveIndicator(false);
            });
    }
    
    updateLiveIndicator(isLive) {
        const indicator = document.getElementById('liveIndicator');
        if (indicator) {
            indicator.classList.remove('connected', 'disconnected', 'error');
            if (isLive) {
                indicator.classList.add('connected');
                indicator.title = window.jsTranslations?.live_mode_active || 'Live Mode: Active';
            } else {
                indicator.classList.add('disconnected');
                indicator.title = window.jsTranslations?.live_mode_inactive || 'Live Mode: Inactive';
            }
        }
    }
    
}

// Global functions for modal handling
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ServiceMonitoring();
});

// Close modals when clicking outside
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.style.display = 'none';
    }
});
