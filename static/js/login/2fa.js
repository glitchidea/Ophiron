/*
Ophiron 2FA Login JavaScript
2FA verification page functions
*/

document.addEventListener('DOMContentLoaded', function() {
    init2FAForm();
    setupCodeInputs();
    checkSession();
});

function init2FAForm() {
    const form = document.getElementById('twoFactorForm');
    const codeInput = document.getElementById('twoFactorCode');
    const backupCodeInput = document.getElementById('backupCode');
    
    // Form submit
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        // Ensure it runs only once
        if (!form.dataset.processing) {
            form.dataset.processing = 'true';
            handle2FAVerification();
        }
    });
    
    // Submit with Enter key
    codeInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            // Ensure it runs only once
            if (!codeInput.dataset.processing) {
                codeInput.dataset.processing = 'true';
                handle2FAVerification();
            }
        }
    });
    
    backupCodeInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            // Ensure it runs only once
            if (!backupCodeInput.dataset.processing) {
                backupCodeInput.dataset.processing = 'true';
                handle2FAVerification();
            }
        }
    });
}

function setupCodeInputs() {
    const codeInput = document.getElementById('twoFactorCode');
    const backupCodeInput = document.getElementById('backupCode');
    
    // Only numeric input (for 2FA code)
    codeInput.addEventListener('input', function(e) {
        e.target.value = e.target.value.replace(/[^0-9]/g, '');
        if (e.target.value.length === 6) {
        // Auto submit when 6 characters are entered
            setTimeout(() => {
                // Ensure it runs only once
                if (!codeInput.dataset.processing) {
                    codeInput.dataset.processing = 'true';
                    handle2FAVerification();
                }
            }, 500);
        }
    });
    
    // Alphanumeric for backup code
    backupCodeInput.addEventListener('input', function(e) {
        e.target.value = e.target.value.replace(/[^A-Z0-9]/g, '').toUpperCase();
    });
}

function toggleBackupCode() {
    const backupGroup = document.getElementById('backupCodeGroup');
    const codeInput = document.getElementById('twoFactorCode');
    const backupCodeInput = document.getElementById('backupCode');
    const toggleBtn = document.querySelector('.backup-toggle-btn');
    
    if (backupGroup.style.display === 'none') {
        // Open backup code mode
        backupGroup.style.display = 'block';
        codeInput.style.display = 'none';
        backupCodeInput.focus();
        toggleBtn.innerHTML = '<i class="fas fa-mobile-alt"></i> Use normal code';
        toggleBtn.onclick = toggleBackupCode;
    } else {
        // Switch back to normal code mode
        backupGroup.style.display = 'none';
        codeInput.style.display = 'block';
        codeInput.focus();
        toggleBtn.innerHTML = '<i class=\"fas fa-key\"></i> Use backup code';
        toggleBtn.onclick = toggleBackupCode;
    }
}

function handle2FAVerification() {
    const codeInput = document.getElementById('twoFactorCode');
    const backupCodeInput = document.getElementById('backupCode');
    const backupGroup = document.getElementById('backupCodeGroup');
    const verifyBtn = document.getElementById('verifyBtn');
    const btnText = verifyBtn.querySelector('span');
    const btnLoading = verifyBtn.querySelector('.btn-loading');
    
    // Hangi input aktifse onu al
    const isBackupCode = backupGroup.style.display !== 'none';
    const token = isBackupCode ? backupCodeInput.value : codeInput.value;
    
    // Validasyon
    if (!token) {
        showNotification('Lütfen kodu girin', 'error');
        return;
    }
    
    if (isBackupCode) {
        if (token.length < 8) {
            showNotification('Yedek kod 8 karakter olmalı', 'error');
            return;
        }
    } else {
        if (token.length !== 6) {
            showNotification('2FA kodu 6 haneli olmalı', 'error');
            return;
        }
    }
    
    // Loading state
    verifyBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoading.style.display = 'block';
    
    // API request
    fetch('/api/2fa/verify-login/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            token: token,
            is_backup_code: isBackupCode
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 1000);
        } else {
            // Show error message nicely
            const errorMessage = data.errors ? data.errors.join(', ') : (data.error || '2FA verification failed');
            showNotification(errorMessage, 'error');
            // Clear inputs
            codeInput.value = '';
            backupCodeInput.value = '';
            codeInput.focus();
        }
    })
    .catch(error => {
        showNotification('2FA verification failed', 'error');
        console.error('2FA verification error:', error);
    })
    .finally(() => {
        // Remove loading state
        verifyBtn.disabled = false;
        btnText.style.display = 'block';
        btnLoading.style.display = 'none';
        
        // Processing flag'ini temizle
        if (codeInput) codeInput.dataset.processing = '';
        if (backupCodeInput) backupCodeInput.dataset.processing = '';
        const form = document.getElementById('twoFactorForm');
        if (form) form.dataset.processing = '';
    });
}

function checkSession() {
    // Session check - if there is no 2FA session, redirect to login
    fetch('/api/2fa/status/')
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                // No session, redirect to login
                window.location.href = '/login/';
            }
        })
        .catch(error => {
            console.error('Session check error:', error);
            window.location.href = '/login/';
        });
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create new notification
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-times-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Auto-focus on page load
document.addEventListener('DOMContentLoaded', function() {
    const codeInput = document.getElementById('twoFactorCode');
    if (codeInput) {
        codeInput.focus();
    }
});
