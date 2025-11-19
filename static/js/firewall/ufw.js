// ===== UFW FIREWALL JAVASCRIPT =====

document.addEventListener('DOMContentLoaded', function() {
    // Sayfa yüklendiğinde UFW durumunu ve kurallarını yükle
    loadUfwStatus();
    loadUfwRules();
    
    // Event listeners
    document.getElementById('refreshUfw').addEventListener('click', function() {
        loadUfwStatus();
        loadUfwRules();
    });
    
    document.getElementById('toggleUfw').addEventListener('click', function() {
        toggleUfw();
    });
    
    
            // Event listeners for improved functionality
    
    // Otomatik status kontrolü (her 3 saniyede bir)
    setInterval(function() {
        checkUfwStatus();
    }, 3000);
    
    // Sayfa focus olduğunda status kontrolü
    window.addEventListener('focus', function() {
        loadUfwStatus();
    });
    
    // Sayfa görünür olduğunda status kontrolü
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            loadUfwStatus();
        }
    });
    
    // Global test function - browser console'dan çağrılabilir
    window.testUfwRules = testUfwRules;
    
});

// ===== UFW DURUM YÜKLEME =====
function loadUfwStatus() {
    const statusIndicator = document.getElementById('ufwStatusIndicator');
    const toggleBtn = document.getElementById('toggleUfw');
    const toggleText = document.getElementById('toggleText');
    
    // Loading durumu
    statusIndicator.querySelector('.status-text').textContent = window.jsTranslations.checking || 'Checking...';
    statusIndicator.querySelector('.status-dot').className = 'status-dot';
    
    fetch('/firewall/ufw/api/status/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('UFW Status API Response:', data); // Debug için
            if (data.success && data.available) {
                if (data.status === 'active') {
                    statusIndicator.querySelector('.status-text').textContent = window.jsTranslations.enabled || 'Active';
                    statusIndicator.querySelector('.status-text').className = 'status-text active';
                    statusIndicator.querySelector('.status-dot').className = 'status-dot active';
                    toggleText.textContent = window.jsTranslations.disable || 'Disable';
                    toggleBtn.className = 'btn-toggle active';
                    toggleBtn.disabled = false;
                    
                    // UFW aktifse kuralları yükle
                    loadUfwRules();
                } else {
                    statusIndicator.querySelector('.status-text').textContent = window.jsTranslations.disabled || 'Inactive';
                    statusIndicator.querySelector('.status-text').className = 'status-text inactive';
                    statusIndicator.querySelector('.status-dot').className = 'status-dot inactive';
                    toggleText.textContent = window.jsTranslations.enable || 'Enable';
                    toggleBtn.className = 'btn-toggle';
                    toggleBtn.disabled = false;
                    
                    // UFW kapalıysa kuralları yükle ve disabled mesajı göster
                    loadUfwRules();
                }
            } else {
                statusIndicator.querySelector('.status-text').textContent = window.jsTranslations.not_available || 'Not Available';
                statusIndicator.querySelector('.status-text').className = 'status-text inactive';
                statusIndicator.querySelector('.status-dot').className = 'status-dot inactive';
                toggleBtn.disabled = true;
                toggleText.textContent = window.jsTranslations.not_available || 'Not Available';
            }
        })
        .catch(error => {
            console.error('Error loading UFW status:', error);
            statusIndicator.querySelector('.status-text').textContent = window.jsTranslations.error || 'Error';
            statusIndicator.querySelector('.status-text').className = 'status-text inactive';
            statusIndicator.querySelector('.status-dot').className = 'status-dot inactive';
            toggleBtn.disabled = true;
            toggleText.textContent = window.jsTranslations.error || 'Error';
        });
}

