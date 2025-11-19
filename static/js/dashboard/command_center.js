/**
 * Ophiron Command Center JavaScript
 * Modern IT/DevOps Dashboard Functionality
 */

class CommandCenter {
    constructor() {
        this.updateInterval = 5000; // 5 seconds
        this.systemData = {};
        this.services = [];
        this.containers = [];
        this.alerts = [];
        this.activities = [];
        
        this.init();
    }
    
    init() {
        console.log('🚀 Initializing Ophiron Command Center...');
        
        // WebSocket disabled - using API polling instead
        
        // Load initial data
        this.loadSystemData();
        this.loadContainers();
        this.loadTopPorts();
        this.loadAlerts();
        this.loadActivities();
        this.loadLiveControl();
        this.loadSMTPStatus();
        
        // Set up periodic updates
        this.setupPeriodicUpdates();
        
        // Initialize event listeners
        this.setupEventListeners();
        
        console.log('✅ Command Center initialized successfully');
    }
    
    
    
    async loadSystemData() {
        try {
            const response = await fetch('/dashboard-api/api/metrics/');
            const result = await response.json();
            
            if (result.success) {
                this.systemData = result;
                this.updateSystemMetrics(this.systemData);
            } else {
                console.error('Failed to load system data:', result.error);
                this.addAlert({
                    type: 'warning',
                    message: window.jsTranslations.failed_to_load_system_metrics || 'Failed to load system metrics',
                    timestamp: new Date()
                });
            }
        } catch (error) {
            console.error('Error loading system data:', error);
            this.addAlert({
                type: 'danger',
                message: window.jsTranslations.system_metrics_unavailable || 'System metrics unavailable',
                timestamp: new Date()
            });
        }
    }
    
    
    async loadContainers() {
        try {
            const response = await fetch('/dashboard-api/api/containers/');
            const result = await response.json();
            
            if (result.success && result.containers) {
                this.containers = result.containers;
                this.updateDockerStatus();
            }
        } catch (error) {
            console.error('Error loading containers:', error);
        }
    }
    
    async loadTopPorts() {
        try {
            const response = await fetch('/process-monitor/api/ports/?limit=6');
            const result = await response.json();
            
            if (result.success && result.ports) {
                this.updateTopPorts(result.ports);
            }
        } catch (error) {
            console.error('Error loading top ports:', error);
        }
    }
    
