// Inspect Tab - Container inspect bilgileri

// Ensure jsTranslations is available
if (typeof window.jsTranslations === 'undefined') {
    window.jsTranslations = {};
}

function loadInspect() {
    console.log('Loading inspect data for container:', currentContainerId);
    
    const inspectData = document.getElementById('inspectData');
    const loadingMsg = window.jsTranslations['Loading inspect data...'] || 'Loading inspect data...';
    inspectData.innerHTML = '<div class="loading">' + loadingMsg + '</div>';
    
    fetch(`/docker-manager/api/container/${currentContainerId}/inspect/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayInspectData(data.inspect);
        } else {
            showInspectError(data.message);
        }
    })
    .catch(error => {
        showInspectError('Inspect data yüklenirken hata oluştu: ' + error.message);
    });
}

function displayInspectData(inspectData) {
    const container = document.getElementById('inspectData');
    
    if (!inspectData) {
        const noDataMsg = window.jsTranslations['No inspect data available'] || 'No inspect data available';
        container.innerHTML = '<div class="error">' + noDataMsg + '</div>';
        return;
    }
    
    // JSON'u güzel formatla
    const formattedJson = JSON.stringify(inspectData, null, 2);
    
    // Syntax highlighting için HTML oluştur
    const highlightedJson = highlightJson(formattedJson);
    
    container.innerHTML = `<pre class="json-content">${highlightedJson}</pre>`;
}

function highlightJson(json) {
    return json
        .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
            let cls = 'json-number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'json-key';
                } else {
                    cls = 'json-string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'json-boolean';
            } else if (/null/.test(match)) {
                cls = 'json-null';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        });
}

function showInspectError(message) {
    const container = document.getElementById('inspectData');
    const errorMsg = (window.jsTranslations['Error'] || 'Error') + ': ' + escapeHtml(message);
    container.innerHTML = '<div class="error">' + errorMsg + '</div>';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// JSON viewer için CSS ekle
const style = document.createElement('style');
style.textContent = `
    .json-content {
        background: #f8f9fa;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 16px;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.4;
        overflow-x: auto;
    }
    
    .json-key {
        color: #0066cc;
        font-weight: bold;
    }
    
    .json-string {
        color: #009900;
    }
    
    .json-number {
        color: #cc6600;
    }
    
    .json-boolean {
        color: #9900cc;
        font-weight: bold;
    }
    
    .json-null {
        color: #999999;
        font-style: italic;
    }
    
    .loading {
        text-align: center;
        padding: 40px;
        color: #718096;
    }
    
    .error {
        color: #dc3545;
        padding: 20px;
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 4px;
    }
`;
document.head.appendChild(style);
