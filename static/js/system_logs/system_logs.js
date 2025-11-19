function renderTabs(categories, onChange) {
    const tabsRoot = document.getElementById('logsTabs');
    if (!tabsRoot) return;
    const labels = [
        { key: 'all', label: 'All Logs' },
        { key: 'system', label: 'System Events' },
        { key: 'kernel', label: 'Kernel Panic' },
        { key: 'cron', label: 'Cron Jobs' },
        { key: 'startup', label: 'Startup/Shutdown' },
        { key: 'critical', label: 'Critical Services' }
    ];
    tabsRoot.innerHTML = labels.map((t,i)=>`<button class="logs-tab ${i===0?'active':''}" data-key="${t.key}">${t.label}</button>`).join('');
    tabsRoot.querySelectorAll('.logs-tab').forEach(btn=>{
        btn.addEventListener('click', ()=>{
            tabsRoot.querySelectorAll('.logs-tab').forEach(b=>b.classList.remove('active'));
            btn.classList.add('active');
            onChange(btn.getAttribute('data-key'));
        });
    });
}

function updateLogDisplay(logsByCategoryOrArray) {
    const container = document.getElementById('logsContainer');
    if (!container) return;
    if (!logsByCategoryOrArray) { 
        container.innerHTML = '<div class="text-muted">No logs found.</div>'; 
        return; 
    }

    // Normalize
    let data = logsByCategoryOrArray;
    if (Array.isArray(logsByCategoryOrArray)) {
        data = { all: logsByCategoryOrArray };
    }

    async function selectAndRender(category) {
        let rows = [];
        if (category === 'all') {
            // Tüm kategorilerden logları birleştir
            rows = [];
            Object.keys(data).forEach(key => {
                if (Array.isArray(data[key])) {
                    rows = rows.concat(data[key]);
                }
            });
            // Tarihe göre sırala (en yeni önce)
            rows.sort((a, b) => {
                const timeA = extractTimestamp(a);
                const timeB = extractTimestamp(b);
                return timeB - timeA;
            });
        } else if (category === 'startup') {
            rows = (data.system || []).filter(l => /boot|shutdown|started|stopped/i.test(l));
        } else if (category === 'critical') {
            rows = (data.system || []).filter(l => /(service|daemon|systemd|failed|error)/i.test(l));
        } else if (['error','warning','info','debug'].includes(category)) {
            try {
                const r = await fetch(`/system-logs/level/${category}/`);
                const j = await r.json();
                rows = j.logs || [];
            } catch(e) { rows = []; }
        } else {
            // Kategori bazlı logları göster
            rows = data[category] || [];
        }
        
        if (!rows.length) { 
            container.innerHTML = '<div class="text-muted">No logs found for this category.</div>'; 
            return; 
        }
        
        // Enhanced log rendering with categorization
        container.innerHTML = rows.map(log => {
            const logClass = getLogLevelClass(log);
            return `<div class="log-entry ${logClass}">${escapeHtml(log)}</div>`;
        }).join('');
        
        // Update log count
        updateLogCount(rows.length);
        
        // Auto scroll if enabled
        if (document.getElementById('autoScroll')?.classList.contains('active')) {
            container.scrollTop = container.scrollHeight;
        }
    }

    // Available categories
    const availableCategories = Object.keys(data);
    renderTabs(availableCategories, selectAndRender);
    selectAndRender('all');
}

function getLogLevelClass(log) {
    const logLower = log.toLowerCase();
    if (logLower.includes('error') || logLower.includes('critical') || logLower.includes('fatal')) {
        return 'error';
    } else if (logLower.includes('warning') || logLower.includes('warn')) {
        return 'warning';
    } else if (logLower.includes('info') || logLower.includes('information')) {
        return 'info';
    } else if (logLower.includes('debug')) {
        return 'debug';
    }
    return '';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function extractTimestamp(log) {
    // Log satırından timestamp çıkarmaya çalış
    const timestampPatterns = [
        /(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})/,  // ISO format
        /(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/,  // Standard format
        /(\w{3} \d{1,2} \d{2}:\d{2}:\d{2})/,      // Short format
        /(\d{2}:\d{2}:\d{2})/                      // Time only
    ];
    
    for (const pattern of timestampPatterns) {
        const match = log.match(pattern);
        if (match) {
            const date = new Date(match[1]);
            if (!isNaN(date.getTime())) {
                return date.getTime();
            }
        }
    }
    
    // Eğer timestamp bulunamazsa, log sırasına göre sırala
    return 0;
}

function updateLogCount(count) {
    const logCountEl = document.getElementById('logCount');
    if (logCountEl) {
        logCountEl.textContent = count;
    }
}


function animateNumber(element, start, end, duration) {
    const startTime = performance.now();
    const difference = end - start;
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function (ease-out)
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const currentValue = Math.round(start + (difference * easeOut));
        
        element.textContent = currentValue;
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }
    
    requestAnimationFrame(updateNumber);
}