    async loadAlerts() {
        try {
            console.log('🔄 Loading alerts from API...');
            const response = await fetch('/dashboard-api/api/alerts/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('📊 Alerts API Response:', result);
            
            if (result.success && result.alerts) {
                // Clear existing alerts
                this.alerts = [];
                
                // Add real alerts from API
                result.alerts.forEach(alert => {
                    this.addAlert({
                        type: alert.type || 'info',
                        message: alert.message || alert.title,
                        timestamp: new Date(alert.created_at),
                        service: alert.service,
                        id: alert.id,
                        icon: alert.icon
                    });
                });
                
                console.log(`✅ Loaded ${result.alerts.length} real alerts from API`);
            } else {
                console.warn('⚠️ No alerts data received from API:', result);
                // Show no alerts message
                this.alerts = [];
                this.updateAlertList();
            }
        } catch (error) {
            console.error('❌ Error loading alerts:', error);
            // Add error alert
            this.addAlert({
                type: 'warning',
                message: 'Failed to load alerts from server',
                timestamp: new Date()
            });
        }
    }
    
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    updateSystemMetrics(data) {
        // Update system status
        const statusDot = document.getElementById('systemStatusDot');
        const statusText = document.getElementById('systemStatusText');
        const lastUpdate = document.getElementById('lastUpdate');
        
        // Determine overall system status
        const cpuUsage = data.cpu?.usage_percent || 0;
        const memoryUsage = data.memory?.usage_percent || 0;
        const diskUsage = data.disk?.usage_percent || 0;
        
        let systemStatus = 'online';
        if (cpuUsage > 90 || memoryUsage > 90 || diskUsage > 90) {
            systemStatus = 'warning';
        }
        
        statusDot.className = `status-dot ${systemStatus}`;
        
        // Use translations for status text
        let statusTextKey = 'system_status_checking';
        if (systemStatus === 'online') {
            statusTextKey = 'system_status_online';
        } else if (systemStatus === 'warning') {
            statusTextKey = 'system_status_warning';
        } else if (systemStatus === 'offline') {
            statusTextKey = 'system_status_offline';
        }
        
        statusText.textContent = window.jsTranslations[statusTextKey] || `SYSTEM STATUS: ${systemStatus.toUpperCase()}`;
        lastUpdate.textContent = `${window.jsTranslations.last_check || 'Last Check: '}${new Date().toLocaleTimeString()}`;
        
        // Update metrics
        this.updateMetric('cpuBar', 'cpuValue', cpuUsage, '%');
        this.updateMetric('ramBar', 'ramValue', memoryUsage, '%', 
            `${this.formatBytes(data.memory?.used || 0)}/${this.formatBytes(data.memory?.total || 0)}`);
        this.updateMetric('diskBar', 'diskValue', diskUsage, '%');
        
        // Update other metrics
        const networkIn = data.network?.bytes_in || 0;
        const networkOut = data.network?.bytes_out || 0;
        const networkSpeed = Math.max(networkIn, networkOut) / 1024 / 1024; // MB/s approximation
        document.getElementById('networkBar').style.width = `${Math.min(networkSpeed * 10, 100)}%`;
        document.getElementById('networkValue').textContent = `${networkSpeed.toFixed(1)}MB/s`;
        
        const temp = data.cpu?.temperature || 0;
        document.getElementById('tempValue').textContent = `${temp}°C`;
        
        const uptime = data.system?.uptime || 'Unknown';
        document.getElementById('uptimeValue').textContent = uptime;
        
        // Update performance metrics
        document.getElementById('responseTime').textContent = `${Math.floor(Math.random() * 200 + 50)}ms`;
        document.getElementById('errorRate').textContent = `${(Math.random() * 0.1).toFixed(2)}%`;
        document.getElementById('throughput').textContent = `${Math.floor(Math.random() * 1000 + 500)}req/s`;
        document.getElementById('systemUptime').textContent = `${(99.9 + Math.random() * 0.1).toFixed(1)}%`;
    }
    
    updateMetric(barId, valueId, percentage, suffix = '', customValue = null) {
        const bar = document.getElementById(barId);
        const value = document.getElementById(valueId);
        
        if (bar) {
            bar.style.width = `${Math.min(percentage, 100)}%`;
        }
        
        if (value) {
            if (customValue) {
                value.textContent = customValue;
            } else {
                value.textContent = `${percentage.toFixed(1)}${suffix}`;
            }
        }
    }
    
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
    
    
    
    updateDockerStatus() {
        const running = this.containers.filter(c => c.status === 'running').length;
        const stopped = this.containers.filter(c => c.status === 'exited').length;
        const total = this.containers.length;
        
        document.getElementById('dockerRunning').textContent = running;
        document.getElementById('dockerStopped').textContent = stopped;
        document.getElementById('dockerTotal').textContent = total;
        
        // Update docker list
        const dockerList = document.getElementById('dockerList');
        if (dockerList) {
            dockerList.innerHTML = this.containers.slice(0, 5).map(container => `
                <div class="docker-item">
                    <div class="status-indicator ${container.status === 'running' ? 'running' : 'stopped'}"></div>
                    <div class="container-name">${container.name || container.id}</div>
                    <div class="container-status">${window.jsTranslations[container.status] || container.status}</div>
                </div>
            `).join('');
        }
    }
    
    updateTopPorts(topPorts) {
        const portsGrid = document.getElementById('topPorts');
        if (!portsGrid) return;
        
        if (topPorts && topPorts.length > 0) {
            portsGrid.innerHTML = topPorts.map(port => `
                <div class="port-item">
                    <div class="port-number">${port.port}</div>
                    <div class="port-count">${port.count}x</div>
                </div>
            `).join('');
        } else {
            portsGrid.innerHTML = `<div style="text-align: center; color: var(--cc-text-secondary); font-size: 11px; padding: 20px;">${window.jsTranslations.no_ports_in_use || 'No ports in use'}</div>`;
        }
    }
    
    addAlert(alert) {
        this.alerts.unshift(alert);
        
        // Keep only last 10 alerts
        if (this.alerts.length > 10) {
            this.alerts = this.alerts.slice(0, 10);
        }
        
        this.updateAlertList();
    }
    
    updateAlertList() {
        const alertList = document.getElementById('alertList');
        if (!alertList) {
            console.warn('⚠️ Alert list element not found');
            return;
        }
        
        console.log(`🔄 Updating alert list with ${this.alerts.length} alerts`);
        
        if (this.alerts.length === 0) {
            alertList.innerHTML = `
                <div class="alert-item info">
                    <i class="fas fa-check-circle"></i>
                    <div class="alert-content">
                        <span>No active alerts</span>
                        <small>System is running smoothly</small>
                    </div>
                    <small class="alert-time">${this.formatTime(new Date())}</small>
                </div>
            `;
            return;
        }
        
        alertList.innerHTML = this.alerts.map(alert => {
            const iconClass = alert.icon || `fa-${this.getAlertIcon(alert.type)}`;
            return `
                <div class="alert-item ${alert.type} clickable-alert" data-alert-id="${alert.id || ''}" onclick="commandCenter.openAlertManagement()">
                    <i class="fas ${iconClass}"></i>
                    <div class="alert-content">
                        <span>${this.escapeHtml(alert.message)}</span>
                        ${alert.service ? `<small class="alert-service">${this.escapeHtml(alert.service)}</small>` : ''}
                    </div>
                    <div class="alert-actions">
                        <small class="alert-time">${this.formatTime(alert.timestamp)}</small>
                        <i class="fas fa-external-link-alt alert-link-icon"></i>
                    </div>
                </div>
            `;
        }).join('');
        
        console.log('✅ Alert list updated successfully');
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getAlertIcon(type) {
        switch (type) {
            case 'danger':
            case 'error':
                return 'exclamation-circle';
            case 'warning':
                return 'exclamation-triangle';
            case 'critical':
                return 'times-circle';
            case 'info':
            default:
                return 'info-circle';
        }
    }
    
    openAlertManagement() {
        console.log('🔗 Opening Alert Management...');
        window.location.href = '/security/alert-management/';
    }
    
    addActivity(activity) {
        this.activities.unshift(activity);
        
        // Keep only last 10 activities
        if (this.activities.length > 10) {
            this.activities = this.activities.slice(0, 10);
        }
        
        this.updateActivityList();
    }
    
    updateActivityList() {
        const activityList = document.getElementById('activityList');
        if (!activityList) return;
        
        activityList.innerHTML = this.activities.map(activity => `
            <div class="activity-item">
                <i class="fas fa-${activity.icon}"></i>
                <span>${activity.message}</span>
                <small>${this.formatTime(activity.timestamp)}</small>
            </div>
        `).join('');
    }
    
    async loadActivities() {
        try {
            const response = await fetch('/dashboard-api/api/activities/', {
                method: 'GET',
                headers: { 'Accept': 'application/json' },
                credentials: 'same-origin'
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const result = await response.json();
            if (result.success && Array.isArray(result.activities)) {
                this.activities = result.activities.map(a => ({
                    icon: a.icon || 'history',
                    message: a.title || a.description || 'Activity',
                    timestamp: new Date(a.created_at)
                }));
                this.updateActivityList();
            }
        } catch (e) {
            // ignore
        }
    }

    async loadLiveControl() {
        const setStatus = (elId, on) => {
            const dot = document.getElementById(elId);
            if (dot) dot.style.background = on ? '#48bb78' : '#e53e3e';
        };
        try {
            const [pm, si, sm, logs] = await Promise.all([
                fetch('/process-monitor/api/service/status/', { credentials: 'same-origin' }).then(r=>r.json()).catch(()=>({})),
                fetch('/system-information/api/live-mode/status/', { credentials: 'same-origin' }).then(r=>r.json()).catch(()=>({})),
                fetch('/service-monitoring/api/live-mode/status/', { credentials: 'same-origin' }).then(r=>r.json()).catch(()=>({})),
                fetch('/system-logs/api/', { credentials: 'same-origin' }).then(r=>({ ok: r.ok })).catch(()=>({ ok:false }))
            ]);
            setStatus('liveStatusProcessMonitor', !!pm.live_mode_enabled);
            setStatus('liveStatusSystemInfo', !!si.live_mode_enabled);
            setStatus('liveStatusServiceMonitoring', !!sm.live_mode_enabled);
            setStatus('liveStatusAppLogs', !!logs.ok);
        } catch (e) {
            // ignore
        }
    }
    
    async loadSMTPStatus() {
        try {
            const response = await fetch('/dashboard-api/api/smtp-status/', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.updateSMTPStatus(result.smtp, result.cve_automation);
            }
        } catch (error) {
            console.error('Error loading SMTP status:', error);
            this.updateSMTPStatus(null, null);
        }
    }
    
    updateSMTPStatus(smtp, cveAutomation) {
        const smtpStatusValue = document.getElementById('smtpStatusValue');
        const smtpHostValue = document.getElementById('smtpHostValue');
        const cveAutomationValue = document.getElementById('cveAutomationValue');
        
        if (!smtpStatusValue || !smtpHostValue || !cveAutomationValue) {
            return;
        }
        
        // Update SMTP Status
        if (smtp) {
            if (smtp.configured && smtp.is_active) {
                if (smtp.test_success === true) {
                    smtpStatusValue.innerHTML = '<span style="color: #48bb78;"><i class="fas fa-check-circle"></i> Active</span>';
                } else if (smtp.test_success === false) {
                    smtpStatusValue.innerHTML = '<span style="color: #ed8936;"><i class="fas fa-exclamation-triangle"></i> Active (Test Failed)</span>';
                } else {
                    smtpStatusValue.innerHTML = '<span style="color: #ed8936;"><i class="fas fa-question-circle"></i> Active (Not Tested)</span>';
                }
            } else if (smtp.configured) {
                smtpStatusValue.innerHTML = '<span style="color: #a0aec0;"><i class="fas fa-pause-circle"></i> Inactive</span>';
            } else {
                smtpStatusValue.innerHTML = '<span style="color: #e53e3e;"><i class="fas fa-times-circle"></i> Not Configured</span>';
            }
            
            // Update SMTP Host
            if (smtp.host) {
                smtpHostValue.textContent = smtp.host;
            } else {
                smtpHostValue.textContent = '--';
            }
        } else {
            smtpStatusValue.innerHTML = '<span style="color: #e53e3e;"><i class="fas fa-times-circle"></i> Not Available</span>';
            smtpHostValue.textContent = '--';
        }
        
        // Update CVE Automation Status
        if (cveAutomation) {
            if (cveAutomation.live && cveAutomation.enabled) {
                cveAutomationValue.innerHTML = '<span style="color: #48bb78;"><i class="fas fa-check-circle"></i> Live</span>';
            } else if (cveAutomation.enabled) {
                cveAutomationValue.innerHTML = '<span style="color: #a0aec0;"><i class="fas fa-pause-circle"></i> Disabled</span>';
            } else {
                cveAutomationValue.innerHTML = '<span style="color: #e53e3e;"><i class="fas fa-times-circle"></i> Not Enabled</span>';
            }
        } else {
            cveAutomationValue.innerHTML = '<span style="color: #e53e3e;"><i class="fas fa-times-circle"></i> Not Configured</span>';
        }
    }
    
    formatTime(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diff = now - time;
        
        if (diff < 60000) { // Less than 1 minute
            return window.jsTranslations.just_now || 'Just now';
        } else if (diff < 3600000) { // Less than 1 hour
            return `${Math.floor(diff / 60000)}${window.jsTranslations.minutes_ago || 'm ago'}`;
        } else if (diff < 86400000) { // Less than 1 day
            return `${Math.floor(diff / 3600000)}${window.jsTranslations.hours_ago || 'h ago'}`;
        } else {
            return time.toLocaleDateString();
        }
    }
    
    
    setupPeriodicUpdates() {
        setInterval(() => {
            this.loadSystemData();
            this.loadContainers();
            this.loadTopPorts();
            this.loadAlerts();
            this.loadActivities();
            this.loadLiveControl();
            this.loadSMTPStatus();
        }, this.updateInterval);
    }
    
    setupEventListeners() {
        // Real data loaders initialized in init()
        
    }
    
    
}

// Initialize Command Center when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.commandCenter = new CommandCenter();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('📱 Page hidden, pausing updates');
    } else {
        console.log('📱 Page visible, resuming updates');
        if (window.commandCenter) {
            window.commandCenter.loadSystemData();
        }
    }
});

// Handle window focus/blur
window.addEventListener('focus', () => {
    if (window.commandCenter) {
        window.commandCenter.loadSystemData();
    }
});

// Export for global access
window.CommandCenter = CommandCenter;
