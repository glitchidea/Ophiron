// Docker Hubs - JavaScript

// Memory cache for data
let dataCache = {
    images: null,
    lastFetch: null,
    cacheDuration: 30 * 60 * 1000 // 30 minutes
};

// Ensure jsTranslations is available
if (typeof window.jsTranslations === 'undefined') {
    window.jsTranslations = {};
}

document.addEventListener('DOMContentLoaded', function() {
    initializeHubs();
});

function initializeHubs() {
    console.log('Initializing Docker Hubs...');
    
    // Search functionality
    setupSearchFunctionality();
    
    
    // Tab functionality
    setupTabFunctionality();
    
    // Load initial data
    loadInitialData();
}

function setupSearchFunctionality() {
    const searchInput = document.getElementById('hubSearch');
    if (searchInput) {
        // Enter key search
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchHub();
            }
        });
        
        // Real-time search with debounce
        let searchTimeout;
        searchInput.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const query = e.target.value.trim();
                if (query.length >= 2) {
                    searchHub();
                } else if (query.length === 0) {
                    // If search is cleared, load all images
                    loadAllImages();
                }
            }, 500); // 500ms debounce
        });
    }
}


function setupTabFunctionality() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            switchTab(tabName);
        });
    });
}

function loadInitialData() {
    // Load all 178 images on page load
    showLoadingIndicator();
    loadAllImages();
}

function showLoadingIndicator() {
    const loadingIndicator = document.getElementById('imagesLoading');
    const imagesGrid = document.getElementById('imagesGrid');
    
    if (loadingIndicator && imagesGrid) {
        loadingIndicator.style.display = 'flex';
        imagesGrid.style.display = 'none';
    }
}

function hideLoadingIndicator() {
    const loadingIndicator = document.getElementById('imagesLoading');
    const imagesGrid = document.getElementById('imagesGrid');
    
    if (loadingIndicator && imagesGrid) {
        loadingIndicator.style.display = 'none';
        imagesGrid.style.display = 'grid';
    }
}

function loadAllImages() {
    console.log('Loading all cached images...');
    
    // Get cached images from server
    fetch('/docker-manager/api/hub/images/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log(`Loaded ${data.results.length} cached images`);
                displayImages(data.results);
                updateImagesCount(data.results.length);
                hideLoadingIndicator();
            } else {
                console.error('Failed to load cached images:', data.message);
                showError('Failed to load images: ' + data.message);
                hideLoadingIndicator();
            }
        })
        .catch(error => {
            console.error('Error loading cached images:', error);
            showError('Error loading images: ' + error.message);
            hideLoadingIndicator();
        });
}

function isCacheValid() {
    if (!dataCache.images || !dataCache.lastFetch) {
        return false;
    }
    
    const now = Date.now();
    const cacheAge = now - dataCache.lastFetch;
    return cacheAge < dataCache.cacheDuration;
}

function clearCache() {
    dataCache.images = null;
    dataCache.lastFetch = null;
    console.log('Cache cleared');
}

function displayImages(images) {
    const imagesGrid = document.getElementById('imagesGrid');
    if (!imagesGrid) return;
    
    // Clear existing images
    imagesGrid.innerHTML = '';
    
    // Create image cards for each image
    images.forEach(image => {
        const imageCard = createImageCard(image);
        imagesGrid.appendChild(imageCard);
    });
}

function createImageCard(image) {
    const card = document.createElement('div');
    card.className = 'image-card';
    card.setAttribute('data-image', image.name);
    
    card.innerHTML = `
        <div class="image-header">
            <div class="image-name">
                <i class="fas fa-cube"></i>
                <span>${image.name}</span>
                ${image.official ? '<span class="official-badge">' + (window.jsTranslations['Official'] || 'Official') + '</span>' : ''}
            </div>
            <div class="image-stats">
                <span class="stars">
                    <i class="fas fa-star"></i>
                    ${Math.round(image.stars || 0)}
                </span>
                <span class="pulls">
                    <i class="fas fa-download"></i>
                    ${Math.round(image.pulls || 0)}
                </span>
            </div>
        </div>
        <div class="image-description">
            ${image.description || (window.jsTranslations['No description available'] || 'No description available')}
        </div>
        <div class="image-tags">
            ${(image.tags || []).map(tag => `<span class="tag">${tag}</span>`).join('')}
        </div>
        <div class="image-actions">
            <button class="action-btn pull" onclick="pullImage('${image.name}')">
                <i class="fas fa-download"></i>
                ${window.jsTranslations['Pull'] || 'Pull'}
            </button>
            <button class="action-btn details" onclick="showImageDetails('${image.name}')">
                <i class="fas fa-info"></i>
                ${window.jsTranslations['Details'] || 'Details'}
            </button>
        </div>
    `;
    
    return card;
}

