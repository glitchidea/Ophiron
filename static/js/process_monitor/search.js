/**
 * Process Monitor - Connection Search Module
 * Handles connection search functionality with detailed reporting
 */

(function() {
    'use strict';
    
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeSearch);
    } else {
        initializeSearch();
    }
    
    function initializeSearch() {
        // ===== SEARCH ELEMENTS =====
        const searchTypeButtons = document.querySelectorAll('.search-type-btn');
        const searchInput = document.getElementById('searchInput');
        const searchHelpText = document.getElementById('searchHelpText');
        const searchBtn = document.getElementById('searchBtn');
        const searchResultsModal = document.getElementById('searchResultsModal');
        
        // Check if search elements exist
        if (!searchTypeButtons.length || !searchInput || !searchBtn || !searchResultsModal) {
            console.warn('Search elements not found. Search module will not initialize.');
            return;
        }
        
        // ===== SEARCH STATE =====
        let currentSearchType = 'pid';
        
        // ===== SEARCH CONFIGURATION =====
        const searchPlaceholders = {
            'pid': 'Enter PID to search...',
            'port': 'Enter port number to search...',
            'ip': 'Enter IP address to search...'
        };
        
        const searchHelpTexts = {
            'pid': 'Search for all connections related to a specific PID',
            'port': 'Search for all connections using a specific port',
            'ip': 'Search for all connections from/to a specific IP address'
        };
        
        // ===== EVENT LISTENERS =====
        
        // Handle search type selection
        searchTypeButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                searchTypeButtons.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                currentSearchType = this.dataset.type;
                
                // Update placeholder and help text
                searchInput.placeholder = searchPlaceholders[currentSearchType];
                searchHelpText.textContent = searchHelpTexts[currentSearchType];
                searchInput.value = '';
                searchInput.focus();
            });
        });
        
        // Handle search button click
        searchBtn.addEventListener('click', performSearch);
        
        // Handle Enter key in search input
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
        
        // ===== SEARCH FUNCTIONS =====
        
        /**
         * Perform connection search
         */
        function performSearch() {
            const searchValue = searchInput.value.trim();
            
            if (!searchValue) {
                // Use global notification function from main script
                if (typeof window.showNotification === 'function') {
                    window.showNotification('Please enter a search value', 'warning');
                } else {
                    alert('Please enter a search value');
                }
                return;
            }
            
            // Open modal and show loading
            if (typeof window.openModal === 'function') {
                window.openModal(searchResultsModal);
            } else {
                searchResultsModal.classList.add('active');
            }
            
            const resultsBody = document.getElementById('searchResultsBody');
            resultsBody.innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Searching...</span>
                </div>
            `;
            
            // Make search request
            fetch(`/process-monitor/api/search/?type=${currentSearchType}&value=${encodeURIComponent(searchValue)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        if (data.found) {
                            displaySearchResults(data.data);
                        } else {
                            displayNoResults(currentSearchType, searchValue);
                        }
                    } else {
                        resultsBody.innerHTML = `
                            <div class="alert alert-error">
                                <i class="fas fa-exclamation-circle"></i>
                                <span>Search failed: ${data.error || 'Unknown error'}</span>
                            </div>
                        `;
                    }
                })
                .catch(error => {
                    console.error('Search error:', error);
                    resultsBody.innerHTML = `
                        <div class="alert alert-error">
                            <i class="fas fa-exclamation-circle"></i>
                            <span>Search failed: ${error.message}</span>
                        </div>
                    `;
                });
        }
        
        /**
         * Display search results in modal
         * @param {Object} data - Search results data
         */
        function displaySearchResults(data) {
            const resultsBody = document.getElementById('searchResultsBody');
            const resultsTitle = document.getElementById('searchResultsTitle');
            
            // Update title with download buttons
            const searchTypeLabel = currentSearchType.toUpperCase();
            resultsTitle.innerHTML = `
                <span>Search Results: ${searchTypeLabel} = ${data.search_value}</span>
                <div class="download-options">
                    <button class="btn-download-report btn-simple" onclick="window.ProcessMonitorSearch.downloadReport('${currentSearchType}', '${data.search_value}', 'simple')" title="Download Simple Report">
                        <i class="fas fa-file-pdf"></i>
                        Simple Report
                    </button>
                    <button class="btn-download-report btn-detailed" onclick="window.ProcessMonitorSearch.downloadReport('${currentSearchType}', '${data.search_value}', 'detailed')" title="Download Detailed Report">
                        <i class="fas fa-file-alt"></i>
                        Detailed Report
                    </button>
                </div>
            `;
            
            let html = '';
            
            // Summary cards
            html += `
                <div class="search-results-summary">
                    <div class="summary-card">
                        <div class="summary-card-value">${data.summary.total_connections}</div>
                        <div class="summary-card-label">Total Connections</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-card-value">${data.summary.unique_processes}</div>
                        <div class="summary-card-label">Unique Processes</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-card-value">${data.summary.unique_ports}</div>
                        <div class="summary-card-label">Unique Ports</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-card-value">${data.summary.unique_ips}</div>
                        <div class="summary-card-label">Unique IPs</div>
                    </div>
                </div>
            `;
            
            // Process details (if available)
            if (Object.keys(data.process_details).length > 0) {
                html += `
                    <div class="search-results-section">
                        <div class="search-section-header">
                            <i class="fas fa-microchip"></i>
                            <h4>Process Information</h4>
                            <span class="search-section-badge">${Object.keys(data.process_details).length}</span>
                        </div>
                        <div class="search-process-grid">
                            ${Object.entries(data.process_details).map(([pid, proc]) => `
                                <div class="search-process-card">
                                    <div class="search-process-header">
                                        <div class="search-process-name">${proc.name || 'Unknown'}</div>
                                        <div class="search-process-pid">PID: ${pid}</div>
                                    </div>
                                    <div class="search-process-stats">
                                        <div class="search-stat-item">
                                            <i class="fas fa-microchip"></i>
                                            <span class="search-stat-label">CPU:</span>
                                            <span class="search-stat-value">${proc.cpu_percent ? proc.cpu_percent.toFixed(1) : '0.0'}%</span>
                                        </div>
                                        <div class="search-stat-item">
                                            <i class="fas fa-memory"></i>
                                            <span class="search-stat-label">Memory:</span>
                                            <span class="search-stat-value">${proc.memory_percent ? proc.memory_percent.toFixed(1) : '0.0'}%</span>
                                        </div>
                                        <div class="search-stat-item">
                                            <i class="fas fa-user"></i>
                                            <span class="search-stat-label">User:</span>
                                            <span class="search-stat-value">${proc.username || 'N/A'}</span>
                                        </div>
                                        <div class="search-stat-item">
                                            <i class="fas fa-power-off"></i>
                                            <span class="search-stat-label">Status:</span>
                                            <span class="search-stat-value">${proc.status || 'N/A'}</span>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            // Port details (if available)
            if (data.port_details && data.port_details.length > 0) {
                html += `
                    <div class="search-results-section">
                        <div class="search-section-header">
                            <i class="fas fa-network-wired"></i>
                            <h4>Port Usage</h4>
                            <span class="search-section-badge">${data.port_details.length}</span>
                        </div>
                        <div class="search-process-grid">
                            ${data.port_details.map(port => `
                                <div class="search-process-card">
                                    <div class="search-process-header">
                                        <div class="search-process-name">Port ${port.port}</div>
                                        <div class="search-process-pid">${port.service_name}</div>
                                    </div>
                                    <div class="search-process-stats">
                                        <div class="search-stat-item">
                                            <i class="fas fa-link"></i>
                                            <span class="search-stat-label">Connections:</span>
                                            <span class="search-stat-value">${port.connection_count}</span>
                                        </div>
                                        <div class="search-stat-item">
                                            <i class="fas fa-cogs"></i>
                                            <span class="search-stat-label">Processes:</span>
                                            <span class="search-stat-value">${port.processes.join(', ')}</span>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            // Connections table
            html += `
                <div class="search-results-section">
                    <div class="search-section-header">
                        <i class="fas fa-exchange-alt"></i>
                        <h4>All Connections</h4>
                        <span class="search-section-badge">${data.connections.length}</span>
                    </div>
                    <div class="table-wrapper">
                        <table class="search-connections-table">
                            <thead>
                                <tr>
                                    <th>PID</th>
                                    <th>Process</th>
                                    <th>Protocol</th>
                                    <th>Local Address</th>
                                    <th>Remote Address</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.connections.map(conn => `
                                    <tr>
                                        <td><span class="pid-badge">${conn.pid || '-'}</span></td>
                                        <td>${conn.process_name || 'Unknown'}</td>
                                        <td><span class="badge badge-protocol">${conn.protocol}</span></td>
                                        <td class="address-cell">${conn.local_address}</td>
                                        <td class="address-cell">${conn.remote_address}</td>
                                        <td><span class="badge badge-status badge-${conn.status.toLowerCase()}">${conn.status}</span></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
            
            resultsBody.innerHTML = html;
        }
        
        /**
         * Display no results message
         * @param {string} searchType - Type of search
         * @param {string} searchValue - Search value
         */
        function displayNoResults(searchType, searchValue) {
            const resultsBody = document.getElementById('searchResultsBody');
            const resultsTitle = document.getElementById('searchResultsTitle');
            
            resultsTitle.textContent = `Search Results: No matches found`;
            
            resultsBody.innerHTML = `
                <div class="search-no-results">
                    <i class="fas fa-search"></i>
                    <p>No connections found for ${searchType}: <strong>${searchValue}</strong></p>
                    <p style="margin-top: 12px; font-size: 14px; color: #a0aec0;">Try searching with a different value or type.</p>
                </div>
            `;
        }
        
        /**
         * Download search report as PDF document
         * @param {string} searchType - Type of search
         * @param {string} searchValue - Search value
         * @param {string} reportType - Type of report (simple/detailed)
         */
        function downloadReport(searchType, searchValue, reportType = 'simple') {
            // Show notification
            if (typeof window.showNotification === 'function') {
                const reportTypeLabel = reportType === 'detailed' ? 'Detailed' : 'Simple';
                window.showNotification(`Generating ${reportTypeLabel} report...`, 'info');
            }
            
            // Create download URL with report type parameter
            const url = `/process-monitor/api/search/download-report/?type=${searchType}&value=${encodeURIComponent(searchValue)}&report_type=${reportType}`;
            
            // Create temporary link and trigger download
            const link = document.createElement('a');
            link.href = url;
            const reportTypeSuffix = reportType === 'detailed' ? '_Detailed' : '_Simple';
            link.download = `ProcessMonitor_Report_${searchType}_${searchValue}${reportTypeSuffix}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Show success notification after a delay
            setTimeout(() => {
                if (typeof window.showNotification === 'function') {
                    const reportTypeLabel = reportType === 'detailed' ? 'Detailed' : 'Simple';
                    window.showNotification(`${reportTypeLabel} report downloaded successfully`, 'success');
                }
            }, 1000);
        }
        
        // ===== PUBLIC API =====
        // Expose downloadReport function globally for inline onclick handlers
        window.ProcessMonitorSearch = {
            downloadReport: downloadReport
        };
        
        console.log('Process Monitor Search module initialized successfully');
    }
})();

