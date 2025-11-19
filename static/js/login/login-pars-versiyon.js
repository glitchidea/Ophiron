// Load version info from JSON
function loadVersionInfo() {
    fetch('../../static/versiyon/versiyon.json')
        .then(response => response.json())
        .then(data => {
            const versionElement = document.querySelector('.footer-text');
            if (versionElement) {
                versionElement.textContent = `Ophiron ${data.version} | ${data.title} ${data.year}`;
            }
        })
        .catch(error => {
            console.log('Version info could not be loaded, using default');
            // Default version info
            const versionElement = document.querySelector('.footer-text');
            if (versionElement) {
                versionElement.textContent = 'Ophiron v2.0.0 | Advanced Security Platform 2025';
            }
        });
}

// Load version info when page loads
document.addEventListener('DOMContentLoaded', loadVersionInfo);
