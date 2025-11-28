// CVE Tab - Container içi CVE taraması

// Ensure jsTranslations is available
if (typeof window.jsTranslations === 'undefined') {
    window.jsTranslations = {};
}

function loadCve() {
    // Sekme açıldığında henüz tarama yapılmadıysa sadece mevcut özet kalsın
    const summaryEl = document.getElementById('cveSummary');
    const resultsEl = document.getElementById('cveResults');

    if (!summaryEl || !resultsEl) {
        console.error('CVE elements not found');
        return;
    }

    // İlk açılışta herhangi bir şey yapmaya gerek yok; kullanıcı butona basınca tarama başlatılacak
}

function loadCveScan() {
    const summaryEl = document.getElementById('cveSummary');
    const resultsEl = document.getElementById('cveResults');

    if (!summaryEl || !resultsEl) {
        console.error('CVE elements not found');
        return;
    }

    const loadingMsg = window.jsTranslations['Loading CVE data...'] || 'Loading CVE data...';
    summaryEl.textContent = loadingMsg;
    resultsEl.innerHTML = '';

    // Container ID'yi mevcut global değişkenden veya URL'den al
    let containerId = typeof currentContainerId !== 'undefined' && currentContainerId
        ? currentContainerId
        : null;

    if (!containerId) {
        const pathParts = window.location.pathname.split('/');
        containerId = pathParts[pathParts.length - 2];
    }

    if (!containerId || containerId === 'null' || containerId === 'undefined') {
        const errorMsg = window.jsTranslations['Container ID not found'] || 'Container ID not found';
        summaryEl.textContent = errorMsg;
        return;
    }

    fetch(`/docker-manager/api/container/${containerId}/cve/scan/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (!body.success) {
                const errorPrefix = window.jsTranslations['Error'] || 'Error';
                const message = body.error || body.message || `HTTP ${status}`;
                summaryEl.textContent = `${errorPrefix}: ${message}`;
                return;
            }

            renderCveSummary(body, summaryEl);
            renderCveResults(body.matched || [], resultsEl);
        })
        .catch(error => {
            const errorPrefix = window.jsTranslations['Error'] || 'Error';
            summaryEl.textContent = `${errorPrefix}: ${error.message}`;
        });
}

function renderCveSummary(data, summaryEl) {
    const osType = data.os_type || 'unknown';
    const totalInstalled = data.total_installed || 0;
    const totalMatched = data.total_matched || 0;
    const totalAdvisories = data.total_advisories || 0;
    const matches = data.matched || [];

    if (totalMatched === 0) {
        const msg = window.jsTranslations['No vulnerabilities found'] || 'No vulnerabilities found';
        summaryEl.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <i class="fas fa-check-circle" style="color: #28a745; font-size: 20px;"></i>
                <div>
                    <strong style="color: #28a745;">${msg}</strong>
                    <div style="font-size: 13px; color: #718096; margin-top: 4px;">
                        OS: <strong>${osType}</strong> | Scanned packages: <strong>${totalInstalled}</strong>
                    </div>
                </div>
            </div>
        `;
        return;
    }

    // Paket bazında say
    const packageSet = new Set();
    matches.forEach(m => {
        if (m.package) packageSet.add(m.package);
    });
    const affectedPackages = packageSet.size;

    // Severity dağılımı
    const severityCounts = { critical: 0, high: 0, medium: 0, low: 0, unknown: 0 };
    matches.forEach(m => {
        const s = (m.severity || 'unknown').toLowerCase();
        if (severityCounts.hasOwnProperty(s)) {
            severityCounts[s]++;
        } else {
            severityCounts.unknown++;
        }
    });

    const severityBadges = [];
    if (severityCounts.critical > 0) {
        severityBadges.push(`<span style="background: #dc3545; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">CRITICAL: ${severityCounts.critical}</span>`);
    }
    if (severityCounts.high > 0) {
        severityBadges.push(`<span style="background: #fd7e14; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">HIGH: ${severityCounts.high}</span>`);
    }
    if (severityCounts.medium > 0) {
        severityBadges.push(`<span style="background: #ffc107; color: #1a202c; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">MEDIUM: ${severityCounts.medium}</span>`);
    }
    if (severityCounts.low > 0) {
        severityBadges.push(`<span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">LOW: ${severityCounts.low}</span>`);
    }

    summaryEl.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <i class="fas fa-exclamation-triangle" style="color: #dc3545; font-size: 24px;"></i>
            <div style="flex: 1;">
                <strong style="color: #dc3545; font-size: 16px;">${totalMatched} CVE${totalMatched > 1 ? 's' : ''} found</strong>
                <div style="font-size: 13px; color: #718096; margin-top: 4px;">
                    OS: <strong>${osType}</strong> | Affected packages: <strong>${affectedPackages}</strong> / ${totalInstalled} | Unique advisories: <strong>${totalAdvisories}</strong>
                </div>
            </div>
        </div>
        ${severityBadges.length > 0 ? `<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px;">${severityBadges.join('')}</div>` : ''}
    `;
}

function renderCveResults(matches, resultsEl) {
    if (!matches || matches.length === 0) {
        resultsEl.innerHTML = '';
        return;
    }

    // Paket bazında grupla
    const byPackage = {};
    matches.forEach(match => {
        const pkgName = match.package || 'unknown';
        if (!byPackage[pkgName]) {
            byPackage[pkgName] = {
                installed_version: match.installed_version || '',
                items: [],
            };
        }
        byPackage[pkgName].items.push(match);
    });

    let html = '<div class="cve-list">';

    // Paketleri alfabetik sırala
    Object.keys(byPackage).sort().forEach(pkgName => {
        const group = byPackage[pkgName];
        const installed = escapeHtml(group.installed_version || '');
        const count = group.items.length;

        // En kritik seviyesi bul
        const severitiesOrder = ['critical', 'high', 'medium', 'low', 'unknown'];
        let maxSeverity = '';
        group.items.forEach(m => {
            const s = (m.severity || '').toLowerCase();
            if (!s) return;
            if (!maxSeverity) {
                maxSeverity = s;
            } else {
                const sIdx = severitiesOrder.indexOf(s);
                const maxIdx = severitiesOrder.indexOf(maxSeverity);
                if (sIdx !== -1 && (maxIdx === -1 || sIdx < maxIdx)) {
                    maxSeverity = s;
                }
            }
        });

        const severityLabel = maxSeverity ? maxSeverity.toUpperCase() : '';
        const uniqueId = `pkg-${pkgName.replace(/[^a-zA-Z0-9]/g, '-')}`;

        html += `
            <div class="cve-package-group" data-package="${escapeHtml(pkgName)}">
                <div class="cve-package-header" onclick="toggleCvePackage('${uniqueId}')">
                    <div class="cve-package-info">
                        <div class="cve-package-name-main">
                            <i class="fas fa-box"></i>
                            <span class="cve-package-name">${escapeHtml(pkgName)}</span>
                            ${severityLabel ? `<span class="cve-severity-badge severity-${maxSeverity}">${severityLabel}</span>` : ''}
                        </div>
                        <div class="cve-package-meta">
                            <span class="cve-version-info">v${installed}</span>
                            <span class="cve-count-badge">${count} CVE${count > 1 ? 's' : ''}</span>
                        </div>
                    </div>
                    <div class="cve-package-toggle">
                        <i class="fas fa-chevron-down toggle-icon" id="icon-${uniqueId}"></i>
                    </div>
                </div>
                <div class="cve-package-body" id="${uniqueId}" style="display: none;">
        `;

        group.items.forEach((match, idx) => {
            const advisory = escapeHtml(match.advisory || '');
            const affected = escapeHtml(match.affected || '');
            const fixed = escapeHtml(match.fixed || '');
            const severity = escapeHtml(match.severity || '');
            const status = escapeHtml(match.status || '');
            const description = escapeHtml(match.description || '');

            html += `
                <div class="cve-entry">
                    <div class="cve-entry-header">
                        <div class="cve-advisory-name">${advisory}</div>
                        <div class="cve-entry-badges">
                            ${severity ? `<span class="cve-severity-tag severity-${(severity || '').toLowerCase()}">${severity}</span>` : ''}
                            ${status ? `<span class="cve-status-tag status-${(status || '').toLowerCase()}">${status}</span>` : ''}
                        </div>
                    </div>
                    <div class="cve-entry-details">
                        ${affected ? `<div class="cve-detail-item"><span class="cve-detail-label">Affected:</span> <span class="cve-detail-value">${affected}</span></div>` : ''}
                        ${fixed ? `<div class="cve-detail-item"><span class="cve-detail-label">Fixed:</span> <span class="cve-detail-value fixed-version">${fixed}</span></div>` : ''}
                        ${description ? `<div class="cve-description">${description}</div>` : ''}
                    </div>
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;
    });

    html += '</div>';
    resultsEl.innerHTML = html;
}

function toggleCvePackage(uniqueId) {
    const body = document.getElementById(uniqueId);
    const icon = document.getElementById(`icon-${uniqueId}`);
    
    if (!body || !icon) return;
    
    if (body.style.display === 'none') {
        body.style.display = 'block';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
    } else {
        body.style.display = 'none';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
    }
}

function escapeHtml(text) {
    if (text === null || text === undefined) {
        return '';
    }
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}


