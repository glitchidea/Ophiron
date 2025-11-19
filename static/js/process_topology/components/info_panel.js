/*
Process Topology Info Panel Component JavaScript
Handles process information display
*/

class ProcessTopologyInfoPanel {
    constructor() {
        this.panel = null;
        this.isVisible = false;
        this.currentProcess = null;
        this.init();
    }

    init() {
        this.panel = document.getElementById('info-panel');
        if (!this.panel) return;

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Close button
        const closeBtn = document.getElementById('close-info-panel');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hide());
        }

        // Action buttons
        const terminateBtn = document.getElementById('terminate-process');
        if (terminateBtn) {
            terminateBtn.addEventListener('click', () => this.terminateProcess());
        }

        const connectionsBtn = document.getElementById('show-connections');
        if (connectionsBtn) {
            connectionsBtn.addEventListener('click', () => this.showConnections());
        }

        const suspendBtn = document.getElementById('suspend-process');
        if (suspendBtn) {
            suspendBtn.addEventListener('click', () => this.suspendProcess());
        }
    }

    show(processData) {
        if (this.panel && processData) {
            this.currentProcess = processData;
            this.updateDisplay(processData);
            this.panel.classList.add('show');
            this.isVisible = true;
        }
    }

    hide() {
        if (this.panel) {
            this.panel.classList.remove('show');
            this.isVisible = false;
            this.currentProcess = null;
        }
    }

    updateDisplay(processData) {
        // Update process information
        this.updateField('process-name', processData.name || '-');
        this.updateField('process-pid', processData.id || '-');
        this.updateField('process-user', processData.username || '-');
        this.updateField('process-cpu', `${processData.cpu_percent || 0}%`);
        this.updateField('process-memory', `${processData.memory_percent || 0}%`);
        this.updateField('process-threads', processData.threads || '-');
        this.updateField('process-started', this.formatDate(processData.started) || '-');
        
        // Update status badge
        this.updateStatusBadge(processData.status);
    }

    updateField(fieldId, value) {
        const element = document.getElementById(fieldId);
        if (element) {
            element.textContent = value;
        }
    }

    updateStatusBadge(status) {
        const badge = document.getElementById('process-status');
        if (badge) {
            badge.textContent = status || '-';
            badge.className = `status-badge ${status || ''}`;
        }
    }

    formatDate(timestamp) {
        if (!timestamp) return '-';
        try {
            return new Date(timestamp).toLocaleString();
        } catch (e) {
            return '-';
        }
    }

    terminateProcess() {
        if (!this.currentProcess) return;

        if (confirm(`Are you sure you want to terminate process ${this.currentProcess.name} (PID: ${this.currentProcess.id})?`)) {
            // Emit terminate event
            const event = new CustomEvent('terminateProcess', {
                detail: { pid: this.currentProcess.id }
            });
            document.dispatchEvent(event);

            if (typeof showToast === 'function') {
                showToast('Warning', 'Process termination requested', 'warning');
            }
        }
    }

    suspendProcess() {
        if (!this.currentProcess) return;

        if (confirm(`Are you sure you want to suspend process ${this.currentProcess.name} (PID: ${this.currentProcess.id})?`)) {
            // Emit suspend event
            const event = new CustomEvent('suspendProcess', {
                detail: { pid: this.currentProcess.id }
            });
            document.dispatchEvent(event);

            if (typeof showToast === 'function') {
                showToast('Warning', 'Process suspension requested', 'warning');
            }
        }
    }

    showConnections() {
        if (!this.currentProcess) return;

        // Emit show connections event
        const event = new CustomEvent('showProcessConnections', {
            detail: { pid: this.currentProcess.id }
        });
        document.dispatchEvent(event);

        // Show connections modal
        const modal = document.getElementById('connectionsModal');
        if (modal) {
            // First populate the content
            this.populateConnectionsContent();
            
            // Then show the modal
            modal.style.display = 'block';
            modal.classList.add('show');
            document.body.classList.add('modal-open');
            
            // Add backdrop
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            backdrop.id = 'modal-backdrop';
            document.body.appendChild(backdrop);
        }
    }

    populateConnectionsContent() {
        if (!this.currentProcess) return;
        
        const contentDiv = document.getElementById('connections-content');
        if (!contentDiv) return;
        
        // Get connections for this process (simplified for now)
        const connections = [
            { type: 'Parent-Child', source: 'system', target: this.currentProcess.name, status: 'Active' },
            { type: 'Network', source: this.currentProcess.name, target: 'network', status: 'Active' }
        ];
        
        // Create connections table
        let html = `
            <div class="connections-info mb-3">
                <h6>Process: ${this.currentProcess.name} (PID: ${this.currentProcess.id})</h6>
                <p class="text-muted">Status: ${this.currentProcess.status} | User: ${this.currentProcess.username}</p>
            </div>
        `;
        
        if (connections.length === 0) {
            html += `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    No connections found for this process.
                </div>
            `;
        } else {
            html += `
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Connection Type</th>
                                <th>Source</th>
                                <th>Target</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            connections.forEach(link => {
                html += `
                    <tr>
                        <td>
                            <span class="badge bg-primary">${link.type}</span>
                        </td>
                        <td>${link.source}</td>
                        <td>${link.target}</td>
                        <td>
                            <span class="badge bg-success">${link.status}</span>
                        </td>
                    </tr>
                `;
            });
            
            html += `
                        </tbody>
                    </table>
                </div>
            `;
        }
        
        contentDiv.innerHTML = html;
    }

    getCurrentProcess() {
        return this.currentProcess;
    }

    isProcessSelected() {
        return this.currentProcess !== null;
    }
}

// Make available globally
window.ProcessTopologyInfoPanel = ProcessTopologyInfoPanel;
