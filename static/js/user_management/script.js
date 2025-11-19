/**
 * User Management JavaScript
 * For managing system users and monitoring user activities
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Modal elements
    const userDetailsModal = document.getElementById('userDetailsModal');
    const userActivitiesModal = document.getElementById('userActivitiesModal');
    const userSessionsModal = document.getElementById('userSessionsModal');
    
    // ===== MODAL MANAGEMENT =====
    
    function openModal(modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    function closeModal(modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
    
    // Expose as global functions for use in other modules
    window.openModal = openModal;
    window.closeModal = closeModal;
    
    // Modal close buttons
    document.querySelectorAll('.modal-close, [data-dismiss="modal"]').forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal);
        });
    });
    
    // Close when clicking outside modal
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this);
            }
        });
    });

    // Close modal with ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal.active');
            if (activeModal) {
                closeModal(activeModal);
            }
        }
    });
    
    // ===== SYNC USERS =====
    
    const syncUsersBtn = document.getElementById('syncUsersBtn');
    if (syncUsersBtn) {
        syncUsersBtn.addEventListener('click', function() {
        const icon = this.querySelector('i');
        const indicator = document.getElementById('syncIndicator');
        
        // Update UI
        icon.classList.add('fa-spin');
        indicator.className = 'sync-indicator syncing';
        indicator.title = window.jsTranslations['Syncing users...'] || 'Syncing users...';
        this.disabled = true;
        
        fetch('/user-management/api/sync/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message || window.jsTranslations['Users synchronized successfully'] || 'Users synchronized successfully', 'success');
                // Refresh the page to show updated data
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showNotification(data.error || window.jsTranslations['Failed to synchronize users'] || 'Failed to synchronize users', 'error');
                indicator.className = 'sync-indicator error';
                indicator.title = window.jsTranslations['Sync failed'] || 'Sync failed';
            }
        })
        .catch(error => {
            console.error('Error syncing users:', error);
            showNotification(window.jsTranslations['Failed to synchronize users'] || 'Failed to synchronize users', 'error');
            indicator.className = 'sync-indicator error';
            indicator.title = window.jsTranslations['Sync failed'] || 'Sync failed';
        })
        .finally(() => {
            icon.classList.remove('fa-spin');
            this.disabled = false;
            setTimeout(() => {
                indicator.className = 'sync-indicator ready';
                indicator.title = window.jsTranslations['Ready'] || 'Ready';
            }, 3000);
        });
        });
    }
    
    // ===== REFRESH DATA =====
    
    const refreshDataBtn = document.getElementById('refreshDataBtn');
    if (refreshDataBtn) {
        refreshDataBtn.addEventListener('click', function() {
        const icon = this.querySelector('i');
        icon.classList.add('fa-spin');
        
        // Refresh all data
        loadUsers();
        loadStats();
        
        // Stop icon animation after 1 second
        setTimeout(() => {
            icon.classList.remove('fa-spin');
        }, 1000);
        });
    }
    
    // ===== FILTER TABS =====
    
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            const filter = this.dataset.filter;
            
            // Update active tab
            document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // Filter users
            filterUsers(filter);
        });
    });
    
    function filterUsers(filter) {
        const rows = document.querySelectorAll('#usersBody tr[data-user-type]');
        
        rows.forEach(row => {
            const userType = row.dataset.userType;
            
            if (filter === 'all' || 
                (filter === 'system' && userType === 'system') ||
                (filter === 'real' && userType === 'real')) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
        
        // Update total count
        const visibleRows = document.querySelectorAll('#usersBody tr[data-user-type]:not([style*="display: none"])');
        document.getElementById('totalUsers').textContent = visibleRows.length;
    }
    
    // ===== LOAD DATA FUNCTIONS =====
    
    function loadUsers() {
        fetch('/user-management/api/users/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateUsersTable(data.users);
                }
            })
            .catch(error => console.error('Error loading users:', error));
    }
    
    function loadStats() {
        fetch('/user-management/api/stats/')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    displayStats(data.stats);
                } else {
                    console.error('Stats API error:', data.error);
                    document.getElementById('statsWidgetBody').innerHTML = `<div class="error-state"><i class="fas fa-exclamation-triangle"></i><span>${window.jsTranslations['Error loading stats'] || 'Error loading stats'}</span></div>`;
                }
            })
            .catch(error => {
                console.error('Error loading stats:', error);
                document.getElementById('statsWidgetBody').innerHTML = `<div class="error-state"><i class="fas fa-exclamation-triangle"></i><span>${window.jsTranslations['Error loading stats'] || 'Error loading stats'}</span></div>`;
            });
    }
    
    
    // ===== UPDATE USERS TABLE =====
    
    function updateUsersTable(users) {
        const tbody = document.getElementById('usersBody');
        
        if (users.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" class="empty-state">
                <i class="fas fa-inbox"></i>
                <span>${window.jsTranslations['No users found'] || 'No users found'}</span>
            </td></tr>`;
            return;
        }
        
        tbody.innerHTML = users.map(user => {
            const userType = user.is_system_user ? 'system' : 'real';
            const statusClass = user.is_active ? 'active' : 'inactive';
            const lastLogin = user.last_login ? new Date(user.last_login).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }) : (window.jsTranslations['Never'] || 'Never');
            
            return `
                <tr data-user-type="${userType}">
                    <td class="username-cell">
                        <div class="user-info">
                            <i class="fas fa-user"></i>
                            <span>${user.username}</span>
                        </div>
                    </td>
                    <td><span class="uid-badge">${user.uid}</span></td>
                    <td><span class="gid-badge">${user.gid}</span></td>
                    <td class="directory-cell">${user.home_directory}</td>
                    <td class="shell-cell">${user.shell}</td>
                    <td>
                        <span class="badge badge-${userType}">
                            ${user.is_system_user ? (window.jsTranslations['System'] || 'System') : (window.jsTranslations['Real'] || 'Real')}
                        </span>
                    </td>
                    <td>
                        <span class="badge badge-status badge-${statusClass}">
                            ${user.is_active ? (window.jsTranslations['Active'] || 'Active') : (window.jsTranslations['Inactive'] || 'Inactive')}
                        </span>
                    </td>
                    <td class="last-login-cell">${lastLogin}</td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn-icon btn-view-details" 
                                    data-user-id="${user.id}"
                                    title="${window.jsTranslations['View Details'] || 'View Details'}">
                                <i class="fas fa-info-circle"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
        // Attach event listeners to new buttons
        attachEventListeners();
    }
    
    // ===== DISPLAY STATS =====
    
    function displayStats(stats) {
        const body = document.getElementById('statsWidgetBody');
        
        body.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">${stats.total_users}</div>
                    <div class="stat-label">${window.jsTranslations['Total Users'] || 'Total Users'}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.active_users}</div>
                    <div class="stat-label">${window.jsTranslations['Active Users'] || 'Active Users'}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.system_users}</div>
                    <div class="stat-label">${window.jsTranslations['System Users'] || 'System Users'}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.real_users}</div>
                    <div class="stat-label">${window.jsTranslations['Real Users'] || 'Real Users'}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.active_sessions}</div>
                    <div class="stat-label">${window.jsTranslations['Active Sessions'] || 'Active Sessions'}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.recent_activities}</div>
                    <div class="stat-label">${window.jsTranslations['Recent Activities'] || 'Recent Activities'}</div>
                </div>
            </div>
        `;
    }
    
    
    // ===== USER DETAILS =====
    
    function viewUserDetails(userId) {
        const body = document.getElementById('userDetailsBody');
        body.innerHTML = `<div class="loading"><i class="fas fa-spinner fa-spin"></i><span>${window.jsTranslations['Loading user details...'] || 'Loading user details...'}</span></div>`;
        
        openModal(userDetailsModal);
        
        // Load both user details and permissions
        Promise.all([
            fetch(`/user-management/api/users/${userId}/`),
            fetch(`/user-management/api/users/${userId}/permissions/`)
        ])
        .then(responses => {
            // Check if responses are ok
            if (!responses[0].ok) {
                throw new Error(`User details API failed: ${responses[0].status}`);
            }
            if (!responses[1].ok) {
                throw new Error(`Permissions API failed: ${responses[1].status}`);
            }
            return Promise.all(responses.map(r => r.json()));
        })
        .then(([userData, permissionsData]) => {
            if (userData.success && permissionsData.success) {
                displayUserDetails(userData.user, permissionsData.permissions);
            } else {
                body.innerHTML = `<div class="alert alert-danger">${window.jsTranslations['Error'] || 'Error'}: ${userData.error || permissionsData.error || 'Unknown error'}</div>`;
            }
        })
        .catch(error => {
            console.error('Error loading user details:', error);
            body.innerHTML = `<div class="alert alert-danger">${window.jsTranslations['Error loading data'] || 'Error loading data'}: ${error.message}</div>`;
        });
    }
    
    function getSystemPermissions(systemPermissions) {
        if (!systemPermissions) return '';
        
        const grantedPermissions = [];
        
        if (systemPermissions.is_root) {
            grantedPermissions.push(`
                <div class="user-details-permission-item granted">
                    <i class="fas fa-check"></i>
                    <span>Root Access</span>
                </div>
            `);
        }
        
        if (systemPermissions.can_modify_system) {
            grantedPermissions.push(`
                <div class="user-details-permission-item granted">
                    <i class="fas fa-check"></i>
                    <span>System Modification</span>
                </div>
            `);
        }
        
        if (systemPermissions.can_install_packages) {
            grantedPermissions.push(`
                <div class="user-details-permission-item granted">
                    <i class="fas fa-check"></i>
                    <span>Package Installation</span>
                </div>
            `);
        }
        
        if (systemPermissions.can_modify_services) {
            grantedPermissions.push(`
                <div class="user-details-permission-item granted">
                    <i class="fas fa-check"></i>
                    <span>Service Management</span>
                </div>
            `);
        }
        
        if (systemPermissions.can_access_logs) {
            grantedPermissions.push(`
                <div class="user-details-permission-item granted">
                    <i class="fas fa-check"></i>
                    <span>Log Access</span>
                </div>
            `);
        }
        
        return grantedPermissions.join('');
    }
    
    function getNetworkPermissions(networkPermissions) {
        if (!networkPermissions) return '';
        
        const grantedPermissions = [];
        
        if (networkPermissions.can_bind_ports) {
            grantedPermissions.push(`
                <div class="user-details-permission-item granted">
                    <i class="fas fa-check"></i>
                    <span>Port Binding</span>
                </div>
            `);
        }
        
        if (networkPermissions.can_use_raw_sockets) {
            grantedPermissions.push(`
                <div class="user-details-permission-item granted">
                    <i class="fas fa-check"></i>
                    <span>Raw Sockets</span>
                </div>
            `);
        }
        
        if (networkPermissions.can_use_privileged_ports) {
            grantedPermissions.push(`
                <div class="user-details-permission-item granted">
                    <i class="fas fa-check"></i>
                    <span>Privileged Ports</span>
                </div>
            `);
        }
        
        return grantedPermissions.join('');
    }

    function displayUserDetails(user, permissions = null) {
        const body = document.getElementById('userDetailsBody');
        
        const lastLogin = user.last_login ? new Date(user.last_login).toLocaleDateString('en-US', {
            month: 'long',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }) : 'Never';
        
        body.innerHTML = `
            <div class="user-details-container">
                <!-- Basic Information -->
                <div class="user-details-info-section">
                    <h4 class="user-details-info-section-title">
                        <i class="fas fa-info-circle"></i>
                        Basic Information
                    </h4>
                    <div class="user-details-info-grid">
                        <div class="user-details-info-item">
                            <span class="user-details-info-label">Username</span>
                            <span class="user-details-info-value">${user.username}</span>
                        </div>
                        <div class="user-details-info-item">
                            <span class="user-details-info-label">UID</span>
                            <span class="user-details-info-value">${user.uid}</span>
                        </div>
                        <div class="user-details-info-item">
                            <span class="user-details-info-label">GID</span>
                            <span class="user-details-info-value">${user.gid}</span>
                        </div>
                        <div class="user-details-info-item">
                            <span class="user-details-info-label">Group</span>
                            <span class="user-details-info-value">${user.group_name}</span>
                        </div>
                        <div class="user-details-info-item">
                            <span class="user-details-info-label">Home Directory</span>
                            <span class="user-details-info-value">${user.home_directory}</span>
                        </div>
                        <div class="user-details-info-item">
                            <span class="user-details-info-label">Shell</span>
                            <span class="user-details-info-value">${user.shell}</span>
                        </div>
                        <div class="user-details-info-item">
                            <span class="user-details-info-label">Type</span>
                            <span class="user-details-info-value">
                                <span class="user-details-badge user-details-badge-${user.is_system_user ? 'system' : 'user'}">
                                    ${user.is_system_user ? 'System User' : 'Real User'}
                                </span>
                            </span>
                        </div>
                        <div class="user-details-info-item">
                            <span class="user-details-info-label">Status</span>
                            <span class="user-details-info-value">
                                <span class="user-details-badge user-details-badge-${user.is_active ? 'active' : 'inactive'}">
                                    ${user.is_active ? 'Active' : 'Inactive'}
                                </span>
                            </span>
                        </div>
                        <div class="user-details-info-item">
                            <span class="user-details-info-label">Last Login</span>
                            <span class="user-details-info-value">${lastLogin}</span>
                        </div>
                    </div>
                </div>
                
                ${permissions ? `
                <!-- User Permissions & Groups -->
                <div class="user-details-permissions-section">
                    <h4 class="user-details-info-section-title">
                        <i class="fas fa-shield-alt"></i>
                        Permissions & Groups
                    </h4>
                    
                    <!-- Groups -->
                    ${permissions.groups && permissions.groups.length > 0 ? `
                    <div class="user-details-permissions-subsection">
                        <h5 class="user-details-permissions-subtitle">
                            <i class="fas fa-users"></i>
                            Group Memberships
                        </h5>
                        <div class="user-details-groups-container">
                            ${permissions.groups.map(group => `
                                <div class="user-details-group-badge ${group.is_primary ? 'primary' : ''}">
                                    <i class="fas fa-users"></i>
                                    <span class="user-details-group-name">${group.name}</span>
                                    <span class="user-details-group-gid">GID: ${group.gid}</span>
                                    ${group.is_primary ? '<span class="user-details-primary-indicator">Primary</span>' : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}
                    
                    <!-- Sudo Access -->
                    ${permissions.sudo_access ? `
                    <div class="user-details-permissions-subsection">
                        <h5 class="user-details-permissions-subtitle">
                            <i class="fas fa-crown"></i>
                            Sudo Access
                        </h5>
                        <div class="user-details-sudo-info">
                            <div class="user-details-sudo-status">
                                <i class="fas fa-check-circle"></i>
                                <span>Has sudo privileges</span>
                            </div>
                            ${permissions.sudo_commands && permissions.sudo_commands.length > 0 ? `
                            <div class="user-details-sudo-commands">
                                <strong>Allowed Commands:</strong>
                                <ul>
                                    ${permissions.sudo_commands.map(cmd => `<li><code>${cmd}</code></li>`).join('')}
                                </ul>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                    ` : ''}
                    
                    <!-- Special Permissions -->
                    ${permissions.special_permissions && permissions.special_permissions.length > 0 ? `
                    <div class="user-details-permissions-subsection">
                        <h5 class="user-details-permissions-subtitle">
                            <i class="fas fa-star"></i>
                            Special Permissions
                        </h5>
                        <div class="user-details-special-permissions-container">
                            ${permissions.special_permissions.map(perm => `
                                <div class="user-details-special-permission-badge ${perm.type}">
                                    <i class="fas fa-${getPermissionIcon(perm)}"></i>
                                    <div class="user-details-permission-content">
                                        <span class="user-details-permission-name">${perm.group || perm.permission}</span>
                                        <span class="user-details-permission-description">${perm.description}</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}
                    
                    <!-- System Permissions (Only show granted ones) -->
                    ${getSystemPermissions(permissions.system_permissions) ? `
                    <div class="user-details-permissions-subsection">
                        <h5 class="user-details-permissions-subtitle">
                            <i class="fas fa-cogs"></i>
                            System Permissions
                        </h5>
                        <div class="user-details-system-permissions-grid">
                            ${getSystemPermissions(permissions.system_permissions)}
                        </div>
                    </div>
                    ` : ''}
                    
                    <!-- Network Permissions (Only show granted ones) -->
                    ${getNetworkPermissions(permissions.network_permissions) ? `
                    <div class="user-details-permissions-subsection">
                        <h5 class="user-details-permissions-subtitle">
                            <i class="fas fa-network-wired"></i>
                            Network Permissions
                        </h5>
                        <div class="user-details-network-permissions-grid">
                            ${getNetworkPermissions(permissions.network_permissions)}
                        </div>
                    </div>
                    ` : ''}
                </div>
                ` : ''}
                
                <!-- Recent Activities -->
                ${user.activities && user.activities.length > 0 ? `
                <div class="user-details-info-section">
                    <h4 class="user-details-info-section-title">
                        <i class="fas fa-history"></i>
                        Recent Activities
                    </h4>
                    <div class="user-details-activities-table-wrapper">
                        <table class="user-details-activities-table">
                            <thead>
                                <tr>
                                    <th>Type</th>
                                    <th>Description</th>
                                    <th>IP Address</th>
                                    <th>Timestamp</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${user.activities.map(activity => `
                                    <tr>
                                        <td><span class="user-details-badge-activity">${activity.activity_type}</span></td>
                                        <td>${activity.description}</td>
                                        <td>${activity.ip_address || 'N/A'}</td>
                                        <td>${new Date(activity.timestamp).toLocaleString()}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
                ` : ''}
                
                <!-- Active Sessions -->
                ${user.sessions && user.sessions.length > 0 ? `
                <div class="user-details-info-section">
                    <h4 class="user-details-info-section-title">
                        <i class="fas fa-desktop"></i>
                        Active Sessions
                    </h4>
                    <div class="user-details-sessions-table-wrapper">
                        <table class="user-details-sessions-table">
                            <thead>
                                <tr>
                                    <th>Session ID</th>
                                    <th>IP Address</th>
                                    <th>Login Time</th>
                                    <th>Last Activity</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${user.sessions.map(session => `
                                    <tr>
                                        <td><code>${session.session_id}</code></td>
                                        <td>${session.ip_address}</td>
                                        <td>${new Date(session.login_time).toLocaleString()}</td>
                                        <td>${new Date(session.last_activity).toLocaleString()}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }
    
    function getPermissionIcon(permission) {
        const iconMap = {
            'group_membership': 'users',
            'privilege': 'crown',
            'capability': 'star',
            'root_access': 'crown',
            'setuid_programs': 'shield-alt'
        };
        return iconMap[permission.type] || 'shield-alt';
    }
    
    
    // ===== UTILITY FUNCTIONS =====
    
    function getTimeAgo(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return `${days}d ago`;
    }
    
    function getActivityIcon(activityType) {
        const icons = {
            'login': 'sign-in-alt',
            'logout': 'sign-out-alt',
            'status_change': 'toggle-on',
            'command': 'terminal',
            'file_access': 'file',
            'system': 'cog'
        };
        return icons[activityType] || 'circle';
    }
    
    // ===== NOTIFICATIONS =====
    
    function showNotification(message, type = 'info') {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        const notification = document.createElement('div');
        notification.className = `alert ${alertClass}`;
        notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);';
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <div>
                    <strong>${message}</strong>
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.transition = 'opacity 0.3s ease';
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    // Expose as global function
    window.showNotification = showNotification;
    
    // ===== EVENT LISTENERS =====
    
    function attachEventListeners() {
        // Detail view buttons
        document.querySelectorAll('.btn-view-details').forEach(button => {
            button.addEventListener('click', function() {
                const userId = this.dataset.userId;
                viewUserDetails(userId);
            });
        });
        
        // Toggle status buttons
    }
    
    // Attach event listeners on initial load
    attachEventListeners();
    
    // ===== CREATE USER BUTTON =====
    
    const createUserBtn = document.getElementById('createUserBtn');
    if (createUserBtn) {
        createUserBtn.addEventListener('click', function() {
            if (window.openCreateUserModal) {
                window.openCreateUserModal();
            }
        });
    }

    // ===== DELETE USER BUTTONS =====
    document.addEventListener('click', function(e) {
        if (e.target.closest('.btn-delete-user')) {
            const button = e.target.closest('.btn-delete-user');
            const username = button.getAttribute('data-username');
            openDeleteUserModal(username);
        }
    });

    // ===== DELETE USER MODAL FUNCTIONS =====
    function openDeleteUserModal(username) {
        const modal = document.getElementById('deleteUserModal');
        const usernameElement = document.getElementById('deleteUsername');
        const userInfoElement = document.getElementById('deleteUserInfo');
        
        if (modal && usernameElement && userInfoElement) {
            usernameElement.textContent = username;
            userInfoElement.textContent = username;
            
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    function closeDeleteUserModal() {
        const modal = document.getElementById('deleteUserModal');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    // Delete user confirmation
    function confirmDeleteUser() {
        const modal = document.getElementById('deleteUserModal');
        const usernameElement = document.getElementById('deleteUsername');
        const confirmBtn = document.getElementById('confirmDeleteUser');
        
        if (!modal || !usernameElement || !confirmBtn) return;
        
        const username = usernameElement.textContent;
        
        // Set loading state
        confirmBtn.disabled = true;
        const originalBtnHtml = confirmBtn.innerHTML;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
        
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Make API call
        fetch(`/user-management/api/delete-user/${username}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success');
                closeDeleteUserModal();
                // Refresh the page to update user list
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showNotification(data.error || 'Failed to delete user', 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting user:', error);
            showNotification(`An unexpected error occurred: ${error.message}`, 'error');
        })
        .finally(() => {
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = originalBtnHtml;
        });
    }

    // Attach delete modal event listeners
    const cancelDeleteBtn = document.getElementById('cancelDeleteUser');
    const confirmDeleteBtn = document.getElementById('confirmDeleteUser');
    
    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', closeDeleteUserModal);
    }
    
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', confirmDeleteUser);
    }

    // Close modal when clicking outside
    const deleteModal = document.getElementById('deleteUserModal');
    if (deleteModal) {
        deleteModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeDeleteUserModal();
            }
        });
    }

    // Close modal with ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && deleteModal && deleteModal.classList.contains('active')) {
            closeDeleteUserModal();
        }
    });
    
    // ===== CREATE USER FUNCTIONALITY =====
    
    
    // Password confirmation validation (if element exists)
    const confirmPasswordElement = document.getElementById('confirm_password');
    if (confirmPasswordElement) {
        confirmPasswordElement.addEventListener('input', function() {
            validatePasswordConfirmation();
        });
    }
    
    // Username validation
    const usernameElement = document.getElementById('username');
    if (usernameElement) {
        usernameElement.addEventListener('input', function() {
            validateUsername();
        });
    }
    
    
    function validateUsername() {
        const usernameInput = document.getElementById('username');
        const username = usernameInput.value.trim();
        
        // Remove existing validation classes
        usernameInput.classList.remove('error', 'success');
        
        if (username.length < 2) {
            usernameInput.classList.add('error');
            return false;
        }
        
        if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
            usernameInput.classList.add('error');
            return false;
        }
        
        usernameInput.classList.add('success');
        return true;
    }
    
    function validatePasswordConfirmation() {
        // Password confirmation validation is no longer needed
        // since we removed the confirm_password field
        return true;
    }
    
    
    // ===== INITIAL DATA LOADING =====
    
    // Use initial data on page load (if available)
    if (window.INITIAL_USERS && window.INITIAL_USERS.length > 0) {
        console.log('⚡ Using initial data, rendering page instantly!');
        updateUsersTable(window.INITIAL_USERS);
    }
    
    // Load additional data
    loadStats();
    
});
