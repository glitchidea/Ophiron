// Terminal Tab - Gerçek Docker terminal mount

// Global değişkenler
if (typeof terminalSocket === 'undefined') {
    var terminalSocket = null;
}
if (typeof terminalConnected === 'undefined') {
    var terminalConnected = false;
}

function loadTerminal() {
    console.log('Loading real Docker terminal...');
    
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
    
    console.log('Connecting to Docker terminal for container:', containerId);
    
    // WebSocket bağlantısı kur
    connectWebSocket(containerId);
}

function connectWebSocket(containerId) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/terminal/${containerId}/`;
    
    console.log('Connecting to WebSocket:', wsUrl);
    
    terminalSocket = new WebSocket(wsUrl);
    
    terminalSocket.onopen = function(event) {
        console.log('WebSocket connected');
        terminalConnected = true;
        
        updateStatus('connected', 'Connected');
        
        const terminalScreen = document.getElementById('terminalScreen');
        terminalScreen.innerHTML = '<div class="terminal-output">Terminal connected. You can now type commands...</div>';
        
        setupTerminal(containerId);
    };
    
    terminalSocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    terminalSocket.onclose = function(event) {
        console.log('WebSocket disconnected');
        terminalConnected = false;
        
        updateStatus('disconnected', 'Disconnected');
        
        const terminalScreen = document.getElementById('terminalScreen');
        terminalScreen.innerHTML += '<div class="terminal-disconnected">Terminal disconnected</div>';
    };
    
    terminalSocket.onerror = function(error) {
        console.error('WebSocket error:', error);
        
        updateStatus('error', 'Connection failed');
        
        const terminalScreen = document.getElementById('terminalScreen');
        terminalScreen.innerHTML = '<div class="terminal-error">WebSocket connection failed</div>';
    };
}

function handleWebSocketMessage(data) {
    const terminalScreen = document.getElementById('terminalScreen');
    
    switch (data.type) {
        case 'connected':
            terminalScreen.innerHTML = '<div class="terminal-connected">' + data.message + '</div>';
            break;
            
        case 'output':
            terminalScreen.innerHTML += `<div class="terminal-output">${escapeHtml(data.data)}</div>`;
            break;
            
        case 'error':
            terminalScreen.innerHTML += `<div class="terminal-error">Error: ${data.message}</div>`;
            break;
    }
    
    // Scroll to bottom
    terminalScreen.scrollTop = terminalScreen.scrollHeight;
}

function setupTerminal(containerId) {
    const terminalScreen = document.getElementById('terminalScreen');
    
    if (!terminalScreen) return;
    
    // Click to focus
    terminalScreen.addEventListener('click', function() {
        this.focus();
    });
    
    // Keyboard events
    terminalScreen.addEventListener('keydown', function(e) {
        if (terminalSocket && terminalConnected) {
            // Send all keystrokes to container
            const message = {
                type: 'input',
                data: e.key
            };
            
            terminalSocket.send(JSON.stringify(message));
            
            // Prevent default behavior for special keys
            if (e.key === 'Enter') {
                e.preventDefault();
            }
        }
    });
    
    // Focus terminal
    terminalScreen.focus();
    terminalScreen.tabIndex = 0;
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
