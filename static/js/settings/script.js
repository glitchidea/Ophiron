/*
Ophiron Settings JavaScript
Settings page functions
*/

document.addEventListener('DOMContentLoaded', function() {
    initSettings();
    setupTabNavigation();
    setupFormHandlers();
    // Load full timezone list into the select
    loadTimezoneOptions();
    
    // Load module settings
    loadDockerManagerSettings();
    loadSystemInfoSettings();
    
    // Setup new event listeners
    setupDockerManagerListeners();
    setupSystemInfoListeners();
});

function initSettings() {
    console.log('Ophiron Settings initialized');
    
    // Get tab parameter from URL
    const urlParams = new URLSearchParams(window.location.search);
    const tab = urlParams.get('tab');
    
    if (tab) {
        showTab(tab);
    }
}

function setupTabNavigation() {
    const tabs = document.querySelectorAll('.settings-tab');
    const panels = document.querySelectorAll('.settings-panel');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            showTab(tabName);
        });
    });
}

function showTab(tabName) {
    // Deactivate all tabs
    document.querySelectorAll('.settings-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Activate selected tab
    const selectedTab = document.querySelector(`.settings-tab[data-tab="${tabName}"]`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Hide all panels
    document.querySelectorAll('.settings-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    
    // Show selected panel
    const selectedPanel = document.getElementById(`${tabName}-panel`);
    if (selectedPanel) {
        selectedPanel.classList.add('active');
    }
}

function setupFormHandlers() {
    // Change password form
    const passwordForm = document.querySelector('#password-panel');
    if (passwordForm) {
        const updatePasswordBtn = passwordForm.querySelector('.btn-primary');
        if (updatePasswordBtn) {
            updatePasswordBtn.addEventListener('click', handlePasswordUpdate);
        }
    }
    
    // General settings form
    const generalForm = document.querySelector('#general-panel');
    if (generalForm) {
        const inputs = generalForm.querySelectorAll('input, select');
        inputs.forEach(input => {
            if (!input.readOnly) {
                input.addEventListener('change', handleGeneralSettingsUpdate);
            }
        });
        // Capture initial values so we can detect real changes later
        setInitialGeneralValues();
    }
    
    // Profile image upload
    const profileImagePreview = document.getElementById('profileImagePreview');
    if (profileImagePreview) {
        profileImagePreview.addEventListener('click', function() {
            document.getElementById('profileImageInput').click();
        });
    }
    
    // Check current profile image on page load
    loadCurrentProfileImage();
    
    // Load 2FA status
    load2FAStatus();
}

function validatePasswordStrength(password) {
    const errors = [];
    
    // Minimum length
    if (password.length < 8) {
        errors.push('Şifre en az 8 karakter olmalı');
    }
    
    // Uppercase check
    if (!/[A-Z]/.test(password)) {
        errors.push('Şifre en az 1 büyük harf içermeli');
    }
    
    // Lowercase check
    if (!/[a-z]/.test(password)) {
        errors.push('Şifre en az 1 küçük harf içermeli');
    }
    
    // Digit check
    if (!/[0-9]/.test(password)) {
        errors.push('Şifre en az 1 rakam içermeli');
    }
    
    // Special character check
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
        errors.push('Şifre en az 1 özel karakter içermeli (!@#$%^&* vb.)');
    }
    
    // Common passwords check
    const commonPasswords = [
        'password', '123456', '123456789', 'qwerty', 'abc123', 
        'password123', 'admin', 'letmein', 'welcome', 'monkey',
        '1234567890', 'password1', 'qwerty123', 'dragon', 'master'
    ];
    if (commonPasswords.includes(password.toLowerCase())) {
        errors.push('Yaygın kullanılan şifreler güvenli değildir');
    }
    
    // Repeating characters check
    if (/(.)\1{2,}/.test(password)) {
        errors.push('Şifre ardışık aynı karakterler içermemeli (aaa, 111 vb.)');
    }
    
    // Keyboard sequence check
    const keyboardSequences = [
        'qwerty', 'asdfgh', 'zxcvbn', '123456', 'abcdef',
        'qwertyuiop', 'asdfghjkl', 'zxcvbnm'
    ];
    const passwordLower = password.toLowerCase();
    for (const sequence of keyboardSequences) {
        if (passwordLower.includes(sequence) || passwordLower.includes(sequence.split('').reverse().join(''))) {
            errors.push('Klavye sıralaması şifreler güvenli değildir');
            break;
        }
    }
    
    return errors;
}

function checkPasswordStrength() {
    const password = document.getElementById('new-password').value;
    const indicator = document.getElementById('passwordStrengthIndicator');
    const strengthFill = document.getElementById('strengthFill');
    const strengthText = document.getElementById('strengthText');
    const strengthRequirements = document.getElementById('strengthRequirements');
    
    if (password.length === 0) {
        indicator.style.display = 'none';
        return;
    }
    
    indicator.style.display = 'block';
    
    // Check password requirements
    const requirements = [
        { text: 'En az 8 karakter', met: password.length >= 8 },
        { text: 'Büyük harf (A-Z)', met: /[A-Z]/.test(password) },
        { text: 'Küçük harf (a-z)', met: /[a-z]/.test(password) },
        { text: 'Rakam (0-9)', met: /[0-9]/.test(password) },
        { text: 'Özel karakter (!@#$%^&*)', met: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password) }
    ];
    
    const metRequirements = requirements.filter(req => req.met).length;
    const totalRequirements = requirements.length;
    
    // Determine strength level
    let strengthLevel, strengthClass, strengthMessage;
    
    if (metRequirements === 0) {
        strengthLevel = 'weak';
        strengthClass = 'weak';
        strengthMessage = 'Very Weak';
    } else if (metRequirements <= 2) {
        strengthLevel = 'weak';
        strengthClass = 'weak';
        strengthMessage = 'Weak';
    } else if (metRequirements <= 3) {
        strengthLevel = 'fair';
        strengthClass = 'fair';
        strengthMessage = 'Fair';
    } else if (metRequirements <= 4) {
        strengthLevel = 'good';
        strengthClass = 'good';
        strengthMessage = 'Good';
    } else {
        strengthLevel = 'strong';
        strengthClass = 'strong';
        strengthMessage = 'Strong';
    }
    
    // Visual updates
    strengthFill.className = `strength-fill ${strengthClass}`;
    strengthText.className = `strength-text ${strengthClass}`;
    strengthText.textContent = `Password Strength: ${strengthMessage}`;
    
    // Requirements list
    let requirementsHtml = '';
    requirements.forEach(req => {
        const iconClass = req.met ? 'fa-check-circle' : 'fa-times-circle';
        const requirementClass = req.met ? 'met' : 'unmet';
        requirementsHtml += `
            <div class="requirement ${requirementClass}">
                <i class="fas ${iconClass}"></i>
                <span>${req.text}</span>
            </div>
        `;
    });
    strengthRequirements.innerHTML = requirementsHtml;
}

// ===== 2FA FUNCTIONS =====
let currentBackupCodes = [];

function load2FAStatus() {
    fetch('/api/2fa/settings-status/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                update2FAStatus(data.is_enabled);
            }
        })
        .catch(error => {
            console.error('2FA status error:', error);
        });
}

function update2FAStatus(isEnabled) {
    const statusIndicator = document.getElementById('statusIndicator');
    const statusValue = document.getElementById('statusValue');
    const enableBtn = document.getElementById('enable2faBtn');
    const disableBtn = document.getElementById('disable2faBtn');
    
    if (isEnabled) {
        statusIndicator.className = 'status-indicator enabled';
        statusValue.textContent = window.jsTranslations.enabled;
        enableBtn.style.display = 'none';
        disableBtn.style.display = 'flex';
    } else {
        statusIndicator.className = 'status-indicator disabled';
        statusValue.textContent = window.jsTranslations.disabled;
        enableBtn.style.display = 'flex';
        disableBtn.style.display = 'none';
    }
}

function setup2FA() {
    const modal = document.getElementById('setupModal');
    modal.style.display = 'flex';
    
    // Generate QR code
    fetch('/api/2fa/setup/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show QR code
            const qrImage = document.getElementById('qrCodeImage');
            const qrLoading = document.getElementById('qrCodeLoading');
            const secretKey = document.getElementById('secretKey');
            const nextBtn = document.getElementById('nextStepBtn');
            const manualSetup = document.getElementById('manualSetup');
            
            qrImage.src = 'data:image/png;base64,' + data.qr_code;
            qrImage.style.display = 'block';
            qrLoading.style.display = 'none';
            secretKey.value = data.secret_key;
            nextBtn.style.display = 'block';
            manualSetup.style.display = 'block';
        } else {
            showNotification(data.errors.join(', '), 'error');
        }
    })
    .catch(error => {
        showNotification('2FA kurulumu başlatılamadı', 'error');
        console.error('2FA setup error:', error);
    });
}

function showVerificationStep() {
    document.getElementById('setupStep1').style.display = 'none';
    document.getElementById('setupStep2').style.display = 'block';
}

