/**
 * IP Analysis JavaScript
 * Detaylı IP analizi ve request tracking için
 */

class IPAnalysis {
    constructor() {
        this.currentIP = null;
        this.currentData = null;
        this.performanceChart = null;
        this.init();
    }

    init() {
        this.bindEvents();
        // Don't auto-load, wait for modal open
    }

    bindEvents() {
        // Refresh button
        document.getElementById('refreshIPAnalysis')?.addEventListener('click', () => {
            this.loadIPAnalysis();
        });

        // Export report button
        document.getElementById('exportIPReport')?.addEventListener('click', () => {
            this.exportReport();
        });

        // IP Details event listeners removed - modal not used

        // Modal close button
        document.querySelector('#ipAnalysisModal .modal-close')?.addEventListener('click', () => {
            this.closeIPAnalysis();
        });

        // Close modal when clicking outside
        document.getElementById('ipAnalysisModal')?.addEventListener('click', (e) => {
            if (e.target.id === 'ipAnalysisModal') {
                this.closeIPAnalysis();
            }
        });

        // IP Details modal close button
        // IP Details modal removed - not used

        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Request filters
        document.getElementById('methodFilter')?.addEventListener('change', () => {
            this.filterRequests();
        });

        document.getElementById('statusFilter')?.addEventListener('change', () => {
            this.filterRequests();
        });

        document.getElementById('pathFilter')?.addEventListener('input', () => {
            this.filterRequests();
        });
    }

    async loadIPAnalysis() {
        try {
            const response = await fetch('/process-monitor/api/ip-analysis/');
            const data = await response.json();
            
            if (data.success) {
                this.displayIPCards(data.ips);
            } else {
                this.showError('Failed to load IP analysis: ' + data.error);
            }
        } catch (error) {
            console.error('Error loading IP analysis:', error);
            this.showError('Error loading IP analysis');
        }
    }

    displayIPCards(ips) {
        const container = document.getElementById('ipCardsGrid');
        
        if (ips.length === 0) {
            container.innerHTML = '<div class="no-data">No IP addresses found</div>';
            return;
        }

        container.innerHTML = ips.map(ip => `
            <div class="ip-card" data-ip="${ip.ip}" onclick="selectIPCard('${ip.ip}')">
                <div class="ip-card-header">
                    <div class="ip-address">
                        <i class="fas fa-globe"></i>
                        <span>${ip.ip}</span>
                    </div>
                    <div class="ip-status ${ip.status}">
                        <i class="fas fa-circle"></i>
                        ${ip.status}
                    </div>
                </div>
                <div class="ip-stats">
                    <div class="ip-stat">
                        <div class="ip-stat-label">Connections</div>
                        <div class="ip-stat-value">${ip.connection_count}</div>
                    </div>
                    <div class="ip-stat">
                        <div class="ip-stat-label">Processes</div>
                        <div class="ip-stat-value">${ip.process_count}</div>
                    </div>
                    <div class="ip-stat">
                        <div class="ip-stat-label">Ports</div>
                        <div class="ip-stat-value">${ip.port_count}</div>
                    </div>
                </div>
                <div class="ip-actions">
                    <!-- Details button removed - IP Details modal not used -->
                </div>
            </div>
        `).join('');
    }

    // viewIPDetails removed - IP Details modal not used

    displayDetailedAnalysis(data) {
        // Update request statistics
        this.updateRequestStats(data.request_statistics);
        
        // Display request history
        this.displayRequestHistory(data.requests);
        
        // Display target servers
        this.displayTargetServers(data.server_analysis);
        
        // Display security analysis
        this.displaySecurityAnalysis(data.detailed_analysis);
        
        // Display performance analysis
        this.displayPerformanceAnalysis(data.detailed_analysis);
        
        // Initialize performance charts
        this.initPerformanceCharts(data.request_statistics);
    }

    updateRequestStats(stats) {
        document.getElementById('totalRequests').textContent = stats.total_requests || 0;
        document.getElementById('avgResponseTime').textContent = `${stats.avg_response_time || 0}ms`;
        document.getElementById('errorRate').textContent = `${stats.error_rate || 0}%`;
        document.getElementById('dataTransferred').textContent = this.formatBytes(stats.total_data_transferred || 0);
    }

