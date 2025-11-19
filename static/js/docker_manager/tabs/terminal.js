// Terminal Tab - Web terminal

// Global değişkenler - sadece bir kez tanımla
if (typeof terminalConnected === 'undefined') {
    var terminalConnected = false;
}
if (typeof terminalHistory === 'undefined') {
    var terminalHistory = [];
}
if (typeof historyIndex === 'undefined') {
    var historyIndex = -1;
}

function loadTerminal() {
    console.log('Loading terminal for container:', currentContainerId);
    
    const terminalOutput = document.getElementById('terminalOutput');
    const terminalInput = document.getElementById('terminalInput');
    
    terminalOutput.innerHTML = '<div class="terminal-line">Connecting to container terminal...</div>';
    
    // Terminal input event listener
    terminalInput.addEventListener('keydown', handleTerminalInput);
    terminalInput.focus();
    
    // Terminal bağlantısını başlat
    connectTerminal();
}

function connectTerminal() {
    fetch(`/docker-manager/api/container/${currentContainerId}/terminal/connect/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            terminalConnected = true;
            addTerminalLine('Connected to container terminal');
            addTerminalLine('Type commands and press Enter to execute');
            addTerminalLine('');
            showPrompt();
        } else {
            addTerminalLine(`Error: ${data.message}`);
            addTerminalLine('Terminal connection failed');
        }
    })
    .catch(error => {
        addTerminalLine(`Connection error: ${error.message}`);
        addTerminalLine('Terminal connection failed');
    });
}

function handleTerminalInput(event) {
    if (event.key === 'Enter') {
        const input = event.target.value.trim();
        if (input) {
            // Komutu geçmişe ekle
            terminalHistory.push(input);
            historyIndex = terminalHistory.length;
            
            // Komutu göster
            addTerminalLine(`$ ${input}`);
            
            // Komutu çalıştır
            executeCommand(input);
            
            // Input'u temizle
            event.target.value = '';
        }
    } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        if (historyIndex > 0) {
            historyIndex--;
            event.target.value = terminalHistory[historyIndex];
        }
    } else if (event.key === 'ArrowDown') {
        event.preventDefault();
        if (historyIndex < terminalHistory.length - 1) {
            historyIndex++;
            event.target.value = terminalHistory[historyIndex];
        } else {
            historyIndex = terminalHistory.length;
            event.target.value = '';
        }
    }
}

function executeCommand(command) {
    if (!terminalConnected) {
        addTerminalLine('Terminal not connected');
        showPrompt();
        return;
    }
    
    fetch(`/docker-manager/api/container/${currentContainerId}/terminal/execute/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command: command })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.output) {
                // Output'u satır satır göster
                const lines = data.output.split('\n');
                lines.forEach(line => {
                    if (line.trim()) {
                        addTerminalLine(line);
                    }
                });
            }
        } else {
            addTerminalLine(`Error: ${data.message}`);
        }
        showPrompt();
    })
    .catch(error => {
        addTerminalLine(`Execution error: ${error.message}`);
        showPrompt();
    });
}

function addTerminalLine(text) {
    const terminalOutput = document.getElementById('terminalOutput');
    const line = document.createElement('div');
    line.className = 'terminal-line';
    line.textContent = text;
    terminalOutput.appendChild(line);
    
    // Scroll'u en alta götür
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

function showPrompt() {
    addTerminalLine('');
    addTerminalLine('$ ');
}

function clearTerminal() {
    const terminalOutput = document.getElementById('terminalOutput');
    terminalOutput.innerHTML = '';
    addTerminalLine('Terminal cleared');
    showPrompt();
}

// Terminal için CSS ekle
const style = document.createElement('style');
style.textContent = `
    .terminal-output {
        background: #1a202c;
        color: #e2e8f0;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.4;
        padding: 16px 20px;
        overflow-y: auto;
        min-height: 400px;
    }
    
    .terminal-line {
        margin-bottom: 2px;
        word-wrap: break-word;
        white-space: pre-wrap;
    }
    
    .terminal-input {
        background: #1a202c;
        color: #e2e8f0;
        border: 1px solid #4a5568;
        border-radius: 4px;
        padding: 8px 12px;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        width: 100%;
    }
    
    .terminal-input:focus {
        outline: none;
        border-color: #007bff;
        box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
    }
    
    .terminal-input-container {
        background: #1a202c;
        border-top: 1px solid #4a5568;
        padding: 12px 20px;
    }
`;
document.head.appendChild(style);
