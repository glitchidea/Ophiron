document.addEventListener('DOMContentLoaded', function(){
    const categorySelect = document.getElementById('ownCategory');
    const filesSelect = document.getElementById('ownFiles');
    // Live controls (Settings-driven)
    let liveTimer = null;
    let liveEnabled = false;
    let liveIntervalSec = 10;
    const todayBtn = document.getElementById('ownTodayBtn');
    const allDownloadBtn = document.getElementById('ownAllDownloadBtn');
    const container = document.getElementById('ownContainer');
    if (!container) return;

    // Enhanced category loading
    Promise.all([
        fetch('/system-logs/own/categories/').then(r=>r.json()),
    ]).then(([cats])=>{
        const categories = cats.categories || [];
        if (categorySelect){
            categorySelect.innerHTML = categories.map(c => `<option value="${c}">${c}</option>`).join('');
            categorySelect.onchange = () => selectCategory(categorySelect.value);
        }

        async function selectCategory(category){
            // files for selected category
            const filesResp = await fetch(`/system-logs/own/category/${encodeURIComponent(category)}/files/`);
            const filesJson = await filesResp.json();
            const files = filesJson.files || [];
            // days no longer required for all-download
            if (filesSelect){
                const opts = [`<option value="">${window.jsTranslations['Select File...'] || 'Select File...'}</option>`].concat(files.map(f=>`<option value="${f}">${f}</option>`));
                filesSelect.innerHTML = opts.join('');
                filesSelect.onchange = () => loadPage(category, filesSelect.value, 1);
            }
            if (allDownloadBtn){
                allDownloadBtn.onclick = (e)=>{
                    e.preventDefault();
                    const cat = categorySelect ? categorySelect.value : category;
                    const currentFile = filesSelect ? filesSelect.value : '';
                    if (!currentFile) {
                        alert(window.jsTranslations['Please select a file to download'] || 'Please select a file to download');
                        return;
                    }
                    const link = document.createElement('a');
                    link.href = `/system-logs/own/category/${encodeURIComponent(cat)}/download/file/${encodeURIComponent(currentFile)}/`;
                    link.download = currentFile;
                    document.body.appendChild(link);
                    // use setTimeout to ensure DOM updated before click (Safari fix)
                    setTimeout(()=>{ link.click(); try { document.body.removeChild(link); } catch(e){} }, 0);
                };
            }
            if (todayBtn){
                todayBtn.onclick = ()=>{
                    // pick latest file by name order; fallback to first if empty
                    const latestFile = files.length ? files[files.length-1] : '';
                    if (filesSelect && latestFile) {
                        filesSelect.value = latestFile;
                        loadPage(category, latestFile, 1);
                    } else {
                        alert(window.jsTranslations['No files available for this module'] || 'No files available for this module');
                    }
                };
            }
            // Initialize with empty selection
            if (filesSelect){ filesSelect.value = ''; }
            const container = document.getElementById('ownContainer');
            if (container) {
                container.innerHTML = `<div class="empty-state"><i class="fas fa-file-alt"></i><h3>${window.jsTranslations['Select a File'] || 'Select a File'}</h3><p>${window.jsTranslations['Please select a log file to view.'] || 'Please select a log file to view.'}</p></div>`;
            }

            // fetch live config from backend (Settings → Modular Settings)
            fetch('/system-logs/own/live-config/')
                .then(r=>r.json())
                .then(cfg=>{
                    liveEnabled = !!cfg.enabled;
                    liveIntervalSec = Math.max(2, parseInt(cfg.interval_sec || '10', 10));
                    applyLive();
                }).catch(()=>{ applyLive(); });
        }

        async function loadPage(category, filename, page){
            if (!filename){
                const container = document.getElementById('ownContainer');
                if (container) {
                    container.innerHTML = `<div class="empty-state"><i class="fas fa-file-alt"></i><h3>${window.jsTranslations['Select a File'] || 'Select a File'}</h3><p>${window.jsTranslations['Please select a log file to view.'] || 'Please select a log file to view.'}</p></div>`;
                }
                return;
            }
            const r = await fetch(`/system-logs/own/category/${encodeURIComponent(category)}/file/${encodeURIComponent(filename)}/?page=${page}&page_size=200`);
            const j = await r.json();
            const lines = j.lines || [];
            container.innerHTML = lines.length ? lines.map(l => `<div class="log-entry">${l}</div>`).join('') : `<div class="text-secondary">${window.jsTranslations['No content found.'] || 'No content found.'}</div>`;
            const total = j.total || 0;
            const size = j.page_size || 200;
            const maxPage = Math.max(Math.ceil(total / size), 1);
            const pager = document.createElement('div');
            pager.className = 'd-flex justify-content-between align-items-center mt-2';
            pager.innerHTML = `
                <span class="logs-meta">${total} ${window.jsTranslations['lines • Page'] || 'lines • Page'} ${page}/${maxPage}</span>
                <div style="display:flex; gap:8px;">
                    <button class="btn-secondary" ${page<=1?'disabled':''} id="ownPrev">${window.jsTranslations['Previous'] || 'Previous'}</button>
                    <button class="btn-secondary" ${page>=maxPage?'disabled':''} id="ownNext">${window.jsTranslations['Next'] || 'Next'}</button>
                </div>`;
            container.appendChild(pager);
            const prev = pager.querySelector('#ownPrev');
            const next = pager.querySelector('#ownNext');
            if (prev) prev.addEventListener('click', ()=> loadPage(category, filename, Math.max(page-1,1)));
            if (next) next.addEventListener('click', ()=> loadPage(category, filename, Math.min(page+1,maxPage)));
        }

        const initial = (categories && categories[0]) || null;
        if (initial){
            if (categorySelect) categorySelect.value = initial;
            selectCategory(initial);
        } else {
            container.innerHTML = `<div class="text-secondary">${window.jsTranslations['No categories found.'] || 'No categories found.'}</div>`;
        }
    }).catch(()=>{
        container.innerHTML = `<div class="text-secondary">${window.jsTranslations['Error occurred while fetching application logs.'] || 'Error occurred while fetching application logs.'}</div>`;
    });

    function applyLive(){
        if (liveTimer) { clearInterval(liveTimer); liveTimer = null; }
        if (!liveEnabled) return;
        const sec = liveIntervalSec || 10;
        liveTimer = setInterval(()=>{
            const cat = categorySelect ? categorySelect.value : '';
            const file = filesSelect ? filesSelect.value : '';
            if (!cat || !file) return;
            loadPage(cat, file, 1);
        }, sec * 1000);
    }
    function renderClientPager(allLines, page, pageSize){
        const container = document.getElementById('ownContainer');
        if (!container) {
            console.error('Container element not found');
            return;
        }
        
        const maxPage = Math.max(Math.ceil(allLines.length / pageSize), 1);
        const start = (page - 1) * pageSize;
        const end = Math.min(start + pageSize, allLines.length);
        
        const logHtml = allLines.slice(start, end).map((line, index) => {
            // Check if this is a file header
            if (line.startsWith('=== ') && line.endsWith(' ===')) {
                return `<div class="file-header">${escapeHtml(line)}</div>`;
            }
            return renderLogEntry(line, index);
        }).join('');
        
        container.innerHTML = logHtml;
        
        const pager = document.createElement('div');
        pager.className = 'pagination';
        pager.innerHTML = `
            <div class="pagination-info">
                <span class="logs-meta">${allLines.length} ${window.jsTranslations['lines • Page'] || 'lines • Page'} ${page}/${maxPage}</span>
            </div>
            <div class="pagination-controls">
                <button class="btn-secondary" ${page<=1?'disabled':''} id="ownPrevAll">${window.jsTranslations['Previous'] || 'Previous'}</button>
                <button class="btn-secondary" ${page>=maxPage?'disabled':''} id="ownNextAll">${window.jsTranslations['Next'] || 'Next'}</button>
            </div>`;
        container.appendChild(pager);
        
        const prev = pager.querySelector('#ownPrevAll');
        const next = pager.querySelector('#ownNextAll');
        if (prev) prev.addEventListener('click', ()=> renderClientPager(allLines, Math.max(page-1,1), pageSize));
        if (next) next.addEventListener('click', ()=> renderClientPager(allLines, Math.min(page+1,maxPage), pageSize));
    }
});


