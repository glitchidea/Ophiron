// Docker Manager - Ana JavaScript dosyası


document.addEventListener('DOMContentLoaded', function() {
    initializeDockerManager();
});

function initializeDockerManager() {
    // Event listener'ları ekle
    setupEventListeners();

    // Arama fonksiyonalitesi
    setupSearchFunctionality();

    // Filtre fonksiyonalitesi
    setupFilterFunctionality();
}

// Container tablosu artık Django template ile oluşturuluyor

function setupEventListeners() {
    // Select All checkbox
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const containerCheckboxes = document.querySelectorAll('.container-checkbox');
            containerCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }

    // Individual container checkboxes
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('container-checkbox')) {
            updateSelectAllState();
        }
    });
}

function setupSearchFunctionality() {
    const searchInput = document.getElementById('containerSearch');
    if (!searchInput) return;
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        filterContainers(searchTerm);
    });
}

function setupFilterFunctionality() {
    const runningOnlyCheckbox = document.getElementById('runningOnly');
    if (!runningOnlyCheckbox) return;
    runningOnlyCheckbox.addEventListener('change', function() {
        filterContainers();
    });
}

function filterContainers(searchTerm = '') {
    const runningOnlyEl = document.getElementById('runningOnly');
    const runningOnly = runningOnlyEl ? runningOnlyEl.checked : false;
    const rows = document.querySelectorAll('#containersTableBody tr');
    if (!rows || rows.length === 0) {
        updateItemCount(0);
        return;
    }
    let visibleCount = 0;
    
    rows.forEach(row => {
        const nameCell = row.querySelector('.container-name');
        const imageCell = row.querySelector('.image-col a');
        const statusCell = row.querySelector('[class*="status-"]');
        
        if (!nameCell || !statusCell) return;
        
        const name = nameCell.textContent.toLowerCase();
        const image = imageCell ? imageCell.textContent.toLowerCase() : '';
        const status = statusCell.textContent;
        
        // Arama terimi kontrolü - name ve image'da ara
        const matchesSearch = searchTerm === '' || 
            name.includes(searchTerm) || 
            image.includes(searchTerm);
        
        // Sadece çalışan container'lar filtresi
        const matchesFilter = !runningOnly || status === 'Running';
        
        if (matchesSearch && matchesFilter) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    // Status bar'daki item sayısını güncelle
    updateItemCount(visibleCount);
}

function updateItemCount(count) {
    const itemsCountElement = document.querySelector('.items-count');
    if (itemsCountElement) {
        itemsCountElement.textContent = `${window.jsTranslations['Showing'] || 'Showing'} ${count} ${window.jsTranslations['items'] || 'items'}`;
    }
}

function updateSelectAllState() {
    const containerCheckboxes = document.querySelectorAll('.container-checkbox');
    const checkedBoxes = document.querySelectorAll('.container-checkbox:checked');
    const selectAllCheckbox = document.getElementById('selectAll');
    
    if (checkedBoxes.length === 0) {
        selectAllCheckbox.indeterminate = false;
        selectAllCheckbox.checked = false;
    } else if (checkedBoxes.length === containerCheckboxes.length) {
        selectAllCheckbox.indeterminate = false;
        selectAllCheckbox.checked = true;
    } else {
        selectAllCheckbox.indeterminate = true;
        selectAllCheckbox.checked = false;
    }
}


// Utility functions
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification(window.jsTranslations['Container ID copied to clipboard'] || 'Container ID copied to clipboard');
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}

function stopContainer(containerId) {
    if (!containerId || containerId === 'null' || containerId === 'undefined') {
        console.error('Invalid containerId for stopContainer:', containerId);
        showNotification(`${window.jsTranslations['Hata:'] || 'Hata:'} ${window.jsTranslations['Container ID not found'] || 'Container ID not found'}`);
        return;
    }
    showNotification(`${window.jsTranslations['Container'] || 'Container'} ${containerId} ${window.jsTranslations['durduruluyor...'] || 'durduruluyor...'}`);
    
    fetch(`/docker-manager/api/container/${containerId}/stop/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`${window.jsTranslations['Container'] || 'Container'} ${containerId} ${window.jsTranslations['durduruldu'] || 'durduruldu'}`);
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(`${window.jsTranslations['Hata:'] || 'Hata:'} ${data.message}`);
        }
    })
    .catch(error => {
        showNotification(`${window.jsTranslations['Hata:'] || 'Hata:'} ${error.message}`);
    });
}

function startContainer(containerId) {
    if (!containerId || containerId === 'null' || containerId === 'undefined') {
        console.error('Invalid containerId for startContainer:', containerId);
        showNotification(`${window.jsTranslations['Hata:'] || 'Hata:'} ${window.jsTranslations['Container ID not found'] || 'Container ID not found'}`);
        return;
    }
    showNotification(`${window.jsTranslations['Container'] || 'Container'} ${containerId} ${window.jsTranslations['başlatılıyor...'] || 'başlatılıyor...'}`);
    
    fetch(`/docker-manager/api/container/${containerId}/start/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`${window.jsTranslations['Container'] || 'Container'} ${containerId} ${window.jsTranslations['başlatıldı'] || 'başlatıldı'}`);
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(`${window.jsTranslations['Hata:'] || 'Hata:'} ${data.message}`);
        }
    })
    .catch(error => {
        showNotification(`${window.jsTranslations['Hata:'] || 'Hata:'} ${error.message}`);
    });
}

