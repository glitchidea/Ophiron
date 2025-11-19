async function fetchJSON(url) {
  const res = await fetch(url, { credentials: 'same-origin' });
  if (!res.ok) throw new Error('Request failed');
  return await res.json();
}

function escapeHtml(text){ const d=document.createElement('div'); d.textContent=text; return d.innerHTML; }

async function loadSummary(forceRefresh = false) {
  const scope = 'global';
  const refreshParam = forceRefresh ? '&refresh=true' : '';
  const data = await fetchJSON(`/dev-packages/api/summary/?scope=${encodeURIComponent(scope)}${refreshParam}`);
  const sel = document.getElementById('devManagerFilter');
  if (sel) {
    const managers = Object.keys(data.managers || {});
    sel.innerHTML = `<option value="">${window.jsTranslations?.all || 'All'}</option>` + managers.map(m => `<option value="${m}">${m}</option>`).join('');
  }
  const wrap = document.getElementById('devManagerSummary');
  if (wrap) {
    const entries = Object.entries(data.managers || {});
    wrap.innerHTML = entries.length ? entries.map(([m, info]) => `
      <div class="pkg-mgr-card" data-manager="${m}">
        <div class="mgr-name">${m}</div>
        <div>
          <span class="mgr-count">${info.installed || 0}</span>
        </div>
      </div>
    `).join('') : `<div class="empty-state">${window.jsTranslations?.no_managers_found || 'No managers found'}</div>`;
  }
}

function getCveBadge(cveCount, severity) {
  if (!cveCount || cveCount === 0) {
    return '<span class="cve-badge cve-safe" title="No known vulnerabilities"><i class="fas fa-shield-alt"></i> Safe</span>';
  }
  
  // Determine badge color based on highest severity
  let badgeClass = 'cve-medium';
  let severityText = 'Medium';
  
  if (severity) {
    if (severity.CRITICAL || severity.HIGH) {
      badgeClass = 'cve-critical';
      severityText = severity.CRITICAL ? 'Critical' : 'High';
    } else if (severity.MEDIUM) {
      badgeClass = 'cve-medium';
      severityText = 'Medium';
    } else if (severity.LOW) {
      badgeClass = 'cve-low';
      severityText = 'Low';
    }
  }
  
  return `<span class="cve-badge ${badgeClass}" title="${cveCount} vulnerability/vulnerabilities found"><i class="fas fa-exclamation-triangle"></i> ${cveCount} CVE${cveCount > 1 ? 's' : ''}</span>`;
}

async function loadInstalled(forceRefresh = false) {
  const scope = 'global';
  const refreshParam = forceRefresh ? '&refresh=true' : '';
  const [installedData, updatesData] = await Promise.all([
    fetchJSON(`/dev-packages/api/installed/?scope=${encodeURIComponent(scope)}${refreshParam}&cves=true`),
    fetchJSON(`/dev-packages/api/updates/?scope=${encodeURIComponent(scope)}${refreshParam}`)
  ]);
  
  const tbody = document.getElementById('devPkgTbody');
  const rows = [];
  const managerFilter = document.getElementById('devManagerFilter')?.value || '';
  const searchFilter = document.getElementById('devSearch')?.value || '';
  
  // Create updates lookup map
  const updatesMap = {};
  if (updatesData && updatesData.data) {
    for (const [manager, updates] of Object.entries(updatesData.data)) {
      updatesMap[manager] = {};
      (updates || []).forEach(update => {
        updatesMap[manager][update.name] = update;
      });
    }
  }
  
  for (const [m, arr] of Object.entries(installedData || {})) {
    if (managerFilter && m !== managerFilter) continue;
    (arr || []).forEach(pkg => {
      // Apply search filter
      if (searchFilter) {
        const searchTerm = searchFilter.toLowerCase();
        const packageText = `${pkg.name} ${pkg.version || ''}`.toLowerCase();
        if (!packageText.includes(searchTerm)) return;
      }
      
      const update = updatesMap[m]?.[pkg.name];
      const updateIndicator = update ? 
        `<sup class="update-indicator ${update.critical ? 'critical' : 'normal'}">${update.critical ? '!' : '↑'}</sup>` : '';
      
      // Get CVE information
      const cveCount = pkg.cve_count || 0;
      const cveSeverity = pkg.cve_severity || {};
      const cveBadge = getCveBadge(cveCount, cveSeverity);
      
      rows.push(`<tr>
        <td>${escapeHtml(pkg.name)}</td>
        <td>${escapeHtml(pkg.version || '')}${updateIndicator}</td>
        <td>${m}</td>
        <td>${cveBadge}</td>
        <td><button class="btn-action details" data-manager="${m}" data-name="${escapeHtml(pkg.name)}" data-version="${escapeHtml(pkg.version || '')}">${window.jsTranslations?.details || 'Details'}</button></td>
      </tr>`);
    });
  }
  tbody.innerHTML = rows.length ? rows.join('') : `<tr><td colspan="5" class="empty-state"><i class="fas fa-inbox"></i><span>${window.jsTranslations?.no_results || 'No results'}</span></td></tr>`;
  // bind details buttons
  tbody.querySelectorAll('.btn-action.details').forEach(btn => {
    btn.addEventListener('click', async () => {
      const m = btn.getAttribute('data-manager');
      const n = btn.getAttribute('data-name');
      const v = btn.getAttribute('data-version');
      await openDetail(m, n, v);
    });
  });
}


