// Terminal Tab - HTTP API ile basit terminal

var terminalConnected = false;
var currentCommand = '';

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
    
    // Basit terminal başlat
    startTerminal(containerId);
}

function startTerminal(containerId) {
    const terminal = document.getElementById('terminal');
    
    // Terminal başlangıç
    terminal.innerHTML = '$ ';
    terminalConnected = true;
    
    // Event listener'ları ekle
    setupTerminalEvents(containerId);
}

function setupTerminalEvents(containerId) {
    const terminal = document.getElementById('terminal');
    
    if (!terminal) return;
    
    // Click to focus
    terminal.addEventListener('click', function() {
        this.focus();
    });
    
    // Keyboard events
    terminal.addEventListener('keydown', function(e) {
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
    terminal.focus();
    terminal.tabIndex = 0;
}

function addChar(char) {
    const terminal = document.getElementById('terminal');
    const lines = terminal.innerHTML.split('<br>');
    const lastLine = lines[lines.length - 1];
    
    if (lastLine.startsWith('$ ')) {
        terminal.innerHTML = terminal.innerHTML.slice(0, -1) + char + '█';
    }
}

function removeLastChar() {
    const terminal = document.getElementById('terminal');
    const lines = terminal.innerHTML.split('<br>');
    const lastLine = lines[lines.length - 1];
    
    if (lastLine.length > 2) { // $ + space + char
        terminal.innerHTML = terminal.innerHTML.slice(0, -2) + '█';
    }
}

function executeCommand(containerId) {
    const terminal = document.getElementById('terminal');
    const lines = terminal.innerHTML.split('<br>');
    const lastLine = lines[lines.length - 1];
    
    // Komutu al
    const command = lastLine.replace('$ ', '').replace('█', '').trim();
    
    if (!command) {
        // Boş komut için yeni prompt
        terminal.innerHTML += '<br>$ ';
        return;
    }
    
    // Komut satırını göster
    terminal.innerHTML = terminal.innerHTML.replace('█', '') + '<br>';
    
    // Loading göster
    terminal.innerHTML += 'Executing...<br>';
    
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
        terminal.innerHTML = terminal.innerHTML.replace('Executing...<br>', '');
        
        if (data.success) {
            const output = data.output || 'No output';
            terminal.innerHTML += output + '<br>';
        } else {
            terminal.innerHTML += 'Error: ' + data.message + '<br>';
        }
        
        // Yeni prompt ekle
        terminal.innerHTML += '$ ';
        
        // Scroll to bottom
        terminal.scrollTop = terminal.scrollHeight;
    })
    .catch(error => {
        // Loading'i kaldır
        terminal.innerHTML = terminal.innerHTML.replace('Executing...<br>', '');
        
        terminal.innerHTML += 'Error: ' + error.message + '<br>';
        terminal.innerHTML += '$ ';
        
        // Scroll to bottom
        terminal.scrollTop = terminal.scrollHeight;
    });
}