// Enhanced log entry rendering
function renderLogEntry(line, index) {
    // Detect log level and apply appropriate styling
    let logClass = 'log-entry';
    let levelIcon = '';
    
    if (line.includes('ERROR') || line.includes('CRITICAL') || line.includes('FATAL')) {
        logClass += ' error';
        levelIcon = '🔴';
    } else if (line.includes('WARNING') || line.includes('WARN')) {
        logClass += ' warning';
        levelIcon = '🟡';
    } else if (line.includes('INFO')) {
        logClass += ' info';
        levelIcon = '🔵';
    } else if (line.includes('DEBUG')) {
        logClass += ' debug';
        levelIcon = '🟣';
    }
    
    // Extract timestamp if present
    const timestampMatch = line.match(/(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/);
    const timestamp = timestampMatch ? timestampMatch[1] : '';
    
    // Format the line
    const formattedLine = escapeHtml(line);
    
    return `
        <div class="${logClass}" data-index="${index}">
            <div class="log-entry-header">
                <span class="log-timestamp">${timestamp}</span>
                <span class="log-level-icon">${levelIcon}</span>
            </div>
            <div class="log-content">${formattedLine}</div>
        </div>
    `;
}

// HTML escaping function
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


// Update log statistics
function updateLogStats(count) {
    const footer = document.querySelector('.logs-foot .logs-meta');
    if (footer) {
        footer.textContent = `${window.jsTranslations['Showing'] || 'Showing'} ${count} ${window.jsTranslations['log entries'] || 'log entries'}`;
    }
    
    const statsElement = document.getElementById('logStats');
    if (statsElement) {
        statsElement.textContent = `${count} ${window.jsTranslations['entries'] || 'entries'}`;
    }
    
    console.log('Updated log stats:', count);
}


