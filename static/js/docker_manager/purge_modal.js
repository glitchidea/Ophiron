// Purge Modal JavaScript - Ophiron Tema

let purgeInProgress = false;
let purgeCancelRequested = false;

// Show Purge Modal
function showPurgeModal() {
    const modal = document.getElementById('purgeModal');
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Reset form
        resetPurgeForm();
        
        // Focus on confirmation input
        setTimeout(() => {
            const confirmationInput = document.getElementById('purgeConfirmation');
            if (confirmationInput) {
                confirmationInput.focus();
            }
        }, 300);
    }
}

// Close Purge Modal
function closePurgeModal() {
    const modal = document.getElementById('purgeModal');
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

// Reset Purge Form
function resetPurgeForm() {
    // Reset checkboxes
    const checkboxes = document.querySelectorAll('#purgeModal input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
    });
    
    // Reset confirmation input
    const confirmationInput = document.getElementById('purgeConfirmation');
    if (confirmationInput) {
        confirmationInput.value = '';
    }
    
    // Hide estimated cleanup
    const estimatedCleanup = document.getElementById('estimatedCleanup');
    if (estimatedCleanup) {
        estimatedCleanup.style.display = 'none';
    }
    
    // Reset execute button
    const executeBtn = document.getElementById('executeBtn');
    if (executeBtn) {
        executeBtn.disabled = true;
    }
    
    // Reset progress
    purgeInProgress = false;
    purgeCancelRequested = false;
}

// Validate Confirmation Input
function validateConfirmation() {
    const confirmationInput = document.getElementById('purgeConfirmation');
    const executeBtn = document.getElementById('executeBtn');
    
    if (confirmationInput && executeBtn) {
        const isValid = confirmationInput.value.toUpperCase() === 'PURGE';
        executeBtn.disabled = !isValid;
        
        if (isValid) {
            confirmationInput.style.borderColor = '#10b981';
        } else {
            confirmationInput.style.borderColor = '#ef4444';
        }
    }
}

// Estimate Cleanup
async function estimateCleanup() {
    const estimateBtn = document.getElementById('estimateBtn');
    const estimatedCleanup = document.getElementById('estimatedCleanup');
    
    if (estimateBtn && estimatedCleanup) {
        estimateBtn.disabled = true;
        estimateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Estimating...';
        
        try {
            // Get selected options
            const options = getSelectedPurgeOptions();
            
            // Make API call to estimate cleanup
            const response = await fetch('/docker-manager/api/estimate-cleanup/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify(options)
            });
            
            if (response.ok) {
                const data = await response.json();
                updateCleanupStats(data);
                estimatedCleanup.style.display = 'block';
            } else {
                showNotification('Failed to estimate cleanup', 'error');
            }
        } catch (error) {
            console.error('Error estimating cleanup:', error);
            showNotification('Error estimating cleanup', 'error');
        } finally {
            estimateBtn.disabled = false;
            estimateBtn.innerHTML = '<i class="fas fa-calculator"></i> Estimate Cleanup';
        }
    }
}

// Get Selected Purge Options
function getSelectedPurgeOptions() {
    return {
        images: document.getElementById('purgeImages').checked,
        volumes: document.getElementById('purgeVolumes').checked
    };
}

// Update Cleanup Stats
function updateCleanupStats(data) {
    const elements = {
        images: document.getElementById('cleanupImages'),
        volumes: document.getElementById('cleanupVolumes')
    };
    
    Object.keys(elements).forEach(key => {
        if (elements[key] && data[key] !== undefined) {
            elements[key].textContent = data[key];
        }
    });
}

