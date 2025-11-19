/**
 * Service Manager - JavaScript Module
 * Handles service management utilities and helpers
 */

(function() {
    'use strict';
    
    // Service categories with colors and icons
    const serviceCategories = {
        'Web Sunucu': { color: '#dc3545', icon: 'fas fa-globe' },
        'Python Uygulama': { color: '#28a745', icon: 'fab fa-python' },
        'Veritabanı': { color: '#007bff', icon: 'fas fa-database' },
        'Sistem Servisi': { color: '#6c757d', icon: 'fas fa-cog' },
        'Ağ Servisi': { color: '#17a2b8', icon: 'fas fa-network-wired' },
        'Güvenlik': { color: '#fd7e14', icon: 'fas fa-shield-alt' },
        'Docker': { color: '#20c997', icon: 'fab fa-docker' },
        'Monitoring': { color: '#e83e8c', icon: 'fas fa-chart-line' },
        'Diğer': { color: '#6f42c1', icon: 'fas fa-ellipsis-h' }
    };
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
    function initialize() {
        console.log('Service Manager module initialized successfully');
    }
    
    /**
     * Get service category information
     */
    function getServiceCategory(categoryName) {
        return serviceCategories[categoryName] || serviceCategories['Diğer'];
    }
    
    /**
     * Format service status for display
     */
    function formatServiceStatus(status) {
        const statusMap = {
            'active': { text: 'Active', class: 'active', icon: 'fas fa-play-circle' },
            'inactive': { text: 'Inactive', class: 'inactive', icon: 'fas fa-stop-circle' },
            'failed': { text: 'Failed', class: 'failed', icon: 'fas fa-exclamation-circle' },
            'activating': { text: 'Activating', class: 'activating', icon: 'fas fa-spinner fa-spin' },
            'deactivating': { text: 'Deactivating', class: 'deactivating', icon: 'fas fa-spinner fa-spin' }
        };
        
        return statusMap[status] || { text: 'Unknown', class: 'unknown', icon: 'fas fa-question-circle' };
    }
    
    /**
     * Format memory usage for display
     */
    function formatMemoryUsage(memory) {
        if (!memory || memory === '0') return '0%';
        return `${memory}%`;
    }
    
    /**
     * Format CPU usage for display
     */
    function formatCPUUsage(cpu) {
        if (!cpu || cpu === '0') return '0%';
        return `${cpu}%`;
    }
    
    /**
     * Format uptime for display
     */
    function formatUptime(uptime) {
        if (!uptime) return 'N/A';
        
        // Parse systemd uptime format
        if (uptime.includes('ago')) {
            return uptime;
        }
        
        // Parse duration format (e.g., "2h 30m 15s")
        const durationMatch = uptime.match(/(\d+h)?\s*(\d+m)?\s*(\d+s)?/);
        if (durationMatch) {
            return uptime;
        }
        
        return uptime;
    }
    
    /**
     * Get service priority based on category and status
     */
    function getServicePriority(service) {
        const category = service.category || 'Diğer';
        const status = service.status || 'inactive';
        
        // High priority services
        const highPriorityCategories = ['Sistem Servisi', 'Ağ Servisi', 'Güvenlik'];
        const highPriorityServices = ['systemd', 'network', 'ssh', 'firewall'];
        
        if (highPriorityCategories.includes(category) || 
            highPriorityServices.some(name => service.name.includes(name))) {
            return 'high';
        }
        
        // Medium priority services
        const mediumPriorityCategories = ['Web Sunucu', 'Veritabanı', 'Docker'];
        
        if (mediumPriorityCategories.includes(category)) {
            return 'medium';
        }
        
        return 'low';
    }
    
    /**
     * Check if service is critical
     */
    function isCriticalService(service) {
        const criticalServices = [
            'systemd', 'network', 'ssh', 'firewall', 'systemd-logind',
            'dbus', 'systemd-resolved', 'systemd-networkd'
        ];
        
        return criticalServices.some(name => service.name.includes(name));
    }
    
    /**
     * Get service health status
     */
    function getServiceHealth(service) {
        const status = service.status || 'inactive';
        const memory = parseFloat(service.memory_usage || '0');
        const cpu = parseFloat(service.cpu_usage || '0');
        
        // Check for high resource usage
        if (memory > 80 || cpu > 80) {
            return 'warning';
        }
        
        // Check for failed services
        if (status === 'failed' || status === 'inactive') {
            return 'error';
        }
        
        // Check for active services
        if (status === 'active') {
            return 'healthy';
        }
        
        return 'unknown';
    }
    
    /**
     * Sort services by priority and status
     */
    function sortServices(services) {
        return services.sort((a, b) => {
            // First by priority
            const priorityA = getServicePriority(a);
            const priorityB = getServicePriority(b);
            
            if (priorityA !== priorityB) {
                const priorityOrder = { 'high': 0, 'medium': 1, 'low': 2 };
                return priorityOrder[priorityA] - priorityOrder[priorityB];
            }
            
            // Then by status (active first)
            const statusA = a.status || 'inactive';
            const statusB = b.status || 'inactive';
            
            if (statusA !== statusB) {
                if (statusA === 'active') return -1;
                if (statusB === 'active') return 1;
            }
            
            // Finally by name
            return a.name.localeCompare(b.name);
        });
    }
    
    /**
     * Filter services by search term
     */
    function filterServices(services, searchTerm) {
        if (!searchTerm) return services;
        
        const term = searchTerm.toLowerCase();
        return services.filter(service => {
            return service.name.toLowerCase().includes(term) ||
                   (service.description && service.description.toLowerCase().includes(term)) ||
                   (service.category && service.category.toLowerCase().includes(term));
        });
    }
    
    /**
     * Group services by category
     */
    function groupServicesByCategory(services) {
        const groups = {};
        
        services.forEach(service => {
            const category = service.category || 'Diğer';
            if (!groups[category]) {
                groups[category] = [];
            }
            groups[category].push(service);
        });
        
        return groups;
    }
    
    /**
     * Get service statistics
     */
    function getServiceStatistics(services) {
        const stats = {
            total: services.length,
            active: 0,
            inactive: 0,
            failed: 0,
            categories: {},
            critical: 0,
            healthy: 0,
            warning: 0,
            error: 0
        };
        
        services.forEach(service => {
            // Count by status
            const status = service.status || 'inactive';
            if (status === 'active') stats.active++;
            else if (status === 'failed') stats.failed++;
            else stats.inactive++;
            
            // Count by category
            const category = service.category || 'Diğer';
            stats.categories[category] = (stats.categories[category] || 0) + 1;
            
            // Count critical services
            if (isCriticalService(service)) {
                stats.critical++;
            }
            
            // Count by health
            const health = getServiceHealth(service);
            if (health === 'healthy') stats.healthy++;
            else if (health === 'warning') stats.warning++;
            else if (health === 'error') stats.error++;
        });
        
        return stats;
    }
    
    /**
     * Validate service name
     */
    function validateServiceName(name) {
        if (!name || name.trim().length === 0) {
            return { valid: false, message: 'Service name is required' };
        }
        
        if (name.length > 100) {
            return { valid: false, message: 'Service name is too long (max 100 characters)' };
        }
        
        // Check for valid characters (alphanumeric, hyphens, underscores)
        if (!/^[a-zA-Z0-9\-_]+$/.test(name)) {
            return { valid: false, message: 'Service name contains invalid characters' };
        }
        
        return { valid: true };
    }
    
    /**
     * Validate service path
     */
    function validateServicePath(path) {
        if (!path || path.trim().length === 0) {
            return { valid: false, message: 'Service path is required' };
        }
        
        if (!path.startsWith('/')) {
            return { valid: false, message: 'Service path must be absolute' };
        }
        
        return { valid: true };
    }
    
    /**
     * Get service action availability
     */
    function getAvailableActions(service) {
        const status = service.status || 'inactive';
        const actions = [];
        
        if (status === 'active') {
            actions.push('stop', 'restart', 'reload');
        } else {
            actions.push('start');
        }
        
        if (service.enabled) {
            actions.push('disable');
        } else {
            actions.push('enable');
        }
        
        // Always allow delete for non-critical services
        if (!isCriticalService(service)) {
            actions.push('delete');
        }
        
        return actions;
    }
    
    /**
     * Format service action for display
     */
    function formatAction(action) {
        const actionMap = {
            'start': { text: 'Start', icon: 'fas fa-play', class: 'primary' },
            'stop': { text: 'Stop', icon: 'fas fa-stop', class: 'danger' },
            'restart': { text: 'Restart', icon: 'fas fa-redo', class: 'warning' },
            'reload': { text: 'Reload', icon: 'fas fa-sync', class: 'info' },
            'enable': { text: 'Enable', icon: 'fas fa-check', class: 'success' },
            'disable': { text: 'Disable', icon: 'fas fa-times', class: 'secondary' },
            'delete': { text: 'Delete', icon: 'fas fa-trash', class: 'danger' }
        };
        
        return actionMap[action] || { text: action, icon: 'fas fa-cog', class: 'secondary' };
    }
    
    // Public API
    window.ServiceManager = {
        getServiceCategory: getServiceCategory,
        formatServiceStatus: formatServiceStatus,
        formatMemoryUsage: formatMemoryUsage,
        formatCPUUsage: formatCPUUsage,
        formatUptime: formatUptime,
        getServicePriority: getServicePriority,
        isCriticalService: isCriticalService,
        getServiceHealth: getServiceHealth,
        sortServices: sortServices,
        filterServices: filterServices,
        groupServicesByCategory: groupServicesByCategory,
        getServiceStatistics: getServiceStatistics,
        validateServiceName: validateServiceName,
        validateServicePath: validateServicePath,
        getAvailableActions: getAvailableActions,
        formatAction: formatAction
    };
    
})();