function verify2FA() {
    const code = document.getElementById('verificationCode').value;
    
    if (!code || code.length !== 6) {
        showNotification('Enter the 6-digit code', 'error');
        return;
    }
    
    fetch('/api/2fa/verify/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            token: code
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentBackupCodes = data.backup_codes;
            showBackupCodes();
        } else {
            showNotification(data.errors.join(', '), 'error');
        }
    })
    .catch(error => {
        showNotification('2FA verification failed', 'error');
        console.error('2FA verify error:', error);
    });
}

function showBackupCodes() {
    document.getElementById('setupStep2').style.display = 'none';
    document.getElementById('setupStep3').style.display = 'block';
    
    const codesList = document.getElementById('codesList');
    codesList.innerHTML = '';
    
    currentBackupCodes.forEach(code => {
        const codeItem = document.createElement('div');
        codeItem.className = 'code-item';
        codeItem.textContent = code;
        codesList.appendChild(codeItem);
    });
}

function closeSetupModal() {
    const modal = document.getElementById('setupModal');
    modal.style.display = 'none';
    
    // Reset modal
    document.getElementById('setupStep1').style.display = 'block';
    document.getElementById('setupStep2').style.display = 'none';
    document.getElementById('setupStep3').style.display = 'none';
    document.getElementById('qrCodeImage').style.display = 'none';
    document.getElementById('qrCodeLoading').style.display = 'flex';
    document.getElementById('verificationCode').value = '';
    
    // Reload 2FA status
    load2FAStatus();
}

function showDisable2FAModal() {
    const modal = document.getElementById('disableModal');
    modal.style.display = 'flex';
    
    // Clear form fields
    document.getElementById('disablePassword').value = '';
    document.getElementById('disableToken').value = '';
    
    // Token type toggle event listeners
    setupTokenTypeToggle();
}

function setupTokenTypeToggle() {
    const tokenTypeBtns = document.querySelectorAll('.token-type-btn');
    const tokenInput = document.getElementById('disableToken');
    
    tokenTypeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons
            tokenTypeBtns.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            
            const tokenType = this.dataset.type;
            
            if (tokenType === 'code') {
                tokenInput.placeholder = 'Enter 6-digit code';
                tokenInput.maxLength = 6;
            } else if (tokenType === 'backup') {
                tokenInput.placeholder = 'Enter backup code';
                tokenInput.maxLength = 8;
            }
        });
    });
}

function closeDisableModal() {
    const modal = document.getElementById('disableModal');
    modal.style.display = 'none';
    
    // Clear form fields
    document.getElementById('disablePassword').value = '';
    document.getElementById('disableToken').value = '';
}

function confirmDisable2FA() {
    const password = document.getElementById('disablePassword').value;
    const token = document.getElementById('disableToken').value;
    const activeTokenType = document.querySelector('.token-type-btn.active').dataset.type;
    
    // Validation
    if (!password) {
        showNotification('Password is required', 'error');
        return;
    }
    
    if (!token) {
        showNotification('2FA code is required', 'error');
        return;
    }
    
    // Token length check
    if (activeTokenType === 'code' && token.length !== 6) {
        showNotification('Enter a 6-digit code', 'error');
        return;
    }
    
    if (activeTokenType === 'backup' && token.length < 6) {
        showNotification('Enter a valid backup code', 'error');
        return;
    }
    
    // Send disable request to API
    fetch('/api/2fa/disable/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            password: password,
            token: token,
            is_backup_code: activeTokenType === 'backup'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            closeDisableModal();
            load2FAStatus();
        } else {
            showNotification(data.errors.join(', '), 'error');
        }
    })
    .catch(error => {
        showNotification('Failed to disable 2FA', 'error');
        console.error('2FA disable error:', error);
    });
}

function copySecretKey() {
    const secretKey = document.getElementById('secretKey');
    secretKey.select();
    document.execCommand('copy');
    showNotification('Secret key copied', 'success');
}

function downloadBackupCodes() {
    const codes = currentBackupCodes.join('\n');
    const blob = new Blob([codes], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ophiron-backup-codes.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    showNotification('Backup codes downloaded', 'success');
}

function handlePasswordUpdate() {
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
        showNotification('Please fill out all fields', 'error');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        showNotification('New passwords do not match', 'error');
        return;
    }
    
    // Strong password policy check
    const passwordErrors = validatePasswordStrength(newPassword);
    if (passwordErrors.length > 0) {
        showNotification(passwordErrors.join(', '), 'error');
        return;
    }
    
    // API'ye şifre değiştirme isteği gönder
    fetch('/api/password/change/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword,
            confirm_password: confirmPassword
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Password changed successfully. For security, you need to sign in again.', 'success');
            // Redirect to login after 2 seconds
            setTimeout(() => {
                window.location.href = '/login/';
            }, 2000);
        } else {
            showNotification(data.errors.join(', '), 'error');
        }
    })
    .catch(error => {
        showNotification('An error occurred while changing the password', 'error');
        console.error('Password change error:', error);
    });
}

function handleGeneralSettingsUpdate(event) {
    const target = event && event.target ? event.target : null;
    if (!target) return;

    const id = target.id;
    const value = target.value;
    const initial = target.dataset.initial;

    if (typeof initial !== 'undefined' && value === initial) {
        return; // No real change
    }

    let promise = null;
    if (id === 'email') {
        promise = updateEmail(value);
    } else if (id === 'fullname') {
        promise = updateName(value);
    } else if (id === 'language') {
        promise = updateLanguage(value);
    } else if (id === 'timezone') {
        promise = updateTimezone(value);
    }

    if (promise && typeof promise.then === 'function') {
        promise.then(() => {
            target.dataset.initial = value;
            showNotification('Settings saved', 'success');
        });
    }
}

function setInitialGeneralValues() {
    const generalForm = document.querySelector('#general-panel');
    if (!generalForm) return;
    const inputs = generalForm.querySelectorAll('input, select');
    inputs.forEach(input => {
        if (!input.readOnly && typeof input.dataset.initial === 'undefined') {
            input.dataset.initial = input.value;
        }
    });
    
    // Load current language preference
    loadCurrentLanguage();
}

function loadCurrentLanguage() {
    const languageSelect = document.getElementById('language');
    if (!languageSelect) return;
    
    // Get current language from Django template context
    // This will be set by the view
    const currentLanguage = languageSelect.dataset.current || 'en';
    languageSelect.value = currentLanguage;
    languageSelect.dataset.initial = currentLanguage;
}

function updateEmail(email) {
    return fetch('/api/profile/update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({ email: email })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Email updated:', data.message);
        }
    })
    .catch(error => console.error('Email update error:', error));
}

function updateName(name) {
    return fetch('/api/profile/update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({ full_name: name })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Name updated:', data.message);
        }
    })
    .catch(error => console.error('Name update error:', error));
}

function updateLanguage(language) {
    console.log('updateLanguage called with:', language);
    return fetch('/api/language/change/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({ language: language })
    })
    .then(response => {
        console.log('Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            console.log('Language updated:', data.message);
            showNotification('Language changed successfully - Reloading page...', 'success');
            
            // Reload the page to apply the new language
            setTimeout(() => {
                console.log('Reloading page...');
                // Force reload from server to get fresh content
                window.location.href = window.location.href + '?t=' + Date.now();
            }, 1500);
        } else {
            console.error('Language update failed:', data.error);
            showNotification('Language change failed: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Language update error:', error);
        showNotification('Language change failed', 'error');
    });
}

function updateTimezone(timezone) {
    return fetch('/api/profile/update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({ timezone: timezone })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Timezone updated:', data.message);
            // Also update session timezone
            fetch('/api/timezone/change/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({ timezone: timezone })
            });
        }
    })
    .catch(error => console.error('Timezone update error:', error));
}

// ===== TIMEZONE LOADER =====
function loadTimezoneOptions() {
    const tzSelect = document.getElementById('timezone');
    if (!tzSelect) return;
    // Show loading state
    const original = tzSelect.innerHTML;
    tzSelect.innerHTML = '<option>Loading…</option>';

    fetch('/api/timezone/list/')
        .then(resp => resp.json())
        .then(data => {
            if (!data.success || !Array.isArray(data.timezones)) {
                throw new Error(data.error || 'Failed to load timezones');
            }
            const current = data.current || 'UTC';
            // Rebuild options
            tzSelect.innerHTML = '';
            data.timezones.forEach(tz => {
                const opt = document.createElement('option');
                opt.value = tz;
                opt.textContent = tz;
                if (tz === current) opt.selected = true;
                tzSelect.appendChild(opt);
            });
            // Ensure the timezone select initial is synced with current value
            tzSelect.dataset.initial = current;
            console.log('Timezone loaded, current selection:', current);
        })
        .catch(err => {
            console.error('Timezone list load error:', err);
            // Fallback back to original options
            tzSelect.innerHTML = original;
        });
}

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

