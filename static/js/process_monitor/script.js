/**
 * Process Monitor JavaScript
 * For monitoring and managing network processes
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Modal elements
    const processDetailsModal = document.getElementById('processDetailsModal');
    const processManagementModal = document.getElementById('processManagementModal');
    const groupViewModal = document.getElementById('groupViewModal');
    const interfaceViewModal = document.getElementById('interfaceViewModal');
    const portDetailsModal = document.getElementById('portDetailsModal');
    const allPortsModal = document.getElementById('allPortsModal');
    // ipDetailsModal removed - not used
    
    // ===== REAL-TIME DATA (WebSocket + Cache Fallback) =====
    
    let ws = null;
    let reconnectInterval = null;
    let isConnecting = false;
    let isLiveMode = false;
    let cacheInterval = null;
    
    // Check live mode status
    function checkLiveModeStatus() {
        fetch('/process-monitor/api/service/status/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    isLiveMode = data.live_mode_enabled;
                    const realtimeEnabled = data.realtime_websocket_enabled;
                    
                    updateConnectionStatus(isLiveMode);
                    
                    if (isLiveMode) {
                        if (realtimeEnabled) {
                            connectWebSocket();
                        } else {
                            startCachePolling();
                        }
                    } else {
                        stopAllConnections();
                    }
                }
            })
            .catch(error => {
                console.error('Live mode status check failed:', error);
                // Fallback: Cache polling
                startCachePolling();
            });
    }
    
    function updateConnectionStatus(isActive) {
        const indicator = document.getElementById('wsIndicator');
        if (indicator) {
            if (isActive) {
                indicator.className = 'ws-indicator connected';
                indicator.title = '🟢 ' + (window.jsTranslations?.live_mode_real_time || 'Live Mode: Real-time data streaming');
            } else {
                indicator.className = 'ws-indicator disconnected';
                indicator.title = '⚫ ' + (window.jsTranslations?.live_mode_disabled || 'Live Mode disabled');
            }
        }
    }
    
    // WebSocket Connection
    function connectWebSocket() {
        if (isConnecting || (ws && ws.readyState === WebSocket.OPEN)) {
            return;
        }
        
        isConnecting = true;
        stopCachePolling(); // Stop cache polling
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/process-monitor/`;
        
        console.log('🔌 WebSocket connecting:', wsUrl);
        
        try {
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                console.log('✅ WebSocket connected! Real-time data streaming started.');
                isConnecting = false;
                
                if (reconnectInterval) {
                    clearInterval(reconnectInterval);
                    reconnectInterval = null;
                }
                
                updateConnectionStatus(true);
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === 'connections_update') {
                    updateConnectionsTable(data.connections);
                } else if (data.type === 'ports_update') {
                    displayPortCards(data.ports);
                }
            };
            
            ws.onerror = function(error) {
                console.error('❌ WebSocket error:', error);
                isConnecting = false;
            };
            
            ws.onclose = function() {
                console.log('⚠️ WebSocket closed. Starting cache fallback...');
                isConnecting = false;
                ws = null;
                
                // Switch to cache polling when WebSocket closes
                startCachePolling();
                
                // Try WebSocket again after 5 seconds
                if (!reconnectInterval) {
                    reconnectInterval = setInterval(function() {
                        if (isLiveMode) {
                            connectWebSocket();
                        }
                    }, 5000);
                }
            };
            
        } catch (error) {
            console.error('❌ WebSocket creation error:', error);
            isConnecting = false;
            startCachePolling(); // Fallback
        }
    }
    
    // Cache Polling (Fallback)
    function startCachePolling() {
        if (cacheInterval) {
            return;
        }
        
        console.log('📡 Cache polling started (Fallback mode)');
        
        // Initial load
        loadDataFromCache();
        
        // Every 2 seconds
        cacheInterval = setInterval(loadDataFromCache, 2000);
    }
    
    function stopCachePolling() {
        if (cacheInterval) {
            clearInterval(cacheInterval);
            cacheInterval = null;
            console.log('Cache polling stopped');
        }
    }
    
    function loadDataFromCache() {
        // Connections
        fetch('/process-monitor/api/connections/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateConnectionsTable(data.connections);
                }
            })
            .catch(error => console.error('Error loading connections:', error));
        
        // Ports
        fetch('/process-monitor/api/ports/?limit=6')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayPortCards(data.ports);
                }
            })
            .catch(error => console.error('Error loading ports:', error));
    }
    
    function stopAllConnections() {
        if (ws) {
            ws.close();
            ws = null;
        }
        stopCachePolling();
        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }
    }
    
    // Use initial data on page load (if available)
    if (window.INITIAL_CONNECTIONS && window.INITIAL_CONNECTIONS.length > 0) {
        console.log('⚡ Using initial data, rendering page instantly!');
        updateConnectionsTable(window.INITIAL_CONNECTIONS);
        
        // Also load initial ports data
        loadDataFromCache(); // Only for ports
    }
    
    // Then check live mode and start WebSocket
    checkLiveModeStatus();
    
    // Close connections on page unload
    window.addEventListener('beforeunload', function() {
        stopAllConnections();
    });
    
    // ===== MODAL MANAGEMENT =====
    
    function openModal(modal) {
        modal.classList.add('active');
    }
    
    function closeModal(modal) {
        modal.classList.remove('active');
    }
    
    // Expose as global functions for use in other modules
    window.openModal = openModal;
    window.closeModal = closeModal;
    
    // Modal close buttons
    document.querySelectorAll('.modal-close, .process-details-close, [data-dismiss="modal"]').forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal, .process-details-modal');
            closeModal(modal);
        });
    });
    
    // Close when clicking outside modal
    document.querySelectorAll('.modal, .process-details-modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this);
            }
        });
    });
    
    // Process Details Modal specific event listeners
    if (processDetailsModal) {
        // Close when clicking outside
        processDetailsModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this);
            }
        });
        
        // Close button
        const closeBtn = processDetailsModal.querySelector('.process-details-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                closeModal(processDetailsModal);
            });
        }
    }
    
    // ===== REFRESH CONNECTIONS =====
    
    document.getElementById('refreshConnections').addEventListener('click', function() {
        const icon = this.querySelector('i');
        icon.classList.add('fa-spin');
        
        // Load data from cache
        loadDataFromCache();
        
        // Stop icon animation after 1 second
        setTimeout(() => {
            icon.classList.remove('fa-spin');
        }, 1000);
    });
    
    function updateConnectionsTable(connections) {
        const tbody = document.getElementById('connectionsBody');
        
        // Update total connection count
        const totalElement = document.getElementById('totalConnections');
        if (totalElement) {
            totalElement.textContent = connections.length;
        }
        
        if (connections.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" class="empty-state">
                <i class="fas fa-inbox"></i>
                <span>${window.jsTranslations?.no_connections_found || 'No connections found'}</span>
            </td></tr>`;
            return;
        }
        
        tbody.innerHTML = connections.map(conn => {
            const statusClass = conn.status.toLowerCase();
            return `
                <tr>
                    <td><span class="pid-badge">${conn.pid || '-'}</span></td>
                    <td class="process-name">${conn.process_name || (window.jsTranslations?.unknown || 'Unknown')}</td>
                    <td><span class="badge badge-protocol">${conn.protocol}</span></td>
                    <td class="address-cell">${conn.local_address}</td>
                    <td class="address-cell">${conn.remote_address || '*:*'}</td>
                    <td><span class="badge badge-status badge-${statusClass}">${conn.status}</span></td>
                    <td>${conn.process_details.memory_percent ? conn.process_details.memory_percent.toFixed(1) : '0.0'}%</td>
                    <td>${conn.process_details.cpu_percent ? conn.process_details.cpu_percent.toFixed(1) : '0.0'}%</td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn-icon btn-view-details" 
                                    data-pid="${conn.pid}"
                                    title="${window.jsTranslations?.view_details || 'View Details'}">
                                <i class="fas fa-info-circle"></i>
                            </button>
                            ${conn.pid && conn.pid !== '-' ? `
                                <button class="btn-icon btn-manage-process" 
                                        data-pid="${conn.pid}"
                                        data-process-name="${conn.process_name || (window.jsTranslations?.unknown || 'Unknown')}"
                                        title="${window.jsTranslations?.process_management || 'Process Management'}">
                                    <i class="fas fa-cogs"></i>
                                </button>
                            ` : ''}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
        // Attach event listeners to new buttons
        attachEventListeners();
    }
    
    // ===== INTERFACE VIEW =====
    
    document.getElementById('interfaceViewBtn').addEventListener('click', function() {
        const body = document.getElementById('interfaceViewBody');
        body.innerHTML = `<div class="loading"><i class="fas fa-spinner fa-spin"></i> ${window.jsTranslations?.loading || 'Loading...'}</div>`;
        
        openModal(interfaceViewModal);
        
        fetch('/process-monitor/api/interfaces/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayInterfaceProcesses(data.interfaces);
                } else {
                    body.innerHTML = `<div class="alert alert-danger">${window.jsTranslations?.error || 'Error'}: ${data.error || 'Unknown error'}</div>`;
                }
            })
            .catch(error => {
                console.error('Error loading interface processes:', error);
                body.innerHTML = `<div class="alert alert-danger">${window.jsTranslations?.error || 'Error'} loading data</div>`;
            });
    });
    
    // ===== IP ANALYSIS =====
    
    document.getElementById('ipAnalysisBtn').addEventListener('click', function() {
        console.log('IP Analysis button clicked');
        
        // Check if Chart.js is loaded
        if (typeof Chart === 'undefined') {
            console.error('Chart.js is not loaded');
            alert('Chart.js library is not loaded. Please refresh the page.');
            return;
        }
        
        // Open IP Analysis modal
        const ipAnalysisModal = document.getElementById('ipAnalysisModal');
        if (ipAnalysisModal) {
            console.log('Opening IP Analysis modal');
            ipAnalysisModal.style.display = 'flex';
            ipAnalysisModal.classList.add('active');
            
            // Load IP analysis data after modal is fully ready
            setTimeout(() => {
                console.log('Loading IP Analysis data...');
                if (window.ipAnalysis) {
                    console.log('IP Analysis module found, loading data');
                    window.ipAnalysis.loadIPAnalysis();
                } else {
                    console.error('IP Analysis module not loaded');
                    // Try to load it manually
                    if (typeof IPAnalysis !== 'undefined') {
                        console.log('Creating new IP Analysis instance');
                        window.ipAnalysis = new IPAnalysis();
                        window.ipAnalysis.loadIPAnalysis();
                    } else {
                        console.error('IPAnalysis class not found');
                    }
                }
            }, 300);
        } else {
            console.error('IP Analysis modal not found');
        }
    });
    
    function displayIPAnalysis(ips) {
        const body = document.getElementById('ipCardsGrid');
        
        if (ips.length === 0) {
            body.innerHTML = '<div class="alert alert-info">No IP addresses found</div>';
            return;
        }
        
        body.innerHTML = `
            ${ips.map(ip => `
                <div class="ip-card" data-ip="${ip.ip}">
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
                            <span class="ip-stat-label">Connections:</span>
                            <span class="ip-stat-value">${ip.connection_count}</span>
                        </div>
                        <div class="ip-stat">
                            <span class="ip-stat-label">Processes:</span>
                            <span class="ip-stat-value">${ip.process_count}</span>
                        </div>
                        <div class="ip-stat">
                            <span class="ip-stat-label">Ports:</span>
                            <span class="ip-stat-value">${ip.port_count}</span>
                        </div>
                    </div>
                    <div class="ip-actions">
                        <!-- Detaylar butonu kaldırıldı -->
                    </div>
                </div>
            `).join('')}
        `;
    }
    
    // viewIPDetails fonksiyonu kaldırıldı
    
    // Eski displayIPDetails fonksiyonu kaldırıldı - artık ip_analysis.js'te displayIPDetailsInModal kullanılıyor
    function displayIPDetails_OLD(data) {
        const body = document.getElementById('ipDetailsBody');
        const ip = data.ip;
        
        body.innerHTML = `
            <div class="ip-details-container">
                <div class="ip-details-header">
                    <div class="ip-info">
                        <h4><i class="fas fa-globe"></i> ${ip}</h4>
                        <div class="ip-meta">
                            <span class="ip-type">${data.ip_type || 'Unknown'}</span>
                            <span class="ip-location">${data.location || 'Unknown Location'}</span>
                        </div>
                    </div>
                    <div class="ip-status-badge ${data.status}">
                        <i class="fas fa-circle"></i>
                        ${data.status}
                    </div>
                </div>
                
                <!-- Connection Summary -->
                <div class="ip-section">
                        <h5><i class="fas fa-link"></i> Connection Summary</h5>
                        <div class="ip-stats-grid">
                            <div class="ip-stat-card">
                                <div class="ip-stat-icon"><i class="fas fa-exchange-alt"></i></div>
                                <div class="ip-stat-content">
                                    <div class="ip-stat-label">Total Connections</div>
                                    <div class="ip-stat-value">${data.total_connections}</div>
                                </div>
                            </div>
                            <div class="ip-stat-card">
                                <div class="ip-stat-icon"><i class="fas fa-cogs"></i"></div>
                                <div class="ip-stat-content">
                                    <div class="ip-stat-label">Processes</div>
                                    <div class="ip-stat-value">${data.process_count}</div>
                                </div>
                            </div>
                            <div class="ip-stat-card">
                                <div class="ip-stat-icon"><i class="fas fa-network-wired"></i></div>
                                <div class="ip-stat-content">
                                    <div class="ip-stat-label">Ports</div>
                                    <div class="ip-stat-value">${data.port_count}</div>
                                </div>
                            </div>
                            <div class="ip-stat-card">
                                <div class="ip-stat-icon"><i class="fas fa-clock"></i></div>
                                <div class="ip-stat-content">
                                    <div class="ip-stat-label">Last Activity</div>
                                    <div class="ip-stat-value">${data.last_activity || 'Unknown'}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Request History -->
                    <div class="ip-section">
                        <h5><i class="fas fa-history"></i> Request History</h5>
                        <div class="request-history">
                            ${data.requests && data.requests.length > 0 ? `
                                <div class="request-list">
                                    ${data.requests.map(req => `
                                        <div class="request-item">
                                            <div class="request-header">
                                                <span class="request-method ${req.method}">${req.method}</span>
                                                <span class="request-path">${req.path}</span>
                                                <span class="request-time">${req.timestamp}</span>
                                            </div>
                                            <div class="request-details">
                                                <div class="request-info">
                                                    <span class="request-label">Status:</span>
                                                    <span class="request-status ${req.status_class}">${req.status}</span>
                                                </div>
                                                <div class="request-info">
                                                    <span class="request-label">Response Time:</span>
                                                    <span class="request-value">${req.response_time}ms</span>
                                                </div>
                                                <div class="request-info">
                                                    <span class="request-label">User Agent:</span>
                                                    <span class="request-value">${req.user_agent || 'N/A'}</span>
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            ` : `
                                <div class="no-requests">
                                    <i class="fas fa-info-circle"></i>
                                    <p>No request history available for this IP</p>
                                </div>
                            `}
                        </div>
                    </div>
                    
                    <!-- Active Connections -->
                    <div class="ip-section">
                        <h5><i class="fas fa-plug"></i> Active Connections</h5>
                        <div class="connections-table">
                            ${data.connections && data.connections.length > 0 ? `
                                <table class="ip-connections-table">
                                    <thead>
                                        <tr>
                                            <th>Local Address</th>
                                            <th>Remote Address</th>
                                            <th>Status</th>
                                            <th>Process</th>
                                            <th>PID</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${data.connections.map(conn => `
                                            <tr>
                                                <td>${conn.local_address}</td>
                                                <td>${conn.remote_address}</td>
                                                <td><span class="status-badge ${conn.status}">${conn.status}</span></td>
                                                <td>${conn.process_name}</td>
                                                <td>${conn.pid}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            ` : `
                                <div class="no-connections">
                                    <i class="fas fa-info-circle"></i>
                                    <p>No active connections found for this IP</p>
                                </div>
                            `}
                        </div>
                    </div>
            </div>
        `;
    }
    
    function displayInterfaceProcesses(interfaces) {
        const body = document.getElementById('interfaceViewBody');
        
        if (interfaces.length === 0) {
            body.innerHTML = '<div class="alert alert-info">No network interfaces found</div>';
            return;
        }
        
        body.innerHTML = `
            <div class="interface-list">
                ${interfaces.map(iface => `
                    <div class="interface-card">
                        <div class="interface-card-header">
                            <div class="interface-card-title">
                                <i class="fas fa-ethernet"></i>
                                <div>
                                    <h4>${iface.interface_name}</h4>
                                    <span class="interface-stats">${iface.unique_processes} processes • ${iface.total_connections} connections</span>
                                </div>
                            </div>
                            <button class="btn-secondary btn-sm toggle-interface" data-target="interface-${iface.interface_name.replace(/[^a-zA-Z0-9]/g, '_')}">
                                <i class="fas fa-chevron-down"></i>
                                Show Details
                            </button>
                        </div>
                        <div class="interface-card-body" id="interface-${iface.interface_name.replace(/[^a-zA-Z0-9]/g, '_')}" style="display: none;">
                            <div class="table-wrapper">
                                <table class="process-table">
                                    <thead>
                                        <tr>
                                            <th>PID</th>
                                            <th>Process</th>
                                            <th>Protocol</th>
                                            <th>Local Address</th>
                                            <th>Remote Address</th>
                                            <th>Status</th>
                                            <th>Memory</th>
                                            <th>CPU</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${iface.connections.map(conn => `
                                            <tr>
                                                <td><span class="pid-badge">${conn.pid || '-'}</span></td>
                                                <td class="process-name">${conn.process_name || 'Unknown'}</td>
                                                <td><span class="badge badge-protocol">${conn.protocol}</span></td>
                                                <td class="address-cell">${conn.local_address}</td>
                                                <td class="address-cell">${conn.remote_address}</td>
                                                <td><span class="badge badge-status badge-${conn.status.toLowerCase()}">${conn.status}</span></td>
                                                <td>${conn.memory_percent ? conn.memory_percent.toFixed(1) : '0.0'}%</td>
                                                <td>${conn.cpu_percent ? conn.cpu_percent.toFixed(1) : '0.0'}%</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        // Attach event listeners to toggle buttons
        body.querySelectorAll('.toggle-interface').forEach(button => {
            button.addEventListener('click', function() {
                const targetId = this.dataset.target;
                const targetBody = document.getElementById(targetId);
                const icon = this.querySelector('i');
                
                if (targetBody.style.display === 'none') {
                    targetBody.style.display = 'block';
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                    this.innerHTML = '<i class="fas fa-chevron-up"></i> Hide Details';
                } else {
                    targetBody.style.display = 'none';
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                    this.innerHTML = '<i class="fas fa-chevron-down"></i> Show Details';
                }
            });
        });
    }
    
    // ===== GROUP VIEW =====
    
    document.getElementById('groupViewBtn').addEventListener('click', function() {
        const body = document.getElementById('groupViewBody');
        body.innerHTML = `<div class="loading"><i class="fas fa-spinner fa-spin"></i> ${window.jsTranslations?.loading || 'Loading...'}</div>`;
        
        openModal(groupViewModal);
        
        fetch('/process-monitor/api/grouped/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayGroupedProcesses(data.processes);
                } else {
                    body.innerHTML = `<div class="alert alert-danger">${window.jsTranslations?.error || 'Error'}: ${data.error || 'Unknown error'}</div>`;
                }
            })
            .catch(error => {
                console.error('Error loading grouped processes:', error);
                body.innerHTML = `<div class="alert alert-danger">${window.jsTranslations?.error || 'Error'} loading data</div>`;
            });
    });
    
    function displayGroupedProcesses(processes) {
        const body = document.getElementById('groupViewBody');
        
        if (processes.length === 0) {
            body.innerHTML = `<div class="alert alert-info">${window.jsTranslations?.no_processes_found || 'No processes found'}</div>`;
            return;
        }
        
        body.innerHTML = `
            <div class="group-grid">
                ${processes.map(proc => `
                    <div class="group-card">
                        <div class="group-card-header">
                            <div class="group-card-title">
                                <i class="fas fa-microchip"></i>
                                ${proc.process_name}
                            </div>
                            <div class="group-card-badge">PID: ${proc.pid}</div>
                        </div>
                        <div class="group-card-stats">
                            <div class="group-stat-item">
                                <span class="group-stat-value">${proc.cpu_percent ? proc.cpu_percent.toFixed(1) : '0.0'}%</span>
                                <span class="group-stat-label">CPU</span>
                            </div>
                            <div class="group-stat-item">
                                <span class="group-stat-value">${proc.memory_percent ? proc.memory_percent.toFixed(1) : '0.0'}%</span>
                                <span class="group-stat-label">Memory</span>
                            </div>
                        </div>
                        <div class="connections-compact-box">
                            <div class="compact-box-header">
                                <i class="fas fa-network-wired"></i>
                                <span>${proc.connections.length} Connections</span>
                            </div>
                            <div class="compact-box-body">
                                ${proc.connections.map(conn => `
                                    <div class="compact-connection-item">
                                        <span class="badge badge-protocol badge-sm">${conn.protocol}</span>
                                        <span class="badge badge-status badge-${conn.status.toLowerCase()} badge-sm">${conn.status}</span>
                                        <span class="compact-address">${conn.local_address} → ${conn.remote_address}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <div style="margin-top: 12px; text-align: center;">
                            <button class="btn-secondary btn-sm view-process-details-from-group" data-pid="${proc.pid}" style="width: 100%;">
                                <i class="fas fa-info-circle"></i>
                                View Full Process Details
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        // Add event listeners to "View Full Process Details" buttons
        const detailButtons = body.querySelectorAll('.view-process-details-from-group');
        detailButtons.forEach(button => {
            button.addEventListener('click', function() {
                const pid = this.getAttribute('data-pid');
                
                // Close Group View modal first
                if (groupViewModal && window.closeModal) {
                    window.closeModal(groupViewModal);
                }
                
                // Then open Process Details modal
                if (window.viewProcessDetails) {
                    window.viewProcessDetails(pid);
                }
            });
        });
    }
    
    // ===== PROCESS DETAILS =====
    
    function viewProcessDetails(pid) {
        const modal = document.getElementById('processDetailsModal');
        const body = document.getElementById('processDetailsBody');
        
        if (!modal || !body) {
            console.error('Process details modal elements not found');
            return;
        }
        
        body.innerHTML = `<div class="loading"><i class="fas fa-spinner fa-spin"></i> ${window.jsTranslations?.loading || 'Loading...'}</div>`;
        
        // Open modal using global openModal function
        if (window.openModal) {
            window.openModal(modal);
        } else {
            modal.classList.add('active');
        }
        
        fetch(`/process-monitor/api/process/${pid}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayProcessDetails(data.data);
                } else {
                    body.innerHTML = `<div class="alert alert-danger">${window.jsTranslations?.error || 'Error'}: ${data.message || 'Unknown error'}</div>`;
                }
            })
            .catch(error => {
                console.error('Error loading process details:', error);
                body.innerHTML = `<div class="alert alert-danger">${window.jsTranslations?.error || 'Error'} loading data</div>`;
            });
    }
    
    // Make viewProcessDetails globally accessible
    window.viewProcessDetails = viewProcessDetails;
    
    function displayProcessDetails(data) {
        const body = document.getElementById('processDetailsBody');
        
        body.innerHTML = `
            ${data.warning ? `
            <div class="alert alert-warning" style="margin-bottom: 20px;">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${data.warning}</span>
            </div>
            ` : ''}
            
            <div class="info-section">
                <h4 class="info-section-title">
                    <i class="fas fa-info-circle"></i>
                    Basic Information
                </h4>
                <div class="process-info-grid">
                    <div class="info-item">
                        <span class="info-label">PID</span>
                        <span class="info-value">${data.pid}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Process Name</span>
                        <span class="info-value">${data.name}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Status</span>
                        <span class="info-value">${data.status}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">User</span>
                        <span class="info-value">${data.username || 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">CPU Usage</span>
                        <span class="info-value">${data.cpu_percent ? data.cpu_percent.toFixed(1) : '0.0'}%</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Memory Usage</span>
                        <span class="info-value">${data.memory_percent ? data.memory_percent.toFixed(1) : '0.0'}%</span>
                    </div>
                </div>
            </div>
            
            ${data.memory_info || data.io_counters ? `
            <div class="memory-io-container">
                ${data.memory_info ? `
                <div class="memory-details-section">
                    <h4 class="info-section-title">
                        <i class="fas fa-memory"></i>
                        Memory Details
                    </h4>
                    <div class="process-info-grid">
                        <div class="info-item">
                            <span class="info-label">RSS</span>
                            <span class="info-value">${data.memory_info.rss_formatted}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">VMS</span>
                            <span class="info-value">${data.memory_info.vms_formatted}</span>
                        </div>
                    </div>
                </div>
                ` : ''}
                
                ${data.io_counters ? `
                <div class="io-statistics-section">
                    <h4 class="info-section-title">
                        <i class="fas fa-hdd"></i>
                        I/O Statistics
                    </h4>
                    <div class="process-info-grid">
                        <div class="info-item">
                            <span class="info-label">Read</span>
                            <span class="info-value">${data.io_counters.read_formatted}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Written</span>
                            <span class="info-value">${data.io_counters.write_formatted}</span>
                        </div>
                    </div>
                </div>
                ` : ''}
            </div>
            ` : ''}
            
            ${data.connections && data.connections.length > 0 ? `
            <div class="info-section">
                <h4 class="info-section-title">
                    <i class="fas fa-network-wired"></i>
                    Connections
                </h4>
                <div class="connections-table-wrapper">
                    <table class="process-connections-table">
                        <thead>
                            <tr>
                                <th>Local Address</th>
                                <th>Remote Address</th>
                                <th>Status</th>
                                <th>Protocol</th>
                                <th>Family</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.connections.map(conn => `
                                <tr>
                                    <td class="address-cell">${conn.laddr || 'N/A'}</td>
                                    <td class="address-cell">${conn.raddr || 'N/A'}</td>
                                    <td><span class="badge badge-status badge-${conn.status.toLowerCase()}">${conn.status}</span></td>
                                    <td><span class="badge badge-protocol">${conn.protocol || 'TCP'}</span></td>
                                    <td><span class="badge badge-family">${conn.family || 'IPv4'}</span></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
            ` : ''}
        `;
    }
    
    // ===== PROCESS MANAGEMENT =====
    
    function manageProcess(pid, processName) {
        const body = document.getElementById('processManagementBody');
        body.innerHTML = `<div class="loading"><i class="fas fa-spinner fa-spin"></i> ${window.jsTranslations?.loading || 'Loading...'}</div>`;
        
        openModal(processManagementModal);
        
        fetch(`/process-monitor/api/process/${pid}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayProcessManagement(data.data, processName);
                } else {
                    body.innerHTML = `<div class="alert alert-danger">${window.jsTranslations?.error || 'Error'}: ${data.message || 'Unknown error'}</div>`;
                }
            })
            .catch(error => {
                console.error('Error loading process management:', error);
                body.innerHTML = `<div class="alert alert-danger">${window.jsTranslations?.error || 'Error'} loading data</div>`;
            });
    }
    
    function displayProcessManagement(data, processName) {
        const body = document.getElementById('processManagementBody');
        
        const actionButtons = {
            stop: { 
                label: window.jsTranslations?.stop_sigterm || 'Stop (SIGTERM)', 
                icon: 'fa-stop', 
                class: 'warning', 
                desc: window.jsTranslations?.stop_sigterm_desc || 'Gracefully stops the process' 
            },
            kill: { 
                label: window.jsTranslations?.force_kill_sigkill || 'Force Kill (SIGKILL)', 
                icon: 'fa-skull', 
                class: 'danger', 
                desc: window.jsTranslations?.force_kill_sigkill_desc || 'Forcefully terminates the process' 
            },
            suspend: { 
                label: window.jsTranslations?.suspend_sigstop || 'Suspend (SIGSTOP)', 
                icon: 'fa-pause', 
                class: '', 
                desc: window.jsTranslations?.suspend_sigstop_desc || 'Suspends the process' 
            },
            resume: { 
                label: window.jsTranslations?.resume_sigcont || 'Resume (SIGCONT)', 
                icon: 'fa-play', 
                class: '', 
                desc: window.jsTranslations?.resume_sigcont_desc || 'Resumes suspended process' 
            },
            restart: { 
                label: window.jsTranslations?.restart || 'Restart', 
                icon: 'fa-redo', 
                class: 'warning', 
                desc: window.jsTranslations?.restart_desc || 'Stops and restarts the process' 
            }
        };
        
        const availableActions = data.available_actions || [];
        
        body.innerHTML = `
            <div class="info-section">
                <h4 class="info-section-title">${processName} (PID: ${data.pid})</h4>
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    ${window.jsTranslations?.process_management_warning || 'Please use operations carefully. Terminating system processes may cause system instability.'}
                </div>
            </div>
            
            <div class="process-management-layout">
                <div class="process-info-section">
                    <h4 class="info-section-title">${window.jsTranslations?.process_information || 'Process Information'}</h4>
                    <div class="process-info-grid-2x2">
                        <div class="info-item">
                            <span class="info-label">${window.jsTranslations?.status || 'Status'}</span>
                            <span class="info-value">${data.status}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">${window.jsTranslations?.cpu || 'CPU'}</span>
                            <span class="info-value">${data.cpu_percent ? data.cpu_percent.toFixed(1) : '0.0'}%</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">${window.jsTranslations?.memory || 'Memory'}</span>
                            <span class="info-value">${data.memory_percent ? data.memory_percent.toFixed(1) : '0.0'}%</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">${window.jsTranslations?.thread_count || 'Thread Count'}</span>
                            <span class="info-value">${data.num_threads || window.jsTranslations?.na || 'N/A'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="available-actions-section">
                    <h4 class="info-section-title">${window.jsTranslations?.available_actions || 'Available Actions'}</h4>
                    <div class="process-actions-vertical">
                        ${availableActions.map(action => {
                            const btn = actionButtons[action];
                            return btn ? `
                                <button class="action-btn ${btn.class}" data-action="${action}" data-pid="${data.pid}">
                                    <div class="action-btn-title">
                                        <i class="fas ${btn.icon}"></i>
                                        ${btn.label}
                                    </div>
                                    <div class="action-btn-desc">${btn.desc}</div>
                                </button>
                            ` : '';
                        }).join('')}
                    </div>
                </div>
            </div>
        `;
        
        // Attach event listeners to action buttons
        body.querySelectorAll('.action-btn').forEach(button => {
            button.addEventListener('click', function() {
                const action = this.dataset.action;
                const pid = this.dataset.pid;
                executeProcessAction(pid, action);
            });
        });
    }
    
    function executeProcessAction(pid, action) {
        const actionText = window.jsTranslations?.[`action_${action}`] || action;
        const confirmMessage = window.jsTranslations?.confirm_action || `Are you sure you want to ${actionText} this process?`;
        if (!confirm(confirmMessage.replace('{action}', actionText))) {
            return;
        }
        
        fetch(`/process-monitor/api/process/${pid}/${action}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message || (window.jsTranslations?.operation_successful || 'Operation successful'), 'success');
                closeModal(processManagementModal);
                // Refresh connections
                document.getElementById('refreshConnections').click();
            } else {
                showNotification(data.error || data.message || (window.jsTranslations?.operation_failed || 'Operation failed'), 'error');
            }
        })
        .catch(error => {
            console.error('Error during process operation:', error);
            showNotification(window.jsTranslations?.operation_could_not_complete || 'Operation could not be completed', 'error');
        });
    }
    
    // ===== NOTIFICATIONS =====
    
    function showNotification(message, type = 'info') {
        // Simple notification system
        // Can be called as: showNotification('message', 'type')
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        const notification = document.createElement('div');
        notification.className = `alert ${alertClass}`;
        notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);';
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <div>
                    <strong>${message}</strong>
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.transition = 'opacity 0.3s ease';
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    // Expose as global function for use in other modules
    window.showNotification = showNotification;
    
    // ===== EVENT LISTENERS =====
    
    function attachEventListeners() {
        // Detail view buttons
        document.querySelectorAll('.btn-view-details').forEach(button => {
            button.addEventListener('click', function() {
                const pid = this.dataset.pid;
                viewProcessDetails(pid);
            });
        });
        
        // Process management buttons
        document.querySelectorAll('.btn-manage-process').forEach(button => {
            button.addEventListener('click', function() {
                const pid = this.dataset.pid;
                const processName = this.dataset.processName;
                manageProcess(pid, processName);
            });
        });
    }
    
    // Attach event listeners on initial load
    attachEventListeners();
    
    // ===== PORT MANAGEMENT =====
    
    // Load ports
    function loadMostUsedPorts() {
        const body = document.getElementById('portsWidgetBody');
        
        fetch('/process-monitor/api/ports/?limit=6')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayPortCards(data.ports);
                } else {
                    body.innerHTML = '<div class="alert alert-danger">Error: Port data could not be loaded</div>';
                }
            })
            .catch(error => {
                console.error('Error loading ports:', error);
                body.innerHTML = '<div class="alert alert-danger">Error loading data</div>';
            });
    }
    
    function displayPortCards(ports) {
        const body = document.getElementById('portsWidgetBody');
        
        if (ports.length === 0) {
            body.innerHTML = `<div class="empty-ports-message">${window.jsTranslations?.no_active_ports || 'No active ports found'}</div>`;
            return;
        }
        
        body.innerHTML = `
            <div class="ports-grid">
                ${ports.map(port => `
                    <div class="port-card" data-port="${port.port}">
                        <div class="port-card-left">
                            <div class="port-number">${port.port}</div>
                            <div class="port-info">
                                <div class="port-service">${port.service_name}</div>
                                <div class="port-connections-count">${port.connection_count} connections</div>
                            </div>
                        </div>
                        <div class="port-card-right">
                            <button class="btn-port-details" data-port="${port.port}">
                                <span>${window.jsTranslations?.details || 'Details'}</span>
                                <i class="fas fa-chevron-right"></i>
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        // Attach event listeners to port cards and buttons
        body.querySelectorAll('.port-card').forEach(card => {
            card.addEventListener('click', function(e) {
                // If not a button, if the card itself was clicked
                if (!e.target.closest('.btn-port-details')) {
                    const port = this.dataset.port;
                    viewPortDetails(port);
                }
            });
        });
        
        body.querySelectorAll('.btn-port-details').forEach(button => {
            button.addEventListener('click', function(e) {
                e.stopPropagation();
                const port = this.dataset.port;
                viewPortDetails(port);
            });
        });
    }
    
    // Show port details
    function viewPortDetails(port) {
        const body = document.getElementById('portDetailsBody');
        const title = document.getElementById('portDetailsTitle');
        
        title.innerHTML = `<i class="fas fa-door-open"></i> ${window.jsTranslations?.port || 'Port'} ${port} ${window.jsTranslations?.details || 'Details'}`;
        body.innerHTML = `<div class="loading"><i class="fas fa-spinner fa-spin"></i><span>${window.jsTranslations?.loading || 'Loading...'}</span></div>`;
        
        openModal(portDetailsModal);
        
        fetch(`/process-monitor/api/port/${port}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayPortDetails(data.data);
                } else {
                    body.innerHTML = `<div class="alert alert-danger">${window.jsTranslations?.error || 'Error'}: ${data.message || 'Unknown error'}</div>`;
                }
            })
            .catch(error => {
                console.error('Error loading port details:', error);
                body.innerHTML = `<div class="alert alert-danger">${window.jsTranslations?.error || 'Error'} loading data</div>`;
            });
    }
    
    function displayPortDetails(data) {
        const body = document.getElementById('portDetailsBody');
        
        body.innerHTML = `
            <div class="port-details-container">
                <!-- Process Information (First) -->
                ${data.processes.length > 0 ? `
                <div class="port-info-section">
                    <h4 class="port-section-title">Process Information</h4>
                    ${data.processes.map(proc => `
                        <div class="process-info-card">
                            <div class="process-info-header">
                                <div>
                                    <div class="process-info-name">${proc.process_name}</div>
                                    <div class="process-info-pid">PID: ${proc.pid}</div>
                                </div>
                            </div>
                            <div class="process-info-stats">
                                <div class="process-stat-item">
                                    <i class="fas fa-microchip"></i>
                                    <div>
                                        <div class="stat-label">CPU</div>
                                        <div class="stat-value">${proc.cpu_percent.toFixed(1)}%</div>
                                    </div>
                                </div>
                                <div class="process-stat-item">
                                    <i class="fas fa-memory"></i>
                                    <div>
                                        <div class="stat-label">Memory</div>
                                        <div class="stat-value">${proc.memory_mb.toFixed(1)} MB</div>
                                    </div>
                                </div>
                                <div class="process-stat-item">
                                    <i class="fas fa-arrow-down"></i>
                                    <div>
                                        <div class="stat-label">Read</div>
                                        <div class="stat-value">${proc.io_read_formatted}</div>
                                    </div>
                                </div>
                                <div class="process-stat-item">
                                    <i class="fas fa-arrow-up"></i>
                                    <div>
                                        <div class="stat-label">Written</div>
                                        <div class="stat-value">${proc.io_write_formatted}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                ` : ''}
                
                <!-- Port Information -->
                <div class="port-info-section">
                    <h4 class="port-section-title">Port Information</h4>
                    <div class="port-info-grid">
                        <div class="info-item">
                            <span class="info-label">Port Number</span>
                            <span class="info-value">${data.port}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Service</span>
                            <span class="info-value">${data.service_name}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Total Connections</span>
                            <span class="info-value">${data.total_connections}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Connection Details -->
                ${data.connections.length > 0 ? `
                <div class="port-info-section">
                    <h4 class="port-section-title">Connection Details</h4>
                    <div class="table-wrapper">
                        <table class="port-details-table">
                            <thead>
                                <tr>
                                    <th>Local Address</th>
                                    <th>Remote Address</th>
                                    <th>Status</th>
                                    <th>PID</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.connections.map(conn => `
                                    <tr>
                                        <td class="address-cell">${conn.local_address}</td>
                                        <td class="address-cell">${conn.remote_address}</td>
                                        <td><span class="badge badge-status badge-${conn.status.toLowerCase()}">${conn.status}</span></td>
                                        <td><span class="pid-badge">${conn.pid}</span></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }
    
    // Show all ports
    document.getElementById('showAllPortsBtn').addEventListener('click', function() {
        const body = document.getElementById('allPortsBody');
        body.innerHTML = `<div class="loading"><i class="fas fa-spinner fa-spin"></i><span>${window.jsTranslations?.loading || 'Loading...'}</span></div>`;
        
        openModal(allPortsModal);
        
        // Request all ports with a high limit (9999 to get all)
        fetch('/process-monitor/api/ports/?limit=9999')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayAllPorts(data.ports);
                } else {
                    body.innerHTML = `<div class="alert alert-danger">${window.jsTranslations?.error || 'Error'}: Port data could not be loaded</div>`;
                }
            })
            .catch(error => {
                console.error('Error loading all ports:', error);
                body.innerHTML = `<div class="alert alert-danger">${window.jsTranslations?.error || 'Error'} loading data</div>`;
            });
    });
    
    function displayAllPorts(ports) {
        const body = document.getElementById('allPortsBody');
        
        if (ports.length === 0) {
            body.innerHTML = `<div class="alert alert-info">${window.jsTranslations?.no_active_ports || 'No active ports found'}</div>`;
            return;
        }
        
        body.innerHTML = `
            <div class="ports-grid ports-grid-full">
                ${ports.map(port => `
                    <div class="port-card" data-port="${port.port}">
                        <div class="port-card-left">
                            <div class="port-number">${port.port}</div>
                            <div class="port-info">
                                <div class="port-service">${port.service_name}</div>
                                <div class="port-connections-count">${port.connection_count} connections</div>
                            </div>
                        </div>
                        <div class="port-card-right">
                            <button class="btn-port-details" data-port="${port.port}">
                                <span>${window.jsTranslations?.details || 'Details'}</span>
                                <i class="fas fa-chevron-right"></i>
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        // Attach event listeners to port cards and buttons
        body.querySelectorAll('.port-card').forEach(card => {
            card.addEventListener('click', function(e) {
                if (!e.target.closest('.btn-port-details')) {
                    const port = this.dataset.port;
                    closeModal(allPortsModal);
                    viewPortDetails(port);
                }
            });
        });
        
        body.querySelectorAll('.btn-port-details').forEach(button => {
            button.addEventListener('click', function(e) {
                e.stopPropagation();
                const port = this.dataset.port;
                closeModal(allPortsModal);
                viewPortDetails(port);
            });
        });
    }
    
    // NOTE: loadMostUsedPorts() is no longer needed
    // WebSocket automatically sends data
    
    // NOTE: Connection Search functionality has been moved to search.js
    // All search-related code is now in a separate module
    
    // Close WebSocket before page unload
    window.addEventListener('beforeunload', function() {
        if (ws) {
            ws.close();
        }
    });
});