// ===== UFW KURALLARI YÜKLEME =====
function loadUfwRules() {
    const rulesLoading = document.getElementById('ufwRulesLoading');
    const rulesTable = document.getElementById('ufwRulesTable');
    const rulesEmpty = document.getElementById('ufwRulesEmpty');
    const rulesTableBody = document.getElementById('ufwRulesTableBody');
    const rulesCount = document.getElementById('rulesCount');
    
    // Önce UFW status'unu kontrol et
    fetch('/firewall/ufw/api/status/')
        .then(response => response.json())
        .then(statusData => {
            // UFW kapalı ise disabled mesajı göster
            if (!statusData.available || statusData.status !== 'active') {
                displayUfwDisabledMessage();
                rulesCount.textContent = '(0)';
                return;
            }
            
            // UFW aktifse kuralları yükle
            rulesLoading.style.display = 'flex';
            rulesTable.style.display = 'none';
            rulesEmpty.style.display = 'none';
            rulesCount.textContent = '(0)';
            
            return fetch('/firewall/ufw/api/rules/');
        })
        .then(response => {
            if (!response) return; // UFW kapalıysa response yok
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data) return; // UFW kapalıysa data yok
            
            rulesLoading.style.display = 'none';
            
            if (data.success && data.rules) {
                console.log('UFW API Response:', data); // Debug için
                const rules = parseUfwRules(data.rules);
                
                if (rules.length > 0) {
                    displayUfwRules(rules);
                    rulesTable.style.display = 'block';
                    rulesCount.textContent = `(${rules.length})`;
                } else {
                    // Eğer hiç kural yoksa ama UFW aktifse, boş durum göster
                    rulesEmpty.style.display = 'flex';
                    rulesCount.textContent = '(0)';
                    rulesEmpty.querySelector('.empty-state p').textContent = 'No firewall rules configured';
                }
            } else {
                // UFW kapalı ise özel mesaj göster
                displayUfwDisabledMessage();
                rulesCount.textContent = '(0)';
            }
        })
        .catch(error => {
            console.error('Error loading UFW rules:', error);
            rulesLoading.style.display = 'none';
            rulesEmpty.style.display = 'flex';
            rulesEmpty.querySelector('.empty-state p').textContent = `Error loading rules: ${error.message}`;
            rulesCount.textContent = '(0)';
        });
}

// ===== UFW KURALLARI PARSE ETME =====
function parseUfwRules(rulesOutput) {
    const lines = rulesOutput.split('\n');
    const rules = [];
    let ruleNumber = 1;
    
    console.log('UFW Rules Output:', rulesOutput); // Debug için
    
    for (let line of lines) {
        line = line.trim();
        
        // Skip empty lines and headers
        if (!line || line.startsWith('Status:') || line.startsWith('To') || line.startsWith('--') || line.startsWith('Firewall loaded')) {
            continue;
        }
        
        // Parse UFW format: "[ 1] 443                        ALLOW IN    172.16.1.1"
        // Handle numbered format with proper spacing
        const numberedMatch = line.match(/^\[\s*(\d+)\]\s+(.+?)\s+(ALLOW|DENY|REJECT|LIMIT)\s+(IN|OUT)\s+(.+)$/);
        if (numberedMatch) {
            const portProtocol = numberedMatch[2].trim();
            const action = numberedMatch[3];
            const direction = numberedMatch[4];
            const from = numberedMatch[5].trim();
            
            const rule = parseRuleContent(portProtocol, action, direction, from);
            rule.ruleNumber = ruleNumber++;
            rules.push(rule);
        }
    }
    
    console.log('Parsed Rules:', rules); // Debug için
    return rules;
}

// ===== RULE CONTENT PARSE ETME =====
function parseRuleContent(portProtocol, action, direction, from) {
    const rule = {
        action: action,
        from: from,
        to: 'Anywhere',
        port: 'Any',
        protocol: 'Any',
        direction: direction
    };
    
    console.log('Parsing rule:', { portProtocol, action, direction, from }); // Debug için
    
    // IPv6 kontrolü - önce IPv6 kontrolü yap
    if (portProtocol.includes('(v6)')) {
        rule.protocol = 'IPv6';
        portProtocol = portProtocol.replace(' (v6)', '');
    }
    
    // Port ve protocol'ü parse et
    if (portProtocol.includes('/')) {
        // Format: "22/tcp", "1000:2000/tcp", "53/udp"
        const parts = portProtocol.split('/');
        rule.port = parts[0];
        rule.protocol = parts[1].toUpperCase();
    } else if (portProtocol.includes(':')) {
        // Port range: "1000:2000"
        rule.port = portProtocol;
        rule.protocol = rule.protocol === 'IPv6' ? 'IPv6' : 'TCP'; // Keep IPv6 if already set
    } else if (/^\d+$/.test(portProtocol)) {
        // Simple port: "22", "80", "443"
        rule.port = portProtocol;
        rule.protocol = rule.protocol === 'IPv6' ? 'IPv6' : 'TCP'; // Keep IPv6 if already set
    } else {
        // Service name or other: "SSH", "HTTP", etc.
        rule.port = portProtocol;
        rule.protocol = rule.protocol === 'IPv6' ? 'IPv6' : 'TCP'; // Keep IPv6 if already set
    }
    
    // From field'ı temizle
    if (from.includes('(v6)')) {
        rule.from = from.replace(' (v6)', '');
    } else {
        rule.from = from;
    }
    
    console.log('Parsed rule:', rule); // Debug için
    return rule;
}