// ===== PROFILE IMAGE FUNCTIONS =====
function loadCurrentProfileImage() {
    // Profile image already loaded in template
    // Just toggle remove button
    const profileImage = document.getElementById('profileImage');
    const removeBtn = document.getElementById('removeProfileBtn');
    
    // Show remove button if not demo avatar
    if (profileImage.src.includes('demo-avatar.svg')) {
        removeBtn.style.display = 'none';
    } else {
        removeBtn.style.display = 'flex';
    }
}

function handleProfileImageUpload(input) {
    const file = input.files[0];
    if (!file) return;
    
    // File validation
    const maxSize = 5 * 1024 * 1024; // 5MB
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    
    if (file.size > maxSize) {
        showNotification('File size cannot exceed 5MB', 'error');
        return;
    }
    
    if (!allowedTypes.includes(file.type)) {
        showNotification('Unsupported file format. Use JPG, PNG, GIF, WebP', 'error');
        return;
    }
    
    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
        document.getElementById('profileImage').src = e.target.result;
    };
    reader.readAsDataURL(file);
    
    // Upload to server
    uploadProfileImage(file);
}

function uploadProfileImage(file) {
    const formData = new FormData();
    formData.append('profile_image', file);
    
    // Add CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/api/profile/upload/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            // Refresh page so template updates
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification(data.errors.join(', '), 'error');
        }
    })
    .catch(error => {
            showNotification('An error occurred while uploading the image', 'error');
        console.error('Upload error:', error);
    });
}

function removeProfileImage() {
    if (confirm('Are you sure you want to remove the profile image?')) {
        fetch('/api/profile/remove/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success');
                // Refresh page so template updates
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showNotification(data.errors.join(', '), 'error');
            }
        })
        .catch(error => {
                showNotification('An error occurred while removing the image', 'error');
            console.error('Remove error:', error);
        });
    }
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

// ===== MODULAR SETTINGS - PROCESS MONITOR =====

// Initialize Process Monitor settings when modules tab is shown
document.addEventListener('DOMContentLoaded', function() {
    const modulesTab = document.querySelector('[data-tab="modules"]');
    if (modulesTab) {
        modulesTab.addEventListener('click', function() {
            loadProcessMonitorStatus();
            loadAppLogsStatus();
            loadSystemInfoStatus();
            loadServiceMonitoringSettings();
        });
        
        // Also load settings immediately if modules tab is already active
        if (modulesTab.classList.contains('active')) {
            loadProcessMonitorStatus();
            loadAppLogsStatus();
            loadSystemInfoStatus();
            loadServiceMonitoringSettings();
        }
    }
    
    // Always load Application Logs status on page load
    loadAppLogsStatus();
    
    // Setup Process Monitor controls
    const liveModeToggle = document.getElementById('processMonitorLiveMode');
    if (liveModeToggle) {
        liveModeToggle.addEventListener('change', function() {
            toggleProcessMonitorLiveMode(this.checked);
        });
    }
    
    // Interval slider
    const intervalSlider = document.getElementById('monitoringIntervalRange');
    const intervalValue = document.getElementById('intervalValue');
    if (intervalSlider && intervalValue) {
        intervalSlider.addEventListener('input', function() {
            intervalValue.textContent = this.value;
        });
    }
    
    // Cache Duration slider
    const cacheDurationSlider = document.getElementById('cacheDurationInput');
    const cacheDurationValue = document.getElementById('cacheDurationValue');
    if (cacheDurationSlider && cacheDurationValue) {
        cacheDurationSlider.addEventListener('input', function() {
            cacheDurationValue.textContent = this.value;
        });
    }
    
    const forceRefreshBtn = document.getElementById('pmForceRefresh');
    if (forceRefreshBtn) {
        forceRefreshBtn.addEventListener('click', function() {
            forceProcessMonitorRefresh();
        });
    }
    
    // Save settings button
    const saveSettingsBtn = document.getElementById('pmSaveSettings');
    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', function() {
            saveProcessMonitorSettings();
        });
    }
});

function loadProcessMonitorStatus() {
    fetch('/process-monitor/api/service/status/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update toggle
                const toggle = document.getElementById('processMonitorLiveMode');
                if (toggle) {
                    toggle.checked = data.live_mode_enabled;
                }
                
                // Update interval slider
                const intervalSlider = document.getElementById('monitoringIntervalRange');
                const intervalValue = document.getElementById('intervalValue');
                if (intervalSlider && intervalValue && data.monitoring_interval) {
                    intervalSlider.value = data.monitoring_interval;
                    intervalValue.textContent = data.monitoring_interval;
                }
                
                // Update cache duration slider
                const cacheDurationSlider = document.getElementById('cacheDurationInput');
                const cacheDurationValue = document.getElementById('cacheDurationValue');
                if (cacheDurationSlider && cacheDurationValue && data.cache_duration) {
                    cacheDurationSlider.value = data.cache_duration;
                    cacheDurationValue.textContent = data.cache_duration;
                }
                
                // Update status
                const serviceStatus = document.getElementById('pmServiceStatus');
                if (serviceStatus) {
                    if (data.live_mode_enabled) {
                        serviceStatus.innerHTML = '<span style="color: #48bb78;">● Active (Global)</span>';
                    } else {
                        serviceStatus.innerHTML = '<span style="color: #cbd5e0;">○ Inactive</span>';
                    }
                }
                
                // Update cache status
                const cacheStatus = document.getElementById('pmCacheStatus');
                if (cacheStatus) {
                    const hasCache = data.cache_status.connections && data.cache_status.ports;
                    cacheStatus.textContent = hasCache ? '✓ Cached' : '✗ Empty';
                    cacheStatus.style.color = hasCache ? '#48bb78' : '#cbd5e0';
                }
                
                // Update last update time
                const lastUpdate = document.getElementById('pmLastUpdate');
                if (lastUpdate) {
                    lastUpdate.textContent = new Date().toLocaleTimeString('tr-TR');
                }
                
                // Update last modified by
                const lastModifiedBy = document.getElementById('pmLastModifiedBy');
                if (lastModifiedBy && data.last_modified_by) {
                    lastModifiedBy.textContent = data.last_modified_by;
                }
            }
        })
        .catch(error => {
            console.error('Failed to load Process Monitor status:', error);
            showNotification('Failed to load status', 'error');
        });
}

// ===== MODULAR SETTINGS - APPLICATION LOGS =====
function loadAppLogsStatus() {
    console.log('Loading Application Logs status...');
    fetch('/system-logs/own/config/get/')
        .then(r=>r.json())
        .then(cfg=>{
            console.log('Application Logs config received:', cfg);
            const toggle = document.getElementById('appLogsLiveMode');
            const slider = document.getElementById('appLogsIntervalRange');
            const label = document.getElementById('appLogsIntervalValue');
            
            console.log('Toggle element:', toggle);
            console.log('Slider element:', slider);
            console.log('Label element:', label);
            
            if (toggle) {
                toggle.checked = !!cfg.config.enabled;
                console.log('Toggle set to:', toggle.checked);
            }
            if (slider && label) {
                const val = parseInt(cfg.config.interval_sec || 10, 10);
                slider.value = val;
                label.textContent = String(val);
                console.log('Slider set to:', val);
            }
        })
        .catch(error => {
            console.error('Failed to load Application Logs status:', error);
        });
}

// Setup Application Logs live mode toggle
const appLogsLiveModeToggle = document.getElementById('appLogsLiveMode');
if (appLogsLiveModeToggle) {
    appLogsLiveModeToggle.addEventListener('change', function() {
        toggleAppLogsLiveMode(this.checked);
    });
}