function updateImagesCount(count) {
    const imagesCount = document.getElementById('imagesCount');
    if (imagesCount) {
        imagesCount.textContent = count;
    }
}

// Search Functions
function searchHub() {
    const query = document.getElementById('hubSearch').value.trim();
    
    console.log('Searching in cache for:', query);
    
    if (!query) {
        // If search is empty, load all images
        loadAllImages();
        return;
    }
    
    // Show loading state
    showLoadingIndicator();
    
    // Search in cached data
    fetch(`/docker-manager/api/hub/search/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log(`Found ${data.results.length} results for: ${query}`);
                displayImages(data.results);
                updateImagesCount(data.results.length);
                hideLoadingIndicator();
            } else {
                console.error('Search failed:', data.message);
                showError('Search failed: ' + data.message);
                hideLoadingIndicator();
            }
        })
        .catch(error => {
            console.error('Search error:', error);
            showError('Search failed: ' + error.message);
            hideLoadingIndicator();
        });
}

function clearSearch() {
    const searchInput = document.getElementById('hubSearch');
    if (searchInput) {
        searchInput.value = '';
        loadAllImages();
    }
}


// Tab Functions
function switchTab(tabName) {
    console.log('Switching to tab:', tabName);
    
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Load tab data
    loadTabData(tabName);
}

function loadTabData(tabName) {
    switch(tabName) {
        case 'images':
            loadPopularImages();
            break;
        case 'extensions':
            loadExtensions();
            break;
        case 'plugins':
            loadPlugins();
            break;
    }
}

function loadPopularImages() {
    console.log('Loading popular images...');
    
    // Show loading state
    showLoadingState();
    
    fetch('/docker-manager/api/hub/search/?page=1&page_size=25')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displaySearchResults(data.results, 'images');
            } else {
                showError('Failed to load images: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Load images error:', error);
            showError('Failed to load images: ' + error.message);
        })
        .finally(() => {
            hideLoadingState();
        });
}

function loadExtensions() {
    console.log('Loading extensions...');
    
    // For now, show placeholder
    const extensionsGrid = document.getElementById('extensionsGrid');
    if (extensionsGrid) {
        extensionsGrid.innerHTML = `
            <div class="loading-container">
                <div class="loading-content">
                    <i class="fas fa-puzzle-piece" style="font-size: 48px; color: #718096; margin-bottom: 16px;"></i>
                    <h3>Extensions Coming Soon</h3>
                    <p>Docker extensions will be available here</p>
                </div>
            </div>
        `;
    }
}

function loadPlugins() {
    console.log('Loading plugins...');
    
    // For now, show placeholder
    const pluginsGrid = document.getElementById('pluginsGrid');
    if (pluginsGrid) {
        pluginsGrid.innerHTML = `
            <div class="loading-container">
                <div class="loading-content">
                    <i class="fas fa-plug" style="font-size: 48px; color: #718096; margin-bottom: 16px;"></i>
                    <h3>Plugins Coming Soon</h3>
                    <p>Docker plugins will be available here</p>
                </div>
            </div>
        `;
    }
}

// Display Functions
function displaySearchResults(results, tabName) {
    console.log('Displaying results:', results.length, 'for tab:', tabName);
    
    const container = document.getElementById(`${tabName}Grid`);
    if (!container) return;
    
    if (results.length === 0) {
        container.innerHTML = `
            <div class="loading-container">
                <div class="loading-content">
                    <i class="fas fa-search" style="font-size: 48px; color: #718096; margin-bottom: 16px;"></i>
                    <h3>No Results Found</h3>
                    <p>Try adjusting your search criteria</p>
                </div>
            </div>
        `;
        return;
    }
    
    // Update count
    const countElement = document.getElementById(`${tabName}Count`);
    if (countElement) {
        countElement.textContent = results.length;
    }
    
    // Generate HTML for results
    let html = '';
    results.forEach(item => {
        html += generateResultCard(item, tabName);
    });
    
    container.innerHTML = html;
}

function generateResultCard(item, type) {
    const name = item.name || 'Unknown';
    const description = item.description || (window.jsTranslations['No description available'] || 'No description available');
    const stars = item.star_count || 0;
    const pulls = item.pull_count || 0;
    const official = item.namespace === 'library';
    
    return `
        <div class="image-card" data-image="${name}">
            <div class="image-header">
                <div class="image-name">
                    <i class="fas fa-cube"></i>
                    <span>${name}</span>
                    ${official ? '<span class="official-badge">' + (window.jsTranslations['Official'] || 'Official') + '</span>' : ''}
                </div>
                <div class="image-stats">
                    <span class="stars">
                        <i class="fas fa-star"></i>
                        ${stars.toLocaleString()}
                    </span>
                    <span class="pulls">
                        <i class="fas fa-download"></i>
                        ${pulls.toLocaleString()}
                    </span>
                </div>
            </div>
            <div class="image-description">
                ${description}
            </div>
            <div class="image-actions">
                <button class="action-btn pull" onclick="pullImage('${name}')">
                    <i class="fas fa-download"></i>
                    ${window.jsTranslations['Pull'] || 'Pull'}
                </button>
                <button class="action-btn details" onclick="showImageDetails('${name}')">
                    <i class="fas fa-info"></i>
                    ${window.jsTranslations['Details'] || 'Details'}
                </button>
            </div>
        </div>
    `;
}

// Action Functions
function pullImage(imageName) {
    console.log('Pulling image:', imageName);
    
    // Pull başladı bildirimi
    showPullNotification(imageName, 'starting');
    
    fetch('/docker-manager/api/hub/pull/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            image_name: imageName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Pull başarılı bildirimi
            showPullNotification(imageName, 'success');
        } else {
            // Pull hata bildirimi
            showPullNotification(imageName, 'error', data.message);
        }
    })
    .catch(error => {
        console.error('Pull error:', error);
        // Pull hata bildirimi
        showPullNotification(imageName, 'error', error.message);
    });
}

function showImageDetails(imageName) {
    console.log('Showing details for image:', imageName);
    
    // Fetch image details from API
    fetch(`/docker-manager/api/hub/repository/library/${imageName}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Use the new modal function
                if (typeof showImageDetailsModal === 'function') {
                    showImageDetailsModal(imageName, data.repository);
                } else {
                    console.error('showImageDetailsModal function not found');
                    showError(window.jsTranslations['Modal function not available'] || 'Modal function not available');
                }
            } else {
                showError((window.jsTranslations['Failed to load image details'] || 'Failed to load image details') + ': ' + data.message);
            }
        })
        .catch(error => {
            console.error('Image details error:', error);
            showError((window.jsTranslations['Error loading image details'] || 'Error loading image details') + ': ' + error.message);
        });
}

