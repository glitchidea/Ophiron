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
        profileImage.style.display = 'block';
        userIcon.style.display = 'none';
    }
}

