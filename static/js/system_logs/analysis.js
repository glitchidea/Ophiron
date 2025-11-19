document.addEventListener('DOMContentLoaded', function(){
    const analyzeBtn = document.getElementById('analyzePatterns');
    if (!analyzeBtn) return;
    analyzeBtn.addEventListener('click', function(){
        const modalEl = document.getElementById('analysisModal');
        if (!modalEl) return;
        // Remove any stale backdrops before opening
        document.querySelectorAll('.modal-backdrop').forEach(e=>e.remove());
        document.body.classList.remove('modal-open');
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
        const commonErrorsDiv = document.getElementById('commonErrors');
        if (commonErrorsDiv) commonErrorsDiv.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Log analizi yapılıyor...</p></div>';
        fetch('/system-logs/analyze/', { headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' } })
            .then(r=>r.json())
            .then(data=>{
                if (typeof initializeCharts === 'function') initializeCharts();
                if (typeof updateAnalysisCharts === 'function') updateAnalysisCharts(data);
            })
            .catch(()=>{ if (commonErrorsDiv) commonErrorsDiv.innerHTML = '<div class="alert alert-danger">An error occurred during log analysis.</div>'; });
    });

    // Ensure backdrop is cleared when modal closes
    const modalEl = document.getElementById('analysisModal');
    if (modalEl) {
        modalEl.addEventListener('hidden.bs.modal', function(){
            document.querySelectorAll('.modal-backdrop').forEach(e=>e.remove());
            document.body.classList.remove('modal-open');
            document.body.style.removeProperty('padding-right');
        });
    }
});


