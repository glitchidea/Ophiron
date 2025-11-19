// Docker Manager - Modal JavaScript dosyası

// Global variables for modal state
let currentContainerId = null;
let currentContainerName = null;

// Wait for window.jsTranslations to be available
function waitForTranslations(callback) {
    if (window.jsTranslations && Object.keys(window.jsTranslations).length > 0) {
        callback();
    } else {
        setTimeout(() => waitForTranslations(callback), 50);
    }
}

// Modal translation function
function applyModalTranslations(modalType) {
    const translations = {
        start: {
            title: 'Start Container',
            message: 'Are you sure you want to start this container?',
            containerIdLabel: 'Container ID:',
            containerNameLabel: 'Container Name:',
            cancelBtn: 'Cancel',
            confirmBtn: 'Start Container'
        },
        stop: {
            title: 'Stop Container',
            message: 'Are you sure you want to stop this container?',
            containerIdLabel: 'Container ID:',
            containerNameLabel: 'Container Name:',
            cancelBtn: 'Cancel',
            confirmBtn: 'Stop Container'
        },
        restart: {
            title: 'Restart Container',
            message: 'Are you sure you want to restart this container?',
            containerIdLabel: 'Container ID:',
            containerNameLabel: 'Container Name:',
            cancelBtn: 'Cancel',
            confirmBtn: 'Restart Container'
        },
        delete: {
            title: 'Delete Container',
            message: 'Are you sure you want to delete this container? This action cannot be undone.',
            containerIdLabel: 'Container ID:',
            containerNameLabel: 'Container Name:',
            warningText: 'This will permanently remove the container and all its data.',
            cancelBtn: 'Cancel',
            confirmBtn: 'Delete Container'
        }
    };
    
    const t = translations[modalType];
    if (!t) return;
    
    // Apply translations using window.jsTranslations
    const setText = (id, key) => {
        const element = document.getElementById(id);
        if (element && window.jsTranslations) {
            element.textContent = window.jsTranslations[key] || key;
        } else if (element) {
            element.textContent = key;
        }
    };
    
    setText(`${modalType}ModalTitle`, t.title);
    setText(`${modalType}ModalMessage`, t.message);
    setText(`${modalType}ContainerIdLabel`, t.containerIdLabel);
    setText(`${modalType}ContainerNameLabel`, t.containerNameLabel);
    setText(`${modalType}CancelBtn`, t.cancelBtn);
    setText(`${modalType}ConfirmBtn`, t.confirmBtn);
    
    if (modalType === 'delete') {
        setText('deleteWarningText', t.warningText);
    }
}

// Modal functions
function showStartModal(containerId, containerName) {
    currentContainerId = containerId;
    currentContainerName = containerName;
    
    // Apply translations
    waitForTranslations(() => applyModalTranslations('start'));
    
    document.getElementById('startContainerId').textContent = containerId;
    document.getElementById('startContainerName').textContent = containerName;
    
    const modal = document.getElementById('startModal');
    modal.style.display = 'flex';
    modal.classList.add('show');
}

function closeStartModal() {
    const modal = document.getElementById('startModal');
    modal.style.display = 'none';
    modal.classList.remove('show');
    currentContainerId = null;
    currentContainerName = null;
}

function confirmStartContainer() {
    if (!currentContainerId) {
        const selected = document.querySelector('.container-checkbox:checked');
        if (selected && selected.dataset && selected.dataset.containerId) {
            currentContainerId = selected.dataset.containerId;
        }
    }
    if (!currentContainerId) return;
    const containerIdToStart = currentContainerId;
    closeStartModal();
    startContainer(containerIdToStart);
}

function showStopModal(containerId, containerName) {
    currentContainerId = containerId;
    currentContainerName = containerName;
    
    // Apply translations
    waitForTranslations(() => applyModalTranslations('stop'));
    
    document.getElementById('stopContainerId').textContent = containerId;
    document.getElementById('stopContainerName').textContent = containerName;
    
    const modal = document.getElementById('stopModal');
    modal.style.display = 'flex';
    modal.classList.add('show');
}

function closeStopModal() {
    const modal = document.getElementById('stopModal');
    modal.style.display = 'none';
    modal.classList.remove('show');
    currentContainerId = null;
    currentContainerName = null;
}

