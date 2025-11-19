/*
Service Builder Templates JavaScript
Template management functionality
*/

// Templates namespace
window.Templates = {
    // Initialize templates functionality
    init: function() {
        this.bindEvents();
    },
    
    // Bind event listeners
    bindEvents: function() {
        // Template card click handlers
        document.addEventListener('click', (event) => {
            if (event.target.closest('[onclick*="useTemplate"]')) {
                const templateId = event.target.closest('[onclick*="useTemplate"]').onclick.toString().match(/'([^']+)'/)[1];
                this.useTemplate(templateId);
            }
            
            if (event.target.closest('[onclick*="viewTemplate"]')) {
                const templateId = event.target.closest('[onclick*="viewTemplate"]').onclick.toString().match(/'([^']+)'/)[1];
                this.viewTemplate(templateId);
            }
        });
    },
    
    // Use template
    useTemplate: function(templateId) {
        ServiceBuilder.utils.showNotification('Redirecting to service creation with template...', 'info');
        
        // Redirect to create service page with template parameter
        setTimeout(() => {
            window.location.href = `/service-builder/create/?template=${templateId}`;
        }, 1000);
    },
    
    // View template details
    viewTemplate: function(templateId) {
        this.loadTemplateDetails(templateId);
    },
    
    // Load template details
    loadTemplateDetails: function(templateId) {
        // Show modal with loading state
        ServiceBuilder.utils.showModal('templateModal', `
            <div class="text-center">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Loading template...</span>
                </div>
                <p>Loading template details...</p>
            </div>
        `);
        
        // Simulate loading template details
        // In a real implementation, you would make an API call here
        setTimeout(() => {
            this.displayTemplateDetails(templateId);
        }, 1000);
    },
    
    // Display template details
    displayTemplateDetails: function(templateId) {
        // This would normally fetch real template data
        const templateContent = `
            <div class="template-details">
                <h4>Template Details</h4>
                <div class="template-info">
                    <p><strong>Template ID:</strong> ${templateId}</p>
                    <p><strong>Type:</strong> Service Template</p>
                    <p><strong>Description:</strong> This is a pre-configured service template.</p>
                </div>
                <div class="template-content">
                    <h5>Template Content:</h5>
                    <pre class="code-block">
[Unit]
Description=Example Service
After=network.target

[Service]
Type=simple
User=www-data
ExecStart=/usr/bin/python3 /path/to/app.py
Restart=always

[Install]
WantedBy=multi-user.target
                    </pre>
                </div>
            </div>
        `;
        
        ServiceBuilder.utils.showModal('templateModal', templateContent);
        
        // Update use template button
        const useBtn = document.getElementById('useTemplateBtn');
        if (useBtn) {
            useBtn.onclick = () => {
                this.useTemplate(templateId);
                ServiceBuilder.utils.hideModal('templateModal');
            };
        }
    }
};

// Global template functions
window.useTemplate = function(templateId) {
    Templates.useTemplate(templateId);
};

window.viewTemplate = function(templateId) {
    Templates.viewTemplate(templateId);
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    Templates.init();
});