document.addEventListener('DOMContentLoaded', async () => {
  document.getElementById('refreshDevBtn')?.addEventListener('click', async () => { 
    const btn = document.getElementById('refreshDevBtn');
    const icon = btn?.querySelector('i');
    if (btn) btn.disabled = true;
    if (icon) icon.classList.add('fa-spin');
    try {
      await loadSummary(true);  // Force refresh
      await loadInstalled(true);  // Force refresh
    } catch (e) {
      console.error('Refresh error:', e);
    } finally {
      if (icon) icon.classList.remove('fa-spin');
      if (btn) btn.disabled = false;
    }
  });
  document.getElementById('devManagerFilter')?.addEventListener('change', async () => { await loadInstalled(); });
  document.getElementById('devSearch')?.addEventListener('input', async () => { await loadInstalled(); });
  // enable overlay click + ESC to close modals
  setupModalDismiss('devPkgDetailModal');
  await loadSummary();
  await loadInstalled();
});

async function openDetail(manager, name, version = '') {
  const scope = 'global';
  try {
    // Always try to fetch CVE data if version is available
    const cveUrl = version ? `/dev-packages/api/cves/${encodeURIComponent(manager)}/${encodeURIComponent(name)}/?version=${encodeURIComponent(version)}` : null;
    
    const [data, cveData] = await Promise.all([
      fetchJSON(`/dev-packages/api/detail/${encodeURIComponent(manager)}/${encodeURIComponent(name)}/?scope=${encodeURIComponent(scope)}`),
      cveUrl ? fetchJSON(cveUrl).catch(err => {
        console.error('CVE fetch error:', err);
        return {success: false, error: err.message};
      }) : Promise.resolve({success: false, error: 'No version provided'})
    ]);
    
    // Debug log
    console.log('CVE Data:', cveData);
    
    document.getElementById('devPkgDetailTitle').textContent = `${name} - ${window.jsTranslations?.details || 'Details'}`;
    const tbody = document.getElementById('devPkgInfoTbody');
    if (tbody) {
      const fields = data.fields || {};
      const show = [
        [window.jsTranslations?.manager || 'Manager', manager],
        [window.jsTranslations?.package || 'Package', data.name || name],
        [window.jsTranslations?.version || 'Version', fields.Version || fields.version || version || ''],
        [window.jsTranslations?.description || 'Description', fields.Description || fields.description || ''],
        [window.jsTranslations?.homepage || 'Homepage', fields.Homepage || fields.homepage || ''],
        [window.jsTranslations?.license || 'License', fields.License || fields.license || ''],
      ];
      tbody.innerHTML = show
        .filter(([, v]) => v && String(v).trim())
        .map(([k, v]) => `<tr><td>${k}</td><td>${escapeHtml(String(v))}</td></tr>`)
        .join('');
    }
    const depsEl = document.getElementById('devPkgDeps');
    if (depsEl) {
      const deps = data.dependencies || [];
      depsEl.innerHTML = deps.length ? deps.map(d => `<span class=\"badge\">${escapeHtml(d)}</span>`).join('') : `<span style=\"color:#718096;\">${window.jsTranslations?.no_dependencies || 'No dependencies'}</span>`;
    }
    
    // Show CVE information if available
    const cveEl = document.getElementById('devPkgCves');
    if (cveEl) {
      // Debug: log CVE data
      console.log('CVE Element found:', !!cveEl);
      console.log('CVE Data success:', cveData.success);
      console.log('CVE Data cves:', cveData.cves);
      console.log('CVE Data length:', cveData.cves?.length);
      
      if (cveData && cveData.success && cveData.cves && cveData.cves.length > 0) {
        const cves = cveData.cves;
        // Debug: log full CVE object
        console.log('Full CVE objects:', JSON.stringify(cves, null, 2));
        
        let cveHtml = '<div class="cve-list">';
        cves.forEach((cve, idx) => {
          console.log(`CVE ${idx + 1} full data:`, cve);
          const severity = cve.severity || 'UNKNOWN';
          const severityClass = severity.toLowerCase();
          const aliases = cve.aliases || [];
          const cveId = aliases.find(a => a.startsWith('CVE-')) || cve.id || 'N/A';
          // Use summary if available, otherwise use details (first 200 chars)
          const hasSummary = cve.summary && cve.summary.trim();
          const hasDetails = cve.details && cve.details.trim();
          const summary = hasSummary ? cve.summary : (hasDetails ? cve.details.substring(0, 200) + (cve.details.length > 200 ? '...' : '') : 'No information available');
          const fullDetails = hasDetails ? cve.details : '';
          const cvssVector = cve.cvss_vector || '';
          const cvssScore = cve.cvss_score || null;
          const published = cve.published || '';
          const modified = cve.modified || '';
          
          // Format dates
          let publishedDate = '';
          if (published) {
            try {
              const date = new Date(published);
              publishedDate = date.toLocaleDateString();
            } catch (e) {}
          }
          
          let modifiedDate = '';
          if (modified) {
            try {
              const date = new Date(modified);
              modifiedDate = date.toLocaleDateString();
            } catch (e) {}
          }
          
          cveHtml += `
            <div class="cve-item cve-${severityClass}">
              <div class="cve-header">
                <div class="cve-id-section">
                  <span class="cve-id">${escapeHtml(cveId)}</span>
                  ${cve.id && cve.id !== cveId ? `<span class="cve-alias">${escapeHtml(cve.id)}</span>` : ''}
                </div>
                <span class="cve-severity cve-${severityClass}">${escapeHtml(severity)}</span>
              </div>
              ${publishedDate ? `<div class="cve-meta"><i class="fas fa-calendar"></i> Published: ${escapeHtml(publishedDate)}</div>` : ''}
              ${modifiedDate && modifiedDate !== publishedDate ? `<div class="cve-meta"><i class="fas fa-edit"></i> Modified: ${escapeHtml(modifiedDate)}</div>` : ''}
              ${summary ? `<div class="cve-summary">${escapeHtml(summary)}</div>` : ''}
              ${fullDetails && fullDetails.length > (hasSummary ? 200 : 0) ? `
                <div class="cve-details">
                  <strong>Full Details:</strong><br>
                  ${escapeHtml(fullDetails)}
                </div>
              ` : ''}
              ${cvssVector ? `
                <div class="cve-cvss">
                  ${cvssScore ? `<div class="cve-score"><strong>CVSS Base Score:</strong> <span class="cvss-score-value cvss-${severityClass}">${cvssScore}</span> (${escapeHtml(severity)})</div>` : ''}
                  <div class="cve-vector"><strong>CVSS Vector:</strong> <code>${escapeHtml(cvssVector)}</code></div>
                </div>
              ` : ''}
              ${cve.references && cve.references.length > 0 ? `
                <div class="cve-references">
                  <strong>References:</strong>
                  ${cve.references.map(ref => 
                    `<a href="${escapeHtml(ref.url || '')}" target="_blank" rel="noopener" title="${escapeHtml(ref.url || '')}">
                      <i class="fas fa-external-link-alt"></i> ${escapeHtml(ref.type || 'Reference')}
                    </a>`
                  ).join(' ')}
                </div>
              ` : ''}
            </div>
          `;
        });
        cveHtml += '</div>';
        cveEl.innerHTML = cveHtml;
      } else {
        cveEl.innerHTML = `<span style="color:#718096;"><i class="fas fa-shield-alt"></i> ${window.jsTranslations?.no_cves || 'No known vulnerabilities'}</span>`;
      }
    }
    
    document.getElementById('devPkgDetailModal').style.display = 'flex';
  } catch (e) {
    console.error('Error loading detail:', e);
    document.getElementById('devPkgDetailTitle').textContent = `${name} - ${window.jsTranslations?.details || 'Details'}`;
    document.getElementById('devPkgInfoTbody').innerHTML = `<tr><td>${window.jsTranslations?.manager || 'Manager'}</td><td>${manager}</td></tr>`;
    document.getElementById('devPkgDeps').innerHTML = `<span style=\"color:#718096;\">${window.jsTranslations?.no_data || 'No data'}</span>`;
    const cveEl = document.getElementById('devPkgCves');
    if (cveEl) {
      cveEl.innerHTML = `<span style="color:#718096;">${window.jsTranslations?.cve_error || 'Error loading CVE data'}</span>`;
    }
    document.getElementById('devPkgDetailModal').style.display = 'flex';
  }
}

function setupModalDismiss(id){
  const el = document.getElementById(id);
  if (!el) return;
  // click outside content
  el.addEventListener('click', (e) => {
    if (e.target === el) el.style.display = 'none';
  });
  // ESC key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && el.style.display === 'flex') el.style.display = 'none';
  });
}


