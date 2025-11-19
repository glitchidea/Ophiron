/*
Ophiron Security Sessions JavaScript
Active sessions page functions - fetching data from Core
*/

document.addEventListener('DOMContentLoaded', function() {
    initSessionsPage();
});

function initSessionsPage() {
    console.log('Ophiron Active Sessions initialized');
    
    // Initialize history selection functionality
    updateDeleteButton();
}

// History selection functions
function toggleSelectAllHistory() {
    const selectAllCheckbox = document.getElementById('selectAllHistory');
    const historyCheckboxes = document.querySelectorAll('.history-checkbox');
    
    historyCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    
    updateDeleteButton();
}

function updateDeleteButton() {
    const checkedBoxes = document.querySelectorAll('.history-checkbox:checked');
    const deleteButton = document.getElementById('deleteSelectedHistory');
    const selectAllCheckbox = document.getElementById('selectAllHistory');
    
    if (checkedBoxes.length > 0) {
        deleteButton.disabled = false;
        deleteButton.textContent = `Delete Selected (${checkedBoxes.length})`;
    } else {
        deleteButton.disabled = true;
        deleteButton.textContent = 'Delete Selected';
    }
    
    // Update select all checkbox state
    const allCheckboxes = document.querySelectorAll('.history-checkbox');
    if (checkedBoxes.length === allCheckboxes.length && allCheckboxes.length > 0) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
    } else if (checkedBoxes.length > 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    }
}

function deleteSelectedHistory() {
    const checkedBoxes = document.querySelectorAll('.history-checkbox:checked');
    const sessionIds = Array.from(checkedBoxes).map(cb => cb.value);
    
    if (sessionIds.length === 0) {
        alert('Please select sessions to delete');
        return;
    }
    
    if (!confirm(`Are you sure you want to delete ${sessionIds.length} session(s)? This action cannot be undone.`)) {
        return;
    }
    
    // Show loading state
    const deleteButton = document.getElementById('deleteSelectedHistory');
    const originalText = deleteButton.innerHTML;
    deleteButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
    deleteButton.disabled = true;
    
    // Send delete request
    fetch('/api/sessions/delete-history/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            session_ids: sessionIds
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove deleted sessions from DOM
            checkedBoxes.forEach(checkbox => {
                const sessionItem = checkbox.closest('.session-item');
                sessionItem.remove();
            });
            
            // Reset selection
            document.getElementById('selectAllHistory').checked = false;
            updateDeleteButton();
            
            // Show success message
            showNotification('Sessions deleted successfully', 'success');
        } else {
            showNotification(data.error || 'Failed to delete sessions', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while deleting sessions', 'error');
    })
    .finally(() => {
        // Reset button state
        deleteButton.innerHTML = originalText;
        deleteButton.disabled = false;
    });
}

function terminateSession(sessionKey) {
    if (confirm('Are you sure you want to terminate this session?')) {
        showNotification('Terminating session...', 'info');
        
        fetch('/api/sessions/terminate/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                session_key: sessionKey
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Session terminated successfully', 'success');
                // Refresh page
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showNotification(data.error || 'An error occurred while terminating the session', 'error');
            }
        })
        .catch(error => {
            console.error('Terminate session error:', error);
            showNotification('An error occurred while terminating the session', 'error');
        });
    }
}

function terminateAllSessions() {
    if (confirm('Are you sure you want to terminate ALL sessions?\n\nThis will:\n• Terminate ALL your sessions including this one\n• Log you out from all devices\n• Require you to sign in again\n\nDo you want to continue?')) {
        showNotification('Terminating all sessions...', 'info');
        
        fetch('/api/sessions/terminate-all/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('All sessions terminated successfully. You need to sign in again.', 'success');
                // Redirect to login after 2 seconds
                setTimeout(() => {
                    window.location.href = '/login/';
                }, 2000);
            } else {
                showNotification(data.error || 'An error occurred while terminating sessions', 'error');
            }
        })
        .catch(error => {
            console.error('Terminate all sessions error:', error);
            showNotification('An error occurred while terminating sessions', 'error');
        });
    }
}

// Global variables for modal
let currentSessionKey = null;
let selectedAnalysisMethod = null;

function openReanalysisModal() {}

function closeReanalysisModal() {
    document.getElementById('reanalysisModal').style.display = 'none';
    currentSessionKey = null;
    selectedAnalysisMethod = null;
}

function startAnalysis() {}

function displayAnalysisResults() {}

// Legacy function for backward compatibility
function reanalyzeLocation() {}

function showNotification(message, type = 'info') {
    // Mevcut bildirimleri kaldır
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Yeni bildirim oluştur
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Stil ekle
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
    
    // 3 saniye sonra kaldır
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// CSS animasyonları ekle
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