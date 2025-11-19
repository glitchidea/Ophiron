/**
 * Create User JavaScript
 * Handles user creation functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Modal elements
    const createUserModal = document.getElementById('createUserModal');
    const createUserForm = document.getElementById('createUserForm');
    const cancelCreateUser = document.getElementById('cancelCreateUser');
    const submitCreateUser = document.getElementById('submitCreateUser');
    
    // ===== MODAL MANAGEMENT =====
    
    function openCreateUserModal() {
        createUserModal.classList.add('active');
        document.body.style.overflow = 'hidden';
        // Focus on username field
        setTimeout(() => {
            document.getElementById('username').focus();
        }, 100);
    }
    
    function closeCreateUserModal() {
        createUserModal.classList.remove('active');
        document.body.style.overflow = '';
        resetForm();
    }
    
    // ===== FORM VALIDATION =====
    
    function validateForm() {
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        
        let isValid = true;
        
        // Validate username
        if (!username) {
            showFieldError('username', window.jsTranslations['Username is required'] || 'Username is required');
            isValid = false;
        } else if (username.length < 2) {
            showFieldError('username', window.jsTranslations['Username must be at least 2 characters long'] || 'Username must be at least 2 characters long');
            isValid = false;
        } else if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
            showFieldError('username', window.jsTranslations['Username can only contain letters, numbers, underscores, and hyphens'] || 'Username can only contain letters, numbers, underscores, and hyphens');
            isValid = false;
        } else {
            clearFieldError('username');
        }
        
        // Validate password
        if (!password) {
            showFieldError('password', window.jsTranslations['Password is required'] || 'Password is required');
            isValid = false;
        } else if (password.length < 6) {
            showFieldError('password', window.jsTranslations['Password must be at least 6 characters long'] || 'Password must be at least 6 characters long');
            isValid = false;
        } else {
            clearFieldError('password');
        }
        
        return isValid;
    }
    
    function showFieldError(fieldName, message) {
        const field = document.getElementById(fieldName);
        const existingError = field.parentNode.querySelector('.form-error');
        
        if (existingError) {
            existingError.remove();
        }
        
        field.classList.add('error');
        field.classList.remove('success');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        field.parentNode.appendChild(errorDiv);
    }
    
    function clearFieldError(fieldName) {
        const field = document.getElementById(fieldName);
        const existingError = field.parentNode.querySelector('.form-error');
        
        if (existingError) {
            existingError.remove();
        }
        
        field.classList.remove('error');
        field.classList.add('success');
    }
    
    // ===== FORM SUBMISSION =====
    
    function submitForm() {
        if (!validateForm()) {
            return;
        }
        
        const formData = new FormData(createUserForm);
        const userData = {
            username: formData.get('username').trim(),
            password: formData.get('password'),
            home_directory: formData.get('home_directory').trim() || null,
            root_dir: formData.get('root_dir').trim() || null,
            grant_sudo: formData.get('grant_sudo') === 'on'
        };
        
        // Set loading state
        createUserForm.classList.add('form-submitting');
        submitCreateUser.disabled = true;
        
        // Submit form
        fetch('/user-management/api/create-user/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Response is not JSON');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showNotification(window.jsTranslations['User created successfully!'] || 'User created successfully!', 'success');
                closeCreateUserModal();
                // Refresh the page to show new user
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showNotification(data.error || window.jsTranslations['Failed to create user'] || 'Failed to create user', 'error');
            }
        })
        .catch(error => {
            console.error('Error creating user:', error);
            if (error.message.includes('Response is not JSON')) {
                showNotification(window.jsTranslations['Server returned invalid response'] || 'Server returned invalid response', 'error');
            } else if (error.message.includes('HTTP error')) {
                showNotification(window.jsTranslations['Server error occurred'] || 'Server error occurred', 'error');
            } else {
                showNotification((window.jsTranslations['Error creating user'] || 'Error creating user') + ': ' + error.message, 'error');
            }
        })
        .finally(() => {
            // Reset loading state
            createUserForm.classList.remove('form-submitting');
            submitCreateUser.disabled = false;
        });
    }
    
    // ===== FORM RESET =====
    
    function resetForm() {
        createUserForm.reset();
        
        // Clear validation states
        const inputs = createUserForm.querySelectorAll('.form-input');
        inputs.forEach(input => {
            input.classList.remove('error', 'success');
        });
        
        // Clear error messages
        const errors = createUserForm.querySelectorAll('.form-error');
        errors.forEach(error => error.remove());
    }
    
    // ===== NOTIFICATION SYSTEM =====
    
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        // Remove notification
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
    
    function getNotificationIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
    
    // ===== EVENT LISTENERS =====
    
    // Form submission
    createUserForm.addEventListener('submit', function(e) {
        e.preventDefault();
        submitForm();
    });
    
    // Cancel button
    cancelCreateUser.addEventListener('click', function() {
        closeCreateUserModal();
    });
    
    // Close modal when clicking outside
    createUserModal.addEventListener('click', function(e) {
        if (e.target === this) {
            closeCreateUserModal();
        }
    });
    
    // Close modal with ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && createUserModal.classList.contains('active')) {
            closeCreateUserModal();
        }
    });
    
    // Real-time validation
    document.getElementById('username').addEventListener('input', function() {
        const username = this.value.trim();
        if (username && /^[a-zA-Z0-9_-]+$/.test(username) && username.length >= 2) {
            clearFieldError('username');
        }
    });
    
    document.getElementById('password').addEventListener('input', function() {
        const password = this.value;
        if (password && password.length >= 6) {
            clearFieldError('password');
        }
    });
    
    // ===== EXPOSE GLOBAL FUNCTIONS =====
    
    window.openCreateUserModal = openCreateUserModal;
    window.closeCreateUserModal = closeCreateUserModal;
});
