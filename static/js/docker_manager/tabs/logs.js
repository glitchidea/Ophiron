// Logs Tab - Canlı log gösterimi

// Global değişkenler - sadece bir kez tanımla
if (typeof logsPaused === 'undefined') {
    var logsPaused = false;
}
if (typeof logsInterval === 'undefined') {
    var logsInterval = null;
}

// Ana container_detail.js'den override edilecek
function loadLogs() {
    console.log('Loading logs for container:', typeof currentContainerId !== 'undefined' ? currentContainerId : 'unknown');
    
    // Önceki interval'ı temizle
    if (typeof logsInterval !== 'undefined' && logsInterval) {
        clearInterval(logsInterval);
    }
    
    // Logs container'ını temizle
    const logsOutput = document.getElementById('logsOutput');
    if (logsOutput) {
        logsOutput.innerHTML = '<div class="log-line">Loading logs...</div>';
    }
    
    // Hemen logları yükle
    loadInitialLogs();
    
    // 3 saniye sonra interval başlat
    setTimeout(() => {
        if (typeof logsInterval !== 'undefined') {
            logsInterval = setInterval(() => {
                if (typeof logsPaused !== 'undefined' && !logsPaused) {
                    updateLogs();
                }
            }, 3000);
        }
    }, 1000);
}

function startLiveLogs() {
    if (typeof logsPaused !== 'undefined' && logsPaused) return;
    
    console.log('Starting live logs for container:', typeof currentContainerId !== 'undefined' ? currentContainerId : 'unknown');
    
    // İlk logları yükle
    loadInitialLogs();
    
    // Her 3 saniyede bir logları güncelle
    logsInterval = setInterval(() => {
        if (!logsPaused) {
            updateLogs();
        }
    }, 3000);
}

function loadInitialLogs() {
    console.log('Fetching logs from API...');
    
    if (typeof currentContainerId === 'undefined') {
        console.error('currentContainerId is not defined');
        return;
    }
    
    fetch(`/docker-manager/api/container/${currentContainerId}/logs/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => {
        console.log('Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Logs API response:', data);
        if (data.success) {
            if (data.logs && data.logs.length > 0) {
                displayLogs(data.logs);
            } else {
                document.getElementById('logsOutput').innerHTML = '<div class="log-line">No logs available for this container</div>';
            }
        } else {
            showLogError(data.message);
        }
    })
    .catch(error => {
        console.error('Logs fetch error:', error);
        showLogError('Logs yüklenirken hata oluştu: ' + error.message);
    });
}

function updateLogs() {
    if (typeof currentContainerId === 'undefined') {
        console.error('currentContainerId is not defined');
        return;
    }
    
    fetch(`/docker-manager/api/container/${currentContainerId}/logs/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Sadece yeni loglar varsa güncelle
            if (data.logs && data.logs.length > 0) {
                displayLogs(data.logs);
            }
        } else {
            console.warn('Log update failed:', data.message);
        }
    })
    .catch(error => {
        console.error('Log update error:', error);
    });
}

function displayLogs(logs) {
    const logsOutput = document.getElementById('logsOutput');
    
    console.log('Displaying logs, count:', logs ? logs.length : 0);
    
    if (!logs || logs.length === 0) {
        logsOutput.innerHTML = '<div class="log-line">No logs available for this container</div>';
        return;
    }
    
    // Logları HTML'e çevir
    let logsHTML = '';
    logs.forEach((log, index) => {
        const timestamp = log.timestamp ? `<span class="log-timestamp">[${log.timestamp}]</span>` : '';
        const stream = log.stream ? `<span class="log-stream log-${log.stream}">${log.stream.toUpperCase()}</span>` : '';
        logsHTML += `<div class="log-line">${timestamp}${stream} ${escapeHtml(log.message)}</div>`;
    });
    
    logsOutput.innerHTML = logsHTML;
    
    // Scroll'u en alta götür
    logsOutput.scrollTop = logsOutput.scrollHeight;
    
    console.log('Logs displayed successfully');
}

function showLogError(message) {
    const logsOutput = document.getElementById('logsOutput');
    logsOutput.innerHTML = `<div class="log-line log-error">Error: ${escapeHtml(message)}</div>`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Logs kontrolleri
function toggleLogs() {
    logsPaused = !logsPaused;
    
    const toggleIcon = document.getElementById('logsToggleIcon');
    const toggleText = document.getElementById('logsToggleText');
    
    if (logsPaused) {
        toggleIcon.className = 'fas fa-play';
        toggleText.textContent = 'Resume';
        if (logsInterval) {
            clearInterval(logsInterval);
        }
    } else {
        toggleIcon.className = 'fas fa-pause';
        toggleText.textContent = 'Pause';
        startLiveLogs();
    }
}

function clearLogs() {
    const logsOutput = document.getElementById('logsOutput');
    logsOutput.innerHTML = '<div class="log-line">Logs cleared</div>';
}

function downloadLogs() {
    fetch(`/docker-manager/api/container/${currentContainerId}/logs/download/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `container-${currentContainerId}-logs.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    })
    .catch(error => {
        showNotification('Logs indirilemedi: ' + error.message);
    });
}

// Tab değiştiğinde interval'ı temizle
document.addEventListener('visibilitychange', function() {
    if (document.hidden && logsInterval) {
        clearInterval(logsInterval);
    } else if (!document.hidden && currentTab === 'logs' && !logsPaused) {
        startLiveLogs();
    }
});

// Sayfa kapatılırken temizlik
window.addEventListener('beforeunload', function() {
    if (logsInterval) {
        clearInterval(logsInterval);
    }
});
