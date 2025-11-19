/**
 * Alert Management JavaScript
 * Manages the alert management page functionality
 */

let currentPage = 1;
let isLoading = false;
let hasMore = true;
let currentFilters = {};
let currentAlertId = null;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚨 Initializing Alert Management...');
    loadAlerts();
    setupEventListeners();
});

function setupEventListeners() {
    // Search input with debounce
    const searchInput = document.getElementById('searchAlerts');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchAlerts();
            }, 300);
        });
    }
}

function loadAlerts(reset = false) {
    if (isLoading) return;
    
    if (reset) {
        currentPage = 1;
        hasMore = true;
        document.getElementById('alertList').innerHTML = '';
    }
    
    isLoading = true;
    showLoading(true);
    
    const alertType = document.getElementById('alertType')?.value || '';
    const alertStatus = document.getElementById('alertStatus')?.value || '';
    const dateRange = document.getElementById('dateRange')?.value || '30';
    const searchTerm = document.getElementById('searchAlerts')?.value || '';
    
    console.log('Filter values:', { alertType, alertStatus, dateRange, searchTerm });
    
    const params = new URLSearchParams({
        type: alertType,
        status: alertStatus,
        date_range: dateRange,
        page: currentPage,
        per_page: 20,
        search: searchTerm
    });
    
    console.log('API URL:', `/api/alert/?${params}`);
    
    fetch(`/api/alert/?${params}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('=== ALERT API RESPONSE ===');
            console.log('Success:', data.success);
            console.log('Alerts count:', data.alerts ? data.alerts.length : 0);
            console.log('Pagination:', data.pagination);
            
            if (data.success && data.alerts) {
                if (reset) {
                    document.getElementById('alertList').innerHTML = '';
                }
                
                if (data.alerts.length === 0 && currentPage === 1) {
                    showEmptyState();
                } else {
                    hideEmptyState();
                    renderAlerts(data.alerts);
                    updatePagination(data.pagination);
                    updateStatistics(data.alerts);
                }
                
                hasMore = data.pagination.has_next;
                currentPage++;
            } else {
                console.warn('No alerts data received:', data);
                if (currentPage === 1) {
                    showEmptyState();
                }
            }
        })
        .catch(error => {
            console.error('Error loading alerts:', error);
            showError('Failed to load alerts: ' + error.message);
        })
        .finally(() => {
            isLoading = false;
            showLoading(false);
        });
}

function renderAlerts(alerts) {
    const alertList = document.getElementById('alertList');
    
    alerts.forEach(alert => {
        const alertElement = createAlertElement(alert);
        alertList.appendChild(alertElement);
    });
}

function createAlertElement(alert) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert-item';
    alertDiv.setAttribute('data-alert-id', alert.id);
    
    const typeClass = alert.type || 'info';
    const isResolved = alert.is_resolved;
    
    alertDiv.innerHTML = `
        <div class="alert-icon ${typeClass}">
            <i class="fas fa-${getAlertIcon(alert.type)}"></i>
        </div>
        <div class="alert-content">
            <div class="alert-header">
                <h3 class="alert-title">${escapeHtml(alert.title)}</h3>
                <span class="alert-type ${typeClass}">${typeClass.toUpperCase()}</span>
            </div>
            <p class="alert-message">${escapeHtml(alert.message)}</p>
            <div class="alert-meta">
                ${alert.service ? `
                    <div class="alert-service">
                        <i class="fas fa-server"></i>
                        <span>${escapeHtml(alert.service)}</span>
                    </div>
                ` : ''}
                <div class="alert-time">
                    <i class="fas fa-clock"></i>
                    <span>${formatTime(alert.created_at)}</span>
                </div>
                ${isResolved && alert.resolved_at ? `
                    <div class="alert-time">
                        <i class="fas fa-check"></i>
                        <span>Resolved ${formatTime(alert.resolved_at)}</span>
                    </div>
                ` : ''}
            </div>
            ${alert.notes ? `
                <div class="alert-notes">
                    <h4><i class="fas fa-sticky-note"></i> Notes</h4>
                    <p>${escapeHtml(alert.notes)}</p>
                </div>
            ` : ''}
        </div>
        <div class="alert-actions">
            <button class="alert-note-btn ${alert.notes ? 'has-note' : ''}" 
                    onclick="openNoteModal(${alert.id})"
                    title="${alert.notes ? 'Edit Note' : 'Add Note'}">
                <i class="fas fa-sticky-note"></i>
                ${alert.notes ? 'Edit Note' : 'Add Note'}
            </button>
            <button class="alert-resolve-btn ${isResolved ? 'resolved' : 'unresolved'}" 
                    onclick="toggleAlertStatus(${alert.id}, ${isResolved})"
                    title="${isResolved ? window.jsTranslations.mark_unresolved : window.jsTranslations.mark_resolved}">
                <i class="fas fa-${isResolved ? 'undo' : 'check'}"></i>
                ${isResolved ? window.jsTranslations.resolved : window.jsTranslations.unresolved}
            </button>
        </div>
    `;
    
    return alertDiv;
}

function getAlertIcon(type) {
    switch (type) {
        case 'critical':
            return 'times-circle';
        case 'warning':
            return 'exclamation-triangle';
        case 'error':
            return 'exclamation-circle';
        case 'info':
        default:
            return 'info-circle';
    }
}

function toggleAlertStatus(alertId, isResolved) {
    const action = isResolved ? 'unresolve' : 'resolve';
    const confirmMessage = isResolved ? 
        window.jsTranslations.confirm_unresolve : 
        window.jsTranslations.confirm_resolve;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    const endpoint = isResolved ? 
        `/dashboard-api/api/alerts/${alertId}/unresolve/` : 
        `/dashboard-api/api/alerts/${alertId}/resolve/`;
    
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`✅ Alert ${alertId} ${action}ed successfully`);
            
            // Update the alert element
            const alertElement = document.querySelector(`[data-alert-id="${alertId}"]`);
            if (alertElement) {
                const button = alertElement.querySelector('.alert-resolve-btn');
                const newStatus = !isResolved;
                
                button.className = `alert-resolve-btn ${newStatus ? 'resolved' : 'unresolved'}`;
                button.innerHTML = `
                    <i class="fas fa-${newStatus ? 'undo' : 'check'}"></i>
                    ${newStatus ? window.jsTranslations.resolved : window.jsTranslations.unresolved}
                `;
                button.setAttribute('onclick', `toggleAlertStatus(${alertId}, ${newStatus})`);
                
                // Add resolved time if resolved
                if (newStatus) {
                    const metaDiv = alertElement.querySelector('.alert-meta');
                    const resolvedTime = document.createElement('div');
                    resolvedTime.className = 'alert-time';
                    resolvedTime.innerHTML = `
                        <i class="fas fa-check"></i>
                        <span>Resolved ${formatTime(new Date().toISOString())}</span>
                    `;
                    metaDiv.appendChild(resolvedTime);
                }
            }
            
            // Show success message
            showNotification(
                isResolved ? window.jsTranslations.alert_unresolved : window.jsTranslations.alert_resolved,
                'success'
            );
            
            // Refresh statistics
            loadAlerts(true);
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error(`❌ Error ${action}ing alert:`, error);
        showNotification(window.jsTranslations.error_occurred + ': ' + error.message, 'error');
    });
}

function updateStatistics(alerts) {
    const stats = {
        critical: 0,
        warning: 0,
        error: 0,
        info: 0,
        resolved: 0
    };
    
    alerts.forEach(alert => {
        if (alert.is_resolved) {
            stats.resolved++;
        } else {
            stats[alert.type] = (stats[alert.type] || 0) + 1;
        }
    });
    
    // Update stat cards
    document.getElementById('criticalCount').textContent = stats.critical;
    document.getElementById('warningCount').textContent = stats.warning;
    document.getElementById('errorCount').textContent = stats.error;
    document.getElementById('infoCount').textContent = stats.info;
    document.getElementById('resolvedCount').textContent = stats.resolved;
}

function updatePagination(pagination) {
    const loadMoreSection = document.getElementById('loadMoreSection');
    const paginationInfo = document.getElementById('paginationInfo');
    
    if (pagination.has_next) {
        loadMoreSection.style.display = 'flex';
    } else {
        loadMoreSection.style.display = 'none';
    }
    
    if (pagination.total_count > 0) {
        paginationInfo.style.display = 'flex';
        document.getElementById('paginationText').textContent = 
            `Showing ${((pagination.current_page - 1) * 20) + 1}-${Math.min(pagination.current_page * 20, pagination.total_count)} of ${pagination.total_count} alerts`;
    } else {
        paginationInfo.style.display = 'none';
    }
}

function filterAlerts() {
    console.log('🔍 Filtering alerts...');
    loadAlerts(true);
}

function searchAlerts() {
    console.log('🔍 Searching alerts...');
    loadAlerts(true);
}

function loadMoreAlerts() {
    if (hasMore && !isLoading) {
        console.log('📄 Loading more alerts...');
        loadAlerts(false);
    }
}

function refreshAlerts() {
    console.log('🔄 Refreshing alerts...');
    loadAlerts(true);
}

function exportAlerts() {
    console.log('📥 Exporting alerts...');
    
    const alertType = document.getElementById('alertType')?.value || '';
    const alertStatus = document.getElementById('alertStatus')?.value || '';
    const dateRange = document.getElementById('dateRange')?.value || '30';
    
    const params = new URLSearchParams({
        type: alertType,
        status: alertStatus,
        date_range: dateRange,
        export: 'csv'
    });
    
    const url = `/api/alert/export/?${params}`;
    window.open(url, '_blank');
}

function showLoading(show) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = show ? 'flex' : 'none';
    }
}

function showEmptyState() {
    const emptyState = document.getElementById('emptyState');
    if (emptyState) {
        emptyState.style.display = 'flex';
    }
}

function hideEmptyState() {
    const emptyState = document.getElementById('emptyState');
    if (emptyState) {
        emptyState.style.display = 'none';
    }
}

function showError(message) {
    console.error('❌ Error:', message);
    // You can implement a toast notification here
    alert(message);
}

function showNotification(message, type = 'info') {
    console.log(`📢 ${type.toUpperCase()}: ${message}`);
    // You can implement a toast notification here
    // For now, just log to console
}

function formatTime(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diff = now - time;
    
    if (diff < 60000) { // Less than 1 minute
        return window.jsTranslations.just_now || 'Just now';
    } else if (diff < 3600000) { // Less than 1 hour
        return `${Math.floor(diff / 60000)}${window.jsTranslations.minutes_ago || 'm ago'}`;
    } else if (diff < 86400000) { // Less than 1 day
        return `${Math.floor(diff / 3600000)}${window.jsTranslations.hours_ago || 'h ago'}`;
    } else {
        return `${Math.floor(diff / 86400000)}${window.jsTranslations.days_ago || 'd ago'}`;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

function openNoteModal(alertId) {
    console.log(`📝 Opening note modal for alert ${alertId}`);
    currentAlertId = alertId;
    
    // Get current note if exists
    const alertElement = document.querySelector(`[data-alert-id="${alertId}"]`);
    const notesDiv = alertElement?.querySelector('.alert-notes p');
    const currentNote = notesDiv ? notesDiv.textContent : '';
    
    document.getElementById('noteText').value = currentNote;
    document.getElementById('noteModal').style.display = 'flex';
}

function closeNoteModal() {
    console.log('❌ Closing note modal');
    document.getElementById('noteModal').style.display = 'none';
    currentAlertId = null;
    document.getElementById('noteText').value = '';
}

async function saveNote() {
    if (!currentAlertId) {
        console.error('❌ No alert ID selected');
        return;
    }
    
    const noteText = document.getElementById('noteText').value.trim();
    
    if (!noteText) {
        alert('Please enter a note');
        return;
    }
    
    try {
        console.log(`💾 Saving note for alert ${currentAlertId}...`);
        
        const response = await fetch(`/api/alert/${currentAlertId}/note/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                note: noteText
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            console.log(`✅ Note saved successfully for alert ${currentAlertId}`);
            
            // Update the alert element
            const alertElement = document.querySelector(`[data-alert-id="${currentAlertId}"]`);
            if (alertElement) {
                // Update or create notes section
                let notesDiv = alertElement.querySelector('.alert-notes');
                if (!notesDiv) {
                    notesDiv = document.createElement('div');
                    notesDiv.className = 'alert-notes';
                    notesDiv.innerHTML = '<h4><i class="fas fa-sticky-note"></i> Notes</h4><p></p>';
                    alertElement.querySelector('.alert-content').appendChild(notesDiv);
                }
                
                notesDiv.querySelector('p').textContent = noteText;
                
                // Update note button
                const noteBtn = alertElement.querySelector('.alert-note-btn');
                noteBtn.className = 'alert-note-btn has-note';
                noteBtn.innerHTML = '<i class="fas fa-sticky-note"></i> Edit Note';
                noteBtn.title = 'Edit Note';
            }
            
            closeNoteModal();
            showNotification('Note saved successfully', 'success');
        } else {
            throw new Error(result.error || 'Unknown error');
        }
        
    } catch (error) {
        console.error('❌ Error saving note:', error);
        showNotification('Error saving note: ' + error.message, 'error');
    }
}

// Global functions for onclick handlers
window.toggleAlertStatus = toggleAlertStatus;
window.filterAlerts = filterAlerts;
window.searchAlerts = searchAlerts;
window.loadMoreAlerts = loadMoreAlerts;
window.refreshAlerts = refreshAlerts;
window.exportAlerts = exportAlerts;
window.openNoteModal = openNoteModal;
window.closeNoteModal = closeNoteModal;
window.saveNote = saveNote;
