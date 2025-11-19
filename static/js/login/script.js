document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('loginForm');
    const btn = document.getElementById('submitBtn');
    const alert = document.getElementById('alert');
    const inputs = document.querySelectorAll('.input-field');
    const snake = document.querySelector('.snake');

    // Start snake animation
    if (snake) {
        snake.style.animation = 'snakeMove 35s linear infinite';
    }

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        alert.classList.remove('show');
        btn.classList.add('loading');
        
        // Get form data
        const formData = new FormData(form);
        
        // Send to Django via AJAX
        fetch('/login/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => {
            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers.get('content-type'));
            
            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Response is not JSON. Server might have returned an error page.');
            }
            
            return response.json();
        })
        .then(data => {
            console.log('Response data:', data);
            btn.classList.remove('loading');
            if (data.success) {
                if (data.requires_2fa) {
                    // 2FA required, redirect to 2FA page
                    showNotification(data.message, 'info');
                    setTimeout(() => {
                        window.location.href = data.redirect;
                    }, 1000);
                } else {
                    // Normal login successful - redirect to dashboard
                    window.location.href = data.redirect;
                }
            } else {
                // Show error message
                alert.classList.add('show');
                const alertText = alert.querySelector('.alert-text');
                alertText.textContent = data.error || 'Login failed';
                
                // Special style for rate limiting
                if (data.rate_limited) {
                    alert.classList.add('rate-limited');
                    alertText.innerHTML = `
                        <i class="fas fa-ban"></i>
                        ${data.error}
                    `;
                } else {
                    alert.classList.remove('rate-limited');
                }
                
                // Show remaining attempts if any
                if (data.remaining_attempts && data.remaining_attempts > 0) {
                    // Remove previous remaining attempts message
                    const existingRemaining = alert.querySelector('.remaining-attempts');
                    if (existingRemaining) {
                        existingRemaining.remove();
                    }
                    
                    const remainingDiv = document.createElement('div');
                    remainingDiv.className = 'remaining-attempts';
                    remainingDiv.innerHTML = `
                        <small style="color: #ff6b6b; font-size: 12px;">
                            <i class="fas fa-exclamation-triangle"></i>
                            Remaining attempts: ${data.remaining_attempts}
                        </small>
                    `;
                    alert.appendChild(remainingDiv);
                } else {
                    // If no remaining attempts, clear old message
                    const existingRemaining = alert.querySelector('.remaining-attempts');
                    if (existingRemaining) {
                        existingRemaining.remove();
                    }
                }
            }
        })
        .catch(error => {
            console.error('Login error:', error);
            btn.classList.remove('loading');
            alert.classList.add('show');
            const alertText = alert.querySelector('.alert-text');
            alertText.textContent = 'An error occurred. Check console for details.';
        });
    });

    inputs.forEach(input => {
        input.addEventListener('input', () => {
            alert.classList.remove('show');
            // Also clear remaining attempts message
            const existingRemaining = alert.querySelector('.remaining-attempts');
            if (existingRemaining) {
                existingRemaining.remove();
            }
        });

        input.addEventListener('focus', () => {
            console.log('Input focused!'); // Debug
            input.parentElement.style.transform = 'scale(1.02)';
            // Move snake towards input area
            if (snake) {
                // Stop normal animation first
                snake.style.animation = 'none';
                snake.style.left = '70%';
                snake.style.top = '30%';
                // After a short delay start the focused animation
                setTimeout(() => {
                    snake.classList.add('focused');
                    snake.style.animation = 'snakeMoveToInput 2s linear infinite';
                    console.log('Snake focused class added!'); // Debug
                }, 50);
            }
        });

        input.addEventListener('blur', () => {
            console.log('Input blurred!'); // Debug
            input.parentElement.style.transform = 'scale(1)';
            // Return snake to normal movement
            if (snake) {
                snake.classList.remove('focused');
                // Restart normal animation
                snake.style.animation = 'snakeMove 35s linear infinite';
                snake.style.left = '';
                snake.style.top = '';
                console.log('Snake focused class removed!'); // Debug
            }
        });
    });
});

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
