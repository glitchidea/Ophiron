// Detailed Analysis Modal JavaScript
class DetailedAnalysisModal {
    constructor() {
        this.modal = null;
        this.currentData = null;
        this.activeTab = 'errors';
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeModal();
    }

    bindEvents() {
        // Modal events
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-bs-target="#detailedAnalysisModal"]')) {
                this.show();
            }
        });

        // Tab events
        document.addEventListener('click', (e) => {
            if (e.target.matches('.analysis-tabs .nav-link')) {
                this.activeTab = e.target.getAttribute('data-bs-target').replace('#', '');
                this.loadTabData();
            }
        });

        // Refresh button
        const refreshBtn = document.getElementById('refreshDetailedAnalysis');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshData();
            });
        }
    }

    initializeModal() {
        this.modal = new bootstrap.Modal(document.getElementById('detailedAnalysisModal'));
    }

    show() {
        this.modal.show();
        this.loadData();
    }

    async loadData() {
        try {
            this.showLoading();
            const response = await fetch('/system-logs/detailed-analysis/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.currentData = data;
            this.renderData();
        } catch (error) {
            console.error('Detailed analysis data loading error:', error);
            this.showError('An error occurred while loading detailed analysis data.');
        }
    }

    async refreshData() {
        const refreshBtn = document.getElementById('refreshDetailedAnalysis');
        if (refreshBtn) {
            const icon = refreshBtn.querySelector('i');
            icon.className = 'fas fa-spinner fa-spin';
            refreshBtn.disabled = true;
        }
        
        await this.loadData();
        
        if (refreshBtn) {
            const icon = refreshBtn.querySelector('i');
            icon.className = 'fas fa-sync-alt';
            refreshBtn.disabled = false;
        }
    }

    renderData() {
        if (!this.currentData) return;
        
        this.renderErrors();
        this.renderWarnings();
        this.renderSecurity();
        this.renderSystem();
        this.renderNetwork();
        this.renderDatabase();
        this.renderServices();
    }

    renderErrors() {
        const container = document.getElementById('errorDetails');
        const categoriesContainer = document.getElementById('errorCategories');
        
        if (!container || !categoriesContainer) return;

        const errors = this.currentData.errors || [];
        const categories = this.currentData.error_categories || {};

        // Render error details
        if (errors.length > 0) {
            container.innerHTML = errors.map((error, index) => `
                <div class="log-entry error" data-index="${index}">
                    <div class="log-entry-header">
                        <span class="log-entry-timestamp">${this.formatTimestamp(error.timestamp)}</span>
                        <span class="log-entry-level error">Error</span>
                    </div>
                    <div class="log-entry-message">${this.escapeHtml(error.message)}</div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-check-circle"></i>
                    <h6>No Errors Found</h6>
                    <p>No errors found in the system.</p>
                </div>
            `;
        }

        // Render error categories
        this.renderCategories(categoriesContainer, categories, 'error');
    }

    renderWarnings() {
        const container = document.getElementById('warningDetails');
        const statsContainer = document.getElementById('warningStats');
        
        if (!container || !statsContainer) return;

        const warnings = this.currentData.warnings || [];
        const stats = this.currentData.warning_stats || {};

        // Render warning details
        if (warnings.length > 0) {
            container.innerHTML = warnings.map((warning, index) => `
                <div class="log-entry warning" data-index="${index}">
                    <div class="log-entry-header">
                        <span class="log-entry-timestamp">${this.formatTimestamp(warning.timestamp)}</span>
                        <span class="log-entry-level warning">Warning</span>
                    </div>
                    <div class="log-entry-message">${this.escapeHtml(warning.message)}</div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-info-circle"></i>
                    <h6>No Warnings Found</h6>
                    <p>No warnings found in the system.</p>
                </div>
            `;
        }

        // Render warning stats
        this.renderStats(statsContainer, stats, 'warning');
    }

    renderSecurity() {
        const container = document.getElementById('securityDetails');
        const categoriesContainer = document.getElementById('securityCategories');
        
        if (!container || !categoriesContainer) return;

        const security = this.currentData.security || [];
        const categories = this.currentData.security_categories || {};

        // Render security details
        if (security.length > 0) {
            container.innerHTML = security.map((item, index) => `
                <div class="log-entry security" data-index="${index}">
                    <div class="log-entry-header">
                        <span class="log-entry-timestamp">${this.formatTimestamp(item.timestamp)}</span>
                        <span class="log-entry-level security">Security</span>
                    </div>
                    <div class="log-entry-message">${this.escapeHtml(item.message)}</div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-shield-alt"></i>
                    <h6>No Security Events Found</h6>
                    <p>No security events found in the system.</p>
                </div>
            `;
        }

        // Render security categories
        this.renderCategories(categoriesContainer, categories, 'security');
    }

    renderDebug() {
        const container = document.getElementById('debugDetails');
        const statsContainer = document.getElementById('debugStats');
        
        if (!container || !statsContainer) return;

        const debug = this.currentData.debug || [];
        const stats = this.currentData.debug_stats || {};

        // Render debug details
        if (debug.length > 0) {
            container.innerHTML = debug.map((item, index) => `
                <div class="log-entry debug" data-index="${index}">
                    <div class="log-entry-header">
                        <span class="log-entry-timestamp">${this.formatTimestamp(item.timestamp)}</span>
                        <span class="log-entry-level debug">Debug</span>
                    </div>
                    <div class="log-entry-message">${this.escapeHtml(item.message)}</div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-bug"></i>
                    <h6>No Debug Information Found</h6>
                    <p>No debug information found in the system.</p>
                </div>
            `;
        }

        // Render debug stats
        this.renderStats(statsContainer, stats, 'debug');
    }

    renderSystem() {
        const container = document.getElementById('systemDetails');
        const statsContainer = document.getElementById('systemStats');
        
        if (!container || !statsContainer) return;

        const system = this.currentData.system || [];
        const stats = this.currentData.system_stats || {};

        // Render system details
        if (system.length > 0) {
            container.innerHTML = system.map((item, index) => `
                <div class="log-entry system" data-index="${index}">
                    <div class="log-entry-header">
                        <span class="log-entry-timestamp">${this.formatTimestamp(item.timestamp)}</span>
                        <span class="log-entry-level system">System</span>
                    </div>
                    <div class="log-entry-message">${this.escapeHtml(item.message)}</div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-desktop"></i>
                    <h6>No System Information Found</h6>
                    <p>No system information found in the system.</p>
                </div>
            `;
        }

        // Render system stats
        this.renderStats(statsContainer, stats, 'system');
    }

    renderNetwork() {
        const container = document.getElementById('networkDetails');
        const statsContainer = document.getElementById('networkStats');
        
        if (!container || !statsContainer) return;

        const network = this.currentData.network || [];
        const stats = this.currentData.network_stats || {};

        // Render network details
        if (network.length > 0) {
            container.innerHTML = network.map((item, index) => `
                <div class="log-entry network" data-index="${index}">
                    <div class="log-entry-header">
                        <span class="log-entry-timestamp">${this.formatTimestamp(item.timestamp)}</span>
                        <span class="log-entry-level network">Network</span>
                    </div>
                    <div class="log-entry-message">${this.escapeHtml(item.message)}</div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-network-wired"></i>
                    <h6>No Network Information Found</h6>
                    <p>No network information found in the system.</p>
                </div>
            `;
        }

        // Render network stats
        this.renderStats(statsContainer, stats, 'network');
    }

    renderDatabase() {
        const container = document.getElementById('databaseDetails');
        const statsContainer = document.getElementById('databaseStats');
        
        if (!container || !statsContainer) return;

        const database = this.currentData.database || [];
        const stats = this.currentData.database_stats || {};

        // Render database details
        if (database.length > 0) {
            container.innerHTML = database.map((item, index) => `
                <div class="log-entry database" data-index="${index}">
                    <div class="log-entry-header">
                        <span class="log-entry-timestamp">${this.formatTimestamp(item.timestamp)}</span>
                        <span class="log-entry-level database">Database</span>
                    </div>
                    <div class="log-entry-message">${this.escapeHtml(item.message)}</div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-database"></i>
                    <h6>No Database Information Found</h6>
                    <p>No database information found in the system.</p>
                </div>
            `;
        }

        // Render database stats
        this.renderStats(statsContainer, stats, 'database');
    }

    renderServices() {
        const container = document.getElementById('serviceDetails');
        const statsContainer = document.getElementById('serviceStats');
        
        if (!container || !statsContainer) return;

        const services = this.currentData.services || [];
        const stats = this.currentData.service_stats || {};

        // Render service details
        if (services.length > 0) {
            container.innerHTML = services.map((service, index) => `
                <div class="log-entry service" data-index="${index}">
                    <div class="log-entry-header">
                        <span class="log-entry-timestamp">${this.formatTimestamp(service.timestamp)}</span>
                        <span class="log-entry-level service">Service</span>
                    </div>
                    <div class="log-entry-message">${this.escapeHtml(service.message)}</div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-cogs"></i>
                    <h6>No Service Information Found</h6>
                    <p>No service information found in the system.</p>
                </div>
            `;
        }

        // Render service stats
        this.renderStats(statsContainer, stats, 'service');
    }

    renderCategories(container, categories, type) {
        if (!container) return;

        const total = Object.values(categories).reduce((sum, count) => sum + count, 0);
        
        if (total === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-chart-pie"></i>
                    <h6>No Categories Found</h6>
                    <p>No category information found for this type.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = Object.entries(categories)
            .sort((a, b) => b[1] - a[1])
            .map(([category, count]) => {
                const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
                return `
                    <div class="category-stat-item">
                        <span class="stat-label">${this.capitalizeFirst(category)}</span>
                        <div>
                            <span class="stat-value">${count}</span>
                            <span class="stat-percentage">(${percentage}%)</span>
                        </div>
                    </div>
                `;
            }).join('');
    }

    renderStats(container, stats, type) {
        if (!container) return;

        if (Object.keys(stats).length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-chart-bar"></i>
                    <h6>No Statistics Found</h6>
                    <p>No statistics found for this type.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = Object.entries(stats)
            .sort((a, b) => b[1] - a[1])
            .map(([stat, value]) => `
                <div class="category-stat-item">
                    <span class="stat-label">${this.capitalizeFirst(stat)}</span>
                    <span class="stat-value">${value}</span>
                </div>
            `).join('');
    }

    loadTabData() {
        // This method can be used to load specific tab data if needed
        // For now, we'll just ensure the current tab is properly rendered
        switch (this.activeTab) {
            case 'errors':
                this.renderErrors();
                break;
            case 'warnings':
                this.renderWarnings();
                break;
            case 'security':
                this.renderSecurity();
                break;
            case 'system':
                this.renderSystem();
                break;
            case 'network':
                this.renderNetwork();
                break;
            case 'database':
                this.renderDatabase();
                break;
            case 'services':
                this.renderServices();
                break;
        }
    }

    showLoading() {
        const containers = [
            'errorDetails', 'warningDetails', 'securityDetails', 
            'systemDetails', 'networkDetails', 'databaseDetails', 'serviceDetails'
        ];
        
        containers.forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                container.innerHTML = `
                    <div class="loading-state">
                        <i class="fas fa-spinner fa-spin"></i>
                        <p>Loading data...</p>
                    </div>
                `;
            }
        });
    }

    showError(message) {
        const containers = [
            'errorDetails', 'warningDetails', 'securityDetails', 
            'systemDetails', 'networkDetails', 'databaseDetails', 'serviceDetails'
        ];
        
        containers.forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <h6>Error</h6>
                        <p>${message}</p>
                    </div>
                `;
            }
        });
    }

    formatTimestamp(timestamp) {
        if (!timestamp) return 'N/A';
        try {
            const date = new Date(timestamp);
            return date.toLocaleString('tr-TR', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch (error) {
            return timestamp;
        }
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    capitalizeFirst(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.detailedAnalysisModal = new DetailedAnalysisModal();
});

// Export for global access
window.DetailedAnalysisModal = DetailedAnalysisModal;
