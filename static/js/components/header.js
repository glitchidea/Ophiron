/*
Ophiron Header JavaScript
Header dropdown menu functions
*/

document.addEventListener('DOMContentLoaded', function() {
    initHeaderDropdown();
    loadHeaderProfileImage();
});

function initHeaderDropdown() {
    const trigger = document.getElementById('userDropdownTrigger');
    const menu = document.getElementById('userDropdownMenu');
    
    if (!trigger || !menu) return;
    
    // Toggle dropdown open/close
    trigger.addEventListener('click', function(e) {
        e.stopPropagation();
        toggleDropdown();
    });
    
    // Close when clicking outside
    document.addEventListener('click', function(e) {
        if (!trigger.contains(e.target) && !menu.contains(e.target)) {
            closeDropdown();
        }
    });
    
    // Close with ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeDropdown();
        }
    });
}

function toggleDropdown() {
    const trigger = document.getElementById('userDropdownTrigger');
    const menu = document.getElementById('userDropdownMenu');
    
    if (menu.classList.contains('show')) {
        closeDropdown();
    } else {
        openDropdown();
    }
}

function openDropdown() {
    const trigger = document.getElementById('userDropdownTrigger');
    const menu = document.getElementById('userDropdownMenu');
    
    trigger.classList.add('active');
    menu.classList.add('show');
}

function closeDropdown() {
    const trigger = document.getElementById('userDropdownTrigger');
    const menu = document.getElementById('userDropdownMenu');
    
    trigger.classList.remove('active');
    menu.classList.remove('show');
}

function loadHeaderProfileImage() {
    // Profile image is already loaded in the template
    // Only adjust visibility
    const profileImage = document.getElementById('headerProfileImage');
    const userIcon = document.getElementById('headerUserIcon');
    
    if (profileImage && userIcon) {
        // Check if image is not the default avatar
        if (profileImage.src && !profileImage.src.includes('demo-avatar.svg')) {
        profileImage.style.display = 'block';
        userIcon.style.display = 'none';
        }
    }
    
    // Also load dropdown profile image
    const dropdownProfileImage = document.getElementById('dropdownProfileImage');
    const dropdownUserIcon = document.getElementById('dropdownUserIcon');
    
    if (dropdownProfileImage && dropdownUserIcon) {
        // Check if image is not the default avatar
        if (dropdownProfileImage.src && !dropdownProfileImage.src.includes('demo-avatar.svg')) {
            dropdownProfileImage.classList.add('show');
            dropdownUserIcon.style.display = 'none';
        } else {
            dropdownUserIcon.style.display = 'block';
        }
    }
}

