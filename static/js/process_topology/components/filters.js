/*
Process Topology Filters Component JavaScript
Handles filter panel functionality
*/

class ProcessTopologyFilters {
    constructor() {
        this.panel = null;
        this.isVisible = false;
        this.init();
    }

    init() {
        this.panel = document.getElementById('topology-controls');
        if (!this.panel) return;

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Close button
        const closeBtn = document.getElementById('close-filters');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hide());
        }

        // Apply filters button
        const applyBtn = document.getElementById('apply-filters');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => this.applyFilters());
        }

        // Real-time search
        const searchInput = document.getElementById('search-process');
        if (searchInput) {
            searchInput.addEventListener('input', () => this.handleSearch());
        }

        // Process limit change
        const processLimit = document.getElementById('process-limit');
        if (processLimit) {
            processLimit.addEventListener('change', () => this.handleLimitChange());
        }
    }

    show() {
        if (this.panel) {
            this.panel.classList.add('show');
            this.isVisible = true;
            
            // Hide settings panel if open
            const settingsPanel = document.getElementById('settings-panel');
            if (settingsPanel && settingsPanel.classList.contains('show')) {
                settingsPanel.classList.remove('show');
            }
        }
    }

    hide() {
        if (this.panel) {
            this.panel.classList.remove('show');
            this.isVisible = false;
        }
    }

    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }

    applyFilters() {
        const filters = this.getFilterValues();
        
        // Emit custom event for main topology manager
        const event = new CustomEvent('filtersApplied', {
            detail: filters
        });
        document.dispatchEvent(event);

        // Show success message
        if (typeof showToast === 'function') {
            showToast('Success', 'Filters applied', 'success');
        }

        // Hide panel
        this.hide();
    }

    getFilterValues() {
        return {
            searchTerm: document.getElementById('search-process')?.value || '',
            focusPid: document.getElementById('focus-pid')?.value || '',
            processLimit: parseInt(document.getElementById('process-limit')?.value) || 100,
            showRunning: document.getElementById('show-running')?.checked || false,
            showSleeping: document.getElementById('show-sleeping')?.checked || false,
            showStopped: document.getElementById('show-stopped')?.checked || false,
            showZombie: document.getElementById('show-zombie')?.checked || false
        };
    }

    handleSearch() {
        // Debounce search
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            const searchTerm = document.getElementById('search-process')?.value || '';
            if (searchTerm.length > 2) {
                this.applyFilters();
            }
        }, 500);
    }

    handleLimitChange() {
        const limit = parseInt(document.getElementById('process-limit')?.value) || 100;
        if (limit < 10) {
            document.getElementById('process-limit').value = 10;
        } else if (limit > 500) {
            document.getElementById('process-limit').value = 500;
        }
    }

    resetFilters() {
        if (document.getElementById('search-process')) {
            document.getElementById('search-process').value = '';
        }
        if (document.getElementById('focus-pid')) {
            document.getElementById('focus-pid').value = '';
        }
        if (document.getElementById('process-limit')) {
            document.getElementById('process-limit').value = 100;
        }
        if (document.getElementById('show-running')) {
            document.getElementById('show-running').checked = true;
        }
        if (document.getElementById('show-sleeping')) {
            document.getElementById('show-sleeping').checked = true;
        }
        if (document.getElementById('show-stopped')) {
            document.getElementById('show-stopped').checked = false;
        }
        if (document.getElementById('show-zombie')) {
            document.getElementById('show-zombie').checked = false;
        }
    }
}

// Make available globally
window.ProcessTopologyFilters = ProcessTopologyFilters;
