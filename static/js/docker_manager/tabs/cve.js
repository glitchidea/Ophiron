// CVE Tab - In-container CVE scanning

// Ensure jsTranslations is available
if (typeof window.jsTranslations === 'undefined') {
    window.jsTranslations = {};
}

function loadCve() {
    // Show i18n-compatible message when tab is opened if scan hasn't been run yet
    const summaryEl = document.getElementById('cveSummary');
    const resultsEl = document.getElementById('cveResults');

    if (!summaryEl || !resultsEl) {
        console.error('CVE elements not found');
        return;
    }

    // If scan hasn't been run yet (only contains text, no HTML), show i18n-compatible message
    // Message from template may be translated by Django {% trans %}, but if still in English
    // translate using window.jsTranslations from JavaScript
    if (summaryEl.children.length === 0) {
        // Only contains text, scan hasn't been run yet
        const currentText = summaryEl.textContent.trim();
        const translatedMessage = window.jsTranslations['No CVE scan has been run yet.'];
        
        // If translation exists in window.jsTranslations and message is in English, translate
        if (translatedMessage && translatedMessage !== 'No CVE scan has been run yet.') {
            // If message is in English (Django didn't translate), translate from JavaScript
            if (currentText === 'No CVE scan has been run yet.') {
                summaryEl.textContent = translatedMessage;
            }
        }
    }
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

    // Get container ID from current global variable or URL
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
    const warning = data.warning || null; // Backward compatibility
    // For SUSE containers: Backend shell check may not be reliable
    // Therefore always show warning for SUSE containers (even if shell is available)
    // Because CVE scanning without shell may produce incomplete/incorrect results
    const shellAvailable = data.shell_available !== undefined ? data.shell_available : true;
    
    // Debug: Check shell status for SUSE containers
    if (osType === 'suse') {
        console.log('SUSE Container CVE Scan Debug:', {
            osType: osType,
            shellAvailable: shellAvailable,
            shellAvailableType: typeof shellAvailable,
            shellAvailableValue: data.shell_available,
            shellAvailableUndefined: data.shell_available === undefined,
            totalMatched: totalMatched,
            data: data
        });
    }

    // For SUSE containers: Show warning when CVE is found
    // Backend shell check may not be reliable, so always show warning
    // CVE scanning without shell may produce incomplete/incorrect results
    if (osType === 'suse' && totalMatched > 0) {
        const warningMsg = window.jsTranslations['Warning'] || 'Warning';
        const warningText = window.jsTranslations['SUSE_SHELL_WARNING_MESSAGE'] || 
                           window.jsTranslations['SUSE Shell Warning Message'] || 
                           '⚠️ Shell access is not available. SUSE/openSUSE containers require shell access for CVE scanning. Scanning without shell may produce incomplete or incorrect results. Please run the container with shell access or use alternative methods.';
        
        // CVE found, show warning as a separate section
        const warningHtml = `
            <div style="display: flex; align-items: flex-start; gap: 12px; padding: 16px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; margin-bottom: 12px;">
                <i class="fas fa-exclamation-triangle" style="color: #ffc107; font-size: 24px; margin-top: 2px;"></i>
                <div style="flex: 1;">
                    <strong style="color: #856404; font-size: 16px; display: block; margin-bottom: 8px;">${warningMsg}</strong>
                    <div style="font-size: 14px; color: #856404; line-height: 1.5;">
                        ${escapeHtml(warningText)}
                    </div>
                    <div style="font-size: 13px; color: #856404; margin-top: 8px; padding-top: 8px; border-top: 1px solid #ffc107;">
                        ${window.jsTranslations['OS'] || 'OS'}: <strong>${osType}</strong> | ${window.jsTranslations['Scanned packages'] || 'Scanned packages'}: <strong>${totalInstalled}</strong>
                    </div>
                </div>
            </div>
        `;
        // Add warning to summary, then show normal results
        summaryEl.innerHTML = warningHtml;
        // Continue rendering normal results (don't return)
    } else if (warning) {
        // Backward compatibility: If old warning message exists (as string)
        const warningMsg = window.jsTranslations['Warning'] || 'Warning';
        summaryEl.innerHTML = `
            <div style="display: flex; align-items: flex-start; gap: 12px; padding: 16px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; margin-bottom: 12px;">
                <i class="fas fa-exclamation-triangle" style="color: #ffc107; font-size: 24px; margin-top: 2px;"></i>
                <div style="flex: 1;">
                    <strong style="color: #856404; font-size: 16px; display: block; margin-bottom: 8px;">${warningMsg}</strong>
                    <div style="font-size: 14px; color: #856404; line-height: 1.5;">
                        ${escapeHtml(warning)}
                    </div>
                    <div style="font-size: 13px; color: #856404; margin-top: 8px; padding-top: 8px; border-top: 1px solid #ffc107;">
                        ${window.jsTranslations['OS'] || 'OS'}: <strong>${osType}</strong> | ${window.jsTranslations['Scanned packages'] || 'Scanned packages'}: <strong>${totalInstalled}</strong>
                    </div>
                </div>
            </div>
        `;
        return;
    }

    if (totalMatched === 0) {
        const msg = window.jsTranslations['No vulnerabilities found'] || 'No vulnerabilities found';
        const osLabel = window.jsTranslations['OS'] || 'OS';
        const scannedPackagesLabel = window.jsTranslations['Scanned packages'] || 'Scanned packages';
        
        // For SUSE containers: Always show warning
        // Backend shell check may not be reliable, so always show warning
        if (osType === 'suse') {
            // CVE scanning without shell in SUSE containers may produce incomplete results
            // In this case we should warn the user
            const warningMsg = window.jsTranslations['Warning'] || 'Warning';
            const suseWarningMsg = window.jsTranslations['SUSE_SHELL_WARNING_MESSAGE'] || 
                window.jsTranslations['SUSE Shell Warning Message'] || 
                window.jsTranslations['SUSE Shell Warning'] || 
                '⚠️ Shell access is not available. SUSE/openSUSE containers require shell access for CVE scanning. Scanning without shell may produce incomplete or incorrect results. Please run the container with shell access or use alternative methods.';
            
            summaryEl.innerHTML = `
                <div style="display: flex; align-items: flex-start; gap: 12px; padding: 16px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; margin-bottom: 12px;">
                    <i class="fas fa-exclamation-triangle" style="color: #ffc107; font-size: 24px; margin-top: 2px;"></i>
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <i class="fas fa-check-circle" style="color: #28a745; font-size: 20px;"></i>
                            <strong style="color: #28a745; font-size: 16px;">${msg}</strong>
                        </div>
                        <div style="font-size: 13px; color: #718096; margin-bottom: 12px;">
                            ${osLabel}: <strong>${osType}</strong> | ${scannedPackagesLabel}: <strong>${totalInstalled}</strong>
                        </div>
                        <div style="padding-top: 12px; border-top: 1px solid #ffc107; margin-top: 12px;">
                            <strong style="color: #856404; font-size: 14px; display: block; margin-bottom: 6px;">
                                <i class="fas fa-exclamation-triangle" style="margin-right: 6px;"></i>${warningMsg}
                            </strong>
                            <div style="font-size: 13px; color: #856404; line-height: 1.5;">
                                ${escapeHtml(suseWarningMsg)}
                            </div>
                        </div>
                    </div>
                </div>
            `;
            return;
        }
        
        summaryEl.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <i class="fas fa-check-circle" style="color: #28a745; font-size: 20px;"></i>
                <div>
                    <strong style="color: #28a745;">${msg}</strong>
                    <div style="font-size: 13px; color: #718096; margin-top: 4px;">
                        ${osLabel}: <strong>${osType}</strong> | ${scannedPackagesLabel}: <strong>${totalInstalled}</strong>
                    </div>
                </div>
            </div>
        `;
        return;
    }

    // Count by package
    const packageSet = new Set();
    matches.forEach(m => {
        if (m.package) packageSet.add(m.package);
    });
    const affectedPackages = packageSet.size;

    // Severity distribution
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

    // If shell is not available in SUSE containers and CVE is found, add warning above CVE results
    let warningHtml = '';
    if (osType === 'suse' && !shellAvailable) {
        const warningMsg = window.jsTranslations['Warning'] || 'Warning';
        const warningText = window.jsTranslations['SUSE_SHELL_WARNING_MESSAGE'] || 
                           window.jsTranslations['SUSE Shell Warning Message'] || 
                           '⚠️ Shell access is not available. SUSE/openSUSE containers require shell access for CVE scanning. Scanning without shell may produce incomplete or incorrect results. Please run the container with shell access or use alternative methods.';
        
        warningHtml = `
            <div style="display: flex; align-items: flex-start; gap: 12px; padding: 16px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; margin-bottom: 12px;">
                <i class="fas fa-exclamation-triangle" style="color: #ffc107; font-size: 24px; margin-top: 2px;"></i>
                <div style="flex: 1;">
                    <strong style="color: #856404; font-size: 16px; display: block; margin-bottom: 8px;">${warningMsg}</strong>
                    <div style="font-size: 14px; color: #856404; line-height: 1.5;">
                        ${escapeHtml(warningText)}
                    </div>
                    <div style="font-size: 13px; color: #856404; margin-top: 8px; padding-top: 8px; border-top: 1px solid #ffc107;">
                        ${window.jsTranslations['OS'] || 'OS'}: <strong>${osType}</strong> | ${window.jsTranslations['Scanned packages'] || 'Scanned packages'}: <strong>${totalInstalled}</strong>
                    </div>
                </div>
            </div>
        `;
    }

    // i18n-compatible CVE count message
    const cveFoundMsg = totalMatched === 1 
        ? `${totalMatched} ${window.jsTranslations['CVE found'] || 'CVE found'}`
        : `${totalMatched} ${window.jsTranslations['CVEs found'] || 'CVEs found'}`;
    
    summaryEl.innerHTML = warningHtml + `
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <i class="fas fa-exclamation-triangle" style="color: #dc3545; font-size: 24px;"></i>
            <div style="flex: 1;">
                <strong style="color: #dc3545; font-size: 16px;">${cveFoundMsg}</strong>
                <div style="font-size: 13px; color: #718096; margin-top: 4px;">
                    ${window.jsTranslations['OS'] || 'OS'}: <strong>${osType}</strong> | ${window.jsTranslations['Affected packages'] || 'Affected packages'}: <strong>${affectedPackages}</strong> / ${totalInstalled} | ${window.jsTranslations['Unique advisories'] || 'Unique advisories'}: <strong>${totalAdvisories}</strong>
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

    // Group by package
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

    // Sort packages alphabetically
    Object.keys(byPackage).sort().forEach(pkgName => {
        const group = byPackage[pkgName];
        const installed = escapeHtml(group.installed_version || '');
        const count = group.items.length;

        // Find the most critical severity level
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
                            <span class="cve-count-badge">${count} ${count === 1 ? (window.jsTranslations['CVE'] || 'CVE') : (window.jsTranslations['CVEs'] || 'CVEs')}</span>
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
                        ${affected ? `<div class="cve-detail-item"><span class="cve-detail-label">${window.jsTranslations['Affected:'] || 'Affected:'}</span> <span class="cve-detail-value">${affected}</span></div>` : ''}
                        ${fixed ? `<div class="cve-detail-item"><span class="cve-detail-label">${window.jsTranslations['Fixed:'] || 'Fixed:'}</span> <span class="cve-detail-value fixed-version">${fixed}</span></div>` : ''}
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


