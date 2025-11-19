/**
 * System Information JavaScript
 * Chart.js ile dinamik grafikler ve WebSocket ile real-time güncelleme
 */

document.addEventListener('DOMContentLoaded', function() {
    // Chart instances
    let cpuChart = null;
    let memoryChart = null;
    let diskChart = null;
    
    // WebSocket connection
    let socket = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    
    // Initialize
    initCharts();
    connectWebSocket();
    checkLiveModeStatus();
    
    // Refresh button
    const refreshBtn = document.getElementById('refreshSystemInfo');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + (window.jsTranslations['Refreshing...'] || 'Refreshing...');
            
            // Request immediate update via WebSocket
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({
                    type: 'request_update'
                }));
            } else {
                // Fallback to HTTP if WebSocket not available
                refreshSystemMetrics();
            }
            
            setTimeout(() => {
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-sync-alt"></i> ' + (window.jsTranslations['Refresh'] || 'Refresh');
            }, 1000);
        });
    }
    
    /**
     * Connect to WebSocket for real-time updates
     */
    function connectWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/system-information/`;
            
            console.log('Attempting WebSocket connection:', wsUrl);
            socket = new WebSocket(wsUrl);
            
            socket.onopen = function(e) {
                console.log('✓ WebSocket connected - Real-time monitoring active');
                reconnectAttempts = 0;
                updateLiveIndicator('connected');
                // Don't show notification, just log
            };
            
            socket.onmessage = function(event) {
                try {
                    const message = JSON.parse(event.data);
                    
                    if (message.type === 'system_metrics') {
                        // Update UI with new metrics
                        updateUIWithMetrics(message.data);
                        console.debug('Metrics updated via WebSocket');
                    } else if (message.type === 'error') {
                        console.error('WebSocket error:', message.message);
                    } else if (message.type === 'pong') {
                        // Handle pong response
                        console.debug('Pong received');
                    }
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            socket.onerror = function(error) {
                console.warn('WebSocket connection failed, switching to HTTP polling');
                updateLiveIndicator('error');
            };
            
            socket.onclose = function(event) {
                console.log('WebSocket disconnected');
                updateLiveIndicator('disconnected');
                
                // Immediately start polling as fallback
                console.log('Starting HTTP polling (5s interval)');
                startPolling();
            };
            
        } catch (error) {
            console.warn('WebSocket not available, using HTTP polling');
            startPolling();
        }
    }
    
    /**
     * Start HTTP polling as fallback
     */
    let pollingInterval = null;
    function startPolling() {
        // Clear any existing polling
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
        
        // Poll every 5 seconds
        pollingInterval = setInterval(() => {
            refreshSystemMetrics();
        }, 5000);
        
        // Also do an immediate refresh
        refreshSystemMetrics();
    }
    
    /**
     * Update UI with new metrics from WebSocket or API
     */
    function updateUIWithMetrics(data) {
        if (!data) return;
        
        console.debug('Updating UI with metrics:', data);
        
        // Update CPU
        if (data.cpu) {
            updateCPUChart(data.cpu);
            updateCPUDisplay(data.cpu);
        }
        
        // Update Memory
        if (data.memory) {
            updateMemoryChart(data.memory);
            updateMemoryDisplay(data.memory);
        }
        
        // Update Disk
        if (data.disk) {
            updateDiskChart(data.disk);
            updateDiskDisplay(data.disk);
        }
        
        // Update other sections as needed
        if (data.network) {
            updateNetworkDisplay(data.network);
        }
        
        // Update last refresh time
        updateLastRefreshTime();
    }
    
    /**
     * Update last refresh time indicator
     */
    function updateLastRefreshTime() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', { hour12: false });
        
        // You can add a small indicator if you want
        console.debug(`UI updated at ${timeStr}`);
    }
    
    /**
     * Show notification to user
     */
    function showNotification(message, type = 'info') {
        // You can implement a toast notification here
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
    
    /**
     * Initialize all charts
     */
    function initCharts() {
        initCPUChart();
        initMemoryChart();
        initDiskChart();
    }
    
    /**
     * Initialize CPU Chart
     */
    function initCPUChart() {
        const ctx = document.getElementById('cpuChart');
        if (!ctx) return;
        
        const usage = window.SYSTEM_DATA?.cpu?.usage_percent || 0;
        
        cpuChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [window.jsTranslations['Used'] || 'Used', window.jsTranslations['Free'] || 'Free'],
                datasets: [{
                    data: [usage, 100 - usage],
                    backgroundColor: [
                        'rgba(79, 172, 254, 0.9)',
                        'rgba(226, 232, 240, 0.8)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed.toFixed(1) + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Initialize Memory Chart
     */
    function initMemoryChart() {
        const ctx = document.getElementById('memoryChart');
        if (!ctx) return;
        
        const usage = window.SYSTEM_DATA?.memory?.percent || 0;
        
        memoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [window.jsTranslations['Used'] || 'Used', window.jsTranslations['Free'] || 'Free'],
                datasets: [{
                    data: [usage, 100 - usage],
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.9)',
                        'rgba(226, 232, 240, 0.8)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed.toFixed(1) + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Initialize Disk Chart
     */
    function initDiskChart() {
        const ctx = document.getElementById('diskChart');
        if (!ctx) return;
        
        const usage = window.SYSTEM_DATA?.disk?.total_percent || 0;
        
        diskChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [window.jsTranslations['Used'] || 'Used', window.jsTranslations['Free'] || 'Free'],
                datasets: [{
                    data: [usage, 100 - usage],
                    backgroundColor: [
                        'rgba(245, 158, 11, 0.9)',
                        'rgba(226, 232, 240, 0.8)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed.toFixed(1) + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Update CPU Chart
     */
    function updateCPUChart(cpuData) {
        if (cpuChart && cpuData) {
            const usage = cpuData.usage_percent || 0;
            cpuChart.data.datasets[0].data = [usage, 100 - usage];
            cpuChart.update('none'); // No animation for smooth updates
        }
    }
    
    /**
     * Update CPU Display
     */
    function updateCPUDisplay(cpuData) {
        if (!cpuData) return;
        
        const cpuUsageValue = document.getElementById('cpuUsageValue');
        if (cpuUsageValue && cpuData.usage_percent !== undefined) {
            cpuUsageValue.textContent = cpuData.usage_percent.toFixed(1) + '%';
        }
    }
    
    /**
     * Update Memory Chart
     */
    function updateMemoryChart(memoryData) {
        if (memoryChart && memoryData) {
            const usage = memoryData.percent || 0;
            memoryChart.data.datasets[0].data = [usage, 100 - usage];
            memoryChart.update('none');
        }
    }
    
    /**
     * Update Memory Display
     */
    function updateMemoryDisplay(memoryData) {
        if (!memoryData) return;
        
        const memoryUsageValue = document.getElementById('memoryUsageValue');
        if (memoryUsageValue && memoryData.percent !== undefined) {
            memoryUsageValue.textContent = memoryData.percent.toFixed(1) + '%';
        }
    }
    
    /**
     * Update Disk Chart
     */
    function updateDiskChart(diskData) {
        if (diskChart && diskData) {
            const usage = diskData.total_percent || 0;
            diskChart.data.datasets[0].data = [usage, 100 - usage];
            diskChart.update('none');
        }
    }
    
    /**
     * Update Disk Display
     */
    function updateDiskDisplay(diskData) {
        if (!diskData) return;
        
        const diskUsageValue = document.getElementById('diskUsageValue');
        if (diskUsageValue && diskData.total_percent !== undefined) {
            diskUsageValue.textContent = diskData.total_percent.toFixed(1) + '%';
        }
    }
    
    /**
     * Update Network Display
     */
    function updateNetworkDisplay(networkData) {
        if (!networkData) return;
        // Network updates can be added here if needed
        console.debug('Network data updated:', networkData);
    }
    
    /**
     * Refresh system metrics from API
     */
    function refreshSystemMetrics() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        
        fetch('/system-information/api/metrics/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
                'X-CSRFToken': csrfToken ? csrfToken.value : ''
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Use the same update function for both WebSocket and HTTP
                updateUIWithMetrics(data.data);
            } else {
                console.error('Failed to fetch system metrics:', data.error);
            }
        })
        .catch(error => {
            console.error('Error fetching system metrics:', error);
        });
    }
    
    /**
     * Update all metrics on the page
     */
    function updateMetrics(data) {
        // Update charts
        if (data.cpu && data.cpu.usage_percent !== undefined) {
            updateCPUChart(data.cpu.usage_percent);
            
            // Update CPU metric value
            const cpuValue = document.querySelector('.metrics-grid .metric-card:nth-child(1) .metric-value');
            if (cpuValue) {
                cpuValue.textContent = data.cpu.usage_percent.toFixed(1) + '%';
            }
            
            // Update CPU details
            updateDetailValue('.metrics-grid .metric-card:nth-child(1)', 'Frequency', data.cpu.frequency + ' MHz');
        }
        
        if (data.memory && data.memory.percent !== undefined) {
            updateMemoryChart(data.memory.percent);
            
            // Update Memory metric value
            const memoryValue = document.querySelector('.metrics-grid .metric-card:nth-child(2) .metric-value');
            if (memoryValue) {
                memoryValue.textContent = data.memory.percent.toFixed(1) + '%';
            }
            
            // Update Memory details
            updateDetailValue('.metrics-grid .metric-card:nth-child(2)', 'Used', data.memory.used + ' GB');
            updateDetailValue('.metrics-grid .metric-card:nth-child(2)', 'Available', data.memory.available + ' GB');
        }
        
        if (data.disk && data.disk.total_percent !== undefined) {
            updateDiskChart(data.disk.total_percent);
            
            // Update Disk metric value
            const diskValue = document.querySelector('.metrics-grid .metric-card:nth-child(3) .metric-value');
            if (diskValue) {
                diskValue.textContent = data.disk.total_percent.toFixed(1) + '%';
            }
            
            // Update Disk details
            updateDetailValue('.metrics-grid .metric-card:nth-child(3)', 'Used', data.disk.used_space + ' GB');
            updateDetailValue('.metrics-grid .metric-card:nth-child(3)', 'Free', data.disk.free_space + ' GB');
        }
    }
    
    /**
     * Update a detail value by label
     */
    function updateDetailValue(cardSelector, label, value) {
        const card = document.querySelector(cardSelector);
        if (!card) return;
        
        const detailItems = card.querySelectorAll('.detail-item');
        detailItems.forEach(item => {
            const labelEl = item.querySelector('.detail-label');
            if (labelEl && labelEl.textContent.toUpperCase() === label.toUpperCase()) {
                const valueEl = item.querySelector('.detail-value');
                if (valueEl) {
                    valueEl.textContent = value;
                }
            }
        });
    }
    
    console.log('✅ System Information module initialized');
});

/**
 * Check live mode status from server
 */
function checkLiveModeStatus() {
    fetch('/system-information/api/live-mode/status/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateLiveIndicator(data.live_mode_enabled ? 'connected' : 'disconnected');
            } else {
                updateLiveIndicator('error');
            }
        })
        .catch(error => {
            console.error('Failed to check live mode status:', error);
            updateLiveIndicator('error');
        });
}

/**
 * Update live indicator status
 */
function updateLiveIndicator(status) {
    const indicator = document.getElementById('wsIndicator');
    if (!indicator) return;
    
    // Remove all status classes
    indicator.classList.remove('connected', 'disconnected', 'error');
    
    // Add appropriate status class
    switch (status) {
        case 'connected':
            indicator.classList.add('connected');
            indicator.title = window.jsTranslations['Live Mode: Active'] || 'Live Mode: Active';
            break;
        case 'disconnected':
            indicator.classList.add('disconnected');
            indicator.title = window.jsTranslations['Live Mode: Inactive'] || 'Live Mode: Inactive';
            break;
        case 'error':
            indicator.classList.add('error');
            indicator.title = window.jsTranslations['Live Mode: Error'] || 'Live Mode: Error';
            break;
    }
}