// filters-grid removed

function analyzeLogPatterns() {
    fetch('/system-logs/analyze/')
        .then(r => r.json())
        .then(data => {
            updateAnalysisCharts(data);
            const modal = new bootstrap.Modal(document.getElementById('analysisModal'));
            modal.show();
        });
}

function exportLogs() {
    const format = 'csv';
    fetch(`/system-logs/export/?format=${format}`)
        .then(r => r.json())
        .then(data => {
            const link = document.createElement('a');
            link.href = `/media/exports/${data.filename}`;
            link.download = data.filename;
            link.click();
        });
}

function refreshLogs() {
    fetch('/system-logs/api/', {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
        credentials: 'same-origin'
    })
        .then(r => r.json())
        .then(data => {
            // Use categories from backend if available
            const categorized = data.categories || {
                system: Array.isArray(data.logs) ? data.logs : (data.system || data.logs || []),
                kernel: data.kernel || [],
                cron: data.cron || [],
                auth: data.auth || [],
                daemon: data.daemon || [],
                boot: data.boot || []
            };
            
            updateLogDisplay(categorized);
            const el = document.getElementById('lastUpdate');
            if (el) el.textContent = new Date().toLocaleTimeString();
        })
        .catch(err => console.error('Error occurred while refreshing logs:', err));
}

// Enhanced Analysis Charts
let errorChart, timelineChart, errorCategoriesChart, hourlyDistributionChart, serviceErrorsChart;

