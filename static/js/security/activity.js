/*
Ophiron Security Activity JavaScript
Account activity history page functions
*/

// Global variables
let currentPage = 1;
let isLoading = false;
let hasMoreData = true;

document.addEventListener('DOMContentLoaded', function() {
    initActivityPage();
    setupFilters();
    loadActivityData();
});

function initActivityPage() {
    console.log('Ophiron Activity History initialized');
}

function setupFilters() {
    const activityType = document.getElementById('activityType');
    const dateRange = document.getElementById('dateRange');
    const statusFilter = document.getElementById('statusFilter');
    
    if (activityType) {
        activityType.addEventListener('change', filterActivities);
    }
    
    if (dateRange) {
        dateRange.addEventListener('change', filterActivities);
    }
    
    if (statusFilter) {
        statusFilter.addEventListener('change', filterActivities);
    }
}

function filterActivities() {
    currentPage = 1;
    hasMoreData = true;
    loadActivityData();
}

function loadActivityData() {
    if (isLoading) return;
    
    isLoading = true;
    showLoading(true);
    
    const activityType = document.getElementById('activityType').value;
    const dateRange = document.getElementById('dateRange').value;
    const statusFilter = document.getElementById('statusFilter').value;
    
    console.log('Filter values:', { activityType, dateRange, statusFilter });
    
    const params = new URLSearchParams({
        type: activityType,
        date_range: dateRange,
        status: statusFilter,
        page: currentPage,
        per_page: 20
    });
    
    console.log('API URL:', `/api/activity/?${params}`);
    
    fetch(`/api/activity/?${params}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('=== API RESPONSE ===');
            console.log('Full API Response:', data);
            console.log('Success:', data?.success);
            console.log('Activities:', data?.activities);
            console.log('Activities Length:', data?.activities?.length || 0);
            
            if (data && data.success) {
                console.log('API Success - Processing activities');
                
                const activities = data.activities || [];
                console.log('Activities to process:', activities);
                
                if (currentPage === 1) {
                    console.log('First page - updating activity list');
                    updateActivityList(activities);
                } else {
                    console.log('Additional page - appending to activity list');
                    appendActivityList(activities);
                }
                
                updatePagination(data.pagination || {});
                hasMoreData = data.pagination?.has_next || false;
                
                // Show success message if no activities found
                if (activities.length === 0) {
                    showNotification(window.jsTranslations.no_activities_found || 'No activities found with the selected filters', 'info');
                }
            } else {
                console.error('API Error Response:', data);
                const errorMsg = data?.error || (window.jsTranslations.error_loading_activities || 'An error occurred while loading activities');
                console.error('Error message:', errorMsg);
                showNotification(errorMsg, 'error');
            }
        })
        .catch(error => {
            console.error('Activity load error:', error);
            showNotification(window.jsTranslations.error_loading_activities || 'An error occurred while loading activities', 'error');
        })
        .finally(() => {
            isLoading = false;
            showLoading(false);
        });
}

function updateActivityList(activities) {
    console.log('=== UPDATE ACTIVITY LIST START ===');
    console.log('Activities received:', activities);
    console.log('Activities length:', activities?.length || 0);
    
    const activityList = document.getElementById('activityList');
    const emptyState = document.getElementById('emptyState');
    const loadMoreSection = document.getElementById('loadMoreSection');
    
    if (!activityList) {
        console.error('Activity list element not found!');
        return;
    }
    
    console.log('Activity list element found:', activityList);
    
    // Clear existing content completely
    activityList.innerHTML = '';
    console.log('Cleared activity list innerHTML');
    
    if (!activities || activities.length === 0) {
        console.log('No activities - showing empty state');
        if (emptyState) {
            emptyState.style.display = 'block';
        }
        if (loadMoreSection) {
            loadMoreSection.style.display = 'none';
        }
        return;
    }
    
    console.log('Hiding empty state, showing activities');
    if (emptyState) {
        emptyState.style.display = 'none';
    }
    
    // Create activities dynamically
    activities.forEach((activity, index) => {
        console.log(`Creating activity ${index + 1}/${activities.length}:`, activity.title);
        try {
            const activityItem = createActivityItem(activity);
            activityList.appendChild(activityItem);
            console.log(`Activity ${index + 1} added to DOM`);
        } catch (error) {
            console.error(`Error creating activity ${index + 1}:`, error);
        }
    });
    
    console.log('=== UPDATE ACTIVITY LIST END ===');
}

function appendActivityList(activities) {
    const activityList = document.getElementById('activityList');
    if (!activityList) return;
    
    activities.forEach(activity => {
        const activityItem = createActivityItem(activity);
        activityList.appendChild(activityItem);
    });
}

function createActivityItem(activity) {
    console.log('Creating activity item for:', activity?.title || 'Unknown');
    
    if (!activity) {
        console.error('Activity data is null or undefined');
        return document.createElement('div');
    }
    
    const item = document.createElement('div');
    item.className = 'activity-item';
    
    const statusClass = activity.status_class || activity.status || 'info';
    const iconClass = activity.icon_class || getActivityIcon(activity.activity_type);
    
    // Escape HTML to prevent XSS
    const title = escapeHtml(activity.title || 'Unknown Activity');
    const description = escapeHtml(activity.description || 'No description');
    const deviceInfo = escapeHtml(activity.device_info || 'Unknown');
    
    item.innerHTML = `
        <div class="activity-icon ${statusClass}">
            <i class="${iconClass}"></i>
        </div>
        <div class="activity-content">
            <div class="activity-header">
                <h3>${title}</h3>
                <span class="activity-time">${formatTime(activity.created_at)}</span>
            </div>
            <p class="activity-description">${description}</p>
            <div class="activity-details">
                <span class="activity-device">${deviceInfo}</span>
            </div>
        </div>
        <div class="activity-status ${statusClass}">
            <i class="${getStatusIcon(activity.status)}"></i>
            ${getStatusText(activity.status)}
        </div>
    `;
    
    console.log('Activity item created successfully');
    return item;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getActivityIcon(type) {
    const icons = {
        'login': 'fas fa-sign-in-alt',
        'logout': 'fas fa-sign-out-alt',
        'password_change': 'fas fa-key',
        '2fa_enable': 'fas fa-shield-alt',
        '2fa_disable': 'fas fa-shield-alt',
        '2fa_verify': 'fas fa-shield-alt',
        'profile_update': 'fas fa-user-edit',
        'profile_image_upload': 'fas fa-image',
        'profile_image_remove': 'fas fa-trash',
        'email_change': 'fas fa-envelope',
        'name_change': 'fas fa-user',
        'language_change': 'fas fa-language',
        'timezone_change': 'fas fa-clock',
        'api_key_regenerate': 'fas fa-key',
        'api_secret_change': 'fas fa-lock',
        'system_preference_change': 'fas fa-cog',
        'failed_login': 'fas fa-times',
        'security_event': 'fas fa-exclamation-triangle'
    };
    return icons[type] || 'fas fa-info-circle';
}

function getStatusIcon(status) {
    const icons = {
        'success': 'fas fa-check-circle',
        'failed': 'fas fa-times-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    };
    return icons[status] || 'fas fa-info-circle';
}

function getStatusText(status) {
    const texts = {
        'success': window.jsTranslations.successful || 'Successful',
        'failed': window.jsTranslations.failed || 'Failed',
        'warning': window.jsTranslations.warning || 'Warning',
        'info': window.jsTranslations.info || 'Info'
    };
    return texts[status] || (window.jsTranslations.unknown || 'Unknown');
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    
    // Use locale-specific formatting (English default)
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

function showLoading(show) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = show ? 'block' : 'none';
    }
}

function updatePagination(pagination) {
    const loadMoreSection = document.getElementById('loadMoreSection');
    const paginationInfo = document.getElementById('paginationInfo');
    const paginationText = document.getElementById('paginationText');
    
    if (pagination.has_next) {
        loadMoreSection.style.display = 'block';
    } else {
        loadMoreSection.style.display = 'none';
    }
    
    if (paginationInfo && paginationText) {
        paginationInfo.style.display = 'block';
        const pageText = window.jsTranslations.page || 'Page';
        const totalText = window.jsTranslations.total || 'Total';
        const activitiesText = window.jsTranslations.activities || 'activities';
        paginationText.textContent = `${pageText} ${pagination.current_page} / ${pagination.total_pages} (${totalText} ${pagination.total_count} ${activitiesText})`;
    }
}

function refreshActivity() {
    currentPage = 1;
    hasMoreData = true;
    showNotification(window.jsTranslations.refreshing_activity || 'Refreshing activity history...', 'info');
    loadActivityData();
}

function exportActivity() {
    showNotification(window.jsTranslations.exporting_activity || 'Exporting activity history...', 'info');
    
    const activityType = document.getElementById('activityType').value;
    const dateRange = document.getElementById('dateRange').value;
    const statusFilter = document.getElementById('statusFilter').value;
    
    const params = new URLSearchParams({
        type: activityType,
        date_range: dateRange,
        status: statusFilter
    });
    
    fetch(`/api/activity/export/?${params}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Export failed');
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ophiron-activity-${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            showNotification(window.jsTranslations.export_success || 'Activity history exported successfully', 'success');
        })
        .catch(error => {
            console.error('Export error:', error);
            showNotification(window.jsTranslations.export_error || 'An error occurred during export', 'error');
        });
}

function loadMoreActivity() {
    if (!hasMoreData || isLoading) return;
    
    currentPage++;
    loadActivityData();
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create new notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#48bb78' : type === 'error' ? '#e53e3e' : '#4299e1'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 8px;
    }
`;
document.head.appendChild(style);