// Modal functions are now handled by image_details_modal.js

// Cache Functions
function refreshCache() {
    console.log('Refreshing cache...');
    
    showLoadingState();
    
    fetch('/docker-manager/api/hub/cache/info/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(window.jsTranslations['Cache refreshed'] || 'Cache refreshed', 'success');
                // Reload current tab
                const activeTab = document.querySelector('.tab-btn.active').dataset.tab;
                loadTabData(activeTab);
            } else {
                showError((window.jsTranslations['Cache refresh failed'] || 'Cache refresh failed') + ': ' + data.message);
            }
        })
        .catch(error => {
            console.error('Cache refresh error:', error);
            showError((window.jsTranslations['Cache refresh failed'] || 'Cache refresh failed') + ': ' + error.message);
        })
        .finally(() => {
            hideLoadingState();
        });
}

function refreshAllData() {
    console.log('Refreshing cache data...');
    
    // Show progress modal
    showProgressModal();
    
    // Start refresh process
    fetch('/docker-manager/api/hub/refresh/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update progress to 100%
            updateProgress(100, window.jsTranslations['Cache refreshed!'] || 'Cache refreshed!', {
                images_loaded: data.images_loaded || 0,
                categories_loaded: data.categories_loaded || 0,
                total_time: 0
            });
            
            // Show success message
            setTimeout(() => {
                hideProgressModal();
                showNotification(window.jsTranslations['Cache refreshed successfully!'] || 'Cache refreshed successfully!', 'success');
                
                // Reload all images
                loadAllImages();
            }, 1000);
        } else {
            hideProgressModal();
            showError((window.jsTranslations['Refresh failed'] || 'Refresh failed') + ': ' + data.message);
        }
    })
    .catch(error => {
        console.error('Refresh error:', error);
        hideProgressModal();
        showError((window.jsTranslations['Refresh failed'] || 'Refresh failed') + ': ' + error.message);
    });
}

