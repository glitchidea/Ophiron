(() => {
    let modalEl;
    let bsModal;
    let charts = {};

    document.addEventListener('DOMContentLoaded', () => {
        modalEl = document.getElementById('ownLogsAnalysisModal');
        if (!modalEl) return;
        bsModal = new bootstrap.Modal(modalEl);

        const openBtn = document.getElementById('openOwnLogsAnalysis');
        if (openBtn) {
            openBtn.addEventListener('click', () => {
                bsModal.show();
                runAnalysis();
            });
        }

        modalEl.addEventListener('hidden.bs.modal', () => {
            // destroy charts to free memory
            Object.values(charts).forEach(c => { try { c.destroy(); } catch(e){} });
            charts = {};
        });
    });

    async function runAnalysis() {
        toggleLoading(true);
        try {
            const catsResp = await fetch('/system-logs/own/categories/');
            const catsJson = await catsResp.json();
            const categories = catsJson.categories || [];

            const allData = { linesByCategory: {}, totalLines: 0, fileCount: 0 };

            // fetch all lines for each category in parallel
            const fetches = categories.map(async (cat) => {
                const r = await fetch(`/system-logs/own/category/${encodeURIComponent(cat)}/lines/all/`);
                const j = await r.json();
                const lines = Array.isArray(j.lines) ? j.lines : [];
                allData.linesByCategory[cat] = lines;
                allData.totalLines += lines.length;
                // estimate file count from file headers if present `=== filename ===`
                const fileHeaders = lines.filter(l => /^=== .* ===$/.test(l));
                allData.fileCount += Math.max(fileHeaders.length, 1);
            });

            await Promise.all(fetches);

            const analysis = analyze(allData.linesByCategory);
            renderMetrics(allData.totalLines, Object.keys(allData.linesByCategory).length, allData.fileCount);
            renderCharts(analysis);
            renderSummaries(analysis);
            renderTopErrorsTable(analysis.topErrors);

            toggleLoading(false);
        } catch (e) {
            console.error('Analysis error', e);
            toggleLoading(false);
        }
    }

    function analyze(linesByCategory) {
        const levelCounts = { error: 0, warning: 0, info: 0, debug: 0, other: 0 };
        const byCategoryCounts = {};
        const timeline = {}; // key: hour label
        const errorMessageCounts = new Map();

        const levelRegex = {
            error: /(ERROR|CRITICAL|FATAL)/i,
            warning: /(WARNING|WARN)/i,
            info: /\bINFO\b/i,
            debug: /\bDEBUG\b/i,
        };

        const timeExtract = (line) => {
            const m = line.match(/(\d{4}-\d{2}-\d{2})[ T](\d{2}):(\d{2}):(\d{2})/);
            if (m) return new Date(`${m[1]}T${m[2]}:${m[3]}:${m[4]}`);
            return null;
        };

        Object.keys(linesByCategory).forEach(cat => {
            const lines = linesByCategory[cat] || [];
            byCategoryCounts[cat] = (byCategoryCounts[cat] || 0) + lines.length;
            lines.forEach(line => {
                // level
                let matched = false;
                for (const k of ['error','warning','info','debug']) {
                    if (levelRegex[k].test(line)) { levelCounts[k]++; matched = true; break; }
                }
                if (!matched) levelCounts.other++;

                // timeline by hour (last 24h focus; but we will compute regardless)
                const d = timeExtract(line);
                if (d) {
                    const key = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:00`;
                    timeline[key] = (timeline[key] || 0) + 1;
                }

                // top error messages: store message portion after level token
                if (levelRegex.error.test(line)) {
                    const msg = extractErrorMessage(line);
                    const current = errorMessageCounts.get(msg) || 0;
                    errorMessageCounts.set(msg, current + 1);
                }
            });
        });

        // last 24h buckets
        const now = new Date();
        const last24Keys = [];
        for (let i = 23; i >= 0; i--) {
            const d = new Date(now.getTime() - i * 3600 * 1000);
            const key = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:00`;
            last24Keys.push(key);
        }
        const timelineData = last24Keys.map(k => timeline[k] || 0);

        // top errors array
        const topErrors = Array.from(errorMessageCounts.entries())
            .sort((a,b) => b[1]-a[1])
            .slice(0, 10)
            .map(([message, count]) => ({ message, count }));

        return { levelCounts, byCategoryCounts, last24Keys, timelineData, topErrors };
    }

    function extractErrorMessage(line) {
        // try to split by level token
        const m = line.match(/(?:ERROR|CRITICAL|FATAL)[:\-\s]+(.+)/i);
        if (m && m[1]) return m[1].trim();
        // fallback: return trimmed whole line
        return line.trim().slice(0, 200);
    }

    function renderMetrics(totalLines, categories, files) {
        setText('metricTotalLines', totalLines);
        setText('metricCategories', categories);
        setText('metricFiles', files);
    }

    function renderCharts(analysis) {
        const { levelCounts, byCategoryCounts, last24Keys, timelineData } = analysis;

        // Levels pie
        const levelsCtx = document.getElementById('chartLevelsPie');
        if (levelsCtx) {
            charts.levels = new Chart(levelsCtx, {
                type: 'doughnut',
                data: {
                    labels: [tr('Error','Error'), tr('Warning','Warning'), tr('Info','Info'), tr('Debug','Debug'), tr('Other','Other')],
                    datasets: [{
                        data: [levelCounts.error, levelCounts.warning, levelCounts.info, levelCounts.debug, levelCounts.other],
                        backgroundColor: ['#ef4444','#f59e0b','#3b82f6','#8b5cf6','#9ca3af']
                    }]
                },
                options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
            });
        }

        // Category bar
        const catCtx = document.getElementById('chartByCategory');
        if (catCtx) {
            const labels = Object.keys(byCategoryCounts);
            const values = labels.map(k => byCategoryCounts[k]);
            charts.byCategory = new Chart(catCtx, {
                type: 'bar',
                data: { labels, datasets: [{ label: tr('Lines','Lines'), data: values, backgroundColor: '#3b82f6' }] },
                options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
            });
        }

        // Timeline line
        const timeCtx = document.getElementById('chartTimeline');
        if (timeCtx) {
            charts.timeline = new Chart(timeCtx, {
                type: 'line',
                data: { labels: last24Keys, datasets: [{ label: tr('Lines','Lines'), data: timelineData, borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.15)', tension: 0.25, fill: true }] },
                options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
            });
        }
    }

    function renderTopErrorsTable(rows) {
        const tbody = document.getElementById('tableTopErrors');
        if (!tbody) return;
        if (!rows || !rows.length) {
            tbody.innerHTML = `<tr><td colspan="2" class="text-muted">${tr('No errors found','No errors found')}</td></tr>`;
            return;
        }
        tbody.innerHTML = rows.map(r => `
            <tr>
                <td>${escapeHtml(r.message)}</td>
                <td class="text-end"><strong>${r.count}</strong></td>
            </tr>
        `).join('');
    }

    function renderSummaries(analysis) {
        const { levelCounts, byCategoryCounts } = analysis;
        const levelsTbody = document.getElementById('tableLevelsSummary');
        const catTbody = document.getElementById('tableByCategorySummary');
        if (levelsTbody) {
            const rows = [
                [tr('Error','Error'), levelCounts.error],
                [tr('Warning','Warning'), levelCounts.warning],
                [tr('Info','Info'), levelCounts.info],
                [tr('Debug','Debug'), levelCounts.debug],
                [tr('Other','Other'), levelCounts.other],
            ];
            levelsTbody.innerHTML = rows.map(r => `
                <tr>
                    <td>${escapeHtml(r[0])}</td>
                    <td class="text-end"><strong>${r[1]}</strong></td>
                </tr>
            `).join('');
        }
        if (catTbody) {
            const labels = Object.keys(byCategoryCounts).sort((a,b)=> (byCategoryCounts[b]-byCategoryCounts[a]));
            catTbody.innerHTML = labels.map(name => `
                <tr>
                    <td>${escapeHtml(name)}</td>
                    <td class="text-end"><strong>${byCategoryCounts[name]}</strong></td>
                </tr>
            `).join('');
        }
    }

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = String(value);
    }

    function toggleLoading(loading) {
        const loadingEl = document.getElementById('ownLogsAnalysisLoading');
        const contentEl = document.getElementById('ownLogsAnalysisContent');
        if (loading) {
            if (loadingEl) loadingEl.classList.remove('d-none');
            if (contentEl) contentEl.classList.add('d-none');
        } else {
            if (loadingEl) loadingEl.classList.add('d-none');
            if (contentEl) contentEl.classList.remove('d-none');
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text == null ? '' : String(text);
        return div.innerHTML;
    }
    function tr(key, fallback) {
        try {
            const dict = (window && window.jsTranslations) ? window.jsTranslations : {};
            return dict[key] || fallback;
        } catch (e) {
            return fallback;
        }
    }
})();


