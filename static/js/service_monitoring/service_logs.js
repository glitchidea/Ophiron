/**
 * Service Logs - JavaScript Module
 * Handles service logs and system logs viewing
 */

(function() {
    'use strict';
    
    let logsModal, systemLogsModal;
    let currentService = null;
    let logsContent, systemLogsContent;
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
    function initialize() {
        // Get modal elements
        logsModal = document.getElementById('serviceLogsModal');
        systemLogsModal = document.getElementById('systemLogsModal');
        logsContent = document.getElementById('logsContent');
        systemLogsContent = document.getElementById('systemLogsContent');
        
        // Initialize event listeners
        initializeEventListeners();
        
        console.log('Service Logs module initialized successfully');
    }
    
    function initializeEventListeners() {
        // Service logs controls
        const refreshLogsBtn = document.getElementById('refreshLogs');
        const clearLogsBtn = document.getElementById('clearLogs');
        const logsServiceFilter = document.getElementById('logsServiceFilter');
        const logsLines = document.getElementById('logsLines');
        
        if (refreshLogsBtn) {
            refreshLogsBtn.addEventListener('click', refreshServiceLogs);
        }
        
        if (clearLogsBtn) {
            clearLogsBtn.addEventListener('click', clearServiceLogs);
        }
        
        if (logsServiceFilter) {
            logsServiceFilter.addEventListener('change', handleServiceFilterChange);
        }
        
        if (logsLines) {
            logsLines.addEventListener('change', refreshServiceLogs);
        }
        
        // System logs controls
        const refreshSystemLogsBtn = document.getElementById('refreshSystemLogs');
        const logPage = document.getElementById('logPage');
        const logPerPage = document.getElementById('logPerPage');
        
        if (refreshSystemLogsBtn) {
            refreshSystemLogsBtn.addEventListener('click', refreshSystemLogs);
        }
        
        if (logPage) {
            logPage.addEventListener('change', refreshSystemLogs);
        }
        
        if (logPerPage) {
            logPerPage.addEventListener('change', refreshSystemLogs);
        }
        
        // Modal close handlers
        setupModalCloseHandlers();
    }
    
    function setupModalCloseHandlers() {
        const modals = [logsModal, systemLogsModal];
        
        modals.forEach(modal => {
            if (modal) {
                const closeBtn = modal.querySelector('.modal-close');
                if (closeBtn) {
                    closeBtn.addEventListener('click', () => closeModal(modal));
                }
                
                // Close on backdrop click
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        closeModal(modal);
                    }
                });
            }
        });
    }
    
    function openLogs(serviceName = null) {
        currentService = serviceName;
        
        if (!logsModal) {
            console.error('Service logs modal not found');
            return;
        }
        
        // Load available services for filter
        loadAvailableServices();
        
        // Set service filter if provided
        if (serviceName && logsServiceFilter) {
            logsServiceFilter.value = serviceName;
        }
        
        showModal(logsModal);
        
        // Load logs
        refreshServiceLogs();
    }
    
    function loadAvailableServices() {
        // This would typically load from the service list
        // For now, we'll use a placeholder
        if (logsServiceFilter) {
            logsServiceFilter.innerHTML = '<option value="">All Services</option>';
        }
    }
    
    function refreshServiceLogs() {
        if (!logsContent) return;
        
        // Show loading state
        logsContent.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Loading logs...</span>
            </div>
        `;
        
        const serviceName = logsServiceFilter ? logsServiceFilter.value : currentService;
        const lines = logsLines ? logsLines.value : 50;
        
        if (!serviceName) {
            logsContent.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-info-circle"></i>
                    <p>Please select a service to view logs</p>
                </div>
            `;
            return;
        }
        
        fetch(`/service-monitoring/api/service/${serviceName}/logs/?lines=${lines}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderServiceLogs(data.logs);
                } else {
                    showError('Failed to load logs: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error loading service logs:', error);
                showError('Failed to load logs: ' + error.message);
            });
    }
    
    function renderServiceLogs(logs) {
        if (!logsContent) return;
        
        if (!logs || logs.length === 0) {
            logsContent.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-alt"></i>
                    <p>No logs available for this service</p>
                </div>
            `;
            return;
        }
        
        const logsHtml = logs.map(log => {
            // Parse log line for better formatting
            const timestamp = extractTimestamp(log);
            const level = extractLogLevel(log);
            const message = extractLogMessage(log);
            
            return `
                <div class="log-entry ${level}">
                    <span class="log-timestamp">${timestamp}</span>
                    <span class="log-level">${level}</span>
                    <span class="log-message">${message}</span>
                </div>
            `;
        }).join('');
        
        logsContent.innerHTML = `
            <div class="logs-container">
                <div class="logs-header">
                    <span>Service Logs (${logs.length} entries)</span>
                    <button class="btn-copy-logs" onclick="copyLogs()">
                        <i class="fas fa-copy"></i>
                        Copy
                    </button>
                </div>
                <div class="logs-list">
                    ${logsHtml}
                </div>
            </div>
        `;
    }
    
    function extractTimestamp(log) {
        // Try to extract timestamp from log line
        const timestampMatch = log.match(/^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})/);
        return timestampMatch ? timestampMatch[1] : '';
    }
    
    function extractLogLevel(log) {
        // Try to extract log level
        if (log.includes('ERROR') || log.includes('FATAL')) return 'error';
        if (log.includes('WARN')) return 'warning';
        if (log.includes('INFO')) return 'info';
        if (log.includes('DEBUG')) return 'debug';
        return 'info';
    }
    
    function extractLogMessage(log) {
        // Remove timestamp and level from log message
        return log.replace(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s*/, '')
                  .replace(/^(ERROR|WARN|INFO|DEBUG|FATAL)\s*/, '');
    }
    
    function clearServiceLogs() {
        if (!logsContent) return;
        
        logsContent.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-trash"></i>
                <p>Logs cleared</p>
            </div>
        `;
    }
    
    function handleServiceFilterChange() {
        refreshServiceLogs();
    }
    
    function openSystemLogs() {
        if (!systemLogsModal) {
            console.error('System logs modal not found');
            return;
        }
        
        showModal(systemLogsModal);
        refreshSystemLogs();
    }
    
    function refreshSystemLogs() {
        if (!systemLogsContent) return;
        
        // Show loading state
        systemLogsContent.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Loading system logs...</span>
            </div>
        `;
        
        const page = logPage ? logPage.value : 1;
        const perPage = logPerPage ? logPerPage.value : 50;
        
        fetch(`/service-monitoring/api/logs/?page=${page}&per_page=${perPage}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderSystemLogs(data.logs, data.pagination);
                } else {
                    showError('Failed to load system logs: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error loading system logs:', error);
                showError('Failed to load system logs: ' + error.message);
            });
    }
    
    function renderSystemLogs(logs, pagination) {
        if (!systemLogsContent) return;
        
        if (!logs || logs.length === 0) {
            systemLogsContent.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-clipboard-list"></i>
                    <p>No system logs available</p>
                </div>
            `;
            return;
        }
        
        const logsHtml = logs.map(log => {
            const statusClass = log.status === 'success' ? 'success' : 
                              log.status === 'error' ? 'error' : 'warning';
            
            return `
                <div class="system-log-entry ${statusClass}">
                    <div class="log-header">
                        <span class="log-service">${log.service_name}</span>
                        <span class="log-action">${log.action}</span>
                        <span class="log-status">${log.status}</span>
                        <span class="log-timestamp">${formatTimestamp(log.timestamp)}</span>
                    </div>
                    <div class="log-message">${log.message}</div>
                    ${log.user ? `<div class="log-user">User: ${log.user}</div>` : ''}
                </div>
            `;
        }).join('');
        
        systemLogsContent.innerHTML = `
            <div class="system-logs-container">
                <div class="logs-header">
                    <span>System Logs (${pagination.total_count} entries)</span>
                </div>
                <div class="system-logs-list">
                    ${logsHtml}
                </div>
                ${renderPagination(pagination)}
            </div>
        `;
    }
    
    function renderPagination(pagination) {
        if (!pagination || pagination.total_pages <= 1) return '';
        
        let paginationHtml = '<div class="pagination">';
        
        // Previous button
        if (pagination.has_previous) {
            paginationHtml += `<button class="btn-page" data-page="${pagination.current_page - 1}">Previous</button>`;
        }
        
        // Page numbers
        for (let i = 1; i <= pagination.total_pages; i++) {
            const isActive = i === pagination.current_page;
            paginationHtml += `<button class="btn-page ${isActive ? 'active' : ''}" data-page="${i}">${i}</button>`;
        }
        
        // Next button
        if (pagination.has_next) {
            paginationHtml += `<button class="btn-page" data-page="${pagination.current_page + 1}">Next</button>`;
        }
        
        paginationHtml += '</div>';
        
        // Add event listeners to pagination buttons
        setTimeout(() => {
            document.querySelectorAll('.btn-page').forEach(btn => {
                btn.addEventListener('click', () => {
                    const page = btn.dataset.page;
                    if (logPage) {
                        logPage.value = page;
                        refreshSystemLogs();
                    }
                });
            });
        }, 100);
        
        return paginationHtml;
    }
    
    function formatTimestamp(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleString();
        } catch (e) {
            return timestamp;
        }
    }
    
    function copyLogs() {
        const logsList = document.querySelector('.logs-list');
        if (logsList) {
            const logsText = logsList.textContent;
            navigator.clipboard.writeText(logsText).then(() => {
                showSuccess('Logs copied to clipboard');
            }).catch(() => {
                showError('Failed to copy logs');
            });
        }
    }
    
    function showModal(modal) {
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }
    
    function closeModal(modal) {
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    function showSuccess(message) {
        // You can implement a toast notification here
        alert('Success: ' + message); // Temporary fallback
    }
    
    function showError(message) {
        // You can implement a toast notification here
        alert('Error: ' + message); // Temporary fallback
    }
    
    // Public API
    window.ServiceLogs = {
        openLogs: openLogs,
        openSystemLogs: openSystemLogs
    };
    
})();
