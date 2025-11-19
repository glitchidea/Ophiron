/**
 * Ophiron Dashboard JavaScript
 * Special functions for the Dashboard page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard
    initDashboard();
    
    // Add event listeners
    setupEventListeners();
    
    // Start animations
    startAnimations();
});

/**
 * Initialize the Dashboard
 */
function initDashboard() {
    console.log('Ophiron Dashboard initialized');
    
    // Show user info
    showUserInfo();
    
    // Check system status
    checkSystemStatus();
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Logout button
    const logoutBtn = document.querySelector('.dashboard-logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    // Action buttons
    const actionBtns = document.querySelectorAll('.dashboard-action-btn');
    actionBtns.forEach(btn => {
        btn.addEventListener('click', handleActionClick);
    });
    
    // Stat cards
    const statCards = document.querySelectorAll('.dashboard-stat-card');
    statCards.forEach(card => {
        card.addEventListener('click', handleStatCardClick);
    });
}

/**
 * Start animations
 */
function startAnimations() {
    // Animation for stat cards
    const statCards = document.querySelectorAll('.dashboard-stat-card');
    statCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Success message animation
    const successMsg = document.querySelector('.dashboard-success');
    if (successMsg) {
        setTimeout(() => {
            successMsg.style.opacity = '1';
            successMsg.style.transform = 'translateY(0)';
        }, 500);
    }
}

/**
 * Show user info
 */
function showUserInfo() {
    const welcomeElement = document.querySelector('.dashboard-welcome');
    if (welcomeElement) {
    // Add real-time clock
        const timeElement = document.createElement('span');
        timeElement.className = 'dashboard-time';
        timeElement.style.fontSize = '0.9em';
        timeElement.style.opacity = '0.8';
        timeElement.style.marginLeft = '10px';
        
        updateTime(timeElement);
        setInterval(() => updateTime(timeElement), 1000);
        
        welcomeElement.appendChild(timeElement);
    }
}

/**
 * Update time
 */
function updateTime(element) {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    element.textContent = `(${timeString})`;
}

/**
 * Check system status
 */
function checkSystemStatus() {
    // System status check
    console.log('Checking system status...');
    
    // Real system status checks could be implemented here
    // For now, just logging
}

/**
 * Handle logout
 */
function handleLogout(event) {
    event.preventDefault();
    
    // Show confirmation message
    if (confirm('Are you sure you want to log out?')) {
        // Loading state
        const btn = event.target;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging out...';
        btn.disabled = true;
        
        // Logout işlemi
        fetch('/logout/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => {
            if (response.ok) {
                window.location.href = '/login/';
            } else {
                throw new Error('Logout failed');
            }
        })
        .catch(error => {
            console.error('Logout error:', error);
            btn.innerHTML = originalText;
            btn.disabled = false;
            alert('An error occurred while logging out. Please try again.');
        });
    }
}

/**
 * Handle action button click
 */
function handleActionClick(event) {
    const action = event.currentTarget.dataset.action;
    
    if (action) {
        // Perform action-specific behavior
        switch (action) {
            case 'security':
                showSecurityPanel();
                break;
            case 'monitoring':
                showMonitoringPanel();
                break;
            case 'users':
                showUsersPanel();
                break;
            case 'settings':
                showSettingsPanel();
                break;
            default:
                console.log('Unknown action:', action);
        }
    }
}

/**
 * Handle stat card click
 */
function handleStatCardClick(event) {
    const statType = event.currentTarget.dataset.stat;
    
    if (statType) {
        // Show stat details
        showStatDetails(statType);
    }
}

/**
 * Show security panel
 */
function showSecurityPanel() {
    showNotification('Security settings page will be added soon', 'info');
}

/**
 * Show monitoring panel
 */
function showMonitoringPanel() {
    showNotification('System monitoring page will be added soon', 'info');
}

/**
 * Show user management panel
 */
function showUsersPanel() {
    showNotification('User management page will be added soon', 'info');
}

/**
 * Show settings panel
 */
function showSettingsPanel() {
    showNotification('General settings page will be added soon', 'info');
}

/**
 * Show stat details
 */
function showStatDetails(statType) {
    showNotification('Detail information will be added soon', 'info');
}

/**
 * Get CSRF token
 */
function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

/**
 * Refresh Dashboard
 */
function refreshDashboard() {
    location.reload();
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `dashboard-notification dashboard-notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#d4edda' : type === 'error' ? '#f8d7da' : '#d1ecf1'};
        color: ${type === 'success' ? '#155724' : type === 'error' ? '#721c24' : '#0c5460'};
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 10px;
        animation: slideInRight 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
