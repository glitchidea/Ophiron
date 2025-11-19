// Mounts Tab - Basit versiyon

// Ensure jsTranslations is available
if (typeof window.jsTranslations === 'undefined') {
    window.jsTranslations = {};
}

function loadMounts() {
    console.log('Loading mounts...');
    
    const mountsList = document.getElementById('mountsList');
    if (!mountsList) {
        console.error('mountsList element not found');
        return;
    }
    
    const loadingMsg = window.jsTranslations['Loading mount information...'] || 'Loading mount information...';
    mountsList.innerHTML = '<div class="loading">' + loadingMsg + '</div>';
    
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
        mountsList.innerHTML = '<div class="error">' + errorMsg + '</div>';
        return;
    }
    
    console.log('Fetching mounts for container:', containerId);
    
    fetch(`/docker-manager/api/container/${containerId}/mounts/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log('Mounts response:', data);
        if (data.success) {
            displayMounts(data);
        } else {
            const errorMsg = (window.jsTranslations['Error'] || 'Error') + ': ' + data.message;
            mountsList.innerHTML = '<div class="error">' + errorMsg + '</div>';
        }
    })
    .catch(error => {
        console.error('Mounts error:', error);
        const errorMsg = (window.jsTranslations['Error'] || 'Error') + ': ' + error.message;
        mountsList.innerHTML = '<div class="error">' + errorMsg + '</div>';
    });
}

function displayMounts(data) {
    const mountsList = document.getElementById('mountsList');
    
    console.log('Displaying mounts data:', data);
    
    let mountsHTML = '<div class="mounts-container">';
    
    // Volume mounts
    if (data.volume_mounts && data.volume_mounts.length > 0) {
        mountsHTML += '<div class="mount-section">';
        mountsHTML += '<h3>Volume Mounts</h3>';
        data.volume_mounts.forEach(mount => {
            mountsHTML += `
                <div class="mount-item">
                    <div class="mount-info">
                        <div class="mount-source">${mount.Source}</div>
                        <div class="mount-destination">${mount.Destination}</div>
                        <div class="mount-type">${mount.Type}</div>
                        <div class="mount-driver">${mount.Driver}</div>
                    </div>
                </div>
            `;
        });
        mountsHTML += '</div>';
    }
    
    // Bind mounts
    if (data.bind_mounts && data.bind_mounts.length > 0) {
        mountsHTML += '<div class="mount-section">';
        mountsHTML += '<h3>Bind Mounts</h3>';
        data.bind_mounts.forEach(mount => {
            mountsHTML += `
                <div class="mount-item">
                    <div class="mount-info">
                        <div class="mount-source">${mount.Source}</div>
                        <div class="mount-destination">${mount.Destination}</div>
                        <div class="mount-type">${mount.Type}</div>
                        <div class="mount-mode">${mount.Mode}</div>
                    </div>
                </div>
            `;
        });
        mountsHTML += '</div>';
    }
    
    // Tmpfs mounts
    if (data.tmpfs_mounts && data.tmpfs_mounts.length > 0) {
        mountsHTML += '<div class="mount-section">';
        mountsHTML += '<h3>Tmpfs Mounts</h3>';
        data.tmpfs_mounts.forEach(mount => {
            mountsHTML += `
                <div class="mount-item">
                    <div class="mount-info">
                        <div class="mount-source">${mount.Source}</div>
                        <div class="mount-destination">${mount.Destination}</div>
                        <div class="mount-type">${mount.Type}</div>
                    </div>
                </div>
            `;
        });
        mountsHTML += '</div>';
    }
    
    if (data.total_count === 0) {
        mountsHTML += '<div class="no-mounts">No mounts found for this container</div>';
    }
    
    mountsHTML += '</div>';
    mountsList.innerHTML = mountsHTML;
    
    console.log('Mounts displayed successfully');
}