function showProgressModal() {
    const modal = document.getElementById('progressModal');
    if (modal) {
        modal.style.display = 'flex';
        
        // Reset progress
        updateProgress(0, window.jsTranslations['Starting refresh process...'] || 'Starting refresh process...', {
            images_loaded: 0,
            categories_loaded: 0,
            total_time: 0
        });
        
        // Start progress simulation
        simulateProgress();
    }
}

function hideProgressModal() {
    const modal = document.getElementById('progressModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function updateProgress(percentage, message, results = null) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const progressStatus = document.getElementById('progressStatus');
    const progressMessage = document.getElementById('progressMessage');
    const imagesLoaded = document.getElementById('imagesLoaded');
    const categoriesLoaded = document.getElementById('categoriesLoaded');
    const timeElapsed = document.getElementById('timeElapsed');
    
    if (progressFill) {
        progressFill.style.width = percentage + '%';
    }
    
    if (progressText) {
        progressText.textContent = percentage + '%';
    }
    
    if (progressStatus) {
        progressStatus.textContent = message;
    }
    
    if (progressMessage) {
        progressMessage.textContent = message;
    }
    
    if (results) {
        if (imagesLoaded) {
            imagesLoaded.textContent = results.images_loaded || 0;
        }
        
        if (categoriesLoaded) {
            categoriesLoaded.textContent = results.categories_loaded || 0;
        }
        
        if (timeElapsed) {
            timeElapsed.textContent = (results.total_time || 0) + 's';
        }
    }
}

function simulateProgress() {
    let progress = 0;
    const steps = [
        { progress: 10, message: window.jsTranslations['Initializing refresh...'] || 'Initializing refresh...' },
        { progress: 25, message: window.jsTranslations['Loading categories...'] || 'Loading categories...' },
        { progress: 50, message: window.jsTranslations['Loading popular images...'] || 'Loading popular images...' },
        { progress: 75, message: window.jsTranslations['Optimizing cache...'] || 'Optimizing cache...' },
        { progress: 90, message: window.jsTranslations['Finalizing refresh...'] || 'Finalizing refresh...' },
        { progress: 100, message: window.jsTranslations['Refresh completed!'] || 'Refresh completed!' }
    ];
    
    let currentStep = 0;
    
    const interval = setInterval(() => {
        if (currentStep < steps.length) {
            const step = steps[currentStep];
            updateProgress(step.progress, step.message);
            currentStep++;
        } else {
            clearInterval(interval);
        }
    }, 800);
}

function clearCache() {
    console.log('Clearing cache...');
    
    if (!confirm(window.jsTranslations['Are you sure you want to clear the cache?'] || 'Are you sure you want to clear the cache?')) {
        return;
    }
    
    showLoadingState();
    
    fetch('/docker-manager/api/hub/cache/clear/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(window.jsTranslations['Cache cleared'] || 'Cache cleared', 'success');
                // Reload current tab
                const activeTab = document.querySelector('.tab-btn.active').dataset.tab;
                loadTabData(activeTab);
            } else {
                showError((window.jsTranslations['Cache clear failed'] || 'Cache clear failed') + ': ' + data.message);
            }
        })
        .catch(error => {
            console.error('Cache clear error:', error);
            showError((window.jsTranslations['Cache clear failed'] || 'Cache clear failed') + ': ' + error.message);
        })
    .finally(() => {
        hideLoadingState();
    });
}

