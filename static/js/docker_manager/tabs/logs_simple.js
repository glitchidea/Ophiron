// Logs Tab - Basit versiyon

// Ensure jsTranslations is available
if (typeof window.jsTranslations === 'undefined') {
    window.jsTranslations = {};
}

function loadLogs() {
    console.log('Loading logs...');
    
    const logsOutput = document.getElementById('logsOutput');
    if (!logsOutput) {
        console.error('logsOutput element not found');
        return;
    }
    
    const loadingMsg = window.jsTranslations['Loading logs...'] || 'Loading logs...';
    logsOutput.innerHTML = '<div class="log-line">' + loadingMsg + '</div>';
    
    // Container ID'yi URL'den al
    const pathParts = window.location.pathname.split('/');
    let containerId = pathParts[pathParts.length - 2];
    if (!containerId || containerId === 'null' || containerId === 'undefined') {
        const metaEl = document.getElementById('containerIdMeta');
        if (metaEl && metaEl.content) {
            containerId = metaEl.content;
        }
    }
    
    if (!containerId) {
        const errorMsg = window.jsTranslations['Container ID not found'] || 'Container ID not found';
        logsOutput.innerHTML = '<div class="log-line log-error">' + errorMsg + '</div>';
        return;
    }
    
    console.log('Fetching logs for container:', containerId);
    
    fetch(`/docker-manager/api/container/${containerId}/logs/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log('Logs response:', data);
        if (data.success) {
            if (data.logs && data.logs.length > 0) {
                displayLogs(data.logs);
            } else {
                const noLogsMsg = window.jsTranslations['No logs available'] || 'No logs available';
                logsOutput.innerHTML = '<div class="log-line">' + noLogsMsg + '</div>';
            }
        } else {
            const errorMsg = (window.jsTranslations['Error'] || 'Error') + ': ' + data.message;
            logsOutput.innerHTML = '<div class="log-line log-error">' + errorMsg + '</div>';
        }
    })
    .catch(error => {
        console.error('Logs error:', error);
        const errorMsg = (window.jsTranslations['Error'] || 'Error') + ': ' + error.message;
        logsOutput.innerHTML = '<div class="log-line log-error">' + errorMsg + '</div>';
    });
}

function displayLogs(logs) {
    const logsOutput = document.getElementById('logsOutput');
    
    console.log('Displaying logs, count:', logs ? logs.length : 0);
    
    if (!logs || logs.length === 0) {
        const noLogsMsg = window.jsTranslations['No logs available'] || 'No logs available';
        logsOutput.innerHTML = '<div class="log-line">' + noLogsMsg + '</div>';
        return;
    }
    
    let logsHTML = '';
    logs.forEach((log, index) => {
        const timestamp = log.timestamp ? `<span class="log-timestamp">[${log.timestamp}]</span>` : '';
        const stream = log.stream ? `<span class="log-stream log-${log.stream}">${log.stream.toUpperCase()}</span>` : '';
        logsHTML += `<div class="log-line">${timestamp}${stream} ${escapeHtml(log.message)}</div>`;
    });
    
    logsOutput.innerHTML = logsHTML;
    logsOutput.scrollTop = logsOutput.scrollHeight;
    
    console.log('Logs displayed successfully');
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