function toggleAppLogsLiveMode(enabled) {
    const interval = document.getElementById('appLogsIntervalRange').value;
    
    // Disable toggle during API call
    const toggle = document.getElementById('appLogsLiveMode');
    toggle.disabled = true;
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/system-logs/own/config/update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            enabled: enabled,
            interval_sec: parseInt(interval, 10)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Application Logs live mode ${enabled ? 'enabled' : 'disabled'}`, 'success');
        } else {
            showNotification('Failed to toggle live mode: ' + data.error, 'error');
            // Revert toggle
            toggle.checked = !enabled;
        }
    })
    .catch(error => {
        console.error('Error toggling Application Logs live mode:', error);
        showNotification('Failed to toggle Application Logs live mode', 'error');
        // Revert toggle
        toggle.checked = !enabled;
    })
    .finally(() => {
        toggle.disabled = false;
    });
}

document.addEventListener('DOMContentLoaded', function(){
    const sliderApp = document.getElementById('appLogsIntervalRange');
    const labelApp = document.getElementById('appLogsIntervalValue');
    if (sliderApp && labelApp) {
        sliderApp.addEventListener('input', function(){ labelApp.textContent = this.value; });
    }
    const saveBtnApp = document.getElementById('appLogsSaveSettings');
    if (saveBtnApp) {
        saveBtnApp.addEventListener('click', function(){
            const toggle = document.getElementById('appLogsLiveMode');
            const slider = document.getElementById('appLogsIntervalRange');
            const payload = {
                enabled: toggle ? !!toggle.checked : false,
                interval_sec: slider ? parseInt(slider.value, 10) : 10
            };
            fetch('/system-logs/own/config/update/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(payload)
            })
            .then(r=>r.json())
            .then(data=>{
                if (data.success) {
                    showNotification('Application Logs settings saved', 'success');
                } else {
                    showNotification('Failed to save: ' + (data.error || 'unknown'), 'error');
                }
            })
            .catch(()=> showNotification('Failed to save settings', 'error'));
        });
    }
});

function toggleProcessMonitorLiveMode(enabled) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/process-monitor/api/service/toggle-live-mode/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            enabled: enabled
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            loadProcessMonitorStatus();
        } else {
            showNotification('Failed to update: ' + data.error, 'error');
            // Revert toggle
            const toggle = document.getElementById('processMonitorLiveMode');
            if (toggle) {
                toggle.checked = !enabled;
            }
        }
    })
    .catch(error => {
        console.error('Failed to toggle live mode:', error);
        showNotification('Failed to update settings', 'error');
        // Revert toggle
        const toggle = document.getElementById('processMonitorLiveMode');
        if (toggle) {
            toggle.checked = !enabled;
        }
    });
}

function saveProcessMonitorSettings() {
    const btn = document.getElementById('pmSaveSettings');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    btn.disabled = true;
    
    const intervalSlider = document.getElementById('monitoringIntervalRange');
    const interval = parseFloat(intervalSlider.value);
    
    const cacheDurationSlider = document.getElementById('cacheDurationInput');
    const cacheDuration = parseInt(cacheDurationSlider.value);
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/process-monitor/api/service/update-settings/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            monitoring_interval: interval,
            cache_duration: cacheDuration
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            loadProcessMonitorStatus();
        } else {
            showNotification('Failed to save: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Failed to save settings:', error);
        showNotification('Failed to save settings', 'error');
    })
    .finally(() => {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    });
}

function forceProcessMonitorRefresh() {
    const btn = document.getElementById('pmForceRefresh');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
    btn.disabled = true;
    
    fetch('/process-monitor/api/service/force-update/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Cache refreshed successfully', 'success');
                loadProcessMonitorStatus();
            } else {
                showNotification('Failed to refresh cache', 'error');
            }
        })
        .catch(error => {
            console.error('Failed to refresh cache:', error);
            showNotification('Failed to refresh cache', 'error');
        })
        .finally(() => {
            btn.innerHTML = originalHTML;
            btn.disabled = false;
        });
}

// ===== LOGS SETTINGS =====

// Load logging status when logs tab is shown
const logsTab = document.querySelector('[data-tab="logs"]');
if (logsTab) {
    logsTab.addEventListener('click', function() {
        loadProcessMonitorLoggingStatus();
    });
}

// Setup Process Monitor logging toggle with auto-save
const processMonitorLoggingToggle = document.getElementById('processMonitorLogging');
if (processMonitorLoggingToggle) {
    processMonitorLoggingToggle.addEventListener('change', function() {
        // Auto-save on toggle
        saveProcessMonitorLoggingSettings();
    });
}

// View logs button removed (will be implemented in separate logs module)

function loadProcessMonitorLoggingStatus() {
    fetch('/process-monitor/api/service/status/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update toggle
                const toggle = document.getElementById('processMonitorLogging');
                if (toggle) {
                    toggle.checked = data.logging_enabled || false;
                }
                
                // Update status text and icon
                const status = document.getElementById('pmLoggingStatus');
                const statusIcon = document.getElementById('pmLoggingStatusIcon');
                if (status) {
                    const enabled = data.logging_enabled;
                    status.textContent = enabled ? window.jsTranslations.enabled : window.jsTranslations.disabled;
                }
                if (statusIcon) {
                    statusIcon.className = 'fas fa-circle';
                    statusIcon.style.color = data.logging_enabled ? '#22c55e' : '#ef4444'; // Green for enabled, red for disabled
                }
                
                // Update last modified by
                const modifiedBy = document.getElementById('pmLoggingModifiedBy');
                if (modifiedBy) {
                    modifiedBy.textContent = data.last_modified_by || 'N/A';
                }
            } else {
                console.error('Failed to load Process Monitor logging status:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading Process Monitor logging status:', error);
            showNotification('Failed to load Process Monitor logging status', 'error');
        });
}

function saveProcessMonitorLoggingSettings() {
    const toggle = document.getElementById('processMonitorLogging');
    const enabled = toggle.checked;
    
    // Disable toggle during save
    toggle.disabled = true;
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/process-monitor/api/service/update-settings/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            logging_enabled: enabled
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Process Monitor logging ' + (enabled ? 'enabled' : 'disabled'), 'success');
            loadProcessMonitorLoggingStatus();
        } else {
            showNotification('Failed to save: ' + data.error, 'error');
            // Revert toggle
            toggle.checked = !enabled;
        }
    })
    .catch(error => {
        console.error('Failed to save Process Monitor logging settings:', error);
        showNotification('Failed to save Process Monitor logging settings', 'error');
        // Revert toggle
        toggle.checked = !enabled;
    })
    .finally(() => {
        toggle.disabled = false;
    });
}

// ===== MODULAR SETTINGS - SYSTEM INFORMATION =====

// Initialize System Information settings when modules tab is shown
document.addEventListener('DOMContentLoaded', function() {
    const modulesTab = document.querySelector('[data-tab="modules"]');
    if (modulesTab) {
        modulesTab.addEventListener('click', function() {
            loadSystemInfoStatus();
        });
    }
    
    // Setup System Information controls
    const siLiveModeToggle = document.getElementById('systemInfoLiveMode');
    if (siLiveModeToggle) {
        siLiveModeToggle.addEventListener('change', function() {
            toggleSystemInfoLiveMode(this.checked);
        });
    }
    
    // Interval slider
    const siIntervalSlider = document.getElementById('siMonitoringIntervalRange');
    const siIntervalValue = document.getElementById('siIntervalValue');
    if (siIntervalSlider && siIntervalValue) {
        siIntervalSlider.addEventListener('input', function() {
            siIntervalValue.textContent = this.value;
        });
    }
    
    // Cache Duration slider
    const siCacheDurationSlider = document.getElementById('siCacheDurationInput');
    const siCacheDurationValue = document.getElementById('siCacheDurationValue');
    if (siCacheDurationSlider && siCacheDurationValue) {
        siCacheDurationSlider.addEventListener('input', function() {
            siCacheDurationValue.textContent = this.value;
        });
    }
    
    const siForceRefreshBtn = document.getElementById('siForceRefresh');
    if (siForceRefreshBtn) {
        siForceRefreshBtn.addEventListener('click', function() {
            forceSystemInfoRefresh();
        });
    }
    
    // Save settings button
    const siSaveSettingsBtn = document.getElementById('siSaveSettings');
    if (siSaveSettingsBtn) {
        siSaveSettingsBtn.addEventListener('click', function() {
            saveSystemInfoSettings();
        });
    }
    
    // Service Monitoring controls
    const serviceMonitoringLiveModeToggle = document.getElementById('serviceMonitoringLiveMode');
    if (serviceMonitoringLiveModeToggle) {
        serviceMonitoringLiveModeToggle.addEventListener('change', function() {
            toggleServiceMonitoringLiveMode(this.checked);
        });
    }
    
    // Service Monitoring interval slider
    const serviceMonitoringIntervalSlider = document.getElementById('serviceMonitoringIntervalRange');
    const serviceMonitoringIntervalValue = document.getElementById('serviceMonitoringIntervalValue');
    if (serviceMonitoringIntervalSlider && serviceMonitoringIntervalValue) {
        serviceMonitoringIntervalSlider.addEventListener('input', function() {
            serviceMonitoringIntervalValue.textContent = this.value;
        });
    }
    
    // Service Monitoring save settings button
    const serviceMonitoringSaveSettingsBtn = document.getElementById('serviceMonitoringSaveSettings');
    if (serviceMonitoringSaveSettingsBtn) {
        serviceMonitoringSaveSettingsBtn.addEventListener('click', function() {
            saveServiceMonitoringSettings();
        });
    }
});

function loadSystemInfoStatus() {
    fetch('/system-information/api/service/status/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const settings = data.settings;
                
                // Update toggle
                const liveModeToggle = document.getElementById('systemInfoLiveMode');
                if (liveModeToggle) {
                    liveModeToggle.checked = settings.live_mode_enabled;
                }
                
                // Update interval slider
                const intervalSlider = document.getElementById('siMonitoringIntervalRange');
                const intervalValue = document.getElementById('siIntervalValue');
                if (intervalSlider && settings.monitoring_interval) {
                    intervalSlider.value = settings.monitoring_interval;
                    if (intervalValue) {
                        intervalValue.textContent = settings.monitoring_interval;
                    }
                }
                
                // Update cache duration slider
                const cacheDurationSlider = document.getElementById('siCacheDurationInput');
                const cacheDurationValue = document.getElementById('siCacheDurationValue');
                if (cacheDurationSlider && settings.cache_duration) {
                    cacheDurationSlider.value = settings.cache_duration;
                    if (cacheDurationValue) {
                        cacheDurationValue.textContent = settings.cache_duration;
                    }
                }
                
                // Update status
                const statusIndicator = document.getElementById('siStatusIndicator');
                const statusText = document.getElementById('siStatus');
                if (statusIndicator && statusText) {
                    if (settings.live_mode_enabled) {
                        statusIndicator.style.color = '#10b981';
                        statusText.textContent = 'Active';
                        statusText.style.color = '#10b981';
                    } else {
                        statusIndicator.style.color = '#94a3b8';
                        statusText.textContent = 'Inactive';
                        statusText.style.color = '#94a3b8';
                    }
                }
                
                // Update cache status
                const cacheStatus = document.getElementById('siCacheStatus');
                if (cacheStatus) {
                    const hasCache = data.cache_available || false;
                    cacheStatus.textContent = hasCache ? '✓ Cached' : '✗ Empty';
                    cacheStatus.style.color = hasCache ? '#48bb78' : '#cbd5e0';
                }
                
                // Update last updated
                const lastUpdated = document.getElementById('siLastUpdated');
                if (lastUpdated && settings.updated_at) {
                    lastUpdated.textContent = settings.updated_at;
                }
                
                // Update last modified by
                const lastModifiedBy = document.getElementById('siLastModifiedBy');
                if (lastModifiedBy && data.settings.last_modified_by) {
                    lastModifiedBy.textContent = data.settings.last_modified_by;
                }
            }
        })
        .catch(error => {
            console.error('Failed to load System Information status:', error);
            showNotification('Failed to load status', 'error');
        });
}

function toggleSystemInfoLiveMode(enabled) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/system-information/api/service/toggle-live-mode/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            enabled: enabled
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            loadSystemInfoStatus();
        } else {
            showNotification('Failed to update: ' + data.error, 'error');
            // Revert toggle
            const toggle = document.getElementById('systemInfoLiveMode');
            if (toggle) {
                toggle.checked = !enabled;
            }
        }
    })
    .catch(error => {
        console.error('Failed to toggle live mode:', error);
        showNotification('Failed to update settings', 'error');
        // Revert toggle
        const toggle = document.getElementById('systemInfoLiveMode');
        if (toggle) {
            toggle.checked = !enabled;
        }
    });
}

function saveSystemInfoSettings() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const intervalSlider = document.getElementById('siMonitoringIntervalRange');
    const cacheDurationSlider = document.getElementById('siCacheDurationInput');
    
    if (!intervalSlider || !cacheDurationSlider) {
        showNotification('Settings elements not found', 'error');
        return;
    }
    
    const monitoringInterval = parseFloat(intervalSlider.value);
    const cacheDuration = parseInt(cacheDurationSlider.value);
    
    fetch('/system-information/api/service/update-settings/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            monitoring_interval: monitoringInterval,
            cache_duration: cacheDuration
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Settings saved successfully', 'success');
            loadSystemInfoStatus();
        } else {
            showNotification('Failed to save: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Failed to save settings:', error);
        showNotification('Failed to save settings', 'error');
    });
}

function forceSystemInfoRefresh() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const btn = document.getElementById('siForceRefresh');
    
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
    }
    
    fetch('/system-information/api/service/force-update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Cache refreshed successfully', 'success');
            setTimeout(() => loadSystemInfoStatus(), 1000);
        } else {
            showNotification('Failed to refresh: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Failed to refresh cache:', error);
        showNotification('Failed to refresh cache', 'error');
    })
    .finally(() => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-sync-alt"></i> Force Refresh';
        }
    });
}

// ===== SERVICE MONITORING SETTINGS =====

function toggleServiceMonitoringLiveMode(enabled) {
    const toggle = document.getElementById('serviceMonitoringLiveMode');
    if (!toggle) return;
    
    toggle.disabled = true;
    
    fetch('/service-monitoring/api/live-mode/toggle/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ enabled: enabled })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
        } else {
            showNotification(data.message || 'Failed to toggle live mode', 'error');
            // Revert toggle
            toggle.checked = !enabled;
        }
    })
    .catch(error => {
        console.error('Error toggling Service Monitoring live mode:', error);
        showNotification('Failed to toggle live mode', 'error');
        // Revert toggle
        toggle.checked = !enabled;
    })
    .finally(() => {
        toggle.disabled = false;
    });
}

function saveServiceMonitoringSettings() {
    const btn = document.getElementById('serviceMonitoringSaveSettings');
    if (!btn) return;
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    
    const liveMode = document.getElementById('serviceMonitoringLiveMode').checked;
    const interval = document.getElementById('serviceMonitoringIntervalRange').value;
    
    const settings = {
        live_mode: liveMode,
        interval: parseInt(interval)
    };
    
    fetch('/service-monitoring/api/live-mode/toggle/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Service Monitoring settings saved successfully', 'success');
        } else {
            showNotification(data.message || 'Failed to save settings', 'error');
        }
    })
    .catch(error => {
        console.error('Error saving Service Monitoring settings:', error);
        showNotification('Failed to save settings', 'error');
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Save Settings';
    });
}

// ===== DOCKER MANAGER LOGGING SETTINGS =====

function loadDockerManagerSettings() {
    // For now, we'll use default values since we don't have API endpoints yet
    // This would be implemented when Docker Manager API is ready
    console.log('Docker Manager settings loading...');
}

function saveDockerManagerSettings() {
    const btn = document.getElementById('dockerManagerSaveSettings');
    if (!btn) return;
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    
    const loggingEnabled = document.getElementById('dockerManagerLogging').checked;
    const logRetention = document.getElementById('dockerManagerLogRetention').value;
    
    // For now, just show a notification since API endpoints don't exist yet
    setTimeout(() => {
        showNotification('Docker Manager logging settings saved (API integration pending)', 'info');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Save Settings';
    }, 1000);
}

// ===== SYSTEM INFORMATION LOGGING SETTINGS =====

function loadSystemInfoSettings() {
    // For now, we'll use default values since we don't have API endpoints yet
    // This would be implemented when System Information API is ready
    console.log('System Information settings loading...');
}

function saveSystemInfoSettings() {
    const btn = document.getElementById('systemInfoSaveSettings');
    if (!btn) return;
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    
    const loggingEnabled = document.getElementById('systemInfoLogging').checked;
    const logRetention = document.getElementById('systemInfoLogRetention').value;
    
    // For now, just show a notification since API endpoints don't exist yet
    setTimeout(() => {
        showNotification('System Information logging settings saved (API integration pending)', 'info');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Save Settings';
    }, 1000);
}

// ===== EVENT LISTENERS =====

function setupDockerManagerListeners() {
    // Docker Manager log retention slider
    const dockerManagerLogRetention = document.getElementById('dockerManagerLogRetention');
    const dockerManagerLogRetentionValue = document.getElementById('dockerManagerLogRetentionValue');
    if (dockerManagerLogRetention && dockerManagerLogRetentionValue) {
        dockerManagerLogRetention.addEventListener('input', function() {
            dockerManagerLogRetentionValue.textContent = this.value;
        });
    }
    
    // Docker Manager save settings button
    const dockerManagerSaveSettingsBtn = document.getElementById('dockerManagerSaveSettings');
    if (dockerManagerSaveSettingsBtn) {
        dockerManagerSaveSettingsBtn.addEventListener('click', function() {
            saveDockerManagerSettings();
        });
    }
}

function setupSystemInfoListeners() {
    // System Information log retention slider
    const systemInfoLogRetention = document.getElementById('systemInfoLogRetention');
    const systemInfoLogRetentionValue = document.getElementById('systemInfoLogRetentionValue');
    if (systemInfoLogRetention && systemInfoLogRetentionValue) {
        systemInfoLogRetention.addEventListener('input', function() {
            systemInfoLogRetentionValue.textContent = this.value;
        });
    }
    
    // System Information save settings button
    const systemInfoSaveSettingsBtn = document.getElementById('systemInfoSaveSettings');
    if (systemInfoSaveSettingsBtn) {
        systemInfoSaveSettingsBtn.addEventListener('click', function() {
            saveSystemInfoSettings();
        });
    }
}

// ===== LOGGING SETTINGS - DOCKER MANAGER =====

// Setup Docker Manager logging toggle with auto-save
const dockerLoggingToggle = document.getElementById('dockerManagerLogging');
if (dockerLoggingToggle) {
    dockerLoggingToggle.addEventListener('change', function() {
        // Auto-save on toggle
        saveDockerLoggingSettings();
    });
}

function loadDockerLoggingStatus() {
    fetch('/docker-manager/api/logging/status/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update toggle
                const toggle = document.getElementById('dockerManagerLogging');
                if (toggle) {
                    toggle.checked = data.logging_enabled || false;
                }
                
                // Update status text and icon
                const status = document.getElementById('dockerLoggingStatus');
                const statusIcon = document.getElementById('dockerLoggingStatusIcon');
                if (status) {
                    const enabled = data.logging_enabled;
                    status.textContent = enabled ? window.jsTranslations.enabled : window.jsTranslations.disabled;
                }
                if (statusIcon) {
                    statusIcon.className = 'fas fa-circle';
                    statusIcon.style.color = data.logging_enabled ? '#22c55e' : '#ef4444'; // Green for enabled, red for disabled
                }
                
                // Update modified by
                const modifiedBy = document.getElementById('dockerLoggingModifiedBy');
                if (modifiedBy) {
                    modifiedBy.textContent = data.last_modified_by || 'N/A';
                }
            } else {
                console.error('Failed to load Docker logging status:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading Docker logging status:', error);
            showNotification('Failed to load Docker logging status', 'error');
        });
}

function saveDockerLoggingSettings() {
    const toggle = document.getElementById('dockerManagerLogging');
    const enabled = toggle.checked;
    
    // Disable toggle during save
    toggle.disabled = true;
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/docker-manager/api/logging/toggle/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ logging_enabled: enabled })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Docker Manager logging ' + (enabled ? 'enabled' : 'disabled'), 'success');
            loadDockerLoggingStatus();
        } else {
            showNotification('Failed to save: ' + data.error, 'error');
            // Revert toggle
            toggle.checked = !enabled;
        }
    })
    .catch(error => {
        console.error('Failed to save Docker logging settings:', error);
        showNotification('Failed to save Docker logging settings', 'error');
        // Revert toggle
        toggle.checked = !enabled;
    })
    .finally(() => {
        toggle.disabled = false;
    });
}

// ===== LOGGING SETTINGS - SYSTEM INFORMATION =====

// Setup System Information logging toggle with auto-save
const systemInfoLoggingToggle = document.getElementById('systemInfoLogging');
if (systemInfoLoggingToggle) {
    systemInfoLoggingToggle.addEventListener('change', function() {
        // Auto-save on toggle
        saveSystemInfoLoggingSettings();
    });
}

function loadSystemInfoLoggingStatus() {
    fetch('/system-information/api/logging/status/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update toggle
                const toggle = document.getElementById('systemInfoLogging');
                if (toggle) {
                    toggle.checked = data.logging_enabled || false;
                }
                
                // Update status text and icon
                const status = document.getElementById('systemInfoLoggingStatus');
                const statusIcon = document.getElementById('systemInfoLoggingStatusIcon');
                if (status) {
                    const enabled = data.logging_enabled;
                    status.textContent = enabled ? window.jsTranslations.enabled : window.jsTranslations.disabled;
                }
                if (statusIcon) {
                    statusIcon.className = 'fas fa-circle';
                    statusIcon.style.color = data.logging_enabled ? '#22c55e' : '#ef4444'; // Green for enabled, red for disabled
                }
                
                // Update modified by
                const modifiedBy = document.getElementById('systemInfoLoggingModifiedBy');
                if (modifiedBy) {
                    modifiedBy.textContent = data.last_modified_by || 'N/A';
                }
            } else {
                console.error('Failed to load System Information logging status:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading System Information logging status:', error);
            showNotification('Failed to load System Information logging status', 'error');
        });
}

function saveSystemInfoLoggingSettings() {
    const toggle = document.getElementById('systemInfoLogging');
    const enabled = toggle.checked;
    
    // Disable toggle during save
    toggle.disabled = true;
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/system-information/api/logging/toggle/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ logging_enabled: enabled })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('System Information logging ' + (enabled ? 'enabled' : 'disabled'), 'success');
            loadSystemInfoLoggingStatus();
        } else {
            showNotification('Failed to save: ' + data.error, 'error');
            // Revert toggle
            toggle.checked = !enabled;
        }
    })
    .catch(error => {
        console.error('Failed to save System Information logging settings:', error);
        showNotification('Failed to save System Information logging settings', 'error');
        // Revert toggle
        toggle.checked = !enabled;
    })
    .finally(() => {
        toggle.disabled = false;
    });
}

// ===== LOGGING SETTINGS - SERVICE MONITORING =====

// Setup Service Monitoring logging toggle with auto-save
const serviceMonitoringLoggingToggle = document.getElementById('serviceMonitoringLogging');
if (serviceMonitoringLoggingToggle) {
    serviceMonitoringLoggingToggle.addEventListener('change', function() {
        // Auto-save on toggle
        saveServiceMonitoringLoggingSettings();
    });
}

function loadServiceMonitoringLoggingStatus() {
    fetch('/service-monitoring/api/logging/status/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update toggle
                const toggle = document.getElementById('serviceMonitoringLogging');
                if (toggle) {
                    toggle.checked = data.logging_enabled || false;
                }
                
                // Update status text and icon
                const status = document.getElementById('serviceMonitoringLoggingStatus');
                const statusIcon = document.getElementById('serviceMonitoringLoggingStatusIcon');
                if (status) {
                    const enabled = data.logging_enabled;
                    status.textContent = enabled ? window.jsTranslations.enabled : window.jsTranslations.disabled;
                }
                if (statusIcon) {
                    statusIcon.className = 'fas fa-circle';
                    statusIcon.style.color = data.logging_enabled ? '#22c55e' : '#ef4444'; // Green for enabled, red for disabled
                }
                
                // Update modified by
                const modifiedBy = document.getElementById('serviceMonitoringLoggingModifiedBy');
                if (modifiedBy) {
                    modifiedBy.textContent = data.last_modified_by || 'N/A';
                }
            } else {
                console.error('Failed to load Service Monitoring logging status:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading Service Monitoring logging status:', error);
            showNotification('Failed to load Service Monitoring logging status', 'error');
        });
}

function saveServiceMonitoringLoggingSettings() {
    const toggle = document.getElementById('serviceMonitoringLogging');
    const enabled = toggle.checked;
    
    // Disable toggle during save
    toggle.disabled = true;
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/service-monitoring/api/logging/toggle/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ logging_enabled: enabled })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Service Monitoring logging ' + (enabled ? 'enabled' : 'disabled'), 'success');
            loadServiceMonitoringLoggingStatus();
        } else {
            showNotification('Failed to save: ' + data.error, 'error');
            // Revert toggle
            toggle.checked = !enabled;
        }
    })
    .catch(error => {
        console.error('Failed to save Service Monitoring logging settings:', error);
        showNotification('Failed to save Service Monitoring logging settings', 'error');
        // Revert toggle
        toggle.checked = !enabled;
    })
    .finally(() => {
        toggle.disabled = false;
    });
}

// ===== SERVICE MONITORING LIVE MODE SETTINGS =====

// Setup Service Monitoring live mode toggle
const serviceMonitoringLiveModeToggle = document.getElementById('serviceMonitoringLiveMode');
if (serviceMonitoringLiveModeToggle) {
    serviceMonitoringLiveModeToggle.addEventListener('change', function() {
        toggleServiceMonitoringLiveMode(this.checked);
    });
}

// Setup Service Monitoring interval slider
const serviceMonitoringIntervalSlider = document.getElementById('serviceMonitoringIntervalRange');
const serviceMonitoringIntervalValue = document.getElementById('serviceMonitoringIntervalValue');
if (serviceMonitoringIntervalSlider && serviceMonitoringIntervalValue) {
    serviceMonitoringIntervalSlider.addEventListener('input', function() {
        serviceMonitoringIntervalValue.textContent = this.value;
    });
}

// Setup Service Monitoring save settings button
const serviceMonitoringSaveSettingsBtn = document.getElementById('serviceMonitoringSaveSettings');
if (serviceMonitoringSaveSettingsBtn) {
    serviceMonitoringSaveSettingsBtn.addEventListener('click', function() {
        saveServiceMonitoringSettings();
    });
}

function loadServiceMonitoringSettings() {
    fetch('/service-monitoring/api/live-mode/status/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update toggle
                const toggle = document.getElementById('serviceMonitoringLiveMode');
                if (toggle) {
                    toggle.checked = data.live_mode_enabled || false;
                }
                
                // Update interval slider
                const intervalSlider = document.getElementById('serviceMonitoringIntervalRange');
                const intervalValue = document.getElementById('serviceMonitoringIntervalValue');
                if (intervalSlider && intervalValue) {
                    intervalSlider.value = data.interval || 2.0;
                    intervalValue.textContent = data.interval || 2.0;
                }
            } else {
                console.error('Failed to load Service Monitoring settings:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading Service Monitoring settings:', error);
            showNotification('Failed to load Service Monitoring settings', 'error');
        });
}

function toggleServiceMonitoringLiveMode(enabled) {
    const interval = document.getElementById('serviceMonitoringIntervalRange').value;
    
    // Disable toggle during API call
    const toggle = document.getElementById('serviceMonitoringLiveMode');
    toggle.disabled = true;
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/service-monitoring/api/live-mode/toggle/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            live_mode: enabled,
            interval: parseFloat(interval)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Service Monitoring live mode ${enabled ? 'enabled' : 'disabled'}`, 'success');
        } else {
            showNotification('Failed to toggle live mode: ' + data.message, 'error');
            // Revert toggle
            toggle.checked = !enabled;
        }
    })
    .catch(error => {
        console.error('Error toggling Service Monitoring live mode:', error);
        showNotification('Failed to toggle Service Monitoring live mode', 'error');
        // Revert toggle
        toggle.checked = !enabled;
    })
    .finally(() => {
        toggle.disabled = false;
    });
}

