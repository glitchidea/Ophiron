// Stats Tab - Container istatistikleri

// Global değişkenler - sadece bir kez tanımla
if (typeof statsInterval === 'undefined') {
    var statsInterval = null;
}
if (typeof cpuChart === 'undefined') {
    var cpuChart = null;
}
if (typeof memoryChart === 'undefined') {
    var memoryChart = null;
}

// Ensure jsTranslations is available
if (typeof window.jsTranslations === 'undefined') {
    window.jsTranslations = {};
}

function loadStats() {
    console.log('Loading stats for container:', currentContainerId);
    
    // Chart'ları başlat
    initializeCharts();
    
    // İlk stats verilerini yükle
    loadStatsData();
    
    // Her 2 saniyede bir stats güncelle
    statsInterval = setInterval(loadStatsData, 2000);
}

function loadStatsData() {
    fetch(`/docker-manager/api/container/${currentContainerId}/stats/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateStats(data.stats);
        } else {
            showStatsError(data.message);
        }
    })
    .catch(error => {
        console.error('Stats error:', error);
    });
}

function updateStats(stats) {
    // CPU kullanımı
    const cpuUsage = document.getElementById('cpuUsage');
    if (cpuUsage && stats.cpu_percent) {
        cpuUsage.textContent = stats.cpu_percent + '%';
    }
    
    // Memory kullanımı
    const memoryUsage = document.getElementById('memoryUsage');
    if (memoryUsage && stats.memory_usage) {
        memoryUsage.textContent = formatBytes(stats.memory_usage);
    }
    
    // Network I/O
    const networkIO = document.getElementById('networkIO');
    if (networkIO && stats.network_io) {
        networkIO.textContent = stats.network_io;
    }
    
    // Block I/O
    const blockIO = document.getElementById('blockIO');
    if (blockIO && stats.block_io) {
        blockIO.textContent = stats.block_io;
    }
    
    // Chart'ları güncelle
    updateCharts(stats);
}

function initializeCharts() {
    const cpuCanvas = document.getElementById('cpuChart');
    const memoryCanvas = document.getElementById('memoryChart');
    
    if (cpuCanvas) {
        cpuChart = new Chart(cpuCanvas, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU %',
                    data: [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
    
    if (memoryCanvas) {
        memoryChart = new Chart(memoryCanvas, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Memory (MB)',
                    data: [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

function updateCharts(stats) {
    const now = new Date().toLocaleTimeString();
    
    // CPU chart güncelle
    if (cpuChart && stats.cpu_percent !== undefined) {
        cpuChart.data.labels.push(now);
        cpuChart.data.datasets[0].data.push(parseFloat(stats.cpu_percent));
        
        // Son 20 veriyi tut
        if (cpuChart.data.labels.length > 20) {
            cpuChart.data.labels.shift();
            cpuChart.data.datasets[0].data.shift();
        }
        
        cpuChart.update('none');
    }
    
    // Memory chart güncelle
    if (memoryChart && stats.memory_usage) {
        const memoryMB = stats.memory_usage / (1024 * 1024);
        memoryChart.data.labels.push(now);
        memoryChart.data.datasets[0].data.push(memoryMB);
        
        // Son 20 veriyi tut
        if (memoryChart.data.labels.length > 20) {
            memoryChart.data.labels.shift();
            memoryChart.data.datasets[0].data.shift();
        }
        
        memoryChart.update('none');
    }
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function showStatsError(message) {
    console.error('Stats error:', message);
    // Hata durumunda varsayılan değerleri göster
    document.getElementById('cpuUsage').textContent = 'N/A';
    document.getElementById('memoryUsage').textContent = 'N/A';
    document.getElementById('networkIO').textContent = 'N/A';
    document.getElementById('blockIO').textContent = 'N/A';
}

// Tab değiştiğinde interval'ı temizle
document.addEventListener('visibilitychange', function() {
    if (document.hidden && statsInterval) {
        clearInterval(statsInterval);
    } else if (!document.hidden && currentTab === 'stats' && !statsInterval) {
        loadStats();
    }
});

// Sayfa kapatılırken temizlik
window.addEventListener('beforeunload', function() {
    if (statsInterval) {
        clearInterval(statsInterval);
    }
});

// Chart.js kütüphanesini yükle
if (!window.Chart) {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
    script.onload = function() {
        // Chart.js yüklendikten sonra charts'ı başlat
        if (currentTab === 'stats') {
            initializeCharts();
        }
    };
    document.head.appendChild(script);
}