// ===== UFW KURALLARI GÖRÜNTÜLEME =====
function displayUfwRules(rules) {
    const rulesTableBody = document.getElementById('ufwRulesTableBody');
    rulesTableBody.innerHTML = '';
    
    rules.forEach(rule => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="col-number">
                <span class="rule-number-badge">${rule.ruleNumber}</span>
            </td>
            <td class="col-action">
                <span class="rule-action ${rule.action.toLowerCase()}">
                    <i class="fas fa-${rule.action === 'ALLOW' ? 'check' : rule.action === 'DENY' ? 'times' : rule.action === 'REJECT' ? 'ban' : 'exclamation-triangle'}"></i>
                    ${rule.action}
                </span>
            </td>
            <td class="col-direction">
                <span class="rule-direction ${rule.direction.toLowerCase()}">
                    <i class="fas fa-${rule.direction === 'IN' ? 'arrow-down' : 'arrow-up'}"></i>
                    ${rule.direction}
                </span>
            </td>
            <td class="col-source">
                <span class="rule-address">${rule.from}</span>
            </td>
            <td class="col-destination">
                <span class="rule-address">${rule.to}</span>
            </td>
            <td class="col-port">
                <span class="rule-port">${rule.port}</span>
            </td>
            <td class="col-protocol">
                <span class="rule-protocol">${rule.protocol}</span>
            </td>
        `;
        rulesTableBody.appendChild(row);
    });
}

// ===== UFW KAPALI MESAJI =====
function displayUfwDisabledMessage() {
    const rulesTable = document.getElementById('ufwRulesTable');
    const rulesEmpty = document.getElementById('ufwRulesEmpty');
    
    // Tabloyu gizle
    rulesTable.style.display = 'none';
    
    // Boş durum mesajını göster
    rulesEmpty.style.display = 'flex';
    rulesEmpty.innerHTML = `
        <i class="fas fa-shield-alt" style="color: #dc3545;"></i>
        <h3>UFW Firewall is Disabled</h3>
        <p>Please enable UFW firewall first to view and manage firewall rules.</p>
        <button id="enableUfwBtn" class="btn-add-rule">
            <i class="fas fa-power-off"></i>
            Enable UFW Firewall
        </button>
    `;
    
    // Enable UFW butonuna event listener ekle
    const enableUfwBtn = document.getElementById('enableUfwBtn');
    if (enableUfwBtn) {
        enableUfwBtn.addEventListener('click', function() {
            toggleUfw();
        });
    }
}

// ===== UFW AÇMA/KAPAMA =====
function toggleUfw() {
    const toggleBtn = document.getElementById('toggleUfw');
    const toggleText = document.getElementById('toggleText');
    const originalText = toggleText.textContent;
    
    // Loading durumu
    toggleBtn.disabled = true;
    toggleText.textContent = 'Processing...';
    
    // Mevcut durumu belirle
    const isCurrentlyActive = toggleBtn.classList.contains('active');
    const action = isCurrentlyActive ? 'disable' : 'enable';
    
    fetch('/firewall/ufw/api/toggle/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            action: action
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('UFW Toggle API Response:', data); // Debug için
        if (data.success) {
            showNotification(data.message, 'success');
            // Durumu hemen güncelle
            updateStatusAfterToggle(action);
            // Kuralları da yenile
            setTimeout(() => {
                loadUfwRules();
                // Status'u da yenile
                loadUfwStatus();
            }, 500);
        } else {
            showNotification(data.error || data.message || 'Failed to toggle UFW', 'error');
        }
    })
    .catch(error => {
        console.error('Error toggling UFW:', error);
        showNotification(`Error: ${error.message}`, 'error');
    })
    .finally(() => {
        toggleBtn.disabled = false;
        toggleText.textContent = originalText;
    });
}

// ===== STATUS GÜNCELLEME =====
function updateStatusAfterToggle(action) {
    const statusIndicator = document.getElementById('ufwStatusIndicator');
    const toggleBtn = document.getElementById('toggleUfw');
    const toggleText = document.getElementById('toggleText');
    
    if (action === 'enable') {
        // Enable yapıldı
        statusIndicator.querySelector('.status-text').textContent = 'Active';
        statusIndicator.querySelector('.status-text').className = 'status-text active';
        statusIndicator.querySelector('.status-dot').className = 'status-dot active';
        toggleText.textContent = 'Disable';
        toggleBtn.className = 'btn-toggle active';
    } else {
        // Disable yapıldı
        statusIndicator.querySelector('.status-text').textContent = 'Inactive';
        statusIndicator.querySelector('.status-text').className = 'status-text inactive';
        statusIndicator.querySelector('.status-dot').className = 'status-dot inactive';
        toggleText.textContent = 'Enable';
        toggleBtn.className = 'btn-toggle';
    }
}

// ===== SESSIZ STATUS KONTROLÜ =====
function checkUfwStatus() {
    fetch('/firewall/ufw/api/status/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.available) {
                const statusIndicator = document.getElementById('ufwStatusIndicator');
                const toggleBtn = document.getElementById('toggleUfw');
                const toggleText = document.getElementById('toggleText');
                
                if (data.status === 'active') {
                    // Eğer status değişmişse güncelle
                    if (!statusIndicator.querySelector('.status-dot').classList.contains('active')) {
                        statusIndicator.querySelector('.status-text').textContent = 'Active';
                        statusIndicator.querySelector('.status-text').className = 'status-text active';
                        statusIndicator.querySelector('.status-dot').className = 'status-dot active';
                        toggleText.textContent = 'Disable';
                        toggleBtn.className = 'btn-toggle active';
                        
                        // Status değiştiğinde kuralları da yenile
                        loadUfwRules();
                    }
                } else {
                    // Eğer status değişmişse güncelle
                    if (!statusIndicator.querySelector('.status-dot').classList.contains('inactive')) {
                        statusIndicator.querySelector('.status-text').textContent = 'Inactive';
                        statusIndicator.querySelector('.status-text').className = 'status-text inactive';
                        statusIndicator.querySelector('.status-dot').className = 'status-dot inactive';
                        toggleText.textContent = 'Enable';
                        toggleBtn.className = 'btn-toggle';
                        
                        // Status değiştiğinde kuralları da yenile
                        loadUfwRules();
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error checking UFW status:', error);
        });
}

// ===== YENİ FONKSİYONLAR =====

// Test UFW Rules - Debug için
function testUfwRules() {
    console.log('Testing UFW rules loading...');
    fetch('/firewall/ufw/api/rules/')
        .then(response => response.json())
        .then(data => {
            console.log('Raw UFW API Response:', data);
            if (data.success && data.rules) {
                console.log('Raw UFW Rules Output:');
                console.log(data.rules);
                const rules = parseUfwRules(data.rules);
                console.log('Parsed Rules:', rules);
            }
        })
        .catch(error => {
            console.error('Test error:', error);
        });
}



// View Rule Details
function viewRuleDetails(ruleNumber) {
    showNotification(`Viewing details for rule ${ruleNumber}`, 'info');
}

// Delete Rule
function deleteRule(ruleNumber) {
    if (confirm(`Are you sure you want to delete rule ${ruleNumber}?`)) {
        showNotification(`Deleting rule ${ruleNumber}...`, 'info');
        // Implement delete functionality here
    }
}

// ===== CSRF TOKEN =====
function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

// ===== NOTIFICATION SISTEMI =====
function showNotification(message, type = 'info') {
    // Mevcut notification'ları temizle
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Yeni notification oluştur
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Notification stilleri
    const colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'info': '#007bff'
    };
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${colors[type] || colors.info};
        color: white;
        padding: 12px 16px;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 12px;
        max-width: 400px;
        animation: slideIn 0.3s ease;
    `;
    
    // Notification içeriği stilleri
    const content = notification.querySelector('.notification-content');
    content.style.cssText = `
        display: flex;
        align-items: center;
        gap: 8px;
        flex: 1;
    `;
    
    // Kapatma butonu stilleri
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.style.cssText = `
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        transition: background 0.2s ease;
    `;
    
    closeBtn.addEventListener('mouseenter', function() {
        this.style.background = 'rgba(255, 255, 255, 0.2)';
    });
    
    closeBtn.addEventListener('mouseleave', function() {
        this.style.background = 'none';
    });
    
    // Body'ye ekle
    document.body.appendChild(notification);
    
    // 5 saniye sonra otomatik kaldır
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// ===== CSS ANIMATIONS =====
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .rule-action {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .rule-action.allow {
        background: #d4edda;
        color: #155724;
    }
    
    .rule-action.deny {
        background: #f8d7da;
        color: #721c24;
    }
    
    .rule-action.reject {
        background: #fff3cd;
        color: #856404;
    }
    
    .status-details {
        font-size: 14px;
    }
    
    .status-item {
        margin-bottom: 8px;
    }
    
    .status-output {
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 4px;
        padding: 8px;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        white-space: pre-wrap;
        max-height: 200px;
        overflow-y: auto;
    }
    
    .status-error {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #dc3545;
        font-size: 14px;
    }
`;
document.head.appendChild(style);
