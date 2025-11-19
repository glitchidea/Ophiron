class ProcessTopologyManager {
    constructor() {
        this.container = null;
        this.svg = null;
        this.width = 0;
        this.height = 0;
        this.nodes = [];
        this.links = [];
        this.simulation = null;
        this.isInitialized = false;
    }

    init() {
        try {
            this.container = document.getElementById('process-topology-container');
            if (!this.container) {
                console.error('Topology container not found');
                return;
            }

            this.setupDimensions();
            this.createSVG();
            this.setupEventListeners();
            this.loadTopologyData();
            this.isInitialized = true;
            
            console.log('ProcessTopologyManager initialized successfully');
        } catch (error) {
            console.error('Error initializing ProcessTopologyManager:', error);
            this.showError('Topoloji yöneticisi başlatılamadı');
        }
    }

    setupDimensions() {
        // Get initial settings for canvas size
        const settings = this.getInitialSettings();
        this.width = settings.canvasWidth;
        this.height = settings.canvasHeight;
    }

    createSVG() {
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .attr('viewBox', `0 0 ${this.width} ${this.height}`)
            .style('background-color', '#f8f9fa');

        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.svg.select('g').attr('transform', event.transform);
            });

        this.svg.call(zoom);

        // Create main group for all elements
        this.svg.append('g').attr('class', 'topology-group');
    }

    setupEventListeners() {
        // Initialize component managers
        this.filtersManager = new ProcessTopologyFilters();
        this.settingsManager = new ProcessTopologySettings();
        this.infoPanelManager = new ProcessTopologyInfoPanel();
        this.snapshotLoaderManager = new ProcessTopologySnapshotLoader();

        // Refresh button
        const refreshBtn = document.getElementById('refresh-topology');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshTopology());
        }

        // Filter toggle
        const filterBtn = document.getElementById('toggle-filters');
        if (filterBtn) {
            filterBtn.addEventListener('click', () => this.filtersManager.toggle());
        }

        // Settings toggle
        const settingsBtn = document.getElementById('toggle-settings');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => this.settingsManager.toggle());
        }

        // Snapshot button
        const snapshotBtn = document.getElementById('create-snapshot');
        if (snapshotBtn) {
            snapshotBtn.addEventListener('click', () => this.createSnapshot());
        }

        // Load snapshots button
        const loadSnapshotsBtn = document.getElementById('load-snapshots');
        if (loadSnapshotsBtn) {
            loadSnapshotsBtn.addEventListener('click', () => this.snapshotLoaderManager.show());
        }

        // Listen for component events
        document.addEventListener('filtersApplied', (e) => this.handleFiltersApplied(e.detail));
        document.addEventListener('settingsChanged', (e) => this.handleSettingsChanged(e.detail));
        document.addEventListener('settingsPreview', (e) => this.handleSettingsPreview(e.detail));
        document.addEventListener('terminateProcess', (e) => this.handleTerminateProcess(e.detail));
        document.addEventListener('suspendProcess', (e) => this.handleSuspendProcess(e.detail));
        document.addEventListener('snapshotLoaded', (e) => this.handleSnapshotLoaded(e.detail));
    }

    async loadTopologyData() {
        try {
            this.showLoading();
            
            const response = await fetch('/process-topology/api/data/');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.nodes = data.nodes || [];
                this.links = data.links || [];
                this.renderTopology();
                this.hideLoading();
            } else {
                throw new Error(data.message || 'Veri yüklenemedi');
            }
        } catch (error) {
            console.error('Error loading topology data:', error);
            this.showError('Topoloji verileri yüklenemedi: ' + error.message);
            this.hideLoading();
        }
    }

    renderTopology() {
        if (!this.svg) return;

        const g = this.svg.select('.topology-group');
        g.selectAll('*').remove();

        if (this.nodes.length === 0) {
            this.showNoDataMessage();
            return;
        }

        // Create links
        const link = g.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(this.links)
            .enter()
            .append('line')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', 2);

        // Create nodes
        const node = g.append('g')
            .attr('class', 'nodes')
            .selectAll('g')
            .data(this.nodes)
            .enter()
            .append('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', this.dragstarted.bind(this))
                .on('drag', this.dragged.bind(this))
                .on('end', this.dragended.bind(this)));

        // Add circles to nodes
        node.append('circle')
            .attr('r', d => {
                const baseSize = Math.sqrt(d.size || 10) + 5;
                const settings = this.getInitialSettings();
                return baseSize * settings.nodeSize;
            })
            .attr('fill', d => this.getNodeColor(d))
            .attr('stroke', '#fff')
            .attr('stroke-width', 2);

        // Add labels
        node.append('text')
            .attr('dx', 12)
            .attr('dy', '.35em')
            .text(d => d.name || d.id)
            .style('font-size', '12px')
            .style('fill', '#333');

        // Add tooltips
        node.append('title')
            .text(d => {
                if (d.status === 'system') {
                    return `System Root\nTotal Processes: ${this.nodes.length - 1}`;
                }
                return `Process: ${d.name}\nPID: ${d.id}\nStatus: ${d.status}\nCPU: ${d.cpu_percent}%\nMemory: ${d.memory_percent}%\nUser: ${d.username}`;
            });

        // Add click event to nodes
        node.on('click', (event, d) => {
            event.stopPropagation();
            event.preventDefault();
            console.log('Node clicked:', d);
            this.selectNode(d);
        });

        // Get initial settings
        const settings = this.getInitialSettings();
        
        // Create simulation
        this.simulation = d3.forceSimulation(this.nodes)
            .force('link', d3.forceLink(this.links).id(d => d.id).distance(settings.nodeDistance))
            .force('charge', d3.forceManyBody().strength(settings.chargeForce))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2).strength(0.1 * settings.centralityForce))
            .force('collision', d3.forceCollide().radius(settings.collisionRadius))
            .on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);

                node.attr('transform', d => `translate(${d.x},${d.y})`);
            });
    }

    getNodeColor(node) {
        // Color based on process status
        const statusColors = {
            'running': '#28a745',      // Green
            'sleeping': '#17a2b8',     // Cyan
            'stopped': '#6c757d',      // Gray
            'zombie': '#dc3545',       // Red
            'disk-sleep': '#ffc107',   // Yellow
            'dead': '#343a40',         // Dark
            'waking': '#20c997',       // Teal
            'parked': '#6f42c1',       // Purple
            'system': '#007bff'        // Blue
        };
        
        return statusColors[node.status] || statusColors[node.type] || '#1f77b4';
    }

    dragstarted(event, d) {
        // Only restart simulation if it's actually a drag, not a click
        if (!event.active) {
            // Check if this is a click (short duration) or drag
            this.dragStartTime = Date.now();
            this.simulation.alphaTarget(0.3).restart();
        }
        d.fx = d.x;
        d.fy = d.y;
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragended(event, d) {
        // Check if this was a click (short duration) or actual drag
        const dragDuration = Date.now() - (this.dragStartTime || 0);
        
        if (!event.active) {
            // Only stop simulation if it was a real drag (longer than 100ms)
            if (dragDuration > 100) {
                this.simulation.alphaTarget(0);
            }
        }
        d.fx = null;
        d.fy = null;
    }

    async refreshTopology() {
        console.log('Refreshing topology...');
        await this.loadTopologyData();
    }

    createSnapshot() {
        console.log('Creating snapshot...');
        console.log('Nodes:', this.nodes);
        console.log('Links:', this.links);
        
        // Check if we have data
        if (!this.nodes || this.nodes.length === 0) {
            console.error('No nodes data available');
            this.showToast('Error', 'No process data available for snapshot', 'error');
            return;
        }
        
        // Get current topology data
        const snapshotData = {
            timestamp: new Date().toISOString(),
            nodes: this.nodes || [],
            links: this.links || [],
            settings: this.getInitialSettings(),
            metadata: {
                totalProcesses: this.nodes ? this.nodes.length : 0,
                totalConnections: this.links ? this.links.length : 0,
                systemInfo: {
                    userAgent: navigator.userAgent,
                    platform: navigator.platform,
                    language: navigator.language
                }
            }
        };
        
        // Create filename with timestamp
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `process-topology-snapshot-${timestamp}.json`;
        
        try {
            // Create and download JSON file
            const dataStr = JSON.stringify(snapshotData, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            
            // Create download link
            const link = document.createElement('a');
            link.href = URL.createObjectURL(dataBlob);
            link.download = filename;
            link.style.display = 'none';
            
            // Trigger download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Clean up
            URL.revokeObjectURL(link.href);
            
            // Show success message
            this.showToast('Snapshot Created', `Process topology saved as ${filename}`, 'success');
            
            console.log('Snapshot created successfully:', filename);
        } catch (error) {
            console.error('Error creating snapshot:', error);
            this.showToast('Error', 'Failed to create snapshot: ' + error.message, 'error');
        }
    }

    showToast(title, message, type) {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.style.position = 'fixed';
            toastContainer.style.top = '80px';
            toastContainer.style.right = '20px';
            toastContainer.style.zIndex = '9999';
            toastContainer.style.display = 'flex';
            toastContainer.style.flexDirection = 'column';
            toastContainer.style.gap = '10px';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast bg-${type || 'primary'}`;
        toast.style.position = 'relative';
        toast.style.marginBottom = '8px';
        toast.style.padding = '12px 16px';
        toast.style.borderRadius = '8px';
        toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        toast.style.minWidth = '280px';
        toast.style.maxWidth = '320px';
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        toast.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        
        toast.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="flex-grow-1">
                    <strong>${title}</strong><br>
                    <small>${message}</small>
                </div>
                <button type="button" class="btn-close btn-close-white ms-2" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateX(0)';
        }, 10);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (toast.parentElement) {
                        toast.remove();
                    }
                }, 300);
            }
        }, 5000);
    }

    toggleFilters() {
        const filterPanel = document.getElementById('topology-controls');
        const settingsPanel = document.getElementById('settings-panel');
        
        if (filterPanel) {
            if (filterPanel.classList.contains('show')) {
                filterPanel.classList.remove('show');
            } else {
                filterPanel.classList.add('show');
                if (settingsPanel) {
                    settingsPanel.classList.remove('show');
                }
            }
        }
    }

    toggleSettings() {
        const settingsPanel = document.getElementById('settings-panel');
        const filterPanel = document.getElementById('topology-controls');
        
        if (settingsPanel) {
            if (settingsPanel.classList.contains('show')) {
                settingsPanel.classList.remove('show');
            } else {
                settingsPanel.classList.add('show');
                if (filterPanel) {
                    filterPanel.classList.remove('show');
                }
            }
        }
    }


    applyFilters() {
        console.log('Applying filters...');
        const searchTerm = document.getElementById('search-process')?.value || '';
        const processLimit = document.getElementById('process-limit')?.value || 100;
        const minConnections = document.getElementById('min-connections')?.value || 0;
        
        // Filter nodes based on criteria
        this.filterNodes(searchTerm, processLimit, minConnections);
        
        // Close filter panel
        const filterPanel = document.getElementById('topology-controls');
        if (filterPanel) {
            filterPanel.classList.remove('show');
        }
        
        if (typeof showToast === 'function') {
            showToast('Success', 'Filters applied', 'success');
        }
    }

    closeSettings() {
        const settingsPanel = document.getElementById('settings-panel');
        if (settingsPanel) {
            settingsPanel.classList.remove('show');
        }
    }

    closeFilters() {
        const filterPanel = document.getElementById('topology-controls');
        if (filterPanel) {
            filterPanel.classList.remove('show');
        }
    }

    filterNodes(searchTerm, processLimit, minConnections) {
        // Filter logic here
        let filteredNodes = this.nodes.filter(node => {
            const matchesSearch = !searchTerm || 
                node.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                node.id.includes(searchTerm);
            
            const hasEnoughConnections = this.links.filter(link => 
                link.source === node.id || link.target === node.id
            ).length >= minConnections;
            
            return matchesSearch && hasEnoughConnections;
        });

        // Limit number of nodes
        filteredNodes = filteredNodes.slice(0, processLimit);
        
        // Update visualization with filtered data
        this.nodes = filteredNodes;
        this.links = filteredLinks;
        this.renderTopology();
    }

    setupSettingsControls() {
        // Node size slider
        const nodeSizeSlider = document.getElementById('node-size');
        const nodeSizeValue = document.getElementById('node-size-value');
        if (nodeSizeSlider && nodeSizeValue) {
            nodeSizeSlider.addEventListener('input', (e) => {
                nodeSizeValue.textContent = e.target.value;
                this.updateNodeSize(parseFloat(e.target.value));
            });
        }

        // Connection thickness slider
        const connectionThicknessSlider = document.getElementById('connection-thickness');
        const connectionThicknessValue = document.getElementById('connection-thickness-value');
        if (connectionThicknessSlider && connectionThicknessValue) {
            connectionThicknessSlider.addEventListener('input', (e) => {
                connectionThicknessValue.textContent = e.target.value;
                this.updateConnectionThickness(parseFloat(e.target.value));
            });
        }

        // Visualization style
        const visualizationStyle = document.getElementById('visualization-style');
        if (visualizationStyle) {
            visualizationStyle.addEventListener('change', (e) => {
                this.changeVisualizationStyle(e.target.value);
            });
        }

        // Color scheme
        const colorScheme = document.getElementById('color-scheme');
        if (colorScheme) {
            colorScheme.addEventListener('change', (e) => {
                this.changeColorScheme(e.target.value);
            });
        }

        // Centrality force slider
        const centralityForceSlider = document.getElementById('centrality-force');
        const centralityForceValue = document.getElementById('centrality-force-value');
        if (centralityForceSlider && centralityForceValue) {
            centralityForceSlider.addEventListener('input', (e) => {
                centralityForceValue.textContent = e.target.value;
                this.updateCentralityForce(parseFloat(e.target.value));
            });
        }

        // Node distribution
        const nodeDistribution = document.getElementById('node-distribution');
        if (nodeDistribution) {
            nodeDistribution.addEventListener('change', (e) => {
                this.changeNodeDistribution(e.target.value);
            });
        }
    }

    updateNodeSize(scale) {
        if (this.svg) {
            this.svg.selectAll('.node circle')
                .attr('r', d => (Math.sqrt(d.size || 10) + 5) * scale);
        }
    }

    updateConnectionThickness(scale) {
        if (this.svg) {
            this.svg.selectAll('.links line')
                .attr('stroke-width', 2 * scale);
        }
    }

    updateCentralityForce(force) {
        if (this.simulation) {
            // Center force'u güncelle - düğümlerin merkeze çekilme gücü
            this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2).strength(force * 0.1));
            
            // Charge force'u güncelle - düğümlerin birbirinden uzaklığı
            this.simulation.force('charge', d3.forceManyBody().strength(-300 * force));
            
            // Link distance'ı da güncelle - bağlantı uzunlukları
            this.simulation.force('link', d3.forceLink(this.links).id(d => d.id).distance(100 / force));
            
            // Collision detection ekle - düğümlerin çakışmasını önle
            this.simulation.force('collision', d3.forceCollide().radius(d => (Math.sqrt(d.size || 10) + 5) * 1.5));
            
            // Simulation'ı yeniden başlat
            this.simulation.alpha(0.3).restart();
        }
    }

    changeVisualizationStyle(style) {
        console.log('Changing visualization style to:', style);
        // Implement different layout algorithms
        if (this.simulation) {
            this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
            this.simulation.alpha(0.3).restart();
        }
    }

    changeColorScheme(scheme) {
        console.log('Changing color scheme to:', scheme);
        if (this.svg) {
            this.svg.selectAll('.node circle')
                .attr('fill', d => this.getNodeColorByScheme(d, scheme));
        }
    }

    changeNodeDistribution(distribution) {
        console.log('Changing node distribution to:', distribution);
        if (this.simulation) {
            const settings = this.getInitialSettings();
            
            switch(distribution) {
                case 'compact':
                    this.simulation.force('charge', d3.forceManyBody().strength(settings.chargeForce * 0.3));
                    this.simulation.force('link', d3.forceLink(this.links).id(d => d.id).distance(settings.nodeDistance * 0.5));
                    this.simulation.force('collision', d3.forceCollide().radius(settings.collisionRadius * 0.8));
                    break;
                case 'spread':
                    this.simulation.force('charge', d3.forceManyBody().strength(settings.chargeForce * 1.5));
                    this.simulation.force('link', d3.forceLink(this.links).id(d => d.id).distance(settings.nodeDistance * 1.5));
                    this.simulation.force('collision', d3.forceCollide().radius(settings.collisionRadius * 1.2));
                    break;
                case 'clustered':
                    this.simulation.force('charge', d3.forceManyBody().strength(settings.chargeForce * 0.7));
                    this.simulation.force('link', d3.forceLink(this.links).id(d => d.id).distance(settings.nodeDistance * 0.8));
                    this.simulation.force('collision', d3.forceCollide().radius(settings.collisionRadius));
                    break;
                case 'linear':
                    this.simulation.force('charge', d3.forceManyBody().strength(settings.chargeForce * 0.2));
                    this.simulation.force('link', d3.forceLink(this.links).id(d => d.id).distance(settings.nodeDistance * 0.3));
                    this.simulation.force('collision', d3.forceCollide().radius(settings.collisionRadius * 0.6));
                    break;
            }
            this.simulation.alpha(0.3).restart();
        }
    }

    getNodeColorByScheme(node, scheme) {
        const colors = {
            'status': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
            'cpu': ['#ff6b6b', '#ffa500', '#ffff00', '#00ff00', '#00ffff'],
            'memory': ['#8b0000', '#ff0000', '#ffa500', '#ffff00', '#00ff00'],
            'user': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        };
        
        const colorArray = colors[scheme] || colors['status'];
        return colorArray[node.type % colorArray.length] || colorArray[0];
    }

    showLoading() {
        const loadingElement = document.getElementById('loading-overlay');
        if (loadingElement) {
            loadingElement.style.display = 'block';
        }
    }

    hideLoading() {
        const loadingElement = document.getElementById('loading-overlay');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }

    showNoDataMessage() {
        const noDataElement = document.getElementById('no-data-message');
        if (noDataElement) {
            noDataElement.style.display = 'block';
        }
    }

    showError(message) {
        console.error(message);
        // You can implement a toast notification here
        if (typeof showToast === 'function') {
            showToast('Error', message, 'error');
        }
    }

    // Component event handlers
    handleFiltersApplied(filters) {
        console.log('Filters applied:', filters);
        // Apply filters to the visualization
        this.applyFilters(filters);
    }

    handleSettingsChanged(settings) {
        console.log('Settings changed:', settings);
        // Apply settings to the visualization
        this.applySettings(settings);
    }

    handleSettingsPreview(settings) {
        console.log('Settings preview:', settings);
        // Apply settings in real-time for preview
        this.applySettings(settings);
    }

    handleTerminateProcess(detail) {
        console.log('Terminate process:', detail);
        // Implement process termination logic
        // This would typically make an API call
    }

    handleSuspendProcess(detail) {
        console.log('Suspend process:', detail);
        // Implement process suspension logic
        // This would typically make an API call
    }

    selectNode(nodeData) {
        console.log('Node selected:', nodeData);
        
        // Update selected node visual (without affecting simulation)
        this.updateNodeSelection(nodeData);
        
        // Show process info panel
        this.showProcessInfo(nodeData);
    }

    updateNodeSelection(selectedNode) {
        // Remove previous selection (visual only, no simulation restart)
        this.svg.selectAll('.node').classed('selected', false);
        
        // Add selection to clicked node (visual only)
        this.svg.selectAll('.node').filter(d => d.id === selectedNode.id)
            .classed('selected', true);
            
        // Don't restart simulation - just update visual selection
        console.log('Node selection updated without simulation restart');
    }

    showProcessInfo(nodeData) {
        console.log('Showing process info for:', nodeData);
        
        // Create or update info panel
        let infoPanel = document.getElementById('process-info-panel');
        
        if (!infoPanel) {
            console.log('Creating new info panel');
            // Create info panel if it doesn't exist
            infoPanel = this.createInfoPanel();
        }
        
        // Populate with node data
        this.populateInfoPanel(infoPanel, nodeData);
        
        // Show the panel
        infoPanel.style.display = 'block';
        console.log('Info panel should be visible now');
    }

    createInfoPanel() {
        const panel = document.createElement('div');
        panel.id = 'process-info-panel';
        panel.className = 'process-info-panel';
        panel.innerHTML = `
            <div class="info-header">
                <h6>Process Information</h6>
                <button class="btn-close" onclick="this.parentElement.parentElement.style.display='none'">×</button>
            </div>
            <div class="info-content">
                <div id="process-details"></div>
            </div>
        `;
        
        // Add to page
        document.querySelector('.process-topology-container').appendChild(panel);
        
        return panel;
    }

    populateInfoPanel(panel, nodeData) {
        const detailsDiv = panel.querySelector('#process-details');
        
        if (nodeData.status === 'system') {
            detailsDiv.innerHTML = `
                <div class="info-item">
                    <label>Type:</label>
                    <span class="badge bg-primary">System Root</span>
                </div>
                <div class="info-item">
                    <label>Total Processes:</label>
                    <span>${this.nodes.length - 1}</span>
                </div>
            `;
        } else {
            // Get connections for this process
            const connections = this.links.filter(link => 
                link.source === nodeData.id || link.target === nodeData.id
            );
            
            detailsDiv.innerHTML = `
                <div class="info-item">
                    <label>Process Name:</label>
                    <span>${nodeData.name}</span>
                </div>
                <div class="info-item">
                    <label>PID:</label>
                    <span>${nodeData.id}</span>
                </div>
                <div class="info-item">
                    <label>Status:</label>
                    <span class="badge bg-${this.getStatusColor(nodeData.status)}">${nodeData.status}</span>
                </div>
                <div class="info-item">
                    <label>CPU Usage:</label>
                    <span>${nodeData.cpu_percent || 0}%</span>
                </div>
                <div class="info-item">
                    <label>Memory Usage:</label>
                    <span>${nodeData.memory_percent || 0}%</span>
                </div>
                <div class="info-item">
                    <label>User:</label>
                    <span>${nodeData.username || 'unknown'}</span>
                </div>
                <div class="info-item">
                    <label>Connections:</label>
                    <span>${connections.length}</span>
                </div>
            `;
        }
    }

    getStatusColor(status) {
        const statusColors = {
            'running': 'success',
            'sleeping': 'info',
            'stopped': 'secondary',
            'zombie': 'danger',
            'disk-sleep': 'warning',
            'dead': 'dark',
            'waking': 'primary',
            'parked': 'primary'
        };
        return statusColors[status] || 'secondary';
    }

    getConnectedProcesses(focusPid) {
        console.log(`Getting connected processes for PID: ${focusPid}`);
        
        // Find all processes connected to the focus PID
        const connectedIds = new Set();
        
        // Add the focus PID itself
        connectedIds.add(focusPid);
        
        // Find all links connected to this PID
        this.links.forEach(link => {
            if (link.source === focusPid || link.source === focusPid.toString()) {
                connectedIds.add(link.target);
            }
            if (link.target === focusPid || link.target === focusPid.toString()) {
                connectedIds.add(link.source);
            }
        });
        
        console.log(`Connected IDs:`, Array.from(connectedIds));
        
        // Get all connected process data
        const connectedProcesses = this.nodes.filter(node => 
            connectedIds.has(node.id) || connectedIds.has(node.id.toString())
        );
        
        console.log(`Found ${connectedProcesses.length} connected processes`);
        return connectedProcesses;
    }

    getConnectedLinks(focusPid) {
        console.log(`Getting connected links for PID: ${focusPid}`);
        
        // Find all links between connected processes
        const connectedIds = new Set();
        connectedIds.add(focusPid);
        connectedIds.add(focusPid.toString());
        
        // Get all connected process IDs
        this.links.forEach(link => {
            if (link.source === focusPid || link.source === focusPid.toString()) {
                connectedIds.add(link.target);
            }
            if (link.target === focusPid || link.target === focusPid.toString()) {
                connectedIds.add(link.source);
            }
        });
        
        console.log(`Connected IDs for links:`, Array.from(connectedIds));
        
        // Filter links to only include those between connected processes
        const connectedLinks = this.links.filter(link => 
            (connectedIds.has(link.source) || connectedIds.has(link.source.toString())) &&
            (connectedIds.has(link.target) || connectedIds.has(link.target.toString()))
        );
        
        console.log(`Found ${connectedLinks.length} connected links`);
        return connectedLinks;
    }


    applyFilters(filters) {
        console.log('Applying filters:', filters);
        
        let filteredNodes = this.nodes;
        let filteredLinks = this.links;
        
        // If focus PID is specified, show only connected processes
        if (filters.focusPid && filters.focusPid.trim() !== '') {
            const focusPid = filters.focusPid.trim();
            console.log(`Focusing on PID: ${focusPid}`);
            
            const connectedNodes = this.getConnectedProcesses(focusPid);
            const connectedLinks = this.getConnectedLinks(focusPid);
            
            if (connectedNodes.length > 0) {
                filteredNodes = connectedNodes;
                filteredLinks = connectedLinks;
                console.log(`Found ${connectedNodes.length} connected processes for PID ${focusPid}`);
            } else {
                console.log(`No processes found connected to PID ${focusPid}`);
                this.showToast('No Connections', `No processes found connected to PID ${focusPid}`, 'warning');
                return;
            }
        } else {
            // Regular filtering
            filteredNodes = this.nodes.filter(node => {
                const matchesSearch = !filters.searchTerm || 
                    node.name.toLowerCase().includes(filters.searchTerm.toLowerCase()) ||
                    node.id.includes(filters.searchTerm);
                
                const hasEnoughConnections = true; // Removed minConnections filter
                
                const matchesState = 
                    (filters.showRunning && node.status === 'running') ||
                    (filters.showSleeping && node.status === 'sleeping') ||
                    (filters.showStopped && node.status === 'stopped') ||
                    (filters.showZombie && node.status === 'zombie');
                
                return matchesSearch && hasEnoughConnections && matchesState;
            });
        }

        // Limit number of nodes
        if (filters.processLimit && filters.processLimit > 0) {
            filteredNodes = filteredNodes.slice(0, filters.processLimit);
        }
        
        console.log(`Filtered to ${filteredNodes.length} nodes and ${filteredLinks.length} links`);
        
        // Update visualization with filtered data
        this.updateVisualization(filteredNodes, filteredLinks);
    }

    updateVisualization(filteredNodes, filteredLinks) {
        console.log('Updating visualization with filtered data');
        
        // Store original data for reference
        this.originalNodes = this.nodes;
        this.originalLinks = this.links;
        
        // Update current data
        this.nodes = filteredNodes;
        this.links = filteredLinks;
        
        // Re-render the topology
        this.renderTopology();
        
        // Update process count display
        const processCountElement = document.getElementById('process-count');
        if (processCountElement) {
            processCountElement.textContent = filteredNodes.length;
        }
        
        console.log(`Visualization updated: ${filteredNodes.length} nodes, ${filteredLinks.length} links`);
    }

    applySettings(settings) {
        // Check if canvas size changed
        if (settings.canvasWidth !== this.width || settings.canvasHeight !== this.height) {
            this.resizeCanvas(settings.canvasWidth, settings.canvasHeight);
        }
        
        // Update node sizes
        this.updateNodeSizes(settings.nodeSize);
        
        // Apply visualization settings
        if (this.simulation) {
            // Update simulation parameters based on settings
            this.simulation.force('charge', d3.forceManyBody().strength(settings.chargeForce * settings.centralityForce));
            this.simulation.force('link', d3.forceLink(this.links).id(d => d.id).distance(settings.nodeDistance * settings.connectionThickness));
            this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2).strength(0.1 * settings.centralityForce));
            this.simulation.force('collision', d3.forceCollide().radius(settings.collisionRadius));
            this.simulation.alpha(0.3).restart();
        }
    }

    updateNodeSizes(nodeSizeMultiplier) {
        if (this.svg) {
            this.svg.selectAll('.node circle')
                .attr('r', d => {
                    const baseSize = Math.sqrt(d.size || 10) + 5;
                    return baseSize * nodeSizeMultiplier;
                });
        }
    }

    resizeCanvas(newWidth, newHeight) {
        // Update dimensions
        this.width = newWidth;
        this.height = newHeight;
        
        // Update SVG size
        if (this.svg) {
            this.svg
                .attr('width', this.width)
                .attr('height', this.height);
        }
        
        // Update center force
        if (this.simulation) {
            this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
            this.simulation.alpha(0.3).restart();
        }
        
        console.log(`Canvas resized to ${this.width}x${this.height}`);
    }

    getInitialSettings() {
        // Get settings from localStorage or use defaults
        const saved = localStorage.getItem('processTopologySettings');
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch (e) {
                console.error('Error loading settings:', e);
            }
        }
        
        // Default settings - daha yakın node'lar için
        return {
            nodeDistance: 50,        // Daha yakın bağlantılar
            chargeForce: -150,       // Daha az itme gücü
            centralityForce: 2.0,    // Daha güçlü merkez çekimi
            collisionRadius: 15,     // Daha küçük çarpışma yarıçapı
            connectionThickness: 1.0,
            nodeSize: 1.0,
            canvasWidth: 800,
            canvasHeight: 600
        };
    }

    handleSnapshotLoaded(data) {
        console.log('Loading snapshot:', data.filename);
        
        try {
            const { snapshotData, filename } = data;
            
            // Validate snapshot data
            if (!snapshotData.nodes || !snapshotData.links) {
                throw new Error('Invalid snapshot data: missing nodes or links');
            }
            
            // Store original data for reference
            this.originalNodes = this.nodes;
            this.originalLinks = this.links;
            
            // Load snapshot data
            this.nodes = snapshotData.nodes;
            this.links = snapshotData.links;
            
            // Apply snapshot settings if available
            if (snapshotData.settings) {
                console.log('Applying snapshot settings:', snapshotData.settings);
                this.applySettings(snapshotData.settings);
            }
            
            // Re-render the topology
            this.renderTopology();
            
            // Update process count display
            const processCountElement = document.getElementById('process-count');
            if (processCountElement) {
                processCountElement.textContent = this.nodes.length;
            }
            
            // Update last updated timestamp
            const lastUpdatedElement = document.getElementById('last-updated');
            if (lastUpdatedElement && snapshotData.timestamp) {
                lastUpdatedElement.textContent = new Date(snapshotData.timestamp).toLocaleString();
            }
            
            // Show success message
            this.showToast('Snapshot Loaded', `Loaded snapshot with ${this.nodes.length} processes and ${this.links.length} connections`, 'success');
            
            console.log(`Snapshot loaded successfully: ${this.nodes.length} nodes, ${this.links.length} links`);
            
        } catch (error) {
            console.error('Error loading snapshot:', error);
            this.showToast('Error', 'Failed to load snapshot: ' + error.message, 'error');
        }
    }
}

// Make ProcessTopologyManager available globally
window.ProcessTopologyManager = ProcessTopologyManager;