function saveServiceMonitoringSettings() {
    const btn = document.getElementById('serviceMonitoringSaveSettings');
    if (!btn) return;
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    
    const liveModeEnabled = document.getElementById('serviceMonitoringLiveMode').checked;
    const interval = document.getElementById('serviceMonitoringIntervalRange').value;
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/service-monitoring/api/live-mode/toggle/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            live_mode: liveModeEnabled,
            interval: parseFloat(interval)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Service Monitoring settings saved successfully', 'success');
        } else {
            showNotification('Failed to save settings: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error saving Service Monitoring settings:', error);
        showNotification('Failed to save Service Monitoring settings', 'error');
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Save Settings';
    });
}

// Initialize all logging statuses on page load
document.addEventListener('DOMContentLoaded', function() {
    loadProcessMonitorLoggingStatus();
    loadDockerLoggingStatus();
    loadSystemInfoLoggingStatus();
    loadServiceMonitoringLoggingStatus();
    loadServiceMonitoringSettings();
    
    // Initialize SMTP settings
    setupSMTPListeners();
    loadSMTPConfig();
    loadCVEAutomation();
});

// ===== SMTP SETTINGS =====

function setupSMTPListeners() {
    // SMTP tab click
    const smtpTab = document.querySelector('[data-tab="smtp"]');
    if (smtpTab) {
        smtpTab.addEventListener('click', function() {
            loadSMTPConfig();
            loadCVEAutomation();
        });
    }
    
    // SMTP provider selection
    const smtpProvider = document.getElementById('smtp-provider');
    if (smtpProvider) {
        smtpProvider.addEventListener('change', function() {
            applySMTPPreset(this.value);
        });
    }
    
    // SMTP save button
    const smtpSaveBtn = document.getElementById('smtp-save-btn');
    if (smtpSaveBtn) {
        smtpSaveBtn.addEventListener('click', saveSMTPConfig);
    }
    
    // SMTP test button
    const smtpTestBtn = document.getElementById('smtp-test-btn');
    if (smtpTestBtn) {
        smtpTestBtn.addEventListener('click', testSMTPConnection);
    }
    
    // CVE automation toggle
    const cveAutomationToggle = document.getElementById('cve-automation-enabled');
    if (cveAutomationToggle) {
        cveAutomationToggle.addEventListener('change', function() {
            const settings = document.getElementById('cve-automation-settings');
            if (settings) {
                settings.style.opacity = this.checked ? '1' : '0.5';
            }
        });
    }
    
    // CVE schedule type change
    const cveScheduleType = document.getElementById('cve-schedule-type');
    if (cveScheduleType) {
        cveScheduleType.addEventListener('change', function() {
            const daysItem = document.getElementById('cve-schedule-days-item');
            const cronItem = document.getElementById('cve-schedule-cron-item');
            
            if (this.value === 'custom') {
                if (daysItem) daysItem.style.display = 'none';
                if (cronItem) cronItem.style.display = 'block';
            } else if (this.value === 'weekly') {
                if (daysItem) daysItem.style.display = 'block';
                if (cronItem) cronItem.style.display = 'none';
            } else {
                if (daysItem) daysItem.style.display = 'none';
                if (cronItem) cronItem.style.display = 'none';
            }
        });
    }
    
    // CVE automation save button
    const cveSaveBtn = document.getElementById('cve-automation-save-btn');
    if (cveSaveBtn) {
        cveSaveBtn.addEventListener('click', saveCVEAutomation);
    }
    
    // CVE automation test button
    const cveTestBtn = document.getElementById('cve-automation-test-btn');
    if (cveTestBtn) {
        cveTestBtn.addEventListener('click', testCVEAutomation);
    }
}