// Execute Purge
async function executePurge() {
    if (purgeInProgress) return;
    
    const confirmationInput = document.getElementById('purgeConfirmation');
    if (!confirmationInput || confirmationInput.value.toUpperCase() !== 'PURGE') {
        showNotification('Please type PURGE to confirm', 'warning');
        return;
    }
    
    purgeInProgress = true;
    purgeCancelRequested = false;
    
    // Close purge modal and show progress modal
    closePurgeModal();
    showPurgeProgressModal();
    
    try {
        const options = getSelectedPurgeOptions();
        
        // Start purge process
        const response = await fetch('/docker-manager/api/purge-system/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(options)
        });
        
        if (response.ok) {
            // Handle streaming response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            while (true) {
                if (purgeCancelRequested) {
                    reader.cancel();
                    break;
                }
                
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const data = JSON.parse(line);
                            updatePurgeProgress(data);
                        } catch (e) {
                            // Handle non-JSON lines
                            addPurgeLog(line);
                        }
                    }
                }
            }
            
            if (!purgeCancelRequested) {
                showNotification('System purge completed successfully', 'success');
                closePurgeProgressModal();
                // Refresh the page to show updated data
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } else {
            throw new Error('Failed to execute purge');
        }
    } catch (error) {
        console.error('Error executing purge:', error);
        showNotification('Error executing purge: ' + error.message, 'error');
        closePurgeProgressModal();
    } finally {
        purgeInProgress = false;
    }
}

// Show Purge Progress Modal
function showPurgeProgressModal() {
    const modal = document.getElementById('purgeProgressModal');
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Reset progress
        const progressFill = document.getElementById('purgeProgress');
        const progressText = document.getElementById('purgeProgressText');
        const purgeLogs = document.getElementById('purgeLogs');
        
        if (progressFill) progressFill.style.width = '0%';
        if (progressText) progressText.textContent = 'Preparing purge...';
        if (purgeLogs) purgeLogs.innerHTML = '<div class="log-line">Starting purge process...</div>';
    }
}

// Close Purge Progress Modal
function closePurgeProgressModal() {
    const modal = document.getElementById('purgeProgressModal');
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

// Update Purge Progress
function updatePurgeProgress(data) {
    const progressFill = document.getElementById('purgeProgress');
    const progressText = document.getElementById('purgeProgressText');
    
    if (data.progress !== undefined && progressFill) {
        progressFill.style.width = data.progress + '%';
    }
    
    if (data.message && progressText) {
        progressText.textContent = data.message;
    }
    
    if (data.log) {
        addPurgeLog(data.log);
    }
}

// Add Purge Log
function addPurgeLog(message) {
    const purgeLogs = document.getElementById('purgeLogs');
    if (purgeLogs) {
        const logLine = document.createElement('div');
        logLine.className = 'log-line';
        logLine.textContent = message;
        purgeLogs.appendChild(logLine);
        purgeLogs.scrollTop = purgeLogs.scrollHeight;
    }
}

// Cancel Purge
function cancelPurge() {
    if (purgeInProgress) {
        purgeCancelRequested = true;
        addPurgeLog('Cancelling purge...');
    }
}

// Get CSRF Token
function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

// Show Notification
function showNotification(message, type = 'info') {
    // This should be implemented based on your notification system
    console.log(`${type.toUpperCase()}: ${message}`);
    
    // Simple alert for now - replace with your notification system
    if (type === 'error') {
        alert('Error: ' + message);
    } else if (type === 'warning') {
        alert('Warning: ' + message);
    } else if (type === 'success') {
        alert('Success: ' + message);
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Confirmation input validation
    const confirmationInput = document.getElementById('purgeConfirmation');
    if (confirmationInput) {
        confirmationInput.addEventListener('input', validateConfirmation);
    }
    
    // Close modal on outside click
    const purgeModal = document.getElementById('purgeModal');
    const purgeProgressModal = document.getElementById('purgeProgressModal');
    
    if (purgeModal) {
        purgeModal.addEventListener('click', function(e) {
            if (e.target === purgeModal) {
                closePurgeModal();
            }
        });
    }
    
    if (purgeProgressModal) {
        purgeProgressModal.addEventListener('click', function(e) {
            if (e.target === purgeProgressModal) {
                // Don't close progress modal on outside click
            }
        });
    }
    
    // ESC key to close modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (purgeInProgress) {
                // Don't close progress modal with ESC
                return;
            }
            
            const purgeModal = document.getElementById('purgeModal');
            if (purgeModal && purgeModal.classList.contains('show')) {
                closePurgeModal();
            }
        }
    });
});