function showMoreOptions(containerId) {
    // Dropdown menü göster
    showNotification(`${window.jsTranslations['More options for'] || 'More options for'} ${containerId}`);
}

function deleteContainer(containerId) {
    if (!containerId || containerId === 'null' || containerId === 'undefined') {
        console.error('Invalid containerId for deleteContainer:', containerId);
        showNotification(`${window.jsTranslations['Hata:'] || 'Hata:'} ${window.jsTranslations['Container ID not found'] || 'Container ID not found'}`);
        return;
    }
    showNotification(`${window.jsTranslations['Container'] || 'Container'} ${containerId} ${window.jsTranslations['siliniyor...'] || 'siliniyor...'}`);
    
    fetch(`/docker-manager/api/container/${containerId}/remove/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`${window.jsTranslations['Container'] || 'Container'} ${containerId} ${window.jsTranslations['silindi'] || 'silindi'}`);
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(`${window.jsTranslations['Hata:'] || 'Hata:'} ${data.message}`);
        }
    })
    .catch(error => {
        showNotification(`${window.jsTranslations['Hata:'] || 'Hata:'} ${error.message}`);
    });
}

function restartContainer(containerId) {
    if (!containerId || containerId === 'null' || containerId === 'undefined') {
        console.error('Invalid containerId for restartContainer:', containerId);
        showNotification(`${window.jsTranslations['Hata:'] || 'Hata:'} ${window.jsTranslations['Container ID not found'] || 'Container ID not found'}`);
        return;
    }
    showNotification(`${window.jsTranslations['Container'] || 'Container'} ${containerId} ${window.jsTranslations['yeniden başlatılıyor...'] || 'yeniden başlatılıyor...'}`);
    
    fetch(`/docker-manager/api/container/${containerId}/restart/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`${window.jsTranslations['Container'] || 'Container'} ${containerId} ${window.jsTranslations['yeniden başlatıldı'] || 'yeniden başlatıldı'}`);
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(`${window.jsTranslations['Hata:'] || 'Hata:'} ${data.message}`);
        }
    })
    .catch(error => {
        showNotification(`${window.jsTranslations['Hata:'] || 'Hata:'} ${error.message}`);
    });
}

function showNotification(message) {
    // Basit notification sistemi
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #007acc;
        color: white;
        padding: 12px 20px;
        border-radius: 4px;
        z-index: 1000;
        font-size: 14px;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Terminal butonu
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('terminal-btn')) {
        showNotification(window.jsTranslations['Opening terminal...'] || 'Opening terminal...');
        // Terminal açma işlemi
    }
});

// Restart butonu - event delegation kullanarak buton içindeki elementlere tıklanabilir
document.addEventListener('click', function(e) {
    // Butona veya buton içindeki bir elemente tıklanıp tıklanmadığını kontrol et
    const restartBtn = e.target.closest('.restart-btn');
    if (restartBtn) {
        if (confirm(window.jsTranslations['Are you sure you want to restart Docker? This will stop all running containers.'] || 'Are you sure you want to restart Docker? This will stop all running containers.')) {
            showNotification(window.jsTranslations['Restarting Docker...'] || 'Restarting Docker...');
            
            fetch('/docker-manager/api/service/restart/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json',
                },
            })
            .then(response => {
                // Response'un JSON olup olmadığını kontrol et
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    // JSON değilse text olarak oku
                    return response.text().then(text => {
                        throw new Error(`Unexpected response format: ${text.substring(0, 100)}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    showNotification(window.jsTranslations['Docker service restarted successfully'] || 'Docker service restarted successfully');
                    // Birkaç saniye sonra sayfayı yenile (Docker servisinin başlaması için)
                    setTimeout(() => {
                        location.reload();
                    }, 3000);
                } else {
                    showNotification(`${window.jsTranslations['Hata:'] || 'Hata:'} ${data.message || 'Unknown error'}`);
                }
            })
            .catch(error => {
                console.error('Docker restart error:', error);
                showNotification(`${window.jsTranslations['Hata:'] || 'Hata:'} ${error.message || 'Failed to restart Docker service'}`);
            });
        }
    }
});