// SMTP Preset Configurations
// Port bilgileri:
// - Gmail: 587 (TLS) veya 465 (SSL) - 587 önerilir
// - Yahoo: 587 (TLS) veya 465 (SSL) - 587 önerilir  
// - Outlook: 587 (TLS) - tek seçenek
// - Office 365: 587 (TLS) - önerilen port
const SMTP_PRESETS = {
    'gmail': {
        host: 'smtp.gmail.com',
        port: 587,
        use_tls: true,
        use_ssl: false,
        description: 'Gmail (requires App Password)',
        alternative_port: 465,
        alternative_ssl: true
    },
    'outlook': {
        host: 'smtp-mail.outlook.com',
        port: 587,
        use_tls: true,
        use_ssl: false,
        description: 'Outlook / Hotmail'
    },
    'yahoo': {
        host: 'smtp.mail.yahoo.com',
        port: 587,
        use_tls: true,
        use_ssl: false,
        description: 'Yahoo Mail',
        alternative_port: 465,
        alternative_ssl: true
    },
    'office365': {
        host: 'smtp.office365.com',
        port: 587,
        use_tls: true,
        use_ssl: false,
        description: 'Office 365'
    },
    'custom': {
        host: '',
        port: 587,
        use_tls: true,
        use_ssl: false,
        description: 'Custom Configuration'
    }
};

