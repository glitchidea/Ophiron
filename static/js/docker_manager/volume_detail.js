// Volume Detail - JavaScript

// Initialize volume detail page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Volume Detail...');
    initializeVolumeDetail();
});

function initializeVolumeDetail() {
    // Setup tab navigation
    setupTabNavigation();
    
    // Setup action buttons
    setupActionButtons();

    // Exit on ESC key
    document.addEventListener('keydown', function onEsc(e) {
        if (e.key === 'Escape') {
            window.location.href = '/docker-manager/volumes/';
        }
    });

    // Exit on outside click (clicks outside the main container)
    document.addEventListener('click', function onOutsideClick(e) {
        const container = document.querySelector('.docker-manager-container');
        if (container && !container.contains(e.target)) {
            window.location.href = '/docker-manager/volumes/';
        }
    });
}

function setupTabNavigation() {
    const navTabs = document.querySelectorAll('.nav-tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    navTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.dataset.tab;
            
            // Remove active class from all tabs and contents
            navTabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            this.classList.add('active');
            const targetContent = document.getElementById(`${targetTab}-content`);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
}

function setupActionButtons() {
    // Delete button functionality is handled by the onclick attribute in HTML
}

function deleteVolume(volumeName) {
    console.log('Deleting volume:', volumeName);
    
    if (confirm(`Are you sure you want to delete volume "${volumeName}"? This action cannot be undone.`)) {
        // Show loading
        showNotification('Deleting volume...', 'info');
        
        // Delete volume
        fetch(`/docker-manager/api/volume/${volumeName}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Volume deleted successfully', 'success');
                // Redirect to volumes page
                setTimeout(() => {
                    window.location.href = '/docker-manager/volumes/';
                }, 1000);
            } else {
                showNotification('Failed to delete volume: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Delete volume error:', error);
            showNotification('Error deleting volume: ' + error.message, 'error');
        });
    }
}

function copyInspectJson() {
    const inspectOutput = document.getElementById('inspectOutput');
    if (inspectOutput) {
        const text = inspectOutput.textContent;
        navigator.clipboard.writeText(text).then(() => {
            showNotification('JSON copied to clipboard', 'success');
        }).catch(err => {
            console.error('Failed to copy: ', err);
            showNotification('Failed to copy JSON', 'error');
        });
    }
}

// Notification function
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Export functions for global access
window.deleteVolume = deleteVolume;
window.copyInspectJson = copyInspectJson;
