async function fetchJSON(url) {
  const res = await fetch(url, { credentials: 'same-origin' });
  if (!res.ok) throw new Error('Request failed');
  return await res.json();
}

function h(el, attrs = {}, children = []) {
  const e = document.createElement(el);
  Object.entries(attrs).forEach(([k, v]) => {
    if (k === 'class') e.className = v; else e.setAttribute(k, v);
  });
  children.forEach(c => {
    if (typeof c === 'string') e.appendChild(document.createTextNode(c)); else e.appendChild(c);
  });
  return e;
}

async function loadSummary() {
  const data = await fetchJSON('/package-manager/api/summary/');
  document.getElementById('statTotalUpdates').textContent = data.total_updates ?? '-';
  const critical = Object.values(data.managers || {}).reduce((a, v) => a + (v.critical || 0), 0);
  document.getElementById('statCritical').textContent = critical;
  document.getElementById('statManagers').textContent = Object.keys(data.managers || {}).length;
  populateManagerFilter(Object.keys(data.managers || {}));
  // render per-manager cards
  const wrap = document.getElementById('managerSummary');
  if (wrap) {
    const entries = Object.entries(data.managers || {});
    wrap.innerHTML = entries.length ? entries.map(([m, info]) => `
      <div class="pkg-mgr-card" data-manager="${m}">
        <div class="mgr-name">${m}</div>
        <div>
          <span class="mgr-count">${info.count || 0}</span>
          ${info.critical ? `<span class="mgr-critical">${info.critical}</span>` : ''}
        </div>
      </div>
    `).join('') : `<div class="empty-state">${window.jsTranslations?.no_managers_found || 'No managers found'}</div>`;
    // click to open updates modal for that manager
    wrap.querySelectorAll('.pkg-mgr-card').forEach(card => {
      card.addEventListener('click', async () => {
        const m = card.getAttribute('data-manager');
        await loadUpdates();
        renderUpdatesList(false, m);
        populateUpdatesManagerFilter(m);
        document.getElementById('updatesModal').style.display = 'flex';
      });
    });
  }
}

let INSTALLED_CACHE = {};
let CURRENT_FILTER = { manager: '', search: '' };
let UPDATES_CACHE = {};

function populateManagerFilter(managers) {
  const sel = document.getElementById('managerFilter');
  sel.innerHTML = `<option value="">${window.jsTranslations?.all || 'All'}</option>` + managers.map(m => `<option value="${m}">${m}</option>`).join('');
}

async function loadInstalled() {
  const data = await fetchJSON('/package-manager/api/installed/');
  INSTALLED_CACHE = data;
  renderTable();
}

function renderTable() {
  const tbody = document.getElementById('pkgTableBody');
  const rows = [];
  const managers = Object.keys(INSTALLED_CACHE || {});
  managers.forEach(m => {
    if (CURRENT_FILTER.manager && CURRENT_FILTER.manager !== m) return;
    (INSTALLED_CACHE[m] || []).forEach(pkg => {
      if (CURRENT_FILTER.search) {
        const s = CURRENT_FILTER.search.toLowerCase();
        const t = `${pkg.name} ${pkg.version || ''}`.toLowerCase();
        if (!t.includes(s)) return;
      }
      const upd = (UPDATES_CACHE[m] || []).find(u => u.name === pkg.name);
      const updateClass = upd ? (upd.critical ? 'sup-update crit' : 'sup-update norm') : '';
      const versionCell = `${pkg.version || ''}${upd ? ` <sup class=\"${updateClass}\" title=\"${window.jsTranslations?.update_available || 'Update available'}\" data-manager=\"${m}\" data-name=\"${pkg.name}\">●</sup>` : ''}`;
      rows.push(`
        <tr>
          <td><span class="pkg-name">${pkg.name}</span></td>
          <td class="pkg-ver">${versionCell}</td>
          <td>${m}</td>
          <td><button class="btn-action details" data-manager="${m}" data-name="${pkg.name}"><i class="fas fa-info"></i> ${window.jsTranslations?.details || 'Details'}</button></td>
        </tr>
      `);
    });
  });
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-state"><i class="fas fa-inbox"></i><span>${window.jsTranslations?.no_results_found || 'No results found'}</span></td></tr>`;
  } else {
    tbody.innerHTML = rows.join('');
  }
  // bind actions
  document.querySelectorAll('.btn-action.details').forEach(el => {
    el.addEventListener('click', async (e) => {
      e.preventDefault();
      const manager = el.getAttribute('data-manager');
      const name = el.getAttribute('data-name');
      await loadDetail(manager, name);
    });
  });
  // bind update superscripts to open updates modal filtered
  document.querySelectorAll('sup.sup-update').forEach(s => {
    s.addEventListener('click', async (e) => {
      e.stopPropagation();
      const m = s.getAttribute('data-manager');
      await loadUpdates();
      renderUpdatesList(false, m);
      populateUpdatesManagerFilter(m);
      document.getElementById('updatesModal').style.display = 'flex';
    });
  });
}