function applySMTPPreset(provider) {
    if (!SMTP_PRESETS[provider]) {
        return;
    }
    
    const preset = SMTP_PRESETS[provider];
    
    document.getElementById('smtp-host').value = preset.host;
    document.getElementById('smtp-port').value = preset.port;
    document.getElementById('smtp-use-tls').checked = preset.use_tls;
    document.getElementById('smtp-use-ssl').checked = preset.use_ssl;
    
    // Show notification
    if (provider !== 'custom') {
        const appliedMsg = (window.jsTranslations.applied_settings || 'Applied {description} settings').replace('{description}', preset.description);
        showNotification(appliedMsg, 'success');
    }
    
    // If not custom, disable manual editing temporarily (optional)
    // Or just let user modify if needed
}

function loadSMTPConfig() {
    fetch('/smtp/api/config/')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.config) {
                const config = data.config;
                
                // Try to detect provider from saved config
                let detectedProvider = 'custom';
                for (const [key, preset] of Object.entries(SMTP_PRESETS)) {
                    if (key !== 'custom' && 
                        config.host === preset.host && 
                        config.port === preset.port &&
                        config.use_tls === preset.use_tls &&
                        config.use_ssl === preset.use_ssl) {
                        detectedProvider = key;
                        break;
                    }
                }
                
                // Set provider dropdown
                document.getElementById('smtp-provider').value = detectedProvider;
                
                // Load config values
                document.getElementById('smtp-host').value = config.host || '';
                document.getElementById('smtp-port').value = config.port || 587;
                document.getElementById('smtp-use-tls').checked = config.use_tls !== false;
                document.getElementById('smtp-use-ssl').checked = config.use_ssl === true;
                document.getElementById('smtp-username').value = config.username || '';
                // From email and name are now automatic - use username as from_email
                document.getElementById('smtp-is-active').checked = config.is_active === true;
            } else {
                // No config exists, set to custom
                document.getElementById('smtp-provider').value = 'custom';
            }
        })
        .catch(error => {
            console.error('Error loading SMTP config:', error);
        });
}

function saveSMTPConfig() {
    const btn = document.getElementById('smtp-save-btn');
    const originalHTML = btn.innerHTML;
    
    // Get form values
    const host = document.getElementById('smtp-host').value.trim();
    const port = parseInt(document.getElementById('smtp-port').value) || 587;
    const username = document.getElementById('smtp-username').value.trim();
    const password = document.getElementById('smtp-password').value;
    const use_tls = document.getElementById('smtp-use-tls').checked;
    const use_ssl = document.getElementById('smtp-use-ssl').checked;
    const is_active = document.getElementById('smtp-is-active').checked;
    
    // Validation
    if (!host) {
        showNotification(window.jsTranslations.please_enter_smtp_host || 'Please enter SMTP host', 'error');
        return;
    }
    
    if (!username) {
        showNotification(window.jsTranslations.please_enter_email_address || 'Please enter email address', 'error');
        return;
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(username)) {
        showNotification(window.jsTranslations.please_enter_valid_email || 'Please enter a valid email address', 'error');
        return;
    }
    
    // Password validation - only required if this is a new config or if user explicitly wants to change it
    // We'll allow saving without password if config already exists (password will be kept)
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + (window.jsTranslations.saving || 'Saving...');
    btn.disabled = true;
    
    const data = {
        host: host,
        port: port,
        use_tls: use_tls,
        use_ssl: use_ssl,
        username: username,
        from_email: username, // Use username as from_email automatically
        from_name: 'Ophiron System', // Default from name
        is_active: is_active,
    };
    
    // Only include password if provided (not empty)
    if (password && password.trim()) {
        data.password = password;
    }
    
    fetch('/smtp/api/config/save/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(window.jsTranslations.smtp_configuration_saved_successfully || 'SMTP configuration saved successfully', 'success');
            // Clear password field for security (password is saved in backend)
            document.getElementById('smtp-password').value = '';
            // Reload config to show updated values (password won't be shown)
            loadSMTPConfig();
        } else {
            showNotification((window.jsTranslations.failed_to_save || 'Failed to save') + ': ' + (data.error || (window.jsTranslations.unknown_error || 'unknown error')), 'error');
        }
    })
    .catch(error => {
        console.error('Error saving SMTP config:', error);
        showNotification(window.jsTranslations.failed_to_save_smtp_configuration || 'Failed to save SMTP configuration', 'error');
    })
    .finally(() => {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    });
}

