/*
Process Topology Snapshot Loader Component JavaScript
Handles snapshot loading functionality
*/

class ProcessTopologySnapshotLoader {
    constructor() {
        this.modal = null;
        this.fileInput = null;
        this.uploadArea = null;
        this.loadingSection = null;
        this.previewSection = null;
        this.errorSection = null;
        this.currentSnapshotData = null;
        this.currentFilename = null;
        this.init();
    }

    init() {
        this.modal = document.getElementById('snapshot-loader-modal');
        this.fileInput = document.getElementById('file-input');
        this.uploadArea = document.getElementById('upload-area');
        this.loadingSection = document.getElementById('loading-section');
        this.previewSection = document.getElementById('preview-section');
        this.errorSection = document.getElementById('error-section');
        
        if (!this.modal) return;
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Close button
        const closeBtn = document.getElementById('close-snapshot-loader');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hide());
        }

        // File input change
        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }

        // Upload area click
        if (this.uploadArea) {
            this.uploadArea.addEventListener('click', () => this.fileInput?.click());
        }

        // Drag and drop
        if (this.uploadArea) {
            this.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
            this.uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            this.uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
        }

        // Load snapshot button
        const loadBtn = document.getElementById('load-snapshot');
        if (loadBtn) {
            loadBtn.addEventListener('click', () => this.loadSnapshot());
        }

        // Cancel button
        const cancelBtn = document.getElementById('cancel-snapshot');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.hide());
        }

        // Retry button
        const retryBtn = document.getElementById('retry-upload');
        if (retryBtn) {
            retryBtn.addEventListener('click', () => this.resetUpload());
        }

        // Close on backdrop click
        const backdrop = this.modal?.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.addEventListener('click', () => this.hide());
        }
    }

    show() {
        if (this.modal) {
            console.log('Showing snapshot loader modal');
            this.modal.style.display = 'flex';
            this.modal.classList.add('show');
            this.resetUpload();
            
            // Force reflow to ensure animation works
            this.modal.offsetHeight;
        } else {
            console.error('Modal element not found');
        }
    }

    hide() {
        if (this.modal) {
            console.log('Hiding snapshot loader modal');
            this.modal.classList.remove('show');
            setTimeout(() => {
                this.modal.style.display = 'none';
            }, 300); // Wait for animation to complete
            this.resetUpload();
        }
    }

    resetUpload() {
        // Reset all sections
        this.hideAllSections();
        this.showUploadSection();
        
        // Reset file input
        if (this.fileInput) {
            this.fileInput.value = '';
        }
        
        // Reset data
        this.currentSnapshotData = null;
        this.currentFilename = null;
    }

    hideAllSections() {
        if (this.loadingSection) this.loadingSection.style.display = 'none';
        if (this.previewSection) this.previewSection.style.display = 'none';
        if (this.errorSection) this.errorSection.style.display = 'none';
    }

    showUploadSection() {
        if (this.uploadArea) {
            this.uploadArea.style.display = 'block';
        }
    }

    showLoadingSection(message = 'Processing snapshot data...') {
        this.hideAllSections();
        if (this.uploadArea) this.uploadArea.style.display = 'none';
        if (this.loadingSection) {
            this.loadingSection.style.display = 'block';
            const messageEl = this.loadingSection.querySelector('#loading-message');
            if (messageEl) messageEl.textContent = message;
        }
    }

    showPreviewSection() {
        this.hideAllSections();
        if (this.previewSection) {
            this.previewSection.style.display = 'block';
        }
    }

    showErrorSection(message = 'Invalid snapshot file format') {
        this.hideAllSections();
        if (this.errorSection) {
            this.errorSection.style.display = 'block';
            const messageEl = this.errorSection.querySelector('#error-message');
            if (messageEl) messageEl.textContent = message;
        }
    }

    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        if (this.uploadArea) {
            this.uploadArea.classList.add('dragover');
        }
    }

    handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        if (this.uploadArea) {
            this.uploadArea.classList.remove('dragover');
        }
    }

    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        if (this.uploadArea) {
            this.uploadArea.classList.remove('dragover');
        }
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }

    async processFile(file) {
        console.log('Processing file:', file.name);
        
        // Validate file type
        if (!file.name.toLowerCase().endsWith('.json')) {
            this.showErrorSection('Please select a valid JSON file');
            return;
        }

        // Show loading
        this.showLoadingSection('Reading snapshot file...');
        
        try {
            // Read file content
            const fileContent = await this.readFileContent(file);
            
            // Parse JSON
            this.showLoadingSection('Parsing snapshot data...');
            const snapshotData = JSON.parse(fileContent);
            
            // Validate snapshot data
            this.showLoadingSection('Validating snapshot data...');
            if (!this.validateSnapshotData(snapshotData)) {
                throw new Error('Invalid snapshot data format');
            }
            
            // Store snapshot data
            this.currentSnapshotData = snapshotData;
            this.currentFilename = file.name;
            
            // Show preview
            this.showPreviewSection();
            this.populatePreview(snapshotData, file.name);
            
            console.log('Snapshot loaded successfully:', snapshotData);
            
        } catch (error) {
            console.error('Error processing file:', error);
            this.showErrorSection(`Error loading snapshot: ${error.message}`);
        }
    }

    readFileContent(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    }

    validateSnapshotData(data) {
        // Check required fields
        if (!data || typeof data !== 'object') return false;
        if (!Array.isArray(data.nodes)) return false;
        if (!Array.isArray(data.links)) return false;
        
        // Check nodes structure
        if (data.nodes.length === 0) return false;
        const firstNode = data.nodes[0];
        if (!firstNode.id || !firstNode.name) return false;
        
        return true;
    }

    populatePreview(snapshotData, filename) {
        console.log('Populating preview with detailed information');
        
        // Basic Information
        this.populateBasicInfo(snapshotData, filename);
        
        // Process Statistics
        this.populateProcessStats(snapshotData);
        
        // Connection Statistics
        this.populateConnectionStats(snapshotData);
        
        // System Information
        this.populateSystemInfo(snapshotData);
        
        // Settings Information
        this.populateSettingsInfo(snapshotData);
        
        // Header info
        const dateEl = document.getElementById('snapshot-date');
        if (dateEl && snapshotData.timestamp) {
            dateEl.textContent = new Date(snapshotData.timestamp).toLocaleString();
        }
        
        const processesEl = document.getElementById('snapshot-processes');
        if (processesEl) {
            processesEl.textContent = `${snapshotData.nodes.length} processes`;
        }
        
        const connectionsEl = document.getElementById('snapshot-connections');
        if (connectionsEl) {
            connectionsEl.textContent = `${snapshotData.links.length} connections`;
        }
    }

    populateBasicInfo(snapshotData, filename) {
        // Filename
        const filenameEl = document.getElementById('snapshot-filename');
        if (filenameEl) {
            filenameEl.textContent = filename;
        }
        
        // Created date
        const createdDateEl = document.getElementById('snapshot-created-date');
        if (createdDateEl && snapshotData.timestamp) {
            createdDateEl.textContent = new Date(snapshotData.timestamp).toLocaleString();
        }
        
        // File size (estimate)
        const fileSizeEl = document.getElementById('snapshot-file-size');
        if (fileSizeEl) {
            const dataSize = JSON.stringify(snapshotData).length;
            const sizeKB = (dataSize / 1024).toFixed(1);
            fileSizeEl.textContent = `${sizeKB} KB`;
        }
        
        // Version
        const versionEl = document.getElementById('snapshot-version');
        if (versionEl) {
            versionEl.textContent = snapshotData.metadata?.version || '1.0';
        }
    }

    populateProcessStats(snapshotData) {
        const totalProcessesEl = document.getElementById('snapshot-total-processes');
        if (totalProcessesEl) {
            totalProcessesEl.textContent = snapshotData.nodes.length;
        }
        
        // Count processes by status
        const statusCounts = {
            running: 0,
            sleeping: 0,
            stopped: 0,
            zombie: 0
        };
        
        snapshotData.nodes.forEach(node => {
            if (statusCounts.hasOwnProperty(node.status)) {
                statusCounts[node.status]++;
            }
        });
        
        const runningEl = document.getElementById('snapshot-running-processes');
        if (runningEl) {
            runningEl.textContent = statusCounts.running;
        }
        
        const sleepingEl = document.getElementById('snapshot-sleeping-processes');
        if (sleepingEl) {
            sleepingEl.textContent = statusCounts.sleeping;
        }
        
        const zombieEl = document.getElementById('snapshot-zombie-processes');
        if (zombieEl) {
            zombieEl.textContent = statusCounts.zombie;
        }
    }

    populateConnectionStats(snapshotData) {
        const totalConnectionsEl = document.getElementById('snapshot-total-connections');
        if (totalConnectionsEl) {
            totalConnectionsEl.textContent = snapshotData.links.length;
        }
        
        // Count connections by type
        const connectionCounts = {
            'parent-child': 0,
            'network': 0,
            'system': 0
        };
        
        snapshotData.links.forEach(link => {
            if (connectionCounts.hasOwnProperty(link.type)) {
                connectionCounts[link.type]++;
            }
        });
        
        const parentChildEl = document.getElementById('snapshot-parent-child-links');
        if (parentChildEl) {
            parentChildEl.textContent = connectionCounts['parent-child'];
        }
        
        const networkEl = document.getElementById('snapshot-network-links');
        if (networkEl) {
            networkEl.textContent = connectionCounts.network;
        }
        
        const systemEl = document.getElementById('snapshot-system-links');
        if (systemEl) {
            systemEl.textContent = connectionCounts.system;
        }
    }

    populateSystemInfo(snapshotData) {
        const sysInfo = snapshotData.metadata?.systemInfo || {};
        
        const platformEl = document.getElementById('snapshot-platform');
        if (platformEl) {
            platformEl.textContent = sysInfo.platform || 'Unknown';
        }
        
        const languageEl = document.getElementById('snapshot-language');
        if (languageEl) {
            languageEl.textContent = sysInfo.language || 'Unknown';
        }
        
        const userAgentEl = document.getElementById('snapshot-user-agent');
        if (userAgentEl) {
            const userAgent = sysInfo.userAgent || 'Unknown';
            userAgentEl.textContent = userAgent.length > 50 ? userAgent.substring(0, 50) + '...' : userAgent;
        }
        
        const browserEl = document.getElementById('snapshot-browser');
        if (browserEl) {
            const userAgent = sysInfo.userAgent || '';
            let browser = 'Unknown';
            if (userAgent.includes('Chrome')) browser = 'Chrome';
            else if (userAgent.includes('Firefox')) browser = 'Firefox';
            else if (userAgent.includes('Safari')) browser = 'Safari';
            else if (userAgent.includes('Edge')) browser = 'Edge';
            browserEl.textContent = browser;
        }
    }

    populateSettingsInfo(snapshotData) {
        const settings = snapshotData.settings || {};
        
        const nodeSizeEl = document.getElementById('snapshot-node-size');
        if (nodeSizeEl) {
            nodeSizeEl.textContent = settings.nodeSize ? `${settings.nodeSize}x` : '1.0x';
        }
        
        const canvasSizeEl = document.getElementById('snapshot-canvas-size');
        if (canvasSizeEl) {
            const width = settings.canvasWidth || 800;
            const height = settings.canvasHeight || 600;
            canvasSizeEl.textContent = `${width} × ${height}`;
        }
        
        const forceSettingsEl = document.getElementById('snapshot-force-settings');
        if (forceSettingsEl) {
            const charge = settings.chargeForce || -150;
            const centrality = settings.centralityForce || 2.0;
            forceSettingsEl.textContent = `Charge: ${charge}, Center: ${centrality}`;
        }
        
        const colorSchemeEl = document.getElementById('snapshot-color-scheme');
        if (colorSchemeEl) {
            colorSchemeEl.textContent = settings.colorScheme || 'Status';
        }
    }

    loadSnapshot() {
        if (!this.currentSnapshotData) {
            console.error('No snapshot data to load');
            return;
        }
        
        console.log('Loading snapshot into topology...');
        
        // Emit custom event for main topology manager
        const event = new CustomEvent('snapshotLoaded', {
            detail: {
                snapshotData: this.currentSnapshotData,
                filename: this.currentFilename
            }
        });
        document.dispatchEvent(event);
        
        // Show success message
        if (typeof showToast === 'function') {
            showToast('Success', 'Snapshot loaded successfully', 'success');
        }
        
        // Hide modal
        this.hide();
    }
}

// Make available globally
window.ProcessTopologySnapshotLoader = ProcessTopologySnapshotLoader;