async function loadDetail(manager, name) {
  const data = await fetchJSON(`/package-manager/api/detail/${encodeURIComponent(manager)}/${encodeURIComponent(name)}/`);
  document.getElementById('pkgDetailTitle').textContent = `${name} - ${window.jsTranslations?.details || 'Details'}`;
  const tbody = document.querySelector('#pkgInfoTable tbody');
  if (tbody) {
    const fields = data.fields || {};
    const show = [
      [window.jsTranslations?.manager || 'Manager', manager],
      [window.jsTranslations?.package || 'Package', data.name || name],
      [window.jsTranslations?.version || 'Version', fields.Version || fields['Installed Version'] || fields['Current Version'] || ''],
      [window.jsTranslations?.architecture || 'Architecture', fields.Architecture || fields.Arch || ''],
      [window.jsTranslations?.description || 'Description', fields.Description || fields.Summary || ''],
      [window.jsTranslations?.homepage || 'Homepage', fields.Homepage || fields.URL || ''],
      [window.jsTranslations?.license || 'License', fields.License || fields.Licenses || ''],
      [window.jsTranslations?.repository || 'Repository', fields.Repository || fields['APT-Sources'] || fields['From'] || ''],
      [window.jsTranslations?.maintainer || 'Maintainer', fields.Maintainer || fields['Packager'] || ''],
    ];
    tbody.innerHTML = show
      .filter(([, v]) => v && String(v).trim())
      .map(([k, v]) => `<tr><td>${k}</td><td>${escapeHtml(String(v))}</td></tr>`)
      .join('');
  }
  const depsEl = document.getElementById('pkgDeps');
  if (depsEl) {
    const deps = data.dependencies || [];
    depsEl.innerHTML = deps.length ? deps.map(d => `<span class="badge">${escapeHtml(d)}</span>`).join('') : `<span style="color:#718096;">${window.jsTranslations?.no_dependencies_found || 'No dependencies found'}</span>`;
  }
  document.getElementById('pkgDetailModal').style.display = 'flex';
}

function closeModal(id){ const el = document.getElementById(id); if(el) el.style.display='none'; }
function escapeHtml(text){ const d=document.createElement('div'); d.textContent=text; return d.innerHTML; }

document.addEventListener('DOMContentLoaded', async () => {
  try {
    document.getElementById('refreshBtn')?.addEventListener('click', async () => {
      await loadSummary();
      await loadInstalled();
    });
    document.getElementById('managerFilter')?.addEventListener('change', (e) => {
      CURRENT_FILTER.manager = e.target.value;
      renderTable();
    });
    document.getElementById('searchInput')?.addEventListener('input', (e) => {
      CURRENT_FILTER.search = e.target.value;
      renderTable();
    });
    await loadSummary();
    await loadUpdates();
    await loadInstalled();
  } catch (e) {
    console.error(e);
  }
});

async function loadUpdates() {
  const res = await fetch('/package-manager/api/updates/');
  const data = await res.json();
  if (data.success) {
    UPDATES_CACHE = data.data || {};
  }
}

function populateUpdatesManagerFilter(selected='') {
  const sel = document.getElementById('updatesManagerFilter');
  if (!sel) return;
  const managers = Object.keys(UPDATES_CACHE || {});
  sel.innerHTML = `<option value="">${window.jsTranslations?.all || 'All'}</option>` + managers.map(m => `<option value="${m}" ${m===selected?'selected':''}>${m}</option>`).join('');
  sel.onchange = () => renderUpdatesList(false, sel.value);
}

function renderUpdatesList(onlyCritical = false, managerFilter = '') {
  const tbody = document.getElementById('updatesTbody');
  if (!tbody) return;
  const rows = [];
  for (const [m, arr] of Object.entries(UPDATES_CACHE || {})) {
    if (managerFilter && m !== managerFilter) continue;
    (arr || []).forEach(u => {
      if (onlyCritical && !u.critical) return;
      rows.push(`
        <tr>
          <td>${escapeHtml(u.name)}</td>
          <td>${escapeHtml(u.current_version || '')}</td>
          <td>${escapeHtml(u.new_version || u.branch || '')}</td>
          <td>${m}</td>
          <td>${u.critical ? `<span class=\"mgr-critical\">${window.jsTranslations?.critical || 'critical'}</span>` : ''}</td>
        </tr>
      `);
    });
  }
  tbody.innerHTML = rows.length ? rows.join('') : `<tr><td colspan="5" class="empty-state"><i class="fas fa-inbox"></i><span>${window.jsTranslations?.no_updates_found || 'No updates found'}</span></td></tr>`;
}


