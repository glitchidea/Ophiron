// Terminal Tab - Çalışan versiyon

// Global değişkenler
if (typeof terminalSocket === 'undefined') {
    var terminalSocket = null;
}
if (typeof terminalConnected === 'undefined') {
    var terminalConnected = false;
}
if (typeof currentCommand === 'undefined') {
    var currentCommand = '';
}

function loadTerminal() {
    console.log('Loading terminal...');
    
    const terminalScreen = document.getElementById('terminalScreen');
    
    if (!terminalScreen) {
        console.error('terminalScreen element not found');
        return;
    }
    
    // Status'u connecting olarak ayarla
    updateStatus('connecting', 'Connecting...');
    
    // Container ID'yi URL'den al
    const pathParts = window.location.pathname.split('/');
    const containerId = pathParts[pathParts.length - 2];
    
    if (!containerId) {
        terminalScreen.innerHTML = '<div class="terminal-error">Container ID not found</div>';
        return;
    }
    
    console.log('Connecting to terminal for container:', containerId);
    
    // Basit terminal başlat
    startSimpleTerminal(containerId);
}

function startSimpleTerminal(containerId) {
    const terminalScreen = document.getElementById('terminalScreen');
    
    // Terminal başlangıç ekranı
    terminalScreen.innerHTML = `
        <div class="terminal-line">
            <span class="prompt">$</span>
            <span class="cursor">█</span>
        </div>
    `;
    
    updateStatus('connected', 'Connected');
    terminalConnected = true;
    
    // Event listener'ları ekle
    setupTerminalEvents(containerId);
}

function setupTerminalEvents(containerId) {
    const terminalScreen = document.getElementById('terminalScreen');
    
    if (!terminalScreen) return;
    
    // Click to focus
    terminalScreen.addEventListener('click', function() {
        this.focus();
    });
    
    // Keyboard events
    terminalScreen.addEventListener('keydown', function(e) {
        if (!terminalConnected) return;
        
        if (e.key === 'Enter') {
            e.preventDefault();
            executeCommand(containerId);
        } else if (e.key === 'Backspace') {
            e.preventDefault();
            removeLastChar();
        } else if (e.key.length === 1) {
            e.preventDefault();
            addChar(e.key);
        }
    });
    
    // Focus terminal
    terminalScreen.focus();
    terminalScreen.tabIndex = 0;
}

function addChar(char) {
    const terminalScreen = document.getElementById('terminalScreen');
    const currentLine = terminalScreen.querySelector('.terminal-line:last-child');
    
    if (currentLine) {
        const cursor = currentLine.querySelector('.cursor');
        if (cursor) {
            // Cursor'dan önceki karakteri al
            const beforeCursor = cursor.textContent;
            cursor.textContent = beforeCursor + char + '█';
        }
    }
}

function removeLastChar() {
    const terminalScreen = document.getElementById('terminalScreen');
    const currentLine = terminalScreen.querySelector('.terminal-line:last-child');
    
    if (currentLine) {
        const cursor = currentLine.querySelector('.cursor');
        if (cursor) {
            const text = cursor.textContent;
            if (text.length > 1) {
                cursor.textContent = text.slice(0, -2) + '█';
            }
        }
    }
}

function executeCommand(containerId) {
    const terminalScreen = document.getElementById('terminalScreen');
    const currentLine = terminalScreen.querySelector('.terminal-line:last-child');
    
    if (!currentLine) return;
    
    // Komutu al
    const command = currentLine.textContent.replace('$', '').replace('█', '').trim();
    
    if (!command) {
        // Boş komut için yeni prompt
        terminalScreen.innerHTML += '<div class="terminal-line"><span class="prompt">$</span><span class="cursor">█</span></div>';
        return;
    }
    
    // Komut satırını göster
    currentLine.innerHTML = `<span class="prompt">$</span> ${command}`;
    
    // Loading göster
    terminalScreen.innerHTML += '<div class="terminal-output">Executing command...</div>';
    
    // API'ye gönder
    fetch(`/docker-manager/api/container/${containerId}/terminal/execute/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command: command })
    })
    .then(response => response.json())
    .then(data => {
        // Loading'i kaldır
        const loading = terminalScreen.querySelector('.terminal-output');
        if (loading) loading.remove();
        
        if (data.success) {
            const output = data.output || 'No output';
            terminalScreen.innerHTML += `<div class="terminal-output">${escapeHtml(output)}</div>`;
        } else {
            terminalScreen.innerHTML += `<div class="terminal-error">Error: ${data.message}</div>`;
        }
        
        // Yeni prompt ekle
        terminalScreen.innerHTML += '<div class="terminal-line"><span class="prompt">$</span><span class="cursor">█</span></div>';
        
        // Scroll to bottom
        terminalScreen.scrollTop = terminalScreen.scrollHeight;
    })
    .catch(error => {
        // Loading'i kaldır
        const loading = terminalScreen.querySelector('.terminal-output');
        if (loading) loading.remove();
        
        terminalScreen.innerHTML += `<div class="terminal-error">Execution error: ${error.message}</div>`;
        terminalScreen.innerHTML += '<div class="terminal-line"><span class="prompt">$</span><span class="cursor">█</span></div>';
        
        // Scroll to bottom
        terminalScreen.scrollTop = terminalScreen.scrollHeight;
    });
}

function updateStatus(status, text) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    if (statusDot && statusText) {
        statusDot.className = `status-dot ${status}`;
        statusText.textContent = text;
    }
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
