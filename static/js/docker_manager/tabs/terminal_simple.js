// Terminal Tab - Basit versiyon

function loadTerminal() {
    console.log('Loading terminal...');
    
    const terminalOutput = document.getElementById('terminalOutput');
    const terminalInput = document.getElementById('terminalInput');
    
    if (!terminalOutput) {
        console.error('terminalOutput element not found');
        return;
    }
    
    terminalOutput.innerHTML = '<div class="loading">Connecting to terminal...</div>';
    
    // Container ID'yi URL'den al
    const pathParts = window.location.pathname.split('/');
    const containerId = pathParts[pathParts.length - 2];
    
    if (!containerId) {
        terminalOutput.innerHTML = '<div class="error">Container ID not found</div>';
        return;
    }
    
    console.log('Connecting to terminal for container:', containerId);
    
    // Terminal bağlantısını test et
    fetch(`/docker-manager/api/container/${containerId}/terminal/connect/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        console.log('Terminal connect response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Terminal connect response:', data);
        if (data.success) {
            terminalOutput.innerHTML = '<div class="terminal-connected">Terminal connected. Type commands below:</div>';
            setupTerminal(containerId);
        } else {
            terminalOutput.innerHTML = `<div class="error">Terminal connection failed: ${data.message}</div>`;
        }
    })
    .catch(error => {
        console.error('Terminal connection error:', error);
        terminalOutput.innerHTML = `<div class="error">Terminal connection error: ${error.message}</div>`;
    });
}

function setupTerminal(containerId) {
    const terminalInput = document.getElementById('terminalInput');
    const terminalOutput = document.getElementById('terminalOutput');
    
    if (terminalInput) {
        terminalInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const command = this.value.trim();
                if (command) {
                    executeCommand(containerId, command);
                    this.value = '';
                }
            }
        });
    }
}

function executeCommand(containerId, command) {
    console.log('Executing command:', command);
    
    const terminalOutput = document.getElementById('terminalOutput');
    
    // Komut satırını göster
    terminalOutput.innerHTML += `<div class="command-line">$ ${command}</div>`;
    
    fetch(`/docker-manager/api/container/${containerId}/terminal/execute/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command: command })
    })
    .then(response => {
        console.log('Command execute response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Command execute response:', data);
        if (data.success) {
            // Komut çıktısını göster
            const output = data.output || 'No output';
            terminalOutput.innerHTML += `<div class="command-output">${escapeHtml(output)}</div>`;
        } else {
            terminalOutput.innerHTML += `<div class="command-error">Error: ${data.message}</div>`;
        }
        
        // Scroll to bottom
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    })
    .catch(error => {
        console.error('Command execution error:', error);
        terminalOutput.innerHTML += `<div class="command-error">Execution error: ${error.message}</div>`;
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    });
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