// Utility Functions
function showLoadingState() {
    const activeTab = document.querySelector('.tab-btn.active').dataset.tab;
    const container = document.getElementById(`${activeTab}Grid`);
    if (container) {
        container.innerHTML = `
            <div class="loading-container">
                <div class="loading-content">
                    <div class="loading-spinner">
                        <i class="fas fa-spinner fa-spin"></i>
                    </div>
                    <h3>${window.jsTranslations['Loading...'] || 'Loading...'}</h3>
                    <p>${window.jsTranslations['Please wait while we fetch the data'] || 'Please wait while we fetch the data'}</p>
                </div>
            </div>
        `;
    }
}

function hideLoadingState() {
    // Loading state will be replaced by actual content
}

function showError(message) {
    console.error(message);
    showNotification(message, 'error');
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

// Pull Notification System
function showPullNotification(imageName, status, errorMessage = '') {
    // Mevcut pull bildirimlerini kaldır
    const existingNotifications = document.querySelectorAll('.pull-notification');
    existingNotifications.forEach(notification => notification.remove());
    
    let message = '';
    let type = 'info';
    let icon = 'fa-info-circle';
    
    switch (status) {
        case 'starting':
            message = (window.jsTranslations['Pulling'] || 'Pulling') + ' ' + imageName + '...';
            type = 'info';
            icon = 'fa-download';
            break;
        case 'success':
            message = imageName + ' ' + (window.jsTranslations['pulled successfully'] || 'pulled successfully!');
            type = 'success';
            icon = 'fa-check-circle';
            break;
        case 'error':
            message = (window.jsTranslations['Failed to pull'] || 'Failed to pull') + ' ' + imageName;
            if (errorMessage) {
                message += ': ' + errorMessage;
            }
            type = 'error';
            icon = 'fa-exclamation-circle';
            break;
    }
    
    // Bildirim oluştur
    const notification = document.createElement('div');
    notification.className = `pull-notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Bildirim stilleri
    const colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'info': '#007bff'
    };
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${colors[type] || colors.info};
        color: white;
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 12px;
        max-width: 400px;
        animation: slideInFromRight 0.3s ease;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;
    
    // Bildirim içeriği stilleri
    const content = notification.querySelector('.notification-content');
    content.style.cssText = `
        display: flex;
        align-items: center;
        gap: 8px;
        flex: 1;
        font-size: 14px;
        font-weight: 500;
    `;
    
    // Kapatma butonu stilleri
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.style.cssText = `
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        transition: background 0.2s ease;
        opacity: 0.8;
    `;
    
    closeBtn.addEventListener('mouseenter', function() {
        this.style.background = 'rgba(255, 255, 255, 0.2)';
        this.style.opacity = '1';
    });
    
    closeBtn.addEventListener('mouseleave', function() {
        this.style.background = 'none';
        this.style.opacity = '0.8';
    });
    
    document.body.appendChild(notification);
    
    // Animasyon CSS'i ekle (eğer yoksa)
    if (!document.getElementById('pull-notification-styles')) {
        const style = document.createElement('style');
        style.id = 'pull-notification-styles';
        style.textContent = `
            @keyframes slideInFromRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOutToRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Otomatik kaldırma süresi
    let autoRemoveTime = 3000; // 3 saniye
    if (status === 'success') {
        autoRemoveTime = 4000; // Başarılı pull için 4 saniye
    } else if (status === 'error') {
        autoRemoveTime = 5000; // Hata için 5 saniye
    }
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOutToRight 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
    }, autoRemoveTime);
}

