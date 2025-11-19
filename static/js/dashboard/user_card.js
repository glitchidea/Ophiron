/**
 * User Card JavaScript
 * Handles user card interactions and animations
 */

class UserCard {
    constructor() {
        this.card = document.querySelector('.user-card');
        this.avatar = document.querySelector('.user-avatar-img, .user-avatar-placeholder');
        this.init();
    }

    init() {
        if (this.card) {
            this.setupEventListeners();
            this.addHoverEffects();
        }
    }

    setupEventListeners() {
        // Avatar click animation
        if (this.avatar) {
            this.avatar.addEventListener('click', () => {
                this.animateAvatar();
            });
        }

        // Card hover effects
        this.card.addEventListener('mouseenter', () => {
            this.card.classList.add('hovered');
        });

        this.card.addEventListener('mouseleave', () => {
            this.card.classList.remove('hovered');
        });
    }

    addHoverEffects() {
        // Add subtle pulse animation to avatar
        if (this.avatar) {
            this.avatar.style.animation = 'pulse 2s infinite';
        }
    }

    animateAvatar() {
        if (this.avatar) {
            this.avatar.style.transform = 'scale(1.1)';
            this.avatar.style.transition = 'transform 0.2s ease';
            
            setTimeout(() => {
                this.avatar.style.transform = 'scale(1)';
            }, 200);
        }
    }

    // Method to update user info dynamically
    updateUserInfo(userData) {
        const nameElement = this.card.querySelector('.user-name');
        const roleElement = this.card.querySelector('.user-role');
        
        if (nameElement && userData.name) {
            nameElement.textContent = userData.name;
        }
        
        if (roleElement && userData.role) {
            roleElement.innerHTML = `
                <i class="fas fa-${userData.roleIcon}"></i>
                ${userData.role}
            `;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new UserCard();
});

// Add CSS animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .user-card.hovered .user-avatar-img,
    .user-card.hovered .user-avatar-placeholder {
        animation: none;
        transform: scale(1.1);
    }
`;
document.head.appendChild(style);
