/**
 * Process Monitor - PID Group Module
 * PID'e göre süreçleri grupla ve göster
 */

(function() {
    'use strict';
    
    // Modal element
    let pidGroupViewModal = null;
    let pidGroupViewBody = null;
    
    /**
     * Initialize PID Group View Module
     */
    function initPIDGroupView() {
        pidGroupViewModal = document.getElementById('pidGroupViewModal');
        pidGroupViewBody = document.getElementById('pidGroupViewBody');
        
        // Buton event listener
        const pidGroupViewBtn = document.getElementById('pidGroupViewBtn');
        if (pidGroupViewBtn) {
            pidGroupViewBtn.addEventListener('click', showPIDGroupView);
        }
        
        console.log('✅ PID Group View module initialized');
    }
    
    /**
     * Show PID Group View Modal
     */
    function showPIDGroupView() {
        if (!pidGroupViewModal || !pidGroupViewBody) {
            console.error('PID Group View modal elements not found');
            return;
        }
        
        // Modal'ı aç
        pidGroupViewModal.classList.add('active');
        
        // Loading göster
        pidGroupViewBody.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Loading PID groups...</span>
            </div>
        `;
        
        // Verileri çek
        fetchPIDGroupedProcesses();
    }
    
    /**
     * Fetch PID Grouped Processes from API
     */
    async function fetchPIDGroupedProcesses() {
        try {
            const response = await fetch('/process-monitor/api/pid-grouped/');
            const data = await response.json();
            
            if (data.success) {
                displayPIDGroupedProcesses(data.processes, data.statistics);
            } else {
                showError('Failed to load PID grouped processes: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error fetching PID grouped processes:', error);
            showError('Network error occurred while loading PID groups');
        }
    }
    
    /**
     * Display PID Grouped Processes
     */
    function displayPIDGroupedProcesses(processes, statistics) {
        if (!processes || processes.length === 0) {
            pidGroupViewBody.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <span>No processes with connections found</span>
                </div>
            `;
            return;
        }
        
        // Statistics summary
        const summaryHtml = statistics ? `
            <div class="search-results-summary" style="margin-bottom: 24px;">
                <div class="summary-card">
                    <div class="summary-card-value">${statistics.total_processes || 0}</div>
                    <div class="summary-card-label">Total PIDs</div>
                </div>
                <div class="summary-card">
                    <div class="summary-card-value">${statistics.total_connections || 0}</div>
                    <div class="summary-card-label">Total Connections</div>
                </div>
                <div class="summary-card">
                    <div class="summary-card-value">${statistics.total_cpu_percent || 0}%</div>
                    <div class="summary-card-label">Total CPU</div>
                </div>
                <div class="summary-card">
                    <div class="summary-card-value">${(statistics.total_memory_mb || 0).toFixed(1)} MB</div>
                    <div class="summary-card-label">Total Memory</div>
                </div>
            </div>
        ` : '';
        
        // Build process cards HTML
        let processCardsHtml = '';
        
        for (const process of processes) {
            const protocolBadges = Object.entries(process.protocols || {})
                .map(([protocol, count]) => `<span class="badge badge-protocol">${protocol} (${count})</span>`)
                .join(' ');
            
            const statusBadges = Object.entries(process.statuses || {})
                .map(([status, count]) => `<span class="badge badge-status badge-${status.toLowerCase()}">${status} (${count})</span>`)
                .join(' ');
            
            processCardsHtml += `
                <div class="group-card">
                    <div class="group-card-header">
                        <div class="group-card-title">
                            <i class="fas fa-desktop"></i>
                            ${escapeHtml(process.process_name)}
                        </div>
                        <div class="group-card-badge">PID: ${process.pid}</div>
                    </div>
                    
                    <div class="group-card-stats">
                        <div class="group-stat-item">
                            <span class="group-stat-value">${process.total_connections}</span>
                            <span class="group-stat-label">Connections</span>
                        </div>
                        <div class="group-stat-item">
                            <span class="group-stat-value">${process.num_threads || 0}</span>
                            <span class="group-stat-label">Threads</span>
                        </div>
                    </div>
                    
                    <div class="info-section" style="margin-bottom: 16px;">
                        <div class="info-item" style="margin-bottom: 8px;">
                            <span class="info-label">CPU Usage</span>
                            <span class="info-value">${(process.cpu_percent || 0).toFixed(1)}%</span>
                        </div>
                        <div class="info-item" style="margin-bottom: 8px;">
                            <span class="info-label">Memory Usage</span>
                            <span class="info-value">${(process.memory_mb || 0).toFixed(1)} MB</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">User</span>
                            <span class="info-value">${escapeHtml(process.username || 'N/A')}</span>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 12px;">
                        <strong style="font-size: 13px; color: #4a5568; display: block; margin-bottom: 8px;">
                            <i class="fas fa-network-wired"></i> Protocols:
                        </strong>
                        <div>${protocolBadges || '<span style="color: #a0aec0;">N/A</span>'}</div>
                    </div>
                    
                    <div style="margin-bottom: 12px;">
                        <strong style="font-size: 13px; color: #4a5568; display: block; margin-bottom: 8px;">
                            <i class="fas fa-info-circle"></i> Statuses:
                        </strong>
                        <div>${statusBadges || '<span style="color: #a0aec0;">N/A</span>'}</div>
                    </div>
                    
                    <div class="connections-compact-box">
                        <div class="compact-box-header">
                            <i class="fas fa-plug"></i>
                            Connections (${process.total_connections})
                        </div>
                        <div class="compact-box-body">
                            ${buildCompactConnectionsList(process.connections)}
                        </div>
                    </div>
                    
                    <div style="margin-top: 12px; text-align: center;">
                        <button class="btn-secondary btn-sm view-process-details-from-pid" data-pid="${process.pid}" style="width: 100%;">
                            <i class="fas fa-info-circle"></i>
                            View Full Process Details
                        </button>
                    </div>
                </div>
            `;
        }
        
        pidGroupViewBody.innerHTML = `
            ${summaryHtml}
            <div class="group-grid">
                ${processCardsHtml}
            </div>
        `;
        
        // Add event listeners to "View Full Process Details" buttons
        const detailButtons = pidGroupViewBody.querySelectorAll('.view-process-details-from-pid');
        detailButtons.forEach(button => {
            button.addEventListener('click', function() {
                const pid = this.getAttribute('data-pid');
                
                // Close PID Group View modal first
                if (pidGroupViewModal && window.closeModal) {
                    window.closeModal(pidGroupViewModal);
                }
                
                // Then open Process Details modal
                if (window.viewProcessDetails) {
                    window.viewProcessDetails(pid);
                }
            });
        });
    }
    
    /**
     * Build compact connections list HTML
     */
    function buildCompactConnectionsList(connections) {
        if (!connections || connections.length === 0) {
            return '<div style="padding: 12px; text-align: center; color: #a0aec0;">No connections</div>';
        }
        
        return connections.map(conn => `
            <div class="compact-connection-item">
                <span class="badge badge-sm badge-protocol">${conn.protocol}</span>
                <span class="compact-address">${escapeHtml(conn.local_address)}</span>
                <span style="color: #a0aec0;">→</span>
                <span class="compact-address">${escapeHtml(conn.remote_address)}</span>
                <span class="badge badge-sm badge-status badge-${conn.status.toLowerCase()}">${conn.status}</span>
            </div>
        `).join('');
    }
    
    /**
     * Show error message
     */
    function showError(message) {
        pidGroupViewBody.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${escapeHtml(message)}</span>
            </div>
        `;
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPIDGroupView);
    } else {
        initPIDGroupView();
    }
    
})();

