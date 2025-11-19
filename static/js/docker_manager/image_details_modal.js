// Image Details Modal - JavaScript

let currentImageName = '';
let currentImageDetails = null;

// Ensure jsTranslations is available
if (typeof window.jsTranslations === 'undefined') {
    window.jsTranslations = {};
}

// Modal Functions
function showImageDetailsModal(imageName, details) {
    console.log('Showing image details modal for:', imageName);
    
    currentImageName = imageName;
    currentImageDetails = details;
    
    // Update modal title
    document.getElementById('modalImageName').textContent = imageName;
    
    // Update basic information
    document.getElementById('detailName').textContent = details.name || imageName;
    document.getElementById('detailDescription').textContent = details.description || (window.jsTranslations['No description available'] || 'No description available');
    document.getElementById('detailOfficial').textContent = details.namespace === 'library' ? (window.jsTranslations['Yes'] || 'Yes') : (window.jsTranslations['No'] || 'No');
    document.getElementById('detailLastUpdated').textContent = formatDate(details.last_updated) || (window.jsTranslations['Unknown'] || 'Unknown');
    
    // Update statistics
    document.getElementById('detailStars').textContent = formatNumber(details.star_count || 0);
    document.getElementById('detailPulls').textContent = formatNumber(details.pull_count || 0);
    
    // Update tags
    updateTagsDisplay(details.tags || ['latest']);
    
    // Show modal
    const modal = document.getElementById('imageDetailsModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }
}

function closeImageDetailsModal() {
    console.log('Closing image details modal');
    
    const modal = document.getElementById('imageDetailsModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restore scrolling
    }
    
    // Clear current data
    currentImageName = '';
    currentImageDetails = null;
}

function pullSelectedImage() {
    if (!currentImageName) {
        showError(window.jsTranslations['No image selected'] || 'No image selected');
        return;
    }
    
    console.log('Pulling image:', currentImageName);
    
    // Show loading state
    const pullBtn = document.querySelector('.btn-primary');
    const originalText = pullBtn.innerHTML;
    pullBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + (window.jsTranslations['Pulling...'] || 'Pulling...');
    pullBtn.disabled = true;
    
    // Call pull API
    fetch('/docker-manager/api/hub/pull/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            image_name: currentImageName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification((window.jsTranslations['Image'] || 'Image') + ' ' + currentImageName + ' ' + (window.jsTranslations['is being pulled...'] || 'is being pulled...'), 'success');
            closeImageDetailsModal();
        } else {
            showError((window.jsTranslations['Pull failed'] || 'Pull failed') + ': ' + data.message);
        }
    })
    .catch(error => {
        console.error('Pull error:', error);
        showError((window.jsTranslations['Pull error'] || 'Pull error') + ': ' + error.message);
    })
    .finally(() => {
        // Restore button state
        pullBtn.innerHTML = originalText;
        pullBtn.disabled = false;
    });
}

// Utility Functions
function formatDate(dateString) {
    if (!dateString) return window.jsTranslations['Unknown'] || 'Unknown';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        return window.jsTranslations['Invalid date'] || 'Invalid date';
    }
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function updateTagsDisplay(tags) {
    const tagsContainer = document.getElementById('detailTags');
    if (!tagsContainer) return;
    
    if (!tags || tags.length === 0) {
        tagsContainer.innerHTML = '<span class="tag">latest</span>';
        return;
    }
    
    tagsContainer.innerHTML = tags.map(tag => 
        `<span class="tag">${tag}</span>`
    ).join('');
}

function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

function showError(message) {
    showNotification(message, 'error');
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Close modal on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeImageDetailsModal();
        }
    });
    
    // Close modal on overlay click
    const overlay = document.querySelector('.modal-overlay');
    if (overlay) {
        overlay.addEventListener('click', closeImageDetailsModal);
    }
});

// Export functions for global use
window.showImageDetailsModal = showImageDetailsModal;
window.closeImageDetailsModal = closeImageDetailsModal;
window.pullSelectedImage = pullSelectedImage;
