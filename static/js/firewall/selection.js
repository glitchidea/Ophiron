// ===== FIREWALL SELECTION JAVASCRIPT =====

document.addEventListener('DOMContentLoaded', function() {
    // Sayfa yüklendiğinde firewall durumlarını kontrol et
    checkFirewallStatus();
    
    // Her 5 saniyede bir durum kontrolü yap
    setInterval(checkFirewallStatus, 5000);
});

// ===== FIREWALL DURUM KONTROLÜ =====
function checkFirewallStatus() {
    const firewalls = ['ufw', 'iptables', 'firewalld'];
    
    firewalls.forEach(firewall => {
        checkSingleFirewall(firewall);
    });
}

function checkSingleFirewall(firewall) {
    const statusElement = document.getElementById(`${firewall}-status`);
    if (!statusElement) return;
    
    const statusDot = statusElement.querySelector('.status-dot');
    const statusText = statusElement.querySelector('.status-text');
    
    // Loading durumu
    statusText.textContent = window.jsTranslations.checking || 'Checking...';
    statusDot.className = 'status-dot';
    
    // API çağrısı yap
    fetch(`/firewall/${firewall}/api/status/`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.available) {
                statusText.textContent = window.jsTranslations.available || 'Available';
                statusText.className = 'status-text available';
                statusDot.className = 'status-dot available';
            } else {
                statusText.textContent = window.jsTranslations.not_available || 'Not Available';
                statusText.className = 'status-text unavailable';
                statusDot.className = 'status-dot unavailable';
            }
        })
        .catch(error => {
            console.error(`Error checking ${firewall} status:`, error);
            statusText.textContent = window.jsTranslations.error || 'Error';
            statusText.className = 'status-text unavailable';
            statusDot.className = 'status-dot unavailable';
        });
}

// ===== FIREWALL SEÇİMİ =====
function selectFirewall(firewall) {
    const statusElement = document.getElementById(`${firewall}-status`);
    const statusText = statusElement.querySelector('.status-text');
    
    // Eğer firewall mevcut değilse uyarı göster
    if (statusText.textContent === 'Not Available' || statusText.textContent === 'Error') {
        showNotification(`${firewall.toUpperCase()} is not available on this system`, 'error');
        return;
    }
    
    // Loading durumu
    statusText.textContent = 'Loading...';
    
    // Firewall yönetim sayfasına yönlendir
    window.location.href = `/firewall/${firewall}/`;
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
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Notification stilleri
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#dc3545' : '#007bff'};
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
`;
document.head.appendChild(style);
