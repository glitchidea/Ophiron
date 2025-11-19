// Error Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Show error time
    updateErrorTime();
    
    // Update time every second
    setInterval(updateErrorTime, 1000);
    
    // Start animations when page loads
    startAnimations();
    
    // Special animation for go back button
    const backButton = document.querySelector('.btn-secondary');
    if (backButton) {
        backButton.addEventListener('click', function(e) {
            e.preventDefault();
            animateBackButton();
        });
    }
    
    // Animation for go to home button
    const homeButton = document.querySelector('.btn-primary');
    if (homeButton) {
        homeButton.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
        });
        
        homeButton.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    }
});

function updateErrorTime() {
    const errorTimeElement = document.getElementById('errorTime');
    if (errorTimeElement) {
        const now = new Date();
        const timeString = now.toLocaleString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        errorTimeElement.textContent = `Error Time: ${timeString}`;
    }
}

function startAnimations() {
    // Shake animation for error icon
    const errorIcon = document.querySelector('.error-icon');
    if (errorIcon) {
        setTimeout(() => {
            errorIcon.style.animation = 'shake 0.5s ease-in-out';
        }, 1000);
    }
    
    // Slowly show error title
    const errorTitle = document.querySelector('.error-title');
    if (errorTitle) {
        errorTitle.style.opacity = '0';
        errorTitle.style.transform = 'translateY(50px)';
        
        setTimeout(() => {
            errorTitle.style.transition = 'all 1s ease-out';
            errorTitle.style.opacity = '1';
            errorTitle.style.transform = 'translateY(0)';
        }, 500);
    }
    
    // Show subtitle
    const errorSubtitle = document.querySelector('.error-subtitle');
    if (errorSubtitle) {
        errorSubtitle.style.opacity = '0';
        errorSubtitle.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            errorSubtitle.style.transition = 'all 0.8s ease-out';
            errorSubtitle.style.opacity = '1';
            errorSubtitle.style.transform = 'translateY(0)';
        }, 800);
    }
    
    // Show description
    const errorDescription = document.querySelector('.error-description');
    if (errorDescription) {
        errorDescription.style.opacity = '0';
        errorDescription.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            errorDescription.style.transition = 'all 0.6s ease-out';
            errorDescription.style.opacity = '1';
            errorDescription.style.transform = 'translateY(0)';
        }, 1200);
    }
    
    // Show buttons
    const errorActions = document.querySelector('.error-actions');
    if (errorActions) {
        errorActions.style.opacity = '0';
        errorActions.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            errorActions.style.transition = 'all 0.8s ease-out';
            errorActions.style.opacity = '1';
            errorActions.style.transform = 'translateY(0)';
        }, 1500);
    }
}

function animateBackButton() {
    const backButton = document.querySelector('.btn-secondary');
    if (backButton) {
        // Button animation
        backButton.style.transform = 'scale(0.95)';
        backButton.style.background = 'rgba(255, 255, 255, 0.3)';
        
        setTimeout(() => {
            backButton.style.transform = 'scale(1)';
            backButton.style.background = 'rgba(255, 255, 255, 0.1)';
            
            // Go back action
            setTimeout(() => {
                if (window.history.length > 1) {
                    window.history.back();
                } else {
                    // If no history, redirect to home page
                    window.location.href = '/';
                }
            }, 200);
        }, 150);
    }
}

// Additional styles for CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
    
    .error-icon {
        animation: bounce 2s infinite, shake 0.5s ease-in-out;
    }
`;
document.head.appendChild(style);
