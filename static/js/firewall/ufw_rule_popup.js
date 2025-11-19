document.addEventListener('DOMContentLoaded', function() {
    // ===== GLOBAL VARIABLES =====
    let ruleToDelete = null;

    // ===== INITIALIZATION =====
    function initialize() {
        setupEventListeners();
        setupFormValidation();
    }

    // ===== MODAL MANAGEMENT =====
    function openRuleModal() {
        const modal = document.getElementById('ufwRuleModal');
        modal.classList.add('show');
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // Reset form
        document.getElementById('ufwRuleForm').reset();
        updateRulePreview();
    }

    function closeRuleModal() {
        const modal = document.getElementById('ufwRuleModal');
        modal.classList.remove('show');
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }

    function openDeleteModal(ruleNumber) {
        const modal = document.getElementById('deleteRuleModal');
        const rule = getRuleByNumber(ruleNumber);
        
        if (rule) {
            ruleToDelete = ruleNumber;
            document.getElementById('ruleToDelete').textContent = rule.raw_line || `Rule ${ruleNumber}`;
            modal.classList.add('show');
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    }

    function closeDeleteModal() {
        const modal = document.getElementById('deleteRuleModal');
        modal.classList.remove('show');
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        ruleToDelete = null;
    }

    // ===== FORM VALIDATION =====
    function setupFormValidation() {
        const form = document.getElementById('ufwRuleForm');
        const inputs = form.querySelectorAll('input, select');
        
        inputs.forEach(input => {
            input.addEventListener('input', validateField);
            input.addEventListener('change', validateField);
        });
        
        // Real-time preview update
        inputs.forEach(input => {
            input.addEventListener('input', updateRulePreview);
            input.addEventListener('change', updateRulePreview);
        });
    }

    function validateField(event) {
        const field = event.target;
        const value = field.value.trim();
        
        // Remove existing validation classes
        field.classList.remove('valid', 'invalid');
        
        // Validate based on field type
        if (field.name === 'source_ip' || field.name === 'dest_ip') {
            if (value && value !== 'any') {
                if (isValidIP(value) || isValidCIDR(value)) {
                    field.classList.add('valid');
                } else {
                    field.classList.add('invalid');
                }
            } else if (value === 'any' || value === '') {
                field.classList.add('valid');
            }
        } else if (field.name === 'ports') {
            if (value && isValidPortInput(value)) {
                field.classList.add('valid');
            } else if (value === '') {
                field.classList.add('valid');
            } else {
                field.classList.add('invalid');
            }
        } else {
            field.classList.add('valid');
        }
    }

    function isValidIP(ip) {
        const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        return ipRegex.test(ip);
    }

    function isValidCIDR(cidr) {
        const cidrRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(?:[0-9]|[1-2][0-9]|3[0-2])$/;
        return cidrRegex.test(cidr);
    }

    function isValidPortInput(ports) {
        if (!ports) return true;
        
        const portRegex = /^(\d+(?:,\d+)*(?::\d+)*|\d+:\d+)$/;
        return portRegex.test(ports.replace(/\s/g, ''));
    }

    // ===== RULE PREVIEW =====
    function updateRulePreview() {
        const preview = document.getElementById('rulePreview');
        const form = document.getElementById('ufwRuleForm');
        const formData = new FormData(form);
        
        const action = formData.get('action') || 'allow';
        const direction = formData.get('direction') || 'in';
        const protocol = formData.get('protocol') || 'tcp';
        const sourceIp = formData.get('source_ip') || '';
        const destIp = formData.get('dest_ip') || '';
        const ports = formData.get('ports') || '';
        const comment = formData.get('comment') || '';
        
        let previewText = `sudo ufw ${action}`;
        
        // Add direction if specified and not 'any'
        if (direction && direction !== 'any') {
            previewText += ` ${direction}`;
        }
        
        // Add protocol if specified and not 'any'
        if (protocol && protocol !== 'any') {
            previewText += ` proto ${protocol}`;
        }
        
        // Add source IP if specified
        if (sourceIp && sourceIp !== 'any') {
            previewText += ` from ${sourceIp}`;
        }
        
        // Add destination IP if specified
        if (destIp && destIp !== 'any') {
            previewText += ` to ${destIp}`;
        }
        
        // Add ports if specified
        if (ports) {
            previewText += ` port ${ports}`;
            if (protocol && protocol !== 'any') {
                previewText += `/${protocol}`;
            }
        }
        
        // Add comment if specified
        if (comment) {
            previewText += ` comment "${comment}"`;
        }
        
        preview.innerHTML = `
            <div class="preview-content">
                <i class="fas fa-terminal"></i>
                <span>${previewText}</span>
            </div>
        `;
        
        preview.classList.add('has-content');
    }

    // ===== RULE CREATION =====
    async function createRule() {
        const form = document.getElementById('ufwRuleForm');
        const formData = new FormData(form);
        
        // Validate form
        if (!validateForm(form)) {
            showError('Lütfen form hatalarını düzeltin');
            return;
        }
        
        const ruleData = {
            action: formData.get('action'),
            direction: formData.get('direction'),
            protocol: formData.get('protocol'),
            source_ip: formData.get('source_ip') || 'any',
            dest_ip: formData.get('dest_ip') || 'any',
            ports: formData.get('ports') || '',
            comment: formData.get('comment') || ''
        };
        
        try {
            showLoading();
            
            const response = await fetch('/firewall/api/ufw/create-rule/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(ruleData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                showSuccess(data.message);
                closeRuleModal();
                // Refresh the main UFW page
                if (typeof loadUfwRules === 'function') {
                    loadUfwRules();
                }
            } else {
                // Show detailed error message
                let errorMessage = data.message || 'Kural oluşturulamadı';
                
                // If there are detailed errors, show them
                if (data.details && Array.isArray(data.details)) {
                    errorMessage += '\n\nDetaylar:\n' + data.details.join('\n');
                }
                
                showDetailedError(errorMessage);
            }
        } catch (error) {
            console.error('Error creating rule:', error);
            showError('Bağlantı hatası: Kural oluşturulamadı');
        }
    }

    function validateForm(form) {
        const inputs = form.querySelectorAll('input, select');
        let isValid = true;
        const errors = [];
        
        inputs.forEach(input => {
            const value = input.value.trim();
            
            // Only validate if there's a value
            if (value) {
                // Additional validation for specific fields
                if (input.name === 'source_ip' && value !== 'any') {
                    if (!isValidIP(value) && !isValidCIDR(value)) {
                        input.classList.add('invalid');
                        isValid = false;
                        errors.push('Geçersiz source IP formatı');
                    } else {
                        input.classList.remove('invalid');
                        input.classList.add('valid');
                    }
                } else if (input.name === 'dest_ip' && value !== 'any') {
                    if (!isValidIP(value) && !isValidCIDR(value)) {
                        input.classList.add('invalid');
                        isValid = false;
                        errors.push('Geçersiz destination IP formatı');
                    } else {
                        input.classList.remove('invalid');
                        input.classList.add('valid');
                    }
                } else if (input.name === 'ports' && value) {
                    if (!isValidPortInput(value)) {
                        input.classList.add('invalid');
                        isValid = false;
                        errors.push('Geçersiz port formatı. Örnek: 8080, 8080,8090, 8080:8090');
                    } else {
                        input.classList.remove('invalid');
                        input.classList.add('valid');
                    }
                } else {
                    input.classList.remove('invalid');
                    input.classList.add('valid');
                }
            } else {
                // No value - remove validation classes
                input.classList.remove('invalid', 'valid');
            }
        });
        
        if (!isValid && errors.length > 0) {
            showError('Form hataları:\n' + errors.join('\n'));
        }
        
        return isValid;
    }

    // ===== RULE DELETION =====
    async function deleteRule(ruleNumber) {
        openDeleteModal(ruleNumber);
    }

    async function confirmDelete() {
        if (!ruleToDelete) return;
        
        try {
            showLoading();
            
            const response = await fetch(`/firewall/api/ufw/delete-rule/${ruleToDelete}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                showSuccess(data.message);
                closeDeleteModal();
                // Refresh the main UFW page
                if (typeof loadUfwRules === 'function') {
                    loadUfwRules();
                }
            } else {
                showError(data.error || 'Failed to delete rule');
            }
        } catch (error) {
            console.error('Error deleting rule:', error);
            showError('Error deleting rule');
        }
    }

    // ===== HELPER FUNCTIONS =====
    function getRuleByNumber(ruleNumber) {
        // This would need to be implemented based on how rules are stored
        // For now, return a placeholder
        return {
            number: ruleNumber,
            raw_line: `Rule ${ruleNumber}`
        };
    }

    function showLoading() {
        // Show loading state if needed
        console.log('Loading...');
    }

    // ===== EVENT LISTENERS =====
    function setupEventListeners() {
        // Add rule button
        const addRuleBtn = document.getElementById('addRuleBtn');
        if (addRuleBtn) {
            addRuleBtn.addEventListener('click', openRuleModal);
        }

        // Modal close buttons
        const closeModal = document.getElementById('closeModal');
        if (closeModal) {
            closeModal.addEventListener('click', closeRuleModal);
        }

        const closeDeleteModal = document.getElementById('closeDeleteModal');
        if (closeDeleteModal) {
            closeDeleteModal.addEventListener('click', closeDeleteModal);
        }

        // Cancel buttons
        const cancelRule = document.getElementById('cancelRule');
        if (cancelRule) {
            cancelRule.addEventListener('click', closeRuleModal);
        }

        const cancelDelete = document.getElementById('cancelDelete');
        if (cancelDelete) {
            cancelDelete.addEventListener('click', closeDeleteModal);
        }

        // Form submission
        const createRuleBtn = document.getElementById('createRule');
        if (createRuleBtn) {
            createRuleBtn.addEventListener('click', createRule);
        }

        const confirmDeleteBtn = document.getElementById('confirmDelete');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', confirmDelete);
        }

        // Close modals on outside click
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    if (modal.id === 'ufwRuleModal') {
                        closeRuleModal();
                    } else if (modal.id === 'deleteRuleModal') {
                        closeDeleteModal();
                    }
                }
            });
        });

        // Close modals on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeRuleModal();
                closeDeleteModal();
            }
        });
    }

    // ===== UTILITY FUNCTIONS =====
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    function showSuccess(message) {
        showNotification(message, 'success');
    }

    function showError(message) {
        showNotification(message, 'error');
    }

    function showInfo(message) {
        showNotification(message, 'info');
    }

    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 16px;
            border-radius: 6px;
            z-index: 1001;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            animation: notificationSlideIn 0.3s ease;
        `;
        
        if (type === 'success') {
            notification.style.background = '#d4edda';
            notification.style.color = '#155724';
            notification.style.border = '1px solid #c3e6cb';
        } else if (type === 'error') {
            notification.style.background = '#f8d7da';
            notification.style.color = '#721c24';
            notification.style.border = '1px solid #f5c6cb';
        } else {
            notification.style.background = '#d1ecf1';
            notification.style.color = '#0c5460';
            notification.style.border = '1px solid #bee5eb';
        }
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, type === 'error' ? 5000 : 3000);
    }

    function showDetailedError(message) {
        // Create a modal for detailed error messages
        const modal = document.createElement('div');
        modal.className = 'modal show';
        modal.style.cssText = `
            position: fixed;
            z-index: 1002;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(2px);
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 600px; width: 90%;">
                <div class="modal-header" style="background: #f8d7da; border-bottom: 1px solid #f5c6cb;">
                    <h3 style="color: #721c24; margin: 0; display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-exclamation-triangle"></i>
                        Kural Oluşturulamadı
                    </h3>
                    <button class="modal-close" onclick="this.closest('.modal').remove()" style="background: none; border: none; font-size: 18px; color: #721c24; cursor: pointer; padding: 4px; border-radius: 4px;">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body" style="padding: 24px;">
                    <div style="background: #f8f9fa; border: 1px solid #e5e5e5; border-radius: 6px; padding: 16px; font-family: monospace; white-space: pre-line; color: #333;">
                        ${message}
                    </div>
                    <div style="margin-top: 16px; padding: 12px; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; color: #856404;">
                        <strong>💡 İpucu:</strong> Lütfen form verilerini kontrol edin:
                        <ul style="margin: 8px 0 0 20px;">
                            <li>IP adresleri: 192.168.1.1 veya 192.168.1.0/24 formatında olmalı</li>
                            <li>Portlar: 8080, 8080,8090, 8080:8090 formatında olmalı</li>
                            <li>Gerekli alanları doldurun</li>
                        </ul>
                    </div>
                </div>
                <div class="modal-footer" style="display: flex; justify-content: flex-end; gap: 12px; padding: 20px 24px; border-top: 1px solid #e5e5e5; background: #f8f9fa;">
                    <button onclick="this.closest('.modal').remove()" style="padding: 10px 20px; border: none; border-radius: 6px; background: #6c757d; color: white; cursor: pointer; font-weight: 600;">
                        <i class="fas fa-times"></i> Kapat
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Close on outside click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        // Close on Escape key
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
    }

    // ===== GLOBAL FUNCTIONS (for onclick handlers) =====
    window.deleteRule = deleteRule;

    // ===== INITIALIZE APPLICATION =====
    initialize();
});
