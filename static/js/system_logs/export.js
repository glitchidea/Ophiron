document.addEventListener('DOMContentLoaded', function(){
    const exportBtn = document.getElementById('exportLogs');
    if (!exportBtn) return;
    // Opening handled in system_logs.js to centralize behavior

    // ===== CATEGORY SELECTION CONTROLS =====
    const selectAllBtn = document.getElementById('selectAllCategories');
    const deselectAllBtn = document.getElementById('deselectAllCategories');
    
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function() {
            const checkboxes = document.querySelectorAll('input[name="logCategories"]');
            checkboxes.forEach(cb => cb.checked = true);
        });
    }
    
    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', function() {
            const checkboxes = document.querySelectorAll('input[name="logCategories"]');
            checkboxes.forEach(cb => cb.checked = false);
        });
    }

    const startExport = document.getElementById('startExport');
    if (startExport) {
        startExport.addEventListener('click', function(){
            const statusEl = document.getElementById('exportStatus');
            
            // Get selected categories
            const selectedCategories = Array.from(document.querySelectorAll('input[name="logCategories"]:checked'))
                .map(cb => cb.value);
            
            if (selectedCategories.length === 0) {
                statusEl.textContent = 'Lütfen en az bir log kategorisi seçin.';
                return;
            }
            
            // Get format and level
            const format = (document.querySelector('input[name="exportFormat"]:checked')?.value || 'csv');
            const level = document.getElementById('logLevelFilter')?.value || 'all';
            
            statusEl.textContent = 'Export başlatılıyor...';
            
            // Build URL with parameters
            const params = new URLSearchParams({
                format: format,
                level: level,
                categories: selectedCategories.join(',')
            });
            
            fetch(`/system-logs/export/?${params}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    // Check if response is a file download
                    const contentType = response.headers.get('content-type');
                    if (contentType && (contentType.includes('text/csv') || contentType.includes('application/json') || contentType.includes('text/plain'))) {
                        // It's a file download
                        return response.blob().then(blob => {
                            const url = window.URL.createObjectURL(blob);
                            const link = document.createElement('a');
                            link.href = url;
                            
                            // Generate filename based on format and categories
                            const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
                            const categoriesStr = selectedCategories.join('_');
                            const filename = `system_logs_${categoriesStr}_${timestamp}.${format}`;
                            
                            link.download = filename;
                            link.click();
                            window.URL.revokeObjectURL(url);
                            
                            statusEl.textContent = 'Export tamamlandı!';
                            
                            // Close modal after download
                            const modalEl = document.getElementById('exportModal');
                            if (modalEl) {
                                const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                                modal.hide();
                            }
                        });
                    } else {
                        // Try to parse as JSON (error response)
                        return response.json().then(data => {
                            statusEl.textContent = data.error || 'Export başarısız.';
                        });
                    }
                })
                .catch(error => {
                    console.error('Export error:', error);
                    statusEl.textContent = 'An error occurred during export.';
                });
        });
    }
});


