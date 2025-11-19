/*
Process Topology Settings Component JavaScript
Handles settings panel functionality
*/

class ProcessTopologySettings {
    constructor() {
        this.panel = null;
        this.isVisible = false;
        this.settings = {};
        this.init();
    }

    init() {
        this.panel = document.getElementById('settings-panel');
        if (!this.panel) return;

        this.loadSettings();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Close button
        const closeBtn = document.getElementById('close-settings');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hide());
        }


        // Range sliders
        this.setupRangeSliders();
        
        // Select dropdowns
        this.setupSelects();
        
        // Real-time preview
        this.setupRealTimePreview();
    }

    setupRangeSliders() {
        const sliders = [
            { id: 'node-size', valueId: 'node-size-value' },
            { id: 'connection-thickness', valueId: 'connection-thickness-value' },
            { id: 'centrality-force', valueId: 'centrality-force-value' },
            { id: 'node-distance', valueId: 'node-distance-value' },
            { id: 'charge-force', valueId: 'charge-force-value' },
            { id: 'collision-radius', valueId: 'collision-radius-value' },
            { id: 'canvas-width', valueId: 'canvas-width-value' },
            { id: 'canvas-height', valueId: 'canvas-height-value' }
        ];

        sliders.forEach(slider => {
            const sliderEl = document.getElementById(slider.id);
            const valueEl = document.getElementById(slider.valueId);
            
            if (sliderEl && valueEl) {
                sliderEl.addEventListener('input', () => {
                    valueEl.textContent = sliderEl.value;
                    this.updatePreview();
                });
            }
        });
    }

    setupSelects() {
        const selects = [
            'visualization-style',
            'node-distribution',
            'color-scheme'
        ];

        selects.forEach(selectId => {
            const selectEl = document.getElementById(selectId);
            if (selectEl) {
                selectEl.addEventListener('change', () => {
                    this.updatePreview();
                });
            }
        });
    }

    show() {
        if (this.panel) {
            this.panel.classList.add('show');
            this.isVisible = true;
            
            // Hide filters panel if open
            const filtersPanel = document.getElementById('topology-controls');
            if (filtersPanel && filtersPanel.classList.contains('show')) {
                filtersPanel.classList.remove('show');
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

    saveSettings() {
        // Auto-save settings to localStorage
        this.settings = this.getSettings();
        localStorage.setItem('processTopologySettings', JSON.stringify(this.settings));
    }

    getSettings() {
        return {
            visualizationStyle: document.getElementById('visualization-style')?.value || 'force',
            nodeDistribution: document.getElementById('node-distribution')?.value || 'compact',
            colorScheme: document.getElementById('color-scheme')?.value || 'status',
            nodeSize: parseFloat(document.getElementById('node-size')?.value) || 1.0,
            connectionThickness: parseFloat(document.getElementById('connection-thickness')?.value) || 1.0,
            centralityForce: parseFloat(document.getElementById('centrality-force')?.value) || 1.0,
            nodeDistance: parseInt(document.getElementById('node-distance')?.value) || 100,
            chargeForce: parseInt(document.getElementById('charge-force')?.value) || -300,
            collisionRadius: parseInt(document.getElementById('collision-radius')?.value) || 20,
            canvasWidth: parseInt(document.getElementById('canvas-width')?.value) || 800,
            canvasHeight: parseInt(document.getElementById('canvas-height')?.value) || 600,
            autoRefresh: document.getElementById('auto-refresh')?.checked || false,
            refreshInterval: parseInt(document.getElementById('refresh-interval')?.value) || 5
        };
    }

    loadSettings() {
        const saved = localStorage.getItem('processTopologySettings');
        if (saved) {
            try {
                this.settings = JSON.parse(saved);
                this.applySettings();
            } catch (e) {
                console.error('Error loading settings:', e);
                this.settings = this.getDefaultSettings();
            }
        } else {
            this.settings = this.getDefaultSettings();
        }
    }

    getDefaultSettings() {
        return {
            visualizationStyle: 'force',
            nodeDistribution: 'compact',
            colorScheme: 'status',
            nodeSize: 1.0,
            connectionThickness: 1.0,
            centralityForce: 1.0,
            nodeDistance: 100,
            chargeForce: -300,
            collisionRadius: 20,
            canvasWidth: 800,
            canvasHeight: 600,
            autoRefresh: true,
            refreshInterval: 5
        };
    }

    applySettings() {
        // Apply settings to form elements
        Object.keys(this.settings).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = this.settings[key];
                } else if (element.type === 'range') {
                    element.value = this.settings[key];
                    // Update value display
                    const valueEl = document.getElementById(key + '-value');
                    if (valueEl) {
                        valueEl.textContent = this.settings[key];
                    }
                } else {
                    element.value = this.settings[key];
                }
            }
        });
    }

    updatePreview() {
        // Emit preview event for real-time updates
        const event = new CustomEvent('settingsPreview', {
            detail: this.getSettings()
        });
        document.dispatchEvent(event);
    }

    setupRealTimePreview() {
        // Real-time preview for all sliders
        const allSliders = [
            'node-size', 'connection-thickness', 'centrality-force',
            'node-distance', 'charge-force', 'collision-radius',
            'canvas-width', 'canvas-height'
        ];

        allSliders.forEach(sliderId => {
            const slider = document.getElementById(sliderId);
            if (slider) {
                slider.addEventListener('input', () => {
                    this.updatePreview();
                });
            }
        });

        // Real-time preview for all selects
        const allSelects = [
            'visualization-style', 'node-distribution', 'color-scheme'
        ];

        allSelects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                select.addEventListener('change', () => {
                    this.updatePreview();
                });
            }
        });

        // Real-time preview for checkboxes
        const autoRefresh = document.getElementById('auto-refresh');
        if (autoRefresh) {
            autoRefresh.addEventListener('change', () => {
                this.updatePreview();
            });
        }

        // Real-time preview for number inputs
        const refreshInterval = document.getElementById('refresh-interval');
        if (refreshInterval) {
            refreshInterval.addEventListener('input', () => {
                this.updatePreview();
            });
        }
    }

    updatePreview() {
        // Get current settings
        const settings = this.getSettings();
        
        // Auto-save to localStorage
        this.saveSettings();
        
        // Emit preview event for real-time updates
        const event = new CustomEvent('settingsPreview', {
            detail: settings
        });
        document.dispatchEvent(event);
    }

    resetSettings() {
        const defaults = this.getDefaultSettings();
        Object.keys(defaults).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = defaults[key];
                } else {
                    element.value = defaults[key];
                }
            }
        });
        
        // Update value displays
        this.setupRangeSliders();
    }
}

// Make available globally
window.ProcessTopologySettings = ProcessTopologySettings;