function confirmStopContainer() {
    if (!currentContainerId) {
        const selected = document.querySelector('.container-checkbox:checked');
        if (selected && selected.dataset && selected.dataset.containerId) {
            currentContainerId = selected.dataset.containerId;
        }
    }
    if (!currentContainerId) return;
    const containerIdToStop = currentContainerId;
    closeStopModal();
    stopContainer(containerIdToStop);
}

function showRestartModal(containerId, containerName) {
    currentContainerId = containerId;
    currentContainerName = containerName;
    
    // Apply translations
    waitForTranslations(() => applyModalTranslations('restart'));
    
    document.getElementById('restartContainerId').textContent = containerId;
    document.getElementById('restartContainerName').textContent = containerName;
    
    const modal = document.getElementById('restartModal');
    modal.style.display = 'flex';
    modal.classList.add('show');
}

function closeRestartModal() {
    const modal = document.getElementById('restartModal');
    modal.style.display = 'none';
    modal.classList.remove('show');
    currentContainerId = null;
    currentContainerName = null;
}

function confirmRestartContainer() {
    if (!currentContainerId) {
        const selected = document.querySelector('.container-checkbox:checked');
        if (selected && selected.dataset && selected.dataset.containerId) {
            currentContainerId = selected.dataset.containerId;
        }
    }
    if (!currentContainerId) return;
    const containerIdToRestart = currentContainerId;
    closeRestartModal();
    restartContainer(containerIdToRestart);
}

function showDeleteModal(containerId, containerName) {
    currentContainerId = containerId;
    currentContainerName = containerName;
    
    // Apply translations
    waitForTranslations(() => applyModalTranslations('delete'));
    
    document.getElementById('deleteContainerId').textContent = containerId;
    document.getElementById('deleteContainerName').textContent = containerName;
    
    const modal = document.getElementById('deleteModal');
    modal.style.display = 'flex';
    modal.classList.add('show');
}

function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    modal.style.display = 'none';
    modal.classList.remove('show');
    currentContainerId = null;
    currentContainerName = null;
}

function confirmDeleteContainer() {
    if (!currentContainerId) {
        const selected = document.querySelector('.container-checkbox:checked');
        if (selected && selected.dataset && selected.dataset.containerId) {
            currentContainerId = selected.dataset.containerId;
        }
    }
    if (!currentContainerId) return;
    const containerIdToDelete = currentContainerId;
    closeDeleteModal();
    deleteContainer(containerIdToDelete);
}

// Make all modal functions globally available
window.showStartModal = showStartModal;
window.closeStartModal = closeStartModal;
window.confirmStartContainer = confirmStartContainer;
window.showStopModal = showStopModal;
window.closeStopModal = closeStopModal;
window.confirmStopContainer = confirmStopContainer;
window.showRestartModal = showRestartModal;
window.closeRestartModal = closeRestartModal;
window.confirmRestartContainer = confirmRestartContainer;
window.showDeleteModal = showDeleteModal;
window.closeDeleteModal = closeDeleteModal;
window.confirmDeleteContainer = confirmDeleteContainer;

// Close modals when clicking outside
window.onclick = function(event) {
    const startModal = document.getElementById('startModal');
    const stopModal = document.getElementById('stopModal');
    const restartModal = document.getElementById('restartModal');
    const deleteModal = document.getElementById('deleteModal');
    
    if (event.target === startModal) {
        closeStartModal();
    } else if (event.target === stopModal) {
        closeStopModal();
    } else if (event.target === restartModal) {
        closeRestartModal();
    } else if (event.target === deleteModal) {
        closeDeleteModal();
    }
}

// Close modals with ESC key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const startModal = document.getElementById('startModal');
        const stopModal = document.getElementById('stopModal');
        const restartModal = document.getElementById('restartModal');
        const deleteModal = document.getElementById('deleteModal');
        
        if (startModal && startModal.style.display === 'flex') {
            closeStartModal();
        } else if (stopModal && stopModal.style.display === 'flex') {
            closeStopModal();
        } else if (restartModal && restartModal.style.display === 'flex') {
            closeRestartModal();
        } else if (deleteModal && deleteModal.style.display === 'flex') {
            closeDeleteModal();
        }
    }
});
