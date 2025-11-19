/**
 * Service Monitoring Live Mode
 * Real-time service status updates via WebSocket
 */

class ServiceMonitoringLiveMode {
    constructor(serviceMonitoring) {
        this.serviceMonitoring = serviceMonitoring;
        this.websocket = null;
        this.isLiveMode = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 1000; // 1 second
        this.connectionStatus = 'disconnected';
        
        this.bindEvents();
    }
    
    bindEvents() {
        // Live mode toggle
        const liveModeToggle = document.getElementById('liveModeToggle');
        if (liveModeToggle) {
            liveModeToggle.addEventListener('click', () => {
                this.toggleLiveMode();
            });
        }
        
        // Page unload - stop live mode
        window.addEventListener('beforeunload', () => {
            this.stopLiveMode();
        });
    }
    
    async toggleLiveMode() {
        const toggle = document.getElementById('liveModeToggle');
        const indicator = document.getElementById('liveIndicator');
        
        if (!toggle || !indicator) return;
        
        const isEnabled = toggle.classList.contains('enabled');
        const newState = !isEnabled;
        
        try {
            // Update UI immediately for better UX
            this.updateLiveModeUI(newState);
            
            if (newState) {
                await this.startLiveMode();
            } else {
                this.stopLiveMode();
            }
            
            this.showLiveModeNotification(newState);
        } catch (error) {
            console.error('Error toggling live mode:', error);
            this.showError('Failed to toggle live mode');
            // Revert UI state
            this.updateLiveModeUI(!newState);
        }
    }
    
    startLiveMode() {
        if (this.isLiveMode) return;
        
        this.isLiveMode = true;
        this.connectWebSocket();
    }
    
    stopLiveMode() {
        this.isLiveMode = false;
        this.disconnectWebSocket();
    }
    
    connectWebSocket() {
        if (this.websocket) return;
        
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/service-monitoring/`;
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('Service Monitoring WebSocket connected');
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('connected');
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing Service Monitoring WebSocket message:', error);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('Service Monitoring WebSocket disconnected');
                this.websocket = null;
                this.updateConnectionStatus('disconnected');
                this.handleConnectionError();
            };
            
            this.websocket.onerror = (error) => {
                console.error('Service Monitoring WebSocket error:', error);
                this.updateConnectionStatus('error');
            };
        } catch (error) {
            console.error('Error connecting Service Monitoring WebSocket:', error);
        }
    }
    
    disconnectWebSocket() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        this.updateConnectionStatus('disconnected');
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'services_update':
                this.handleServicesUpdate(data.services);
                break;
            case 'service_status_update':
                this.handleServiceStatusUpdate(data.service_name, data.details);
                break;
            default:
                console.log('Unknown Service Monitoring WebSocket message type:', data.type);
        }
    }
    
    handleServicesUpdate(services) {
        // Update services list with new data
        this.serviceMonitoring.services = services;
        this.serviceMonitoring.renderServices();
        
        // Update stats
        this.serviceMonitoring.updateStats();
    }
    
    handleServiceStatusUpdate(serviceName, details) {
        // Update specific service status
        const serviceRow = document.querySelector(`[data-service="${serviceName}"]`);
        if (serviceRow) {
            this.serviceMonitoring.updateServiceRow(serviceRow, details);
        }
    }
    
    handleConnectionError() {
        if (!this.isLiveMode) return;
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Service Monitoring WebSocket reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, this.reconnectInterval * this.reconnectAttempts);
        } else {
            console.error('Service Monitoring WebSocket max reconnection attempts reached');
            this.updateConnectionStatus('error');
            this.showError('Live mode connection failed. Please refresh the page.');
        }
    }
    
    updateConnectionStatus(status) {
        this.connectionStatus = status;
        const indicator = document.getElementById('liveIndicator');
        if (!indicator) return;
        
        const wsIndicator = indicator.querySelector('.ws-indicator');
        if (!wsIndicator) return;
        
        // Remove all status classes
        wsIndicator.classList.remove('connected', 'disconnected', 'error');
        
        // Add appropriate status class
        switch (status) {
            case 'connected':
                wsIndicator.classList.add('connected');
                break;
            case 'disconnected':
                wsIndicator.classList.add('disconnected');
                break;
            case 'error':
                wsIndicator.classList.add('error');
                break;
        }
    }
    
    updateLiveModeUI(enabled) {
        const toggle = document.getElementById('liveModeToggle');
        const indicator = document.getElementById('liveIndicator');
        
        if (toggle) {
            if (enabled) {
                toggle.classList.add('enabled');
            } else {
                toggle.classList.remove('enabled');
            }
        }
        
        if (indicator) {
            if (enabled) {
                indicator.style.display = 'flex';
            } else {
                indicator.style.display = 'none';
            }
        }
    }
    
    showLiveModeNotification(enabled) {
        const message = enabled ? 'Live mode enabled' : 'Live mode disabled';
        const type = enabled ? 'success' : 'info';
        this.serviceMonitoring.showNotification(message, type);
    }
    
    showError(message) {
        this.serviceMonitoring.showNotification(message, 'error');
    }
    
    // Public method to check if live mode is active
    isActive() {
        return this.isLiveMode && this.connectionStatus === 'connected';
    }
    
    // Public method to get connection status
    getConnectionStatus() {
        return this.connectionStatus;
    }
}