function initializeCharts() {
    // Error levels chart
    const errorCtx = document.getElementById('errorChart');
    if (errorCtx) {
        errorChart = new Chart(errorCtx.getContext('2d'), {
            type: 'bar',
            data: { 
                labels: ['Error', 'Warning', 'Info', 'Debug'], 
                datasets: [{ 
                    data: [0,0,0,0], 
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)', 
                        'rgba(255, 206, 86, 0.8)', 
                        'rgba(75, 192, 192, 0.8)', 
                        'rgba(153, 102, 255, 0.8)'
                    ] 
                }] 
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false, 
                plugins: { legend: { display: false } }, 
                scales: { 
                    y: { 
                        beginAtZero: true, 
                        ticks: { 
                            stepSize: 5,
                            maxTicksLimit: 20
                        } 
                    } 
                } 
            }
        });
    }

    // Timeline chart
    const timelineCtx = document.getElementById('timelineChart');
    if (timelineCtx) {
        timelineChart = new Chart(timelineCtx.getContext('2d'), {
            type: 'line',
            data: { 
                labels: [], 
                datasets: [{ 
                    label: 'Log Sayısı', 
                    data: [], 
                    borderColor: 'rgba(75, 192, 192, 1)', 
                    tension: 0.1 
                }] 
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false, 
                plugins: { legend: { display: false } }, 
                scales: { 
                    y: { 
                        beginAtZero: true, 
                        ticks: { 
                            stepSize: 5,
                            maxTicksLimit: 20
                        } 
                    } 
                } 
            }
        });
    }

    // Error categories chart
    const errorCategoriesCtx = document.getElementById('errorCategoriesChart');
    if (errorCategoriesCtx) {
        errorCategoriesChart = new Chart(errorCategoriesCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['System', 'Service', 'Permission', 'Network', 'Database', 'Security', 'Other'],
                datasets: [{
                    data: [0, 0, 0, 0, 0, 0, 0],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 206, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(153, 102, 255, 0.8)',
                        'rgba(255, 159, 64, 0.8)',
                        'rgba(199, 199, 199, 0.8)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Hourly distribution chart
    const hourlyCtx = document.getElementById('hourlyDistributionChart');
    if (hourlyCtx) {
        hourlyDistributionChart = new Chart(hourlyCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: Array.from({length: 24}, (_, i) => i + ':00'),
                datasets: [{
                    label: 'Log Count',
                    data: new Array(24).fill(0),
                    backgroundColor: 'rgba(54, 162, 235, 0.8)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    // Service errors chart
    const serviceCtx = document.getElementById('serviceErrorsChart');
    if (serviceCtx) {
        serviceErrorsChart = new Chart(serviceCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Error Count',
                    data: [],
                    backgroundColor: 'rgba(255, 99, 132, 0.8)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
}

function updateAnalysisCharts(data) {
    if (!data || typeof data !== 'object') {
        console.error('Invalid data for updateAnalysisCharts:', data);
        return;
    }
    
    try {

    // Update summary cards
    const e = document.getElementById('modalErrorCount');
    if (e) e.textContent = data.error_count || 0;
    const w = document.getElementById('modalWarningCount');
    if (w) w.textContent = data.warning_count || 0;
    const i = document.getElementById('modalInfoCount');
    if (i) i.textContent = data.info_count || 0;
    const d = document.getElementById('modalDebugCount');
    if (d) d.textContent = data.debug_count || 0;

    // Update error levels chart
    if (errorChart) {
        errorChart.data.datasets[0].data = [
            data.error_count || 0, 
            data.warning_count || 0, 
            data.info_count || 0, 
            data.debug_count || 0
        ];
        errorChart.update();
    }

    // Update timeline chart
    if (timelineChart) {
        const timelineData = data.timeline_data || [];
        // Limit data points to prevent chart performance issues
        const limitedData = timelineData.slice(-30); // Last 30 points
        const formatted = limitedData.map(item => ({ 
            x: new Date(item.timestamp), 
            y: item.count || 0 
        })).sort((a,b) => a.x - b.x);
        
        timelineChart.data.labels = formatted.map(item => 
            item.x.toLocaleString('en-US', {hour:'2-digit', minute:'2-digit'})
        );
        timelineChart.data.datasets[0].data = formatted.map(item => item.y);
        timelineChart.update();
    }

    // Update error categories chart
    if (errorCategoriesChart && data.error_categories) {
        errorCategoriesChart.data.datasets[0].data = [
            data.error_categories.system || 0,
            data.error_categories.service || 0,
            data.error_categories.permission || 0,
            data.error_categories.network || 0,
            data.error_categories.database || 0,
            data.error_categories.security || 0,
            data.error_categories.other || 0
        ];
        errorCategoriesChart.update();
    }

    // Update hourly distribution chart
    if (hourlyDistributionChart && data.hourly_distribution) {
        // Limit to 24 hours to prevent performance issues
        const limitedHourlyData = data.hourly_distribution.slice(0, 24);
        hourlyDistributionChart.data.datasets[0].data = limitedHourlyData;
        hourlyDistributionChart.update();
    }

    // Update service errors chart
    if (serviceErrorsChart && data.service_stats) {
        const services = Object.keys(data.service_stats);
        const counts = Object.values(data.service_stats);
        
        serviceErrorsChart.data.labels = services.slice(0, 10); // Top 10 services
        serviceErrorsChart.data.datasets[0].data = counts.slice(0, 10);
        serviceErrorsChart.update();
    }

    // Update common errors
    const commonErrorsDiv = document.getElementById('commonErrors');
    if (commonErrorsDiv) {
        try {
            if (data && data.common_patterns && typeof data.common_patterns === 'object') {
                const patternEntries = Object.entries(data.common_patterns);
                console.log('Common patterns entries:', patternEntries);
                
                if (patternEntries.length > 0) {
                    const patterns = patternEntries
                        .filter(([pattern, count]) => pattern && typeof count === 'number' && count > 0)
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 10); // Top 10 patterns
                    
                    console.log('Filtered patterns:', patterns);
                    
                    if (patterns.length > 0) {
                        commonErrorsDiv.innerHTML = `
                            <div class="row">
                                ${patterns.map(([pattern, count], index) => 
                                    `<div class="col-md-6 mb-3">
                                        <div class="card border-danger">
                                            <div class="card-body p-2">
                                                <div class="d-flex justify-content-between align-items-center">
                                                    <small class="text-muted">#${index + 1}</small>
                                                    <span class="badge bg-danger">${count}</span>
                                                </div>
                                                <div class="mt-1">
                                                    <code class="text-dark" style="font-size: 11px; word-break: break-all;">${escapeHtml(pattern)}</code>
                                                </div>
                                            </div>
                                        </div>
                                    </div>`
                                ).join('')}
                            </div>
                        `;
                    } else {
                        commonErrorsDiv.innerHTML = '<div class="text-muted">No valid error patterns found.</div>';
                    }
                } else {
                    commonErrorsDiv.innerHTML = '<div class="text-muted">No common error patterns found.</div>';
                }
            } else {
                commonErrorsDiv.innerHTML = '<div class="text-muted">No common error patterns found.</div>';
            }
        } catch (error) {
            console.error('Error rendering common patterns:', error);
            commonErrorsDiv.innerHTML = '<div class="alert alert-warning">Error displaying common patterns.</div>';
        }
    }
    } catch (error) {
        console.error('Error in updateAnalysisCharts:', error);
        // Don't show error in UI here, let the calling function handle it
    }
}

document.addEventListener('DOMContentLoaded', function(){
    // Enhanced event listeners with modern functionality
    const refreshBtn = document.getElementById('refreshLogs');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            // Add loading state
            const icon = refreshBtn.querySelector('i');
            const originalClass = icon.className;
            icon.className = 'fas fa-spinner fa-spin';
            refreshBtn.disabled = true;
            
            refreshLogs().finally(() => {
                icon.className = originalClass;
                refreshBtn.disabled = false;
            });
        });
    }
    
    // Export modal
    const exportBtn = document.getElementById('exportLogs');
    if (exportBtn) exportBtn.addEventListener('click', function(){
        const modalEl = document.getElementById('exportModal');
        if (!modalEl) return;
        document.querySelectorAll('.modal-backdrop').forEach(e=>e.remove());
        document.body.classList.remove('modal-open');
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    });
    
    // Analysis modal
    const analyzeBtn = document.getElementById('analyzePatterns');
    if (analyzeBtn) analyzeBtn.addEventListener('click', function(){
        const modalEl = document.getElementById('analysisModal');
        if (!modalEl) return;
        
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
        
        // Initialize charts if not already done
        if (!errorChart || !timelineChart || !errorCategoriesChart || !hourlyDistributionChart || !serviceErrorsChart) {
            initializeCharts();
        }
        
        const commonErrorsDiv = document.getElementById('commonErrors');
        if (commonErrorsDiv) commonErrorsDiv.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Analyzing logs...</p></div>';
        
        // Only fetch analysis data when modal is actually opened
        fetch('/system-logs/analyze/', { 
            headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' } 
        })
            .then(r => {
                if (!r.ok) {
                    throw new Error(`HTTP ${r.status}: ${r.statusText}`);
                }
                return r.json();
            })
            .then(data => {
                console.log('Analysis data received:', data);
                if (data && !data.error) {
                    try {
                        updateAnalysisCharts(data);
                    } catch (chartError) {
                        console.error('Chart update error:', chartError);
                        if (commonErrorsDiv) {
                            commonErrorsDiv.innerHTML = `
                                <div class="alert alert-warning">
                                    <strong>Chart Error:</strong> Error updating charts: ${chartError.message}
                                </div>
                            `;
                        }
                    }
                } else {
                    throw new Error(data?.error || 'Unknown analysis error');
                }
            })
            .catch(error => { 
                console.error('Analysis error:', error);
                if (commonErrorsDiv) {
                    commonErrorsDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <strong>Analysis Error:</strong> ${error.message || 'An error occurred during log analysis.'}
                        </div>
                    `;
                }
            });
    });
    
    // Search functionality
    const searchInput = document.getElementById('logSearch');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                filterLogsBySearch(this.value);
            }, 300);
        });
    }
    
    // Level filter
    const levelFilter = document.getElementById('logLevel');
    if (levelFilter) {
        levelFilter.addEventListener('change', function() {
            filterLogsByLevel(this.value);
        });
    }
    
    // Clear logs
    const clearBtn = document.getElementById('clearLogs');
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            const container = document.getElementById('logsContainer');
            if (container) {
                container.innerHTML = '<div class="text-muted">Logs cleared.</div>';
                updateLogCount(0);
            }
        });
    }
    
    // Auto scroll toggle
    const autoScrollBtn = document.getElementById('autoScroll');
    if (autoScrollBtn) {
        autoScrollBtn.addEventListener('click', function() {
            this.classList.toggle('active');
            const container = document.getElementById('logsContainer');
            if (this.classList.contains('active') && container) {
                container.scrollTop = container.scrollHeight;
            }
        });
    }
});

function filterLogsBySearch(searchTerm) {
    const container = document.getElementById('logsContainer');
    if (!container) return;
    
    const logEntries = container.querySelectorAll('.log-entry');
    const term = searchTerm.toLowerCase();
    
    logEntries.forEach(entry => {
        const text = entry.textContent.toLowerCase();
        if (text.includes(term)) {
            entry.style.display = 'block';
        } else {
            entry.style.display = 'none';
        }
    });
}

function filterLogsByLevel(level) {
    const container = document.getElementById('logsContainer');
    if (!container) return;
    
    const logEntries = container.querySelectorAll('.log-entry');
    
    logEntries.forEach(entry => {
        if (level === 'all') {
            entry.style.display = 'block';
        } else {
            const hasLevel = entry.classList.contains(level);
            entry.style.display = hasLevel ? 'block' : 'none';
        }
    });
}


