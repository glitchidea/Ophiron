// Terminal Tab - Sıfırdan geliştirilmiş

function loadTerminal() {
    console.log('Loading new terminal...');
    
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
    
    console.log('Starting terminal for container:', containerId);
    
    // Terminal'i başlat
    initTerminal(containerId);
}

function initTerminal(containerId) {
    const terminal = document.getElementById('terminal');
    
    // Terminal'i temizle
    terminal.innerHTML = '';
    
    // Başlangıç prompt'u
    addLine('$ ');
    
    // Event listener'ları ekle
    setupEvents(containerId);
}

function setupEvents(containerId) {
    const terminal = document.getElementById('terminal');
    
    // Click to focus
    terminal.addEventListener('click', function() {
        this.focus();
    });
    
    // Keyboard events
    terminal.addEventListener('keydown', function(e) {
        handleKeyPress(e, containerId);
    });
    
    // Focus terminal
    terminal.focus();
    terminal.tabIndex = 0;
}

function handleKeyPress(e, containerId) {
    const terminal = document.getElementById('terminal');
    
    if (e.key === 'Enter') {
        e.preventDefault();
        executeCommand(containerId);
    } else if (e.key === 'Backspace') {
        e.preventDefault();
        removeChar();
    } else if (e.key.length === 1) {
        e.preventDefault();
        addChar(e.key);
    }
}

function addChar(char) {
    const terminal = document.getElementById('terminal');
    const lines = terminal.innerHTML.split('<br>');
    const lastLine = lines[lines.length - 1];
    
    if (lastLine.startsWith('$ ')) {
        terminal.innerHTML = terminal.innerHTML.slice(0, -1) + char + '█';
    }
}

function removeChar() {
    const terminal = document.getElementById('terminal');
    const lines = terminal.innerHTML.split('<br>');
    const lastLine = lines[lines.length - 1];
    
    if (lastLine.length > 2) {
        terminal.innerHTML = terminal.innerHTML.slice(0, -2) + '█';
    }
}

function addLine(text) {
    const terminal = document.getElementById('terminal');
    terminal.innerHTML += text;
}

function executeCommand(containerId) {
    const terminal = document.getElementById('terminal');
    const lines = terminal.innerHTML.split('<br>');
    const lastLine = lines[lines.length - 1];
    
    // Komutu al
    const command = lastLine.replace('$ ', '').replace('█', '').trim();
    
    if (!command) {
        addLine('<br>$ ');
        return;
    }
    
    // Komut satırını göster
    terminal.innerHTML = terminal.innerHTML.replace('█', '') + '<br>';
    
    // Loading
    addLine('Executing...<br>');
    
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
            addLine(output + '<br>');
        } else {
            addLine('Error: ' + data.message + '<br>');
        }
        
        // Yeni prompt
        addLine('$ ');
        
        // Scroll
        terminal.scrollTop = terminal.scrollHeight;
    })
    .catch(error => {
        terminal.innerHTML = terminal.innerHTML.replace('Executing...<br>', '');
        addLine('Error: ' + error.message + '<br>');
        addLine('$ ');
        terminal.scrollTop = terminal.scrollHeight;
    });
}