function testSMTPConnection() {
    const btn = document.getElementById('smtp-test-btn');
    const resultDiv = document.getElementById('smtp-test-result');
    const originalHTML = btn.innerHTML;
    
    // Get form values
    const host = document.getElementById('smtp-host').value.trim();
    const port = parseInt(document.getElementById('smtp-port').value) || null;
    const username = document.getElementById('smtp-username').value.trim();
    const password = document.getElementById('smtp-password').value;
    const use_tls = document.getElementById('smtp-use-tls').checked;
    const use_ssl = document.getElementById('smtp-use-ssl').checked;
    
    // Basic validation
    if (!host && !username) {
        showNotification(window.jsTranslations.please_configure_smtp_first || 'Please configure SMTP settings first (host and email)', 'error');
        return;
    }
    
    // Email validation (if username is provided)
    if (username) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(username)) {
            showNotification(window.jsTranslations.please_enter_valid_email || 'Please enter a valid email address', 'error');
            return;
        }
    }
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + (window.jsTranslations.testing || 'Testing...');
    btn.disabled = true;
    resultDiv.style.display = 'none';
    
    // Build data object - only include fields that have values
    // Backend will use saved config values for missing fields
    const data = {};
    if (host) data.host = host;
    if (port) data.port = port;
    if (username) data.username = username;
    if (password) data.password = password;
    data.use_tls = use_tls;
    data.use_ssl = use_ssl;
    
    fetch('/smtp/api/config/test/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        resultDiv.style.display = 'block';
        if (data.success) {
            resultDiv.style.backgroundColor = '#c6f6d5';
            resultDiv.style.color = '#22543d';
            resultDiv.innerHTML = '<i class="fas fa-check-circle"></i> ' + (window.jsTranslations.smtp_connection_test_successful || 'Connection test successful!');
            showNotification(window.jsTranslations.smtp_connection_test_successful || 'SMTP connection test successful', 'success');
            // Reload config to update test status
            loadSMTPConfig();
        } else {
            resultDiv.style.backgroundColor = '#fed7d7';
            resultDiv.style.color = '#742a2a';
            resultDiv.innerHTML = '<i class="fas fa-times-circle"></i> ' + (data.error || (window.jsTranslations.connection_test_failed || 'Connection test failed'));
            showNotification((window.jsTranslations.smtp_connection_test_failed || 'SMTP connection test failed') + ': ' + (data.error || (window.jsTranslations.unknown_error || 'unknown error')), 'error');
        }
    })
    .catch(error => {
        console.error('Error testing SMTP connection:', error);
        resultDiv.style.display = 'block';
        resultDiv.style.backgroundColor = '#fed7d7';
        resultDiv.style.color = '#742a2a';
        resultDiv.innerHTML = '<i class="fas fa-times-circle"></i> ' + (window.jsTranslations.error_testing_connection || 'Error testing connection');
        showNotification(window.jsTranslations.failed_to_test_smtp_connection || 'Failed to test SMTP connection', 'error');
    })
    .finally(() => {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    });
}

function loadCVEAutomation() {
    fetch('/smtp/api/automations/')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.automations) {
                // Find CVE automation
                const cveAutomation = data.automations.find(a => a.automation_type === 'cve');
                
                if (cveAutomation) {
                    document.getElementById('cve-automation-enabled').checked = cveAutomation.is_enabled;
                    document.getElementById('cve-schedule-type').value = cveAutomation.schedule_type || 'daily';
                    document.getElementById('cve-schedule-time').value = cveAutomation.schedule_time || '06:00';
                    document.getElementById('cve-schedule-days').value = cveAutomation.schedule_days || '';
                    document.getElementById('cve-schedule-cron').value = cveAutomation.schedule_cron || '';
                    // Recipients field is hidden, but we keep it for backward compatibility
                    document.getElementById('cve-recipients').value = (cveAutomation.recipients || []).join('\n');
                    document.getElementById('cve-min-cves').value = (cveAutomation.config || {}).min_cves || 0;
                    document.getElementById('cve-send-always').checked = (cveAutomation.config || {}).send_always || false;
                    
                    // Update status
                    document.getElementById('cve-automation-status-value').textContent = 
                        cveAutomation.is_enabled ? (window.jsTranslations.enabled || 'Enabled') : (window.jsTranslations.disabled || 'Disabled');
                    document.getElementById('cve-automation-last-run').textContent = 
                        cveAutomation.last_run_at ? new Date(cveAutomation.last_run_at).toLocaleString() : (window.jsTranslations.never || 'Never');
                    document.getElementById('cve-automation-next-run').textContent = 
                        cveAutomation.next_run_at ? new Date(cveAutomation.next_run_at).toLocaleString() : (window.jsTranslations.not_scheduled || 'Not scheduled');
                    
                    // Trigger schedule type change to show/hide fields
                    document.getElementById('cve-schedule-type').dispatchEvent(new Event('change'));
                }
            }
        })
        .catch(error => {
            console.error('Error loading CVE automation:', error);
        });
}

function saveCVEAutomation() {
    const btn = document.getElementById('cve-automation-save-btn');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + (window.jsTranslations.saving || 'Saving...');
    btn.disabled = true;
    
    // Recipients are now automatic - will be set from user's email
    // Keep empty array for backward compatibility
    const recipients = [];
    
    const data = {
        automation_type: 'cve',
        name: 'CVE Email Automation',
        is_enabled: document.getElementById('cve-automation-enabled').checked,
        schedule_type: document.getElementById('cve-schedule-type').value,
        schedule_time: document.getElementById('cve-schedule-time').value,
        schedule_days: document.getElementById('cve-schedule-days').value,
        schedule_cron: document.getElementById('cve-schedule-cron').value,
        recipients: recipients, // Empty - will use user's email automatically
        config: {
            min_cves: parseInt(document.getElementById('cve-min-cves').value) || 0,
            send_always: document.getElementById('cve-send-always').checked,
        }
    };
    
    fetch('/smtp/api/automations/save/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(window.jsTranslations.cve_automation_saved_successfully || 'CVE automation settings saved successfully', 'success');
            loadCVEAutomation();
        } else {
            showNotification((window.jsTranslations.failed_to_save || 'Failed to save') + ': ' + (data.error || (window.jsTranslations.unknown_error || 'unknown error')), 'error');
        }
    })
    .catch(error => {
        console.error('Error saving CVE automation:', error);
        showNotification(window.jsTranslations.failed_to_save_cve_automation || 'Failed to save CVE automation settings', 'error');
    })
    .finally(() => {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    });
}

function testCVEAutomation() {
    // First, save the automation to get an ID
    const saveBtn = document.getElementById('cve-automation-save-btn');
    saveBtn.click();
    
    // Wait a bit, then try to run it
    setTimeout(() => {
        fetch('/smtp/api/automations/')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.automations) {
                    const cveAutomation = data.automations.find(a => a.automation_type === 'cve');
                    if (cveAutomation && cveAutomation.id) {
                        const testBtn = document.getElementById('cve-automation-test-btn');
                        const originalHTML = testBtn.innerHTML;
                        testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + (window.jsTranslations.running || 'Running...');
                        testBtn.disabled = true;
                        
                        fetch(`/smtp/api/automations/${cveAutomation.id}/run/`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                            }
                        })
                        .then(response => response.json())
                        .then(result => {
                            if (result.success) {
                                showNotification((window.jsTranslations.test_completed || 'Test completed') + ': ' + result.message, 'success');
                            } else {
                                showNotification((window.jsTranslations.test_failed || 'Test failed') + ': ' + (result.error || result.message || (window.jsTranslations.unknown_error || 'unknown error')), 'error');
                            }
                            loadCVEAutomation();
                        })
                        .catch(error => {
                            console.error('Error running CVE automation:', error);
                            showNotification(window.jsTranslations.failed_to_run_cve_automation_test || 'Failed to run CVE automation test', 'error');
                        })
                        .finally(() => {
                            testBtn.innerHTML = originalHTML;
                            testBtn.disabled = false;
                        });
                    }
                }
            })
            .catch(error => {
                console.error('Error loading automations:', error);
            });
    }, 1000);
}
