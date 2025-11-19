// Terminal Tab - Basit gerçek terminal mount

var terminalSocket = null;
var terminalConnected = false;

function loadTerminal() {
    console.log('Loading terminal...');
    
    const terminal = document.getElementById('terminal');
    if (!terminal) {
        console.error('Terminal element not found');
        return;
    }
    
    // Container ID'yi URL'den al
    const pathParts = window.location.pathname.split('/');
    const containerId = pathParts[pathParts.length - 2];
    
    if (!containerId) {
        terminal.innerHTML = 'Container ID not found';
        return;
    }
    
    console.log('Connecting to terminal for container:', containerId);
    
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
        
        const terminal = document.getElementById('terminal');
        terminal.innerHTML = '';
        
        setupTerminal();
    };
    
    terminalSocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };
    
    terminalSocket.onclose = function(event) {
        console.log('WebSocket disconnected');
        terminalConnected = false;
        
        const terminal = document.getElementById('terminal');
        terminal.innerHTML += '\nTerminal disconnected\n';
    };
    
    terminalSocket.onerror = function(error) {
        console.error('WebSocket error:', error);
        
        const terminal = document.getElementById('terminal');
        terminal.innerHTML = 'WebSocket connection failed';
    };
}

function handleMessage(data) {
    const terminal = document.getElementById('terminal');
    
    switch (data.type) {
        case 'output':
            terminal.innerHTML += data.data;
            break;
            
        case 'error':
            terminal.innerHTML += data.message;
            break;
    }
    
    // Scroll to bottom
    terminal.scrollTop = terminal.scrollHeight;
}

function setupTerminal() {
    const terminal = document.getElementById('terminal');
    
    if (!terminal) return;
    
    // Click to focus
    terminal.addEventListener('click', function() {
        this.focus();
    });
    
    // Keyboard events
    terminal.addEventListener('keydown', function(e) {
        if (terminalSocket && terminalConnected) {
            // Send all keystrokes to container
            const message = {
                type: 'input',
                data: e.key
            };
            
            terminalSocket.send(JSON.stringify(message));
        }
    });
    
    // Focus terminal
    terminal.focus();
    terminal.tabIndex = 0;
}
