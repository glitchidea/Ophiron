<div align="center">

<img src="../static/images/ophiron.svg" alt="Ophiron Logo" width="140">

# Ophiron

**Gelişmiş Sistem İzleme ve Güvenlik Yönetim Platformu**

[Web Sitesi](https://ophiron.glitchidea.com/) • [Hata Bildir](https://github.com/glitchidea/Ophiron/issues) • [Topluluk](https://github.com/glitchidea/Ophiron/discussions)

</div>

---

## Hakkında

Ophiron; izleme, güvenlik taraması, servis ve Docker yönetimi gibi modüllerle Linux sunucularını gerçek zamanlı yönetmenizi sağlar.

### 🎯 Özellikler

#### 📊 Dashboard
- **Gerçek Zamanlı Metrikler**: CPU, RAM, Disk, Ağ kullanımı (WebSocket)
- **Sistem Durumu**: Çalışan servisler, aktif kullanıcılar, sistem yükü, uptime
- **Grafikler**: CPU/RAM/Disk/Ağ kullanım grafikleri
- **Hızlı Erişim**: Son işlemler, kritik uyarılar, modül erişim butonları

#### 🔒 Security (Güvenlik)
- **Package Manager**: Apt, pacman, yay, flatpak, dnf, zypper, snap desteği
- **Developer Packages**: Python (pip, pipx, conda, poetry), Node.js (npm, yarn, pnpm), PHP (composer), Ruby (gem), Rust (cargo), Go, .NET
- **CVE Scanner**: Arch, Fedora, Debian, Ubuntu için CVE taraması; batch işleme, güvenlik açığı tespiti

#### 🌐 Network
- **Process Monitor**: WebSocket ile canlı süreç izleme, port ve ağ bağlantıları, PID/Port/IP gruplama, PDF raporlama
- **Service Monitor**: Systemd servisleri için başlatma/durdurma/yeniden başlatma, kategori bazında filtreleme
- **Service Builder**: Systemd servis dosyası oluşturma, şablon desteği (Python, Node.js, PHP, Ruby, Rust, Go, .NET), port kontrolü

#### 🖥️ System
- **Process Topology**: Süreçler arası ilişkilerin görselleştirilmesi, parent-child ilişkileri, snapshot kaydetme
- **System Logs**: Syslog, kernel, auth, daemon, boot, cron logları; journalctl entegrasyonu, filtreleme, arama, dışa aktarma
- **User Management**: Sistem kullanıcıları, grup üyelikleri, aktivite geçmişi, oturum yönetimi
- **Firewall**: UFW ve iptables yönetimi, kural ekleme/silme/düzenleme
- **System Information**: CPU, RAM, disk, ağ bilgileri; live mode desteği
- **Docker Manager**: Container, image, volume yönetimi; Docker Hub entegrasyonu, loglar, terminal erişimi

#### ⚙️ Settings
- **Profil**: Profil resmi, dil seçimi (TR/EN/DE), zaman dilimi
- **Güvenlik**: Şifre değiştirme, 2FA (QR kod/manuel), yedek kodlar
- **Modül Ayarları**: Process Monitor, System Information, Service Monitoring için live mode ayarları
- **Log Yönetimi**: Modül bazında log açma/kapama
- **SMTP**: E-posta konfigürasyonu, CVE email otomasyonu (daily/weekly/monthly/cron)

#### 🔐 Güvenlik ve Erişim
- **Kimlik Doğrulama**: Kullanıcı adı/şifre, 2FA desteği
- **Oturum Yönetimi**: Güvenli token'lar, zaman aşımı, oturum geçmişi
- **Aktivite Takibi**: Kullanıcı aktivite logları, IP takibi
- **Erişim Kontrolü**: Rol bazlı erişim, izin yönetimi

#### 🌍 Uluslararasılaştırma
- Türkçe, İngilizce, Almanca tam arayüz desteği
- Tüm modüller çoklu dil desteğine sahip

#### 🏗️ Altyapı
- **Backend**: Django (Python), Gunicorn/Daphne
- **Task Queue**: Redis + Celery
- **Reverse Proxy**: Nginx
- **Real-time**: WebSocket desteği

---

## Kurulum

### Geliştirme (Yerel)
```bash
git clone https://github.com/glitchidea/Ophiron.git
cd Ophiron
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Üretim (Kısa Özet)
- `collectstatic` çalıştırın; Gunicorn/Daphne ile servis edin
- Nginx reverse proxy + HTTPS önerilir

```bash
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## Çalıştırma

Ophiron'u çalıştırmak için aşağıdaki adımları izleyin:

### 1. Redis'i Başlatın

Redis, Celery için gerekli bir mesaj kuyruğu broker'ıdır. Docker kullanarak Redis'i başlatın:

```bash
docker run -d --name redis -p 6379:6379 redis:latest
```

Veya docker-compose kullanıyorsanız, docker-compose.yml dosyanıza Redis servisini ekleyebilirsiniz.

### 2. Celery Worker'ı Başlatın

Celery, arka plan görevlerini işlemek için kullanılır. Yeni bir terminal penceresinde şu komutu çalıştırın:

```bash
celery -A core worker --loglevel=info --pool=solo
```

**Root kullanıcı ile Celery Worker:**
```bash
sudo venv/bin/celery -A core worker --loglevel=info --pool=solo
```

**Not:** `--pool=solo` parametresi Windows ve bazı geliştirme ortamlarında gereklidir. Üretim ortamında genellikle `--pool=prefork` kullanılır.

### 3. Django Uygulamasını Başlatın

Ana uygulamayı başlatın:

**Geliştirme ortamı için:**
```bash
python manage.py runserver 0.0.0.0:8000
```

**Root kullanıcı ile başlatma (sudo gerekli işlemler için):**
```bash
sudo venv/bin/python manage.py runserver 0.0.0.0:8000
```

**Üretim ortamı için:**
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

**Root kullanıcı ile üretim ortamı:**
```bash
sudo venv/bin/gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Tam Çalıştırma Sırası

1. Redis'i başlatın (Docker ile)
2. Celery worker'ı başlatın (ayrı terminal)
3. Django uygulamasını başlatın

Tüm servisler çalıştıktan sonra, uygulamaya tarayıcınızdan erişebilirsiniz.

---

## Lisans ve Ticari Kullanım

### Ticari/Kurumsal Kullanım Zorunluluğu

Bu projeyi **ticari amaçlarla** veya **kurumsal ortamda** kullanmayı planlıyorsanız, aşağıdaki durumlar için **lisans alma ve onay zorunluluğu** bulunmaktadır:

- ✅ Bu projeden **doğrudan veya dolaylı gelir** elde edilecekse
- ✅ **Kurumsal/ticari** bir ortamda kullanılacaksa
- ✅ Müşterilere **hizmet olarak** sunulacaksa
- ✅ **Ticari bir ürün veya hizmetin** parçası olarak kullanılacaksa

### Bildirim ve Onay Süreci

Yukarıdaki durumlardan herhangi biri sizin için geçerliyse, **kullanıma başlamadan önce** aşağıdaki bilgileri içeren bir e-posta göndermeniz **zorunludur**:

**E-posta Adresi:** info@glitchidea.com

**E-postada bulunması gerekenler:**
- Şirket/Kurum adı
- Kullanım amacı ve kapsamı
- Beklenen kullanıcı sayısı
- Kullanım süresi
- İletişim bilgileri

Onay alınmadan ticari/kurumsal kullanım yapılması **lisans ihlali** sayılır.

### Kişisel/Araştırma Kullanımı

Kişisel projeler, eğitim amaçlı kullanım ve açık kaynak araştırma projeleri için lisans gerekliliği bulunmamaktadır.

---