    displayRequestHistory(requests) {
        const container = document.getElementById('requestList');
        
        if (!requests || requests.length === 0) {
            container.innerHTML = '<div class="no-data">No request history available</div>';
            return;
        }

        container.innerHTML = requests.map(req => `
            <div class="request-item" data-method="${req.method}" data-status="${req.status_code}" onclick="ipAnalysis.showRequestDetails('${req.request_id || Math.random()}')">
                <div class="request-header">
                    <span class="request-method ${req.method}">${req.method}</span>
                    <span class="request-path">${req.path}</span>
                    <span class="request-time">${this.formatTimestamp(req.timestamp)}</span>
                </div>
                <div class="request-details">
                    <div class="request-info">
                        <div class="request-label">Status</div>
                        <div class="request-value">
                            <span class="request-status ${this.getStatusClass(req.status_code)}">${req.status_code}</span>
                        </div>
                    </div>
                    <div class="request-info">
                        <div class="request-label">Response Time</div>
                        <div class="request-value">${req.response_time}ms</div>
                    </div>
                    <div class="request-info">
                        <div class="request-label">Operation</div>
                        <div class="request-value">${req.operation || 'N/A'}</div>
                    </div>
                    <div class="request-info">
                        <div class="request-label">Data Size</div>
                        <div class="request-value">${this.formatBytes((req.request_size || 0) + (req.response_size || 0))}</div>
                    </div>
                    <div class="request-info">
                        <div class="request-label">Sensitivity</div>
                        <div class="request-value">${req.data_sensitivity || 'N/A'}</div>
                    </div>
                    <div class="request-info">
                        <div class="request-label">Compliance</div>
                        <div class="request-value">${req.compliance_required ? 'Required' : 'Not Required'}</div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    displayTargetServers(serverAnalysis) {
        const container = document.getElementById('serversGrid');
        
        if (!serverAnalysis || Object.keys(serverAnalysis).length === 0) {
            container.innerHTML = '<div class="no-data">No target servers found</div>';
            return;
        }

        container.innerHTML = Object.entries(serverAnalysis).map(([server, details]) => `
            <div class="server-card">
                <div class="server-header">
                    <div class="server-address">${server}</div>
                    <div class="server-type">${details.server_type}</div>
                </div>
                <div class="server-details">
                    <div class="server-detail">
                        <div class="server-detail-label">Port Type</div>
                        <div class="server-detail-value">${details.port_type}</div>
                    </div>
                    <div class="server-detail">
                        <div class="server-detail-label">Secure</div>
                        <div class="server-detail-value">${details.is_secure ? 'Yes' : 'No'}</div>
                    </div>
                    <div class="server-detail">
                        <div class="server-detail-label">Common Service</div>
                        <div class="server-detail-value">${details.is_common_service ? 'Yes' : 'No'}</div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    displaySecurityAnalysis(analysis) {
        if (!analysis || !analysis.security_analysis) return;

        const security = analysis.security_analysis;
        
        document.getElementById('securityRiskLevel').textContent = security.security_risk_level || 'Unknown';
        document.getElementById('suspiciousRequests').textContent = security.suspicious_requests || 0;
        document.getElementById('failedAuthAttempts').textContent = security.failed_auth_attempts || 0;

        // Display recommendations
        const recommendationsContainer = document.getElementById('securityRecommendations');
        if (analysis.recommendations && analysis.recommendations.length > 0) {
            recommendationsContainer.innerHTML = analysis.recommendations.map(rec => `
                <div class="recommendation-item">
                    <i class="fas fa-lightbulb"></i>
                    <span>${rec}</span>
                </div>
            `).join('');
        } else {
            recommendationsContainer.innerHTML = '<div class="no-data">No security recommendations available</div>';
        }
    }

    displayPerformanceAnalysis(analysis) {
        if (!analysis || !analysis.performance_analysis) return;

        const performance = analysis.performance_analysis;
        
        document.getElementById('performanceRating').textContent = performance.performance_rating || 'Unknown';
        document.getElementById('maxResponseTime').textContent = `${performance.max_response_time || 0}ms`;
        document.getElementById('activeConnections').textContent = performance.active_connections || 0;
    }

    initPerformanceCharts(stats) {
        // Process Distribution Chart (Doughnut)
        this.createProcessDistributionChart();
        
        // Connection Types Chart (Doughnut)
        this.createConnectionTypesChart();
        
        // System Health Chart (Doughnut)
        this.createSystemHealthChart();
        
        // Resource Usage Chart (Line)
        this.createResourceUsageChart(stats);
        
        // Port Usage Chart (Bar)
        this.createPortUsageChart(stats);
    }

    createProcessDistributionChart() {
        const ctx = document.getElementById('processDistributionChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Active', 'Idle', 'Waiting'],
                datasets: [{
                    data: [65, 25, 10],
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                cutout: '70%'
            }
        });
    }

    createConnectionTypesChart() {
        const ctx = document.getElementById('connectionTypesChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['HTTP', 'HTTPS', 'WebSocket'],
                datasets: [{
                    data: [40, 45, 15],
                    backgroundColor: ['#3b82f6', '#10b981', '#8b5cf6'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                cutout: '70%'
            }
        });
    }

    createSystemHealthChart() {
        const ctx = document.getElementById('systemHealthChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Healthy', 'Warning', 'Critical'],
                datasets: [{
                    data: [80, 15, 5],
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                cutout: '70%'
            }
        });
    }

    createResourceUsageChart(stats) {
        const ctx = document.getElementById('resourceUsageChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                datasets: [{
                    label: 'CPU Usage (%)',
                    data: [25, 35, 45, 30, 40, 35],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Memory Usage (%)',
                    data: [40, 45, 50, 35, 55, 45],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: '#e2e8f0'
                        }
                    },
                    x: {
                        grid: {
                            color: '#e2e8f0'
                        }
                    }
                }
            }
        });
    }

    createPortUsageChart(stats) {
        const ctx = document.getElementById('portUsageChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Port 80', 'Port 443', 'Port 22', 'Port 21', 'Port 25', 'Port 53'],
                datasets: [{
                    label: 'Usage Count',
                    data: [45, 38, 25, 15, 12, 8],
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(139, 92, 246, 0.8)',
                        'rgba(236, 72, 153, 0.8)'
                    ],
                    borderColor: [
                        '#3b82f6',
                        '#10b981',
                        '#f59e0b',
                        '#ef4444',
                        '#8b5cf6',
                        '#ec4899'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#e2e8f0'
                        }
                    },
                    x: {
                        grid: {
                            color: '#e2e8f0'
                        }
                    }
                }
            }
        });
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab panels
        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }

    filterRequests() {
        const methodFilter = document.getElementById('methodFilter').value;
        const statusFilter = document.getElementById('statusFilter').value;
        const pathFilter = document.getElementById('pathFilter').value.toLowerCase();

        const requestItems = document.querySelectorAll('.request-item');
        
        requestItems.forEach(item => {
            const method = item.dataset.method;
            const status = item.dataset.status;
            const path = item.querySelector('.request-path').textContent.toLowerCase();

            const methodMatch = !methodFilter || method === methodFilter;
            const statusMatch = !statusFilter || 
                (statusFilter === '200' && status < 400) ||
                (statusFilter === '400' && status >= 400);
            const pathMatch = !pathFilter || path.includes(pathFilter);

            if (methodMatch && statusMatch && pathMatch) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }

    // showDetailedSection removed - IP Details modal not used

    // loadIPDetails removed - IP Details modal not used

    closeIPAnalysis() {
        const modal = document.getElementById('ipAnalysisModal');
        modal.style.display = 'none';
    }

    // IP Details functions removed - modal not used

    selectIPCard(ip) {
        // Remove selected class from all cards
        document.querySelectorAll('.ip-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Add selected class to clicked card
        const selectedCard = document.querySelector(`[data-ip="${ip}"]`);
        if (selectedCard) {
            selectedCard.classList.add('selected');
        }
        
        // Show IP details in pop-up modal
        this.showIPDetailsModal(ip);
    }

    // displayIPDetailsInModal removed - IP Details modal not used

    // displayIPDetailsInRightPanel removed - IP Details modal not used
    
    createCharts(data) {
        this.createConnectionTypesChart(data.active_connections || []);
        this.createProcessDistributionChart(data.associated_processes || []);
        this.createSystemHealthChart();
        this.createResourceUsageChart();
        this.createPortUsageChart(data.active_connections || []);
    }
    
    createConnectionTypesChart(connections) {
        const canvas = document.getElementById('connectionTypesChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Connection status'larını say
        const statusCounts = {};
        connections.forEach(conn => {
            const status = conn.status || 'unknown';
            statusCounts[status] = (statusCounts[status] || 0) + 1;
        });
        
        const labels = Object.keys(statusCounts);
        const data = Object.values(statusCounts);
        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    hoverBorderWidth: 4,
                    hoverBorderColor: '#f1f5f9'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 14,
                            weight: '600'
                        },
                        bodyFont: {
                            size: 12
                        },
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                cutout: '60%',
                animation: {
                    animateRotate: false,
                    animateScale: false,
                    duration: 0
                }
            }
        });
    }
    
    createProcessDistributionChart() {
        const canvas = document.getElementById('processDistributionChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Mock data for process distribution
        const processCounts = {
            'Cursor.exe': 3,
            'chrome.exe': 2,
            'firefox.exe': 1,
            'notepad.exe': 1,
            'Unknown': 2
        };
        
        const labels = Object.keys(processCounts);
        const data = Object.values(processCounts);
        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
        
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    hoverBorderWidth: 4,
                    hoverBorderColor: '#f1f5f9'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 14,
                            weight: '600'
                        },
                        bodyFont: {
                            size: 12
                        },
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                animation: {
                    animateRotate: false,
                    animateScale: false,
                    duration: 0
                }
            }
        });
    }
    
    createPortUsageChart(connections) {
        const canvas = document.getElementById('portUsageChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Port kullanımını say
        const portCounts = {};
        connections.forEach(conn => {
            const port = conn.local_port || conn.remote_port || '0';
            portCounts[port] = (portCounts[port] || 0) + 1;
        });
        
        // En çok kullanılan 10 port
        const sortedPorts = Object.entries(portCounts)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 10);
        
        const labels = sortedPorts.map(([port]) => `Port ${port}`);
        const data = sortedPorts.map(([,count]) => count);
        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'];
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Connections',
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderColor: colors.slice(0, labels.length),
                    borderWidth: 2,
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 14,
                            weight: '600'
                        },
                        bodyFont: {
                            size: 12
                        },
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#f1f5f9',
                            lineWidth: 1
                        },
                        ticks: {
                            font: {
                                size: 11,
                                weight: '500'
                            },
                            color: '#64748b'
                        }
                    },
                    x: {
                        grid: {
                            color: '#f1f5f9',
                            lineWidth: 1
                        },
                        ticks: {
                            font: {
                                size: 11,
                                weight: '500'
                            },
                            color: '#64748b'
                        }
                    }
                },
                animation: {
                    duration: 0
                }
            }
        });
    }
    
    createSystemHealthChart() {
        const canvas = document.getElementById('systemHealthChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Simulated system health data
        const healthData = {
            labels: ['CPU', 'Memory', 'Network', 'Disk'],
            datasets: [{
                data: [75, 60, 85, 40],
                backgroundColor: [
                    '#ef4444', // CPU - Red
                    '#10b981', // Memory - Green
                    '#3b82f6', // Network - Blue
                    '#f59e0b'  // Disk - Orange
                ],
                borderWidth: 3,
                borderColor: '#ffffff',
                hoverBorderWidth: 4,
                hoverBorderColor: '#f1f5f9'
            }]
        };
        
        new Chart(ctx, {
            type: 'doughnut',
            data: healthData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 14,
                            weight: '600'
                        },
                        bodyFont: {
                            size: 12
                        },
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                cutout: '60%',
                animation: {
                    animateRotate: false,
                    animateScale: false,
                    duration: 0
                }
            }
        });
    }
    
    createResourceUsageChart() {
        const canvas = document.getElementById('resourceUsageChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Simulated resource usage over time
        const timeLabels = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'];
        const cpuData = [20, 35, 60, 80, 45, 30];
        const memoryData = [40, 50, 70, 85, 60, 45];
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: timeLabels,
                datasets: [
                    {
                        label: 'CPU %',
                        data: cpuData,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderWidth: 3,
                        pointBackgroundColor: '#ef4444',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Memory %',
                        data: memoryData,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 3,
                        pointBackgroundColor: '#10b981',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 14,
                            weight: '600'
                        },
                        bodyFont: {
                            size: 12
                        },
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: '#f1f5f9',
                            lineWidth: 1
                        },
                        ticks: {
                            font: {
                                size: 11,
                                weight: '500'
                            },
                            color: '#64748b'
                        }
                    },
                    x: {
                        grid: {
                            color: '#f1f5f9',
                            lineWidth: 1
                        },
                        ticks: {
                            font: {
                                size: 11,
                                weight: '500'
                            },
                            color: '#64748b'
                        }
                    }
                },
                animation: {
                    duration: 0
                }
            }
        });
    }

    renderConnectionsList(connections) {
        if (!connections || connections.length === 0) {
            return '<div class="no-data">No active connections</div>';
        }
        
        return connections.slice(0, 5).map((conn, index) => `
            <div class="connection-item detailed" onclick="showConnectionDetails(${index})">
                <div class="connection-header">
                    <div class="connection-ports">
                        <span class="port-label">Local:</span>
                        <span class="local-port">${conn.local_port || 'N/A'}</span>
                        <i class="fas fa-arrow-right"></i>
                        <span class="port-label">Remote:</span>
                        <span class="remote-port">${conn.remote_port || 'N/A'}</span>
                    </div>
                    <div class="connection-status ${conn.status}">
                        <i class="fas fa-circle"></i>
                        ${conn.status || 'unknown'}
                    </div>
                </div>
                <div class="connection-details">
                    <div class="detail-row">
                        <span class="detail-label">Process:</span>
                        <span class="detail-value">
                            <i class="fas fa-cog"></i>
                            ${conn.process_name || 'Unknown'}
                        </span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Protocol:</span>
                        <span class="detail-value">TCP</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Family:</span>
                        <span class="detail-value">IPv4</span>
                    </div>
                </div>
                <div class="connection-actions">
                    <button class="btn-details" onclick="event.stopPropagation(); showConnectionDetails(${index})">
                        <i class="fas fa-eye"></i>
                        View Details
                    </button>
                </div>
            </div>
        `).join('');
    }

    renderProcessesList(processes) {
        if (!processes || processes.length === 0) {
            return `
                <div class="no-data">
                    <i class="fas fa-microchip"></i>
                    <span>No associated processes found</span>
                </div>
            `;
        }
        
        return processes.slice(0, 6).map((proc, index) => {
            const cpuPercent = proc.cpu_percent || 0;
            const memoryPercent = proc.memory_percent || 0;
            const status = proc.status || 'running';
            const statusClass = status.toLowerCase();
            
            return `
                <div class="process-item detailed" onclick="showProcessDetails(${index})" data-process-id="${proc.pid || index}">
                    <div class="process-header">
                        <div class="process-name">
                            <i class="fas fa-microchip"></i>
                            <span>${proc.name || 'Unknown Process'}</span>
                        </div>
                        <div class="process-pid">
                            <span class="pid-label">PID:</span>
                            <span class="pid-value">${proc.pid || 'N/A'}</span>
                        </div>
                    </div>
                    <div class="process-details">
                        <div class="detail-row">
                            <span class="detail-label">CPU Usage:</span>
                            <span class="detail-value">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${Math.min(cpuPercent, 100)}%"></div>
                                </div>
                                <span class="progress-text">${cpuPercent}%</span>
                            </span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Memory Usage:</span>
                            <span class="detail-value">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${Math.min(memoryPercent, 100)}%"></div>
                                </div>
                                <span class="progress-text">${memoryPercent}%</span>
                            </span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Status:</span>
                            <span class="detail-value">
                                <span class="status-badge ${statusClass}">
                                    <i class="fas fa-circle"></i>
                                    ${status.charAt(0).toUpperCase() + status.slice(1)}
                                </span>
                            </span>
                        </div>
                        ${proc.threads ? `
                            <div class="detail-row">
                                <span class="detail-label">Threads:</span>
                                <span class="detail-value">
                                    <i class="fas fa-code-branch"></i>
                                    ${proc.threads}
                                </span>
                            </div>
                        ` : ''}
                        ${proc.start_time ? `
                            <div class="detail-row">
                                <span class="detail-label">Start Time:</span>
                                <span class="detail-value">
                                    <i class="fas fa-clock"></i>
                                    ${this.formatTime(proc.start_time)}
                                </span>
                            </div>
                        ` : ''}
                    </div>
                    <div class="process-actions">
                        <button class="btn-details" onclick="event.stopPropagation(); showProcessDetails(${index})">
                            <i class="fas fa-eye"></i>
                            View Details
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    showError(message) {
        // Create error notification
        const notification = document.createElement('div');
        notification.className = 'error-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    showConnectionDetailsModal(connection) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        
        // Format connection status
        const status = connection.status || 'unknown';
        const statusClass = status.toLowerCase().replace('_', '_');
        
        // Format addresses with better display
        const localAddress = connection.local_address || connection.local_port || 'N/A';
        const remoteAddress = connection.remote_address || connection.remote_port || 'N/A';
        
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 class="modal-title">
                            <i class="fas fa-link"></i>
                            Connection Details
                        </h3>
                        <button class="modal-close" onclick="this.closest('.modal').remove()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="connection-details-full">
                            <div class="detail-section">
                                <h4><i class="fas fa-network-wired"></i> Network Information</h4>
                                <div class="detail-grid">
                                    <div class="detail-item">
                                        <span class="detail-label">Local Address</span>
                                        <div class="detail-value">
                                            <i class="fas fa-desktop"></i>
                                            <div class="address-display">
                                                <i class="fas fa-map-marker-alt"></i>
                                                ${localAddress}
                                            </div>
                                        </div>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Remote Address</span>
                                        <div class="detail-value">
                                            <i class="fas fa-globe"></i>
                                            <div class="address-display">
                                                <i class="fas fa-external-link-alt"></i>
                                                ${remoteAddress}
                                            </div>
                                        </div>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Connection Status</span>
                                        <div class="detail-value">
                                            <i class="fas fa-circle"></i>
                                            <span class="connection-status ${statusClass}">
                                                <i class="fas fa-circle"></i>
                                                ${status.toUpperCase()}
                                            </span>
                                        </div>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Protocol</span>
                                        <div class="detail-value">
                                            <i class="fas fa-shield-alt"></i>
                                            <span class="protocol-badge tcp">
                                                <i class="fas fa-lock"></i>
                                                TCP
                                            </span>
                                        </div>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Family</span>
                                        <div class="detail-value">
                                            <i class="fas fa-network-wired"></i>
                                            IPv4
                                        </div>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Connection Type</span>
                                        <div class="detail-value">
                                            <i class="fas fa-plug"></i>
                                            ${connection.type || 'Outbound'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="detail-section process-info-enhanced">
                                <h4><i class="fas fa-microchip"></i> Process Information</h4>
                                <div class="detail-grid">
                                    <div class="detail-item">
                                        <span class="detail-label">Process Name</span>
                                        <div class="detail-value">
                                            <i class="fas fa-cog"></i>
                                            ${connection.process_name || 'Unknown Process'}
                                        </div>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Process ID</span>
                                        <div class="detail-value">
                                            <i class="fas fa-hashtag"></i>
                                            ${connection.process_id || 'N/A'}
                                        </div>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Thread Count</span>
                                        <div class="detail-value">
                                            <i class="fas fa-code-branch"></i>
                                            ${connection.thread_count || 'N/A'}
                                        </div>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">CPU Usage</span>
                                        <div class="detail-value">
                                            <i class="fas fa-tachometer-alt"></i>
                                            ${connection.cpu_usage || 'N/A'}%
                                        </div>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Memory Usage</span>
                                        <div class="detail-value">
                                            <i class="fas fa-memory"></i>
                                            ${this.formatBytes(connection.memory_usage || 0)}
                                        </div>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Start Time</span>
                                        <div class="detail-value">
                                            <i class="fas fa-clock"></i>
                                            ${connection.start_time ? this.formatTime(connection.start_time) : 'N/A'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            ${connection.security_info ? `
                                <div class="detail-section">
                                    <h4><i class="fas fa-shield-alt"></i> Security Information</h4>
                                    <div class="detail-grid">
                                        <div class="detail-item">
                                            <span class="detail-label">Encryption</span>
                                            <div class="detail-value">
                                                <i class="fas fa-lock"></i>
                                                ${connection.security_info.encrypted ? 'Encrypted' : 'Unencrypted'}
                                            </div>
                                        </div>
                                        <div class="detail-item">
                                            <span class="detail-label">Certificate</span>
                                            <div class="detail-value">
                                                <i class="fas fa-certificate"></i>
                                                ${connection.security_info.certificate || 'N/A'}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ` : ''}
                            
                            <div class="detail-section">
                                <h4><i class="fas fa-chart-line"></i> Performance Metrics</h4>
                                <div class="detail-grid">
                                    <div class="detail-item">
                                        <span class="detail-label">Data Transferred</span>
                                        <div class="detail-value">
                                            <i class="fas fa-download"></i>
                                            ${this.formatBytes(connection.data_transferred || 0)}
                                        </div>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Packets Sent</span>
                                        <div class="detail-value">
                                            <i class="fas fa-paper-plane"></i>
                                            ${connection.packets_sent || 'N/A'}
                                        </div>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Packets Received</span>
                                        <div class="detail-value">
                                            <i class="fas fa-inbox"></i>
                                            ${connection.packets_received || 'N/A'}
                                        </div>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Connection Duration</span>
                                        <div class="detail-value">
                                            <i class="fas fa-hourglass-half"></i>
                                            ${connection.duration || 'N/A'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        modal.style.display = 'flex';
    }
    
    showProcessDetailsModal(process) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 class="modal-title">
                            <i class="fas fa-cog"></i>
                            Process Details
                        </h3>
                        <button class="modal-close" onclick="this.closest('.modal').remove()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="process-details-full">
                            <div class="detail-section">
                                <h4><i class="fas fa-info-circle"></i> Process Information</h4>
                                <div class="detail-grid">
                                    <div class="detail-item">
                                        <span class="detail-label">Process Name:</span>
                                        <span class="detail-value">${process.name || 'Unknown'}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Process ID:</span>
                                        <span class="detail-value">${process.pid || 'N/A'}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Status:</span>
                                        <span class="detail-value status-running">Running</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="detail-section">
                                <h4><i class="fas fa-chart-bar"></i> Resource Usage</h4>
                                <div class="detail-grid">
                                    <div class="detail-item">
                                        <span class="detail-label">CPU Usage:</span>
                                        <span class="detail-value">${process.cpu_percent || 0}%</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Memory Usage:</span>
                                        <span class="detail-value">${process.memory_percent || 0}%</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        modal.style.display = 'flex';
    }
    
    async showIPDetailsModal(ip) {
        try {
            const response = await fetch(`/process-monitor/api/ip-details/?ip=${encodeURIComponent(ip)}`);
            const data = await response.json();
            
            if (data.success) {
                this.currentData = data;
                this.createIPDetailsModal(data);
            } else {
                this.showError('Failed to load IP details: ' + data.error);
            }
        } catch (error) {
            console.error('Error loading IP details:', error);
            this.showError('Error loading IP details');
        }
    }
    
    createIPDetailsModal(data) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 class="modal-title">
                            <i class="fas fa-globe"></i>
                            IP Analysis: ${data.ip}
                        </h3>
                        <button class="modal-close" onclick="this.closest('.modal').remove()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="ip-details-modal-content">
                            <!-- IP Summary -->
                            <div class="ip-summary-section">
                                <div class="ip-header">
                                    <div class="ip-address">
                                        <i class="fas fa-globe"></i>
                                        <span>${data.ip}</span>
                                    </div>
                                    <div class="ip-status ${data.status}">
                                        <i class="fas fa-circle"></i>
                                        ${data.status}
                                    </div>
                                </div>
                                
                                <div class="ip-summary">
                                    <div class="summary-stats">
                                        <div class="stat-item">
                                            <div class="stat-label">Connections</div>
                                            <div class="stat-value">${data.connection_summary.total_connections}</div>
                                        </div>
                                        <div class="stat-item">
                                            <div class="stat-label">Processes</div>
                                            <div class="stat-value">${data.connection_summary.unique_processes}</div>
                                        </div>
                                        <div class="stat-item">
                                            <div class="stat-label">Ports</div>
                                            <div class="stat-value">${data.connection_summary.unique_ports}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Analysis Charts -->
                            <div class="ip-charts">
                                <h4><i class="fas fa-chart-pie"></i> Analysis Charts</h4>
                                <div class="charts-container">
                                    <div class="chart-row three-columns">
                                        <div class="chart-item">
                                            <h5>Connection Types</h5>
                                            <canvas id="modalConnectionTypesChart" width="160" height="100"></canvas>
                                        </div>
                                        <div class="chart-item">
                                            <h5>Process Distribution</h5>
                                            <canvas id="modalProcessDistributionChart" width="160" height="100"></canvas>
                                        </div>
                                        <div class="chart-item">
                                            <h5>System Health</h5>
                                            <canvas id="modalSystemHealthChart" width="160" height="100"></canvas>
                                        </div>
                                    </div>
                                    <div class="chart-row two-columns">
                                        <div class="chart-item">
                                            <h5>Resource Usage</h5>
                                            <canvas id="modalResourceUsageChart" width="200" height="120"></canvas>
                                        </div>
                                        <div class="chart-item">
                                            <h5>Port Usage</h5>
                                            <canvas id="modalPortUsageChart" width="200" height="120"></canvas>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Associated Processes -->
                            <div class="ip-processes">
                                <h4><i class="fas fa-cogs"></i> Associated Processes</h4>
                                <div class="processes-list">
                                    ${this.renderProcessesList(data.associated_processes || [])}
                                </div>
                            </div>
                            
                            <!-- Active Connections -->
                            <div class="ip-connections">
                                <h4><i class="fas fa-link"></i> Active Connections</h4>
                                <div class="connections-list">
                                    ${this.renderConnectionsList(data.active_connections || [])}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        modal.style.display = 'flex';
        
        // Create charts in modal
        setTimeout(() => {
            this.createModalCharts(data);
        }, 100);
    }
    
    createModalCharts(data) {
        this.createModalConnectionTypesChart(data.active_connections || []);
        this.createModalProcessDistributionChart(data.associated_processes || []);
        this.createModalSystemHealthChart();
        this.createModalResourceUsageChart();
        this.createModalPortUsageChart(data.active_connections || []);
    }
    
    createModalConnectionTypesChart(connections) {
        const canvas = document.getElementById('modalConnectionTypesChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        const statusCounts = {};
        connections.forEach(conn => {
            const status = conn.status || 'unknown';
            statusCounts[status] = (statusCounts[status] || 0) + 1;
        });
        
        const labels = Object.keys(statusCounts);
        const data = Object.values(statusCounts);
        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    hoverBorderWidth: 4,
                    hoverBorderColor: '#f1f5f9'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 14,
                            weight: '600'
                        },
                        bodyFont: {
                            size: 12
                        },
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                cutout: '60%',
                animation: {
                    animateRotate: false,
                    animateScale: false,
                    duration: 0
                }
            }
        });
    }
    
    createModalProcessDistributionChart(processes) {
        const canvas = document.getElementById('modalProcessDistributionChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        const processCounts = {};
        processes.forEach(proc => {
            const name = proc.name || 'Unknown';
            processCounts[name] = (processCounts[name] || 0) + 1;
        });
        
        const labels = Object.keys(processCounts);
        const data = Object.values(processCounts);
        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
        
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    hoverBorderWidth: 4,
                    hoverBorderColor: '#f1f5f9'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 14,
                            weight: '600'
                        },
                        bodyFont: {
                            size: 12
                        },
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                animation: {
                    animateRotate: false,
                    animateScale: false,
                    duration: 0
                }
            }
        });
    }
    
    createModalSystemHealthChart() {
        const canvas = document.getElementById('modalSystemHealthChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        const healthData = {
            labels: ['CPU', 'Memory', 'Network', 'Disk'],
            datasets: [{
                data: [75, 60, 85, 40],
                backgroundColor: [
                    '#ef4444', '#10b981', '#3b82f6', '#f59e0b'
                ],
                borderWidth: 3,
                borderColor: '#ffffff',
                hoverBorderWidth: 4,
                hoverBorderColor: '#f1f5f9'
            }]
        };
        
        new Chart(ctx, {
            type: 'doughnut',
            data: healthData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 14,
                            weight: '600'
                        },
                        bodyFont: {
                            size: 12
                        },
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                cutout: '60%',
                animation: {
                    animateRotate: false,
                    animateScale: false,
                    duration: 0
                }
            }
        });
    }
    
    createModalResourceUsageChart() {
        const canvas = document.getElementById('modalResourceUsageChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        const timeLabels = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'];
        const cpuData = [20, 35, 60, 80, 45, 30];
        const memoryData = [40, 50, 70, 85, 60, 45];
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: timeLabels,
                datasets: [
                    {
                        label: 'CPU %',
                        data: cpuData,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderWidth: 3,
                        pointBackgroundColor: '#ef4444',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Memory %',
                        data: memoryData,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 3,
                        pointBackgroundColor: '#10b981',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 14,
                            weight: '600'
                        },
                        bodyFont: {
                            size: 12
                        },
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: '#f1f5f9',
                            lineWidth: 1
                        },
                        ticks: {
                            font: {
                                size: 11,
                                weight: '500'
                            },
                            color: '#64748b'
                        }
                    },
                    x: {
                        grid: {
                            color: '#f1f5f9',
                            lineWidth: 1
                        },
                        ticks: {
                            font: {
                                size: 11,
                                weight: '500'
                            },
                            color: '#64748b'
                        }
                    }
                },
                animation: {
                    duration: 0
                }
            }
        });
    }
    
    createModalPortUsageChart(connections) {
        const canvas = document.getElementById('modalPortUsageChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        const portCounts = {};
        connections.forEach(conn => {
            const port = conn.local_port || conn.remote_port || '0';
            portCounts[port] = (portCounts[port] || 0) + 1;
        });
        
        const sortedPorts = Object.entries(portCounts)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 10);
        
        const labels = sortedPorts.map(([port]) => `Port ${port}`);
        const data = sortedPorts.map(([,count]) => count);
        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'];
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Connections',
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderColor: colors.slice(0, labels.length),
                    borderWidth: 2,
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 14,
                            weight: '600'
                        },
                        bodyFont: {
                            size: 12
                        },
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#f1f5f9',
                            lineWidth: 1
                        },
                        ticks: {
                            font: {
                                size: 11,
                                weight: '500'
                            },
                            color: '#64748b'
                        }
                    },
                    x: {
                        grid: {
                            color: '#f1f5f9',
                            lineWidth: 1
                        },
                        ticks: {
                            font: {
                                size: 11,
                                weight: '500'
                            },
                            color: '#64748b'
                        }
                    }
                },
                animation: {
                    duration: 0
                }
            }
        });
    }

    exportReport() {
        if (!this.currentData) {
            this.showError('No data available to export');
            return;
        }

        // Create and download report
        const reportData = {
            ip: this.currentData.ip,
            timestamp: new Date().toISOString(),
            analysis: this.currentData
        };

        const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ip-analysis-${this.currentData.ip}-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    showRequestDetails(requestId) {
        // Find the request in current data
        const request = this.currentData.requests.find(req => req.request_id === requestId);
        if (!request) return;

        // Show detailed request info section
        const detailSection = document.getElementById('detailedRequestInfo');
        detailSection.style.display = 'block';
        detailSection.scrollIntoView({ behavior: 'smooth' });

        // Populate detailed information
        this.populateRequestDetails(request);
    }

    populateRequestDetails(request) {
        // Overview tab
        document.getElementById('overview-tab').innerHTML = `
            <div class="request-overview">
                <div class="overview-grid">
                    <div class="overview-item">
                        <div class="overview-label">Request ID</div>
                        <div class="overview-value">${request.request_id || 'N/A'}</div>
                    </div>
                    <div class="overview-item">
                        <div class="overview-label">Session ID</div>
                        <div class="overview-value">${request.session_id || 'N/A'}</div>
                    </div>
                    <div class="overview-item">
                        <div class="overview-label">Connection ID</div>
                        <div class="overview-value">${request.connection_id || 'N/A'}</div>
                    </div>
                    <div class="overview-item">
                        <div class="overview-label">Business Context</div>
                        <div class="overview-value">${request.business_context || 'N/A'}</div>
                    </div>
                    <div class="overview-item">
                        <div class="overview-label">Data Sensitivity</div>
                        <div class="overview-value">${request.data_sensitivity || 'N/A'}</div>
                    </div>
                    <div class="overview-item">
                        <div class="overview-label">Compliance Required</div>
                        <div class="overview-value">${request.compliance_required ? 'Yes' : 'No'}</div>
                    </div>
                </div>
            </div>
        `;

        // Headers tab
        document.getElementById('headers-tab').innerHTML = `
            <div class="headers-section">
                <h4>Request Headers</h4>
                <div class="headers-list">
                    ${Object.entries(request.headers || {}).map(([key, value]) => `
                        <div class="header-item">
                            <div class="header-key">${key}</div>
                            <div class="header-value">${value}</div>
                        </div>
                    `).join('')}
                </div>
                <h4>Response Headers</h4>
                <div class="headers-list">
                    ${Object.entries(request.response_headers || {}).map(([key, value]) => `
                        <div class="header-item">
                            <div class="header-key">${key}</div>
                            <div class="header-value">${value}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        // Performance tab
        document.getElementById('performance-tab').innerHTML = `
            <div class="performance-section">
                <div class="performance-charts">
                    <h3><i class="fas fa-chart-line"></i> Performance Analysis</h3>
                    
                    <!-- Top Row: 3 Circular Charts -->
                    <div class="chart-grid">
                        <div class="chart-container">
                            <div class="chart-title">Process Distribution</div>
                            <canvas id="processDistributionChart"></canvas>
                        </div>
                        <div class="chart-container">
                            <div class="chart-title">Connection Types</div>
                            <canvas id="connectionTypesChart"></canvas>
                        </div>
                        <div class="chart-container">
                            <div class="chart-title">System Health</div>
                            <canvas id="systemHealthChart"></canvas>
                        </div>
                    </div>
                    
                    <!-- Bottom Row: Resource Usage & Port Usage -->
                    <div class="chart-grid-bottom">
                        <div class="chart-container">
                            <div class="chart-title">Resource Usage</div>
                            <canvas id="resourceUsageChart"></canvas>
                        </div>
                        <div class="chart-container">
                            <div class="chart-title">Port Usage</div>
                            <canvas id="portUsageChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Security tab
        document.getElementById('security-tab').innerHTML = `
            <div class="security-section">
                <div class="security-info">
                    <div class="security-item">
                        <div class="security-label">Audit Trail</div>
                        <div class="security-value">${request.audit_trail ? 'Enabled' : 'Disabled'}</div>
                    </div>
                    <div class="security-item">
                        <div class="security-label">Remote Address</div>
                        <div class="security-value">${request.remote_address || 'N/A'}</div>
                    </div>
                    <div class="security-item">
                        <div class="security-label">Local Address</div>
                        <div class="security-value">${request.local_address || 'N/A'}</div>
                    </div>
                    <div class="security-item">
                        <div class="security-label">Protocol</div>
                        <div class="security-value">${request.protocol || 'N/A'}</div>
                    </div>
                </div>
                ${request.error_details ? `
                    <div class="error-details">
                        <h4>Error Details</h4>
                        <div class="error-content">${request.error_details}</div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    // Utility functions
    formatTimestamp(timestamp) {
        if (!timestamp) return 'N/A';
        return new Date(timestamp).toLocaleString();
    }

    formatTime(timestamp) {
        if (!timestamp) return 'N/A';
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString();
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    getStatusClass(statusCode) {
        if (statusCode >= 200 && statusCode < 300) return 'success';
        if (statusCode >= 400) return 'error';
        return 'warning';
    }

}

// Initialize IP Analysis when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ipAnalysis = new IPAnalysis();
});

// Global functions for external access - viewIPDetails removed

window.selectIPCard = function(ip) {
    if (window.ipAnalysis) {
        window.ipAnalysis.selectIPCard(ip);
    }
};

window.showConnectionDetails = function(index) {
    if (window.ipAnalysis && window.ipAnalysis.currentData) {
        const connections = window.ipAnalysis.currentData.active_connections || [];
        if (connections[index]) {
            window.ipAnalysis.showConnectionDetailsModal(connections[index]);
        }
    }
};

window.showProcessDetails = function(index) {
    if (window.ipAnalysis && window.ipAnalysis.currentData) {
        const processes = window.ipAnalysis.currentData.associated_processes || [];
        if (processes[index]) {
            window.ipAnalysis.showProcessDetailsModal(processes[index]);
        }
    }
};

