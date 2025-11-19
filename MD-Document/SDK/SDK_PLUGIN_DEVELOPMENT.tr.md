# SDK ile Plugin Geliştirmek

> Ophiron plugin ekosisteminde kendi aracınızı geliştirmeniz için ihtiyacınız olan tüm adımlar: mimariden CLI kullanımına, Go backend ve Django entegrasyonundan Makefile/metaveri kurallarına, ayarlar/i18n, test ve dağıtıma kadar tek bir kılavuzda toplandı.

---

## ⚡ Hızlı Başlangıç (5 Dakika)

### Adım 1: SDK Kurulumu (İlk Kez - Tek Sefer)

**Sistem Geneli Kurulum (Önerilen):**
```bash
cd sdk
sudo make install
```

**veya Kullanıcı Dizini (Sudo Olmadan):**
```bash
cd sdk
make build
mkdir -p ~/.local/bin
cp bin/ophiron-sdk ~/.local/bin/
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc
```

**Test Et:**
```bash
ophiron-sdk --help
```

---

### Adım 2: Plugin Oluştur

SDK kurulumunu yaptıktan sonra artık `ophiron-sdk` her yerden kullanılabilir:

```bash
cd plugins

ophiron-sdk create \
  --name my_security_tool \
  --author "Your Name" \
  --email "you@example.com" \
  --developer-github "https://github.com/yourusername" \
  --project-github "https://github.com/yourusername/my_security_tool" \
  --category security \
  --languages "en,tr" \
  --version "1.0.0" \
  --os-support "linux,darwin"
```

---

### Adım 3: Build ve Test

```bash
cd my_security_tool
make deps      # Go dependencies indir
make build     # Binary oluştur
make test      # Test et
```

---

### Adım 4: Django'ya Entegre Et

```bash
cd ../..  # Ophiron root'a dön
source venv/bin/activate
python manage.py collectstatic --noinput
```

---

### Adım 5: Tarayıcıda Aç

```
http://localhost/my_security_tool
```

---

### ⚙️ Kritik Kararlar

- **Embedded Mode** (önerilen): `plugin.json`'dan `go_port` alanını sil → Port gerekmez, her istek izole
- **Port Mode**: `go_port: 8081` bırak → Hızlı ama sürekli çalışan servis gerekir

---

## İçindekiler
1. [Genel Bakış ve Mimarinin Özeti](#genel-bakış-ve-mimarinin-özeti)
2. [Ön Gereksinimler ve Ortam Kurulumu](#ön-gereksinimler-ve-ortam-kurulumu)
3. [SDK Kurulumu ve CLI Komutları](#sdk-kurulumu-ve-cli-komutları)
4. [Yeni Plugin Oluşturma](#yeni-plugin-oluşturma)
5. [plugin.json Şeması ve Metadata](#pluginjson-şeması-ve-metadata)
6. [Makefile Standartları ve Build Akışı](#makefile-standartları-ve-build-akışı)
7. [Go Backend Geliştirme](#go-backend-geliştirme)
8. [Django Entegrasyonu](#django-entegrasyonu)
9. [Frontend, Statik Dosyalar ve i18n](#frontend-statik-dosyalar-ve-i18n)
10. [Plugin Ayarları (Settings) ve Güvenli Veri Yönetimi](#plugin-ayarları-settings-ve-güvenli-veri-yönetimi)
11. [Test, Paketleme ve Dağıtım](#test-paketleme-ve-dağıtım)
12. [Sorun Giderme, En İyi Pratikler ve Kontrol Listeleri](#sorun-giderme-en-iyi-pratikler-ve-kontrol-listeleri)
13. [Hızlı Referans (Cheat Sheet)](#hızlı-referans-cheat-sheet)

---

## Genel Bakış ve Mimarinin Özeti

Ophiron plugin sistemi, Django tabanlı web katmanını Go ile yazılmış servislerle birleştiren modüler bir mimaridir. SDK, geliştiricilerin Django'nun `startapp` komutuna benzer şekilde tek komutla yeni plugin başlatmasını sağlar ve aşağıdaki bileşenlerle entegre çalışır:

### Temel Bileşenler

- **plugins/registry.py**: Plugin'leri keşfeder, etkin/pasif durumlarını yönetir, otomatik URL routing.
- **plugins/base.py**: Base plugin sınıfı, metadata yönetimi, Go bridge başlatma.
- **plugins/go_bridge.py**: Port Mode için Go servisleri ile HTTP iletişimi.
- **plugins/embedded_bridge.py**: Embedded Mode için Go servisleri ile stdin/stdout iletişimi.
- **plugins/scheduler.py**: Zamanlanmış görevler için scheduler sistemi.
- **plugins/auto_scheduler.py**: Plugin.json'dan otomatik görev oluşturma.
- **plugins/utils.py**: Ayar yönetimi, servis restart ve izin kontrolleri.
- **SDK**: `sdk` içinde yer alan Go tabanlı CLI; şablon üretir, doğrular, dil ekler.

### Çalışma Modları

**Embedded Mode (Önerilen) ✅:**
- Her istek için izole Go prosesi
- Port gerektirmez
- stdin/stdout üzerinden JSON iletişimi
- Otomatik PID yönetimi
- Daha güvenli ve kaynak verimli

**Port Mode:**
- Sürekli çalışan Go HTTP sunucusu
- Ayrı port gerektirir (8081-8099 arası)
- Düşük gecikme, hızlı yanıt
- Daha fazla kaynak kullanımı

### Güvenlik Katmanları

**1. Sandbox Metadata (plugin.json):**
- Plugin.json'da sandbox ayarları tanımlanır:
  - `max_cpu`: CPU kullanım yüzdesi limiti (%)
  - `max_memory`: RAM kullanım limiti (bytes)
  - `file_system_access`: Dosya erişim modu (readonly/readwrite/none)
  - `network_access`: Ağ erişimi izni (bool)
  - `allowed_paths`: İzin verilen dizinler ([])
  - `allowed_ports`: İzin verilen portlar ([])
- **Not:** Bu ayarlar şu anda metadata olarak kaydedilir, aktif enforcement gelecek sürümlerde eklenecektir.

**2. Go Kodu Gizliliği:**
- Go kaynak kodları gösterilmez
- Sadece derlenmiş binary çalışır
- Reverse engineering zorlaştırılır

**3. API Gateway:**
- Tüm istekler Django üzerinden geçer
- `@login_required` decorator'ı ile korunur
- Django Permission sistemi entegrasyonu
- CSRF token kontrolü
- Rate limiting (opsiyonel)

**4. Isolated Process:**
- Her plugin ayrı process olarak çalışır (özellikle Embedded Mode'da)
- Crash durumunda diğer plugin'leri etkilemez
- Process izolasyonu ile resource leak önleme

### Plugin Lifecycle ve Django Signals

Plugin'ler Django'nun `AppConfig.ready()` metodunu kullanarak sistem başlatıldığında çalışabilir:

**Örnek Kullanım:**
```python
# plugins/my_plugin/apps.py
from django.apps import AppConfig
from plugins.base import BasePlugin

class MyPluginConfig(AppConfig):
    name = 'plugins.my_plugin'
    verbose_name = 'My Plugin'
    
    def ready(self):
        """Plugin yüklendiğinde çalışır"""
        # Plugin instance oluştur
        plugin = BasePlugin('my_plugin')
        
        # Django signals'a bağlan
        from django.contrib.auth.signals import user_logged_in
        user_logged_in.connect(self.on_user_login)
    
    def on_user_login(self, sender, request, user, **kwargs):
        """Kullanıcı giriş yaptığında çalışır"""
        print(f"User {user.username} logged in")
```

**Django Signals Kullanımı:**
- `user_logged_in`: Kullanıcı giriş yaptığında
- `user_logged_out`: Kullanıcı çıkış yaptığında
- `post_save`, `pre_save`: Model kayıt işlemlerinde
- `request_started`, `request_finished`: HTTP request lifecycle

**Zamanlanmış Görevler:**
Plugin'ler `plugin.json` içinde `scheduled_tasks` tanımlayarak otomatik görevler oluşturabilir (detaylar için ilgili bölüme bakın).

### Veri Akışı

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Browser   │────────▶│    Django    │────────▶│  Go Backend │
│  (Frontend) │         │   (View)     │         │   (Binary)  │
└─────────────┘         └──────────────┘         └─────────────┘
       │                       │                         │
       │  1. HTTP Request      │  2. JSON via stdin     │
       │                       │     or HTTP POST        │
       │                       │                         │
       │  4. JSON Response     │  3. JSON Response      │
       │◀────────────────────── │◀────────────────────── │
       │                       │                         │
       │                       ▼                         │
       │              ┌──────────────┐                  │
       │              │  i18n, Auth, │                  │
       │              │   Settings   │                  │
       │              └──────────────┘                  │
       │                                                 │
       │              ┌──────────────┐                  │
       └─────────────▶│   Sandbox    │◀─────────────────┘
                      │  Monitoring  │
                      └──────────────┘
```

**Detaylı Adımlar:**
1. Kullanıcı tarayıcıdan plugin sayfasına gider (Django template)
2. JavaScript fetch ile API endpoint'e istek gönderir (CSRF token ile)
3. Django view, `BasePlugin.go_bridge.request()` ile Go backend'e JSON gönderir
4. Go uygulaması embedded veya port modunda isteği işler
5. Go, JSON response döner (stdout veya HTTP response)
6. Django view i18n, ayarlar ve logging işler
7. JSON response frontend'e döner
8. JavaScript UI'ı günceller

### Registry Sistemi

**Otomatik Plugin Keşfi:**
```python
# plugins/registry.py
class PluginRegistry:
    def load_all_plugins(self):
        # 1. plugins/ ve plugins/downloader/ dizinlerini tarar
        # 2. Her dizindeki plugin.json dosyasını yükler
        # 3. Plugin metadata'sını bellekte saklar (_plugins dict)
        # 4. Hatalı plugin'leri atlar, devam eder
        
    def get_plugin_urls(self):
        # Plugin'lerin route ve urls.py bilgilerini döner
        # (route, plugin_name, plugin_path) tuple'ları
```

**Django Settings Entegrasyonu:**
```python
# core/settings.py
def load_plugins():
    # 1. plugins/ ve plugins/downloader/ dizinlerini tarar
    # 2. plugin.json olan ve urls.py/views.py içeren dizinleri bulur
    # 3. INSTALLED_APPS'e 'plugins.{name}' veya 
    #    'plugins.downloader.{name}' olarak ekler
    # Django başlatıldığında otomatik çalışır
```

**Core URL Entegrasyonu:**
```python
# core/urls.py
def load_plugin_urls():
    from plugins.registry import PluginRegistry
    registry = PluginRegistry()
    plugin_urls = registry.get_plugin_urls()
    
    for route, plugin_name, plugin_path in plugin_urls:
        # downloader altındaki plugin'ler için özel path
        if 'downloader' in str(plugin_path):
            module_path = f'plugins.downloader.{plugin_name}.urls'
        else:
            module_path = f'plugins.{plugin_name}.urls'
        
        urlpatterns.append(path(f'{route}/', include(module_path)))
```

---

## Ön Gereksinimler ve Ortam Kurulumu

| Bileşen | Minimum Versiyon | Not |
|---------|------------------|-----|
| Python  | 3.10+            | Ophiron projesi için |
| Go      | 1.21+            | SDK ve plugin backend'i |
| Node    | Opsiyonel        | Frontend bağımlılıkları |
| Docker  | Opsiyonel        | İzole geliştirme |

### Repository ve Sanal Ortam
```bash
cd /home/jonh/Desktop/ophiron
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### SDK Kurulumu

**Seçenek 1: Sistem Geneli Kurulum (Önerilen)**
```bash
cd sdk
sudo make install
# SDK artık her yerden kullanılabilir: ophiron-sdk
```

**Seçenek 2: Manuel Kurulum (Sudo olmadan)**
```bash
cd sdk
make build
sudo cp bin/ophiron-sdk /usr/local/bin/
# veya sudo olmadan:
mkdir -p ~/.local/bin
cp bin/ophiron-sdk ~/.local/bin/
export PATH=$PATH:~/.local/bin
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
```

**Seçenek 3: Lokal Build (Development)**
```bash
cd sdk
make build
# Binary: sdk/bin/ophiron-sdk
# Kullanım: ./bin/ophiron-sdk veya PATH'e ekle
export PATH=$PATH:$(pwd)/bin
```

**Test:**
```bash
ophiron-sdk --help
ophiron-sdk create --help
```

---

## SDK Kurulumu ve CLI Komutları

```bash
ophiron-sdk --help
ophiron-sdk create --help
ophiron-sdk validate --help
ophiron-sdk add-language --help
```

Sık kullanılan komutlar:
- `create`: Yeni plugin şablonu üretir.
- `validate`: `plugin.json` ve dosya yapısını kontrol eder.
- `add-language`: Ek i18n paketleri oluşturur.

### CLI Parametrelerinin Özeti

| Parametre | Açıklama | Zorunlu |
|-----------|----------|---------|
| `--name` | Plugin adı (snake_case) | ✅ |
| `--author` | Geliştirici adı | ✅ |
| `--description` | Kısa açıklama | ✅ |
| `--category` | `security`, `network`, `monitoring`, `automation`, `development`, `storage`, `other` | ✅ |
| `--languages` | Desteklenen diller, `"en,tr,de"` formatında | ✅ |
| `--version` | Semantic versiyon (varsayılan `1.0.0`) | ✅ |
| `--email` | Geliştirici email adresi | ✅ (Makefile metadata için) |
| `--developer-github` | Profil URL'si | ✅ |
| `--project-github` | Plugin reposu | ✅ |
| `--os-support` | `linux,darwin,windows` vb. | ✅ |
| `--port` | Port mode kullanacaksanız | Opsiyonel |

---

## Yeni Plugin Oluşturma

> **Ön Koşul:** SDK'yı kurmuş olmalısınız. Kurulum için [SDK Kurulumu](#ön-gereksinimler-ve-ortam-kurulumu) bölümüne bakın.

### 1. Plugin Oluşturma Komutu

SDK kurulumu yaptıktan sonra `ophiron-sdk` komutu her yerden kullanılabilir:

```bash
cd plugins

ophiron-sdk create \
  --name url_scanner \
  --author "Jane Doe" \
  --email "jane@example.com" \
  --developer-github "https://github.com/janedoe" \
  --project-github "https://github.com/janedoe/url_scanner" \
  --description "Scan URLs with VirusTotal" \
  --category security \
  --languages "en,tr,de" \
  --version "1.0.0" \
  --os-support "linux,darwin,windows"
```

### 2. Oluşturulan Dizin Yapısı
```
url_scanner/
├── plugin.json              # Plugin metadata ve ayarlar
├── Makefile                 # Build komutları ve metadata
├── README.md                # Plugin dokümantasyonu
├── __init__.py              # Python package marker
├── apps.py                  # Django AppConfig
├── views.py                 # Django views
├── urls.py                  # URL routing
├── go/
│   ├── go.mod               # Go dependencies
│   ├── go.sum
│   └── main.go              # Go backend
├── templates/
│   └── plugins/
│       └── url_scanner/
│           └── index.html   # Ana template
├── static/
│   └── plugins/
│       └── url_scanner/
│           ├── css/
│           │   └── style.css
│           └── js/
│               └── main.js
└── locale/
    ├── en/
    │   └── LC_MESSAGES/
    │       └── django.po
    ├── tr/
    │   └── LC_MESSAGES/
    │       └── django.po
    └── de/
        └── LC_MESSAGES/
            └── django.po
```

**Plugin Kurulum Konumu:**
- Geliştirme: `/plugins/url_scanner/` (ana plugins dizini)
- İndirilen: `/plugins/downloader/url_scanner/` (marketplace veya manuel kurulum)

**Not:** SDK tarafından locale dosyaları, temel template ve CSS/JS şablonları otomatik doldurulur.

---

## plugin.json Şeması ve Metadata

### SDK ile Oluşturulan Plugin.json (Port Mode)
SDK `create` komutu ile varsayılan olarak port mode için şablon oluşturulur:

```json
{
  "name": "url_scanner",
  "display_name": {"en": "URL Scanner", "tr": "URL Tarayıcı"},
  "version": "1.0.0",
  "description": {
    "en": "Scan URLs with VirusTotal",
    "tr": "URL'leri VirusTotal ile tara"
  },
  "author": {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "github": "https://github.com/janedoe"
  },
  "category": "security",
  "icon": "fas fa-cube",
  "route": "url_scanner",
  "supported_languages": ["en", "tr", "de"],
  "go_port": 8081,
  "go_binary": "url_scanner",
  "permissions": ["view_url_scanner"],
  "dependencies": [],
  "compatibility": {
    "ophiron_version": ">=1.0.0",
    "python_version": ">=3.8",
    "go_version": ">=1.19"
  },
  "settings": {},
  "dashboard_widget": {"enabled": false},
  "project_github": "https://github.com/janedoe/url_scanner",
  "sandbox": {
    "enabled": true,
    "allowed_ports": [8081],
    "allowed_paths": ["/tmp"],
    "max_memory": 268435456,
    "max_cpu": 25,
    "network_access": false,
    "file_system_access": "readonly"
  }
}
```

### Embedded Mode için Minimal Örnek
Embedded mode kullanmak için `go_port` alanını kaldırın:

```json
{
  "name": "url_scanner",
  "display_name": {"en": "URL Scanner", "tr": "URL Tarayıcı"},
  "version": "1.0.0",
  "description": {
    "en": "Scan URLs with VirusTotal",
    "tr": "URL'leri VirusTotal ile tara"
  },
  "author": {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "github": "https://github.com/janedoe"
  },
  "project_github": "https://github.com/janedoe/url_scanner",
  "category": "security",
  "icon": "fas fa-shield-virus",
  "route": "url-scanner",
  "supported_languages": ["en", "tr", "de"],
  "go_binary": "url_scanner",
  "permissions": ["view_url_scanner", "scan_url"],
  "dependencies": [],
  "compatibility": {
    "ophiron_version": ">=1.0.0",
    "python_version": ">=3.10",
    "go_version": ">=1.21"
  },
  "settings": {},
  "dashboard_widget": {"enabled": false},
  "sudo_required": false,
  "sandbox": {
    "enabled": true,
    "allowed_paths": ["/tmp"],
    "max_memory": 536870912,
    "max_cpu": 50,
    "network_access": true,
    "file_system_access": "readonly"
  }
}
```

### Önemli Alanlar

**Çalışma Modu Seçimi:**
- **`go_port`** varsa → **Port Mode** (sürekli çalışan HTTP server)
- **`go_port`** yoksa → **Embedded Mode** (her istek için izole process)

**Zorunlu Alanlar:**
- **`name`**: Plugin internal adı (snake_case)
- **`display_name`**: Çok dilli gösterim adı
- **`version`**: Semantic versioning (örn: "1.0.0")
- **`description`**: Çok dilli açıklama
- **`author.name`**: Geliştirici adı
- **`category`**: security, network, monitoring, automation, development, storage, other
- **`route`**: Plugin URL path'i (örn: "url-scanner" → `/url-scanner/`)
- **`go_binary`**: Çalıştırılabilir binary adı

**Önemli Opsiyonel Alanlar:**
- **`permissions`**: Django izinleri; `view_<plugin>`, özel API izinleri
- **`settings`**: Kullanıcı yapılandırma alanları (API key, ayarlar vb.)
- **`sudo_required` + `sudo_reason`**: Kernel/disk işlemleri için
- **`sandbox`**: Bellek, CPU, ağ ve dosya erişim limitleri (metadata olarak)
- **`project_github` / `author.github`**: Marketplace ve destek için önerilen
- **`scheduled_tasks`**: Otomatik zamanlanmış görevler
- **`dashboard_widget`**: Dashboard widget entegrasyonu

### Settings Şeması (Örnek)
```json
"settings": {
  "api_key": {
    "type": "string",
    "required": true,
    "default": "",
    "description": {
      "en": "VirusTotal API Key",
      "tr": "VirusTotal API Anahtarı"
    },
    "placeholder": {
      "en": "Enter your API key"
    }
  },
  "scan_timeout": {
    "type": "integer",
    "required": false,
    "default": 60,
    "min": 10,
    "max": 300
  }
}
```

### Zamanlanmış Görevler (Scheduled Tasks)
Plugin'ler otomatik zamanlanmış görevler tanımlayabilir. `plugin.json`'a ekleyin:

```json
"scheduled_tasks": [
  {
    "endpoint": "/api/daily-scan",
    "schedule_type": "daily",
    "schedule_time": "02:00",
    "enabled": true,
    "requires_api_key": true,
    "data": {
      "scan_depth": "full"
    }
  },
  {
    "endpoint": "/api/weekly-report",
    "schedule_type": "weekly",
    "schedule_days": ["monday"],
    "schedule_time": "08:00",
    "enabled": true
  },
  {
    "endpoint": "/api/custom-task",
    "schedule_type": "cron",
    "schedule_cron": "0 */6 * * *",
    "enabled": false
  }
]
```

**Schedule Type Seçenekleri:**
- `daily`: Her gün belirtilen saatte
- `weekly`: Belirtilen günlerde (`schedule_days`: ["monday", "tuesday", ...])
- `monthly`: Ayın belirtilen gününde (`schedule_day`: 1-31)
- `cron`: Cron expression (`schedule_cron`: "0 */6 * * *")

**Önemli:** Zamanlanmış görevler sistem başlatıldığında `plugins/auto_scheduler.py` tarafından otomatik oluşturulur.

---

## Makefile Standartları ve Build Akışı

SDK'nın ürettiği Makefile, geliştirici kimliği ve platform bilgilerini içerir.

```makefile
.PHONY: build test clean run dev deps fmt lint validate package build-prod build-all

# ============================================
# Plugin Metadata (Zorunlu Bilgiler)
# ============================================
PLUGIN_NAME := url_scanner
VERSION := 1.0.0
BINARY_NAME := url_scanner
GO_PORT := 8081

# Developer Bilgileri
DEVELOPER_NAME := Jane Doe
DEVELOPER_EMAIL := jane@example.com
DEVELOPER_GITHUB := https://github.com/janedoe

# Proje Bilgileri
PROJECT_GITHUB := https://github.com/janedoe/url_scanner

# Desteklenen İşletim Sistemleri
SUPPORTED_OS := linux darwin windows

# API Endpoints (dokümantasyon amaçlı)
API_ENDPOINTS := /api/health /api/scan

# Build
build:
	@echo "Building $(PLUGIN_NAME) v$(VERSION)..."
	cd go && go build -ldflags="-s -w" -o $(BINARY_NAME) .

# Tüm platformlar için build
build-all: clean
	@mkdir -p dist/binaries
	@for os in $(SUPPORTED_OS); do \
		... # linux/darwin/windows için GOOS/GOARCH kombinasyonları
	done

run:
	cd go && MODE=embedded ./$(BINARY_NAME)

dev:
	@which air >/dev/null || go install github.com/cosmtrek/air@latest
	cd go && MODE=embedded air

test:
	cd go && go test -v ./...

deps:
	cd go && go mod download && go mod tidy

build-prod:
	cd go && CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o $(BINARY_NAME) .

package: build-prod
	mkdir -p dist
	zip -r dist/$(PLUGIN_NAME)-$(VERSION).zip plugin.json go/$(BINARY_NAME) templates/ static/ README.md
```

**Notlar:**
- Metadata blokları Marketplace yayın süreçleri için gereklidir.
- `build-all` çıktıları `dist/binaries/` altında tutulur.
- Paketleme sırasında `.git`, `.DS_Store` vb. dosyalar hariç tutulur.

---

## Go Backend Geliştirme

### Embedded Mode Ana Şablon
```go
package main

import (
    "bufio"
    "encoding/json"
    "fmt"
    "log"
    "os"
    "time"
)

type EmbeddedRequest struct {
    Method   string                 `json:"method"`
    Endpoint string                 `json:"endpoint"`
    Data     map[string]interface{} `json:"data"`
    APIKey   string                 `json:"api_key"`
}

type EmbeddedResponse struct {
    Status  string      `json:"status"`
    Message string      `json:"message,omitempty"`
    Data    interface{} `json:"data,omitempty"`
    Time    string      `json:"time"`
}

func main() {
    scanner := bufio.NewScanner(os.Stdin)
    log.SetOutput(os.Stderr)

    for scanner.Scan() {
        line := scanner.Text()
        if line == "" {
            continue
        }

        var req EmbeddedRequest
        if err := json.Unmarshal([]byte(line), &req); err != nil {
            sendErrorResponse(fmt.Sprintf("Invalid request: %v", err))
            continue
        }

        resp := handleRequest(req)
        bytes, _ := json.Marshal(resp)
        fmt.Println(string(bytes))
    }
}
```

### Port Mode Örneği
```go
func main() {
    port := flag.String("port", "8091", "Server port")
    flag.Parse()

    mux := http.NewServeMux()
    mux.HandleFunc("/api/health", handleHealth)
    mux.HandleFunc("/api/scan", handleScan)

    server := &http.Server{Addr: ":" + *port, Handler: mux}
    log.Printf("Server on %s", *port)
    log.Fatal(server.ListenAndServe())
}
```

### Embedded Mode vs Port Mode Karar Tablosu

| Özellik | Embedded Mode | Port Mode |
|---------|---------------|-----------|
| **Process Model** | Her istek için yeni process | Sürekli çalışan HTTP server |
| **Port Gereksinimi** | ❌ Yok | ✅ Gerekli (8081-8099) |
| **İletişim** | stdin/stdout JSON | HTTP JSON API |
| **Kaynak Kullanımı** | Düşük (ephemeral) | Yüksek (persistent) |
| **Gecikme** | ~200-500ms (process start) | ~10-50ms (HTTP call) |
| **İzolasyon** | ✅ Mükemmel | ⚠️ Orta |
| **Crash Etkisi** | Sadece o istek | Tüm istekler |
| **Önerilen Kullanım** | Düşük frekanslı, güvenlik kritik | Yüksek frekanslı, hızlı response |

### Go Backend En İyi Pratikler

**Embedded Mode İçin:**
```go
func main() {
    // MUTLAKA: Log'ları stderr'e yönlendir (stdout JSON için)
    log.SetOutput(os.Stderr)
    
    scanner := bufio.NewScanner(os.Stdin)
    for scanner.Scan() {
        line := scanner.Text()
        if line == "" {
            continue
        }
        
        var req EmbeddedRequest
        if err := json.Unmarshal([]byte(line), &req); err != nil {
            sendErrorResponse(fmt.Sprintf("Invalid request: %v", err))
            continue
        }
        
        // API key kontrolü
        if req.APIKey == "" && isAPIKeyRequired(req.Endpoint) {
            sendErrorResponse("API key required")
            continue
        }
        
        // Panic recovery
        func() {
            defer func() {
                if r := recover(); r != nil {
                    sendErrorResponse(fmt.Sprintf("Panic: %v", r))
                }
            }()
            
            resp := handleRequest(req)
            bytes, _ := json.Marshal(resp)
            fmt.Println(string(bytes)) // stdout'a JSON yaz
        }()
    }
}
```

**Port Mode İçin:**
```go
func main() {
    port := getEnv("PORT", "8081")
    
    mux := http.NewServeMux()
    mux.HandleFunc("/api/health", handleHealth)
    mux.HandleFunc("/api/scan", handleScan)
    
    server := &http.Server{
        Addr:         ":" + port,
        Handler:      mux,
        ReadTimeout:  30 * time.Second,
        WriteTimeout: 30 * time.Second,
    }
    
    log.Printf("Server starting on port %s", port)
    log.Fatal(server.ListenAndServe())
}
```

**Genel Best Practices:**
- ✅ Timeout kullan: `context.WithTimeout` ile uzun işlemleri sınırla
- ✅ Hata mesajları açık ve kullanıcı dostu olsun
- ✅ API key'i environment değişken veya request'ten al
- ✅ Büyük dosya işlemlerinde streaming kullan
- ✅ Concurrency için `sync.WaitGroup` veya `errgroup` kullan
- ❌ Global state kullanma (her request izole olmalı)
- ❌ Panic'e izin verme, her zaman recover et
- ❌ stdout'a log yazma (embedded mode'da sadece JSON response)

---

## Django Entegrasyonu

### apps.py ve __init__.py
```python
# __init__.py
default_app_config = 'plugins.url_scanner.apps.UrlScannerConfig'

# apps.py
from django.apps import AppConfig

class UrlScannerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.url_scanner'
    verbose_name = 'URL Scanner'
```

### urls.py
```python
from django.urls import path
from . import views

app_name = 'url_scanner'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('api/scan/', views.scan_api, name='scan'),
    path('api/check-key/', views.check_api_key_api, name='check_key'),
]
```

### views.py (Embedded Mode Örneği)
```python
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.shortcuts import render
import json

from plugins.base import BasePlugin
from plugins.utils import get_plugin_setting

@login_required
def index_view(request):
    """Plugin ana sayfası"""
    return render(request, 'plugins/url_scanner/index.html', {
        'plugin': BasePlugin('url_scanner').get_metadata(),
    })

@require_http_methods(["POST"])
@login_required
def scan_api(request):
    """URL tarama API endpoint"""
    # Embedded mode için plugin instance oluştur
    plugin = BasePlugin('url_scanner', use_embedded=True)
    
    # Request body'den veri al
    data = json.loads(request.body)
    url = data.get('url', '').strip()

    if not url:
        return JsonResponse({
            'status': 'error', 
            'message': 'URL is required'
        }, status=400)

    # Kullanıcı ayarlarından API key al
    api_key = get_plugin_setting('url_scanner', 'api_key', 
                                  user=request.user, default='')
    if not api_key:
        return JsonResponse({
            'status': 'error', 
            'message': 'API key not configured'
        }, status=400)

    # Go backend'e istek gönder
    response = plugin.go_bridge.request(
        method='POST',
        endpoint='/api/scan',
        data={'url': url},
        api_key=api_key,
        timeout=30
    )

    return JsonResponse(response, status=200 if response.get('status') == 'success' else 400)
```

### views.py (Port Mode Örneği)
```python
@require_http_methods(["POST"])
@login_required
def scan_api(request):
    """URL tarama API endpoint (Port Mode)"""
    # Port mode için plugin instance (use_embedded=False)
    plugin = BasePlugin('url_scanner', use_embedded=False)
    
    # Go service çalışıyor mu kontrol et
    if not plugin.go_bridge.is_running():
        plugin.go_bridge.start_service()
    
    data = json.loads(request.body)
    url = data.get('url', '').strip()

    if not url:
        return JsonResponse({
            'status': 'error', 
            'message': 'URL is required'
        }, status=400)

    # HTTP request ile Go backend'e istek gönder
    try:
        response = plugin.go_bridge.request('POST', '/api/scan', data={'url': url})
        return JsonResponse(response.json(), status=response.status_code)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Service error: {str(e)}'
        }, status=500)
```

**Önemli Notlar:**
- **Embedded Mode:** `BasePlugin(..., use_embedded=True)` - Her istek için yeni process
- **Port Mode:** `BasePlugin(..., use_embedded=False)` - HTTP istekleri sürekli çalışan servise
- **Ayar Yönetimi:** `get_plugin_setting()` ve `set_plugin_setting()` kullan
- **CSRF Token:** Django template'de `{% csrf_token %}` veya JavaScript'te `getCookie('csrftoken')`
- **Response Format:** Go backend'den gelen JSON'u direkt frontend'e aktar

---

## Frontend, Statik Dosyalar ve i18n

### Template Yapısı
```html
{% extends 'plugins/base.html' %}
{% load i18n %}
{% load static %}

{% block plugin_title %}{% trans "URL Scanner" %}{% endblock %}
{% block plugin_styles %}
<link rel="stylesheet" href="{% static 'plugins/url_scanner/css/style.css' %}">
{% endblock %}

{% block plugin_content %}
<!-- UI -->
{% endblock %}

{% block plugin_scripts %}
<script src="{% static 'plugins/url_scanner/js/main.js' %}"></script>
{% endblock %}
```

### JavaScript ile API Çağrısı
```javascript
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('scan-btn');
  const input = document.getElementById('url-input');
  const csrf = window.CSRF_TOKEN || getCookie('csrftoken');

  btn.addEventListener('click', () => {
    fetch('/url-scanner/api/scan/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf,
      },
      body: JSON.stringify({ url: input.value.trim() }),
    })
      .then(res => res.json())
      .then(renderResults)
      .catch(err => showError(err.message));
  });
});
```

### Çoklu Dil Desteği (i18n) - Detaylı Kılavuz

#### 1. Temel Yapı

Plugin'iniz birden fazla dilde çalışabilir. SDK otomatik olarak locale yapısını oluşturur:

```
my_plugin/
└── locale/
    ├── en/LC_MESSAGES/
    │   ├── django.po      # Çeviri kaynağı
    │   └── django.mo      # Derlenmiş çeviri
    ├── tr/LC_MESSAGES/
    │   ├── django.po
    │   └── django.mo
    └── de/LC_MESSAGES/
        ├── django.po
        └── django.mo
```

#### 2. Çeviri Dosyası Oluşturma (.po Dosyaları)

**İngilizce (locale/en/LC_MESSAGES/django.po):**
```po
# English translations for My Plugin
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: en\n"

# Basit çeviri
msgid "URL Scanner"
msgstr "URL Scanner"

msgid "Scan URL"
msgstr "Scan URL"

msgid "Enter URL to scan"
msgstr "Enter URL to scan"

msgid "Scanning..."
msgstr "Scanning..."

msgid "Results"
msgstr "Results"

msgid "Error"
msgstr "Error"

# Değişkenli çeviri
#, python-format
msgid "Scanned %(count)s URLs"
msgstr "Scanned %(count)s URLs"

# Çoğul çeviri
msgid "Found %(count)s threat"
msgid_plural "Found %(count)s threats"
msgstr[0] "Found %(count)s threat"
msgstr[1] "Found %(count)s threats"
```

**Türkçe (locale/tr/LC_MESSAGES/django.po):**
```po
# Turkish translations for My Plugin
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: tr\n"

msgid "URL Scanner"
msgstr "URL Tarayıcı"

msgid "Scan URL"
msgstr "URL Tara"

msgid "Enter URL to scan"
msgstr "Taranacak URL'yi girin"

msgid "Scanning..."
msgstr "Taranıyor..."

msgid "Results"
msgstr "Sonuçlar"

msgid "Error"
msgstr "Hata"

#, python-format
msgid "Scanned %(count)s URLs"
msgstr "%(count)s URL tarandı"

msgid "Found %(count)s threat"
msgid_plural "Found %(count)s threats"
msgstr[0] "%(count)s tehdit bulundu"
msgstr[1] "%(count)s tehdit bulundu"
```

**Almanca (locale/de/LC_MESSAGES/django.po):**
```po
# German translations for My Plugin
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: de\n"

msgid "URL Scanner"
msgstr "URL-Scanner"

msgid "Scan URL"
msgstr "URL scannen"

msgid "Enter URL to scan"
msgstr "Geben Sie die zu scannende URL ein"

msgid "Scanning..."
msgstr "Wird gescannt..."

msgid "Results"
msgstr "Ergebnisse"

msgid "Error"
msgstr "Fehler"

#, python-format
msgid "Scanned %(count)s URLs"
msgstr "%(count)s URLs gescannt"

msgid "Found %(count)s threat"
msgid_plural "Found %(count)s threats"
msgstr[0] "%(count)s Bedrohung gefunden"
msgstr[1] "%(count)s Bedrohungen gefunden"
```

#### 3. Template'de Çeviri Kullanımı

**Basit Çeviriler:**
```html
{% load i18n %}

<h1>{% trans "URL Scanner" %}</h1>
<p>{% trans "Enter URL to scan" %}</p>
<button>{% trans "Scan URL" %}</button>
```

**Değişkenli Çeviriler:**
```html
{% load i18n %}

<!-- Tek değişken -->
<p>
{% blocktrans with count=url_count %}
Scanned {{ count }} URLs
{% endblocktrans %}
</p>

<!-- Çoklu değişken -->
<p>
{% blocktrans with total=total_count success=success_count %}
Scanned {{ total }} URLs, {{ success }} successful
{% endblocktrans %}
</p>
```

**Çoğul Çeviriler:**
```html
{% load i18n %}

<p>
{% blocktrans count counter=threat_count %}
Found {{ counter }} threat
{% plural %}
Found {{ counter }} threats
{% endblocktrans %}
</p>
```

**Context ile Çeviriler (aynı kelime farklı anlamlarda):**
```html
{% trans "Save" context "button" %}
{% trans "Save" context "menu" %}
```

#### 4. JavaScript'te Çeviri

**Yöntem 1: Template'de Tanımla**
```html
<script>
const translations = {
    'scanning': '{% trans "Scanning..." %}',
    'error': '{% trans "Error" %}',
    'results': '{% trans "Results" %}',
    'scan_completed': '{% trans "Scan completed successfully" %}',
    'invalid_url': '{% trans "Invalid URL format" %}',
};

// Kullanım
function showMessage(key) {
    alert(translations[key]);
}
</script>
```

**Yöntem 2: Django i18n JavaScript Catalog**
```html
{% load i18n %}

<script src="{% url 'javascript-catalog' %}"></script>
<script>
    // gettext kullanımı
    alert(gettext('Scanning...'));
    
    // ngettext (çoğul)
    var count = 5;
    var message = ngettext(
        'Found %s threat',
        'Found %s threats',
        count
    );
    alert(interpolate(message, [count]));
    
    // pgettext (context)
    alert(pgettext('button', 'Save'));
</script>
```

#### 5. Python/Django View'de Çeviri

```python
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

@login_required
def scan_api(request):
    # Basit çeviri
    message = _("Scan started successfully")
    
    # Değişkenli çeviri
    error = _("Failed to scan %(url)s") % {'url': url}
    
    # Çoğul çeviri
    count = 5
    result = ngettext(
        'Found %(count)d threat',
        'Found %(count)d threats',
        count
    ) % {'count': count}
    
    return JsonResponse({'message': message})
```

#### 6. Çevirileri Derleme ve Aktifleştirme

```bash
cd /home/jonh/Desktop/ophiron

# Sanal ortamı aktifleştir
source venv/bin/activate

# TÜM plugin'ler için çevirileri derle
python manage.py compilemessages

# Sadece belirli bir dil için
python manage.py compilemessages --locale=tr
python manage.py compilemessages --locale=de

# Django'yu yeniden başlat
sudo systemctl restart ophiron
```

#### 7. Yeni Dil Ekleme

**SDK ile (Önerilen):**
```bash
cd /home/jonh/Desktop/ophiron/plugins
ophiron-sdk add-language --plugin my_plugin --language fr
```

Bu komut otomatik olarak:
- `locale/fr/LC_MESSAGES/` dizinini oluşturur
- `django.po` dosyasını oluşturur
- `plugin.json`'daki `supported_languages` dizisine ekler

**Manuel:**
```bash
cd /home/jonh/Desktop/ophiron/plugins/my_plugin

# Dizin oluştur
mkdir -p locale/fr/LC_MESSAGES

# .po dosyası oluştur
cat > locale/fr/LC_MESSAGES/django.po << 'EOF'
# French translations for My Plugin
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: fr\n"

msgid "URL Scanner"
msgstr "Scanner d'URL"

msgid "Scan URL"
msgstr "Scanner l'URL"

msgid "Enter URL to scan"
msgstr "Entrez l'URL à scanner"
EOF

# plugin.json'ı güncelle
# "supported_languages": ["en", "tr", "de", "fr"]
```

#### 8. plugin.json'da Çoklu Dil

```json
{
  "name": "url_scanner",
  "display_name": {
    "en": "URL Scanner",
    "tr": "URL Tarayıcı",
    "de": "URL-Scanner",
    "fr": "Scanner d'URL"
  },
  "description": {
    "en": "Scan URLs for security threats",
    "tr": "URL'leri güvenlik tehditleri için tarayın",
    "de": "URLs auf Sicherheitsbedrohungen scannen",
    "fr": "Scanner les URL pour les menaces de sécurité"
  },
  "supported_languages": ["en", "tr", "de", "fr"],
  "settings": {
    "api_key": {
      "type": "string",
      "description": {
        "en": "VirusTotal API Key",
        "tr": "VirusTotal API Anahtarı",
        "de": "VirusTotal API-Schlüssel",
        "fr": "Clé API VirusTotal"
      },
      "placeholder": {
        "en": "Enter your API key",
        "tr": "API anahtarınızı girin",
        "de": "Geben Sie Ihren API-Schlüssel ein",
        "fr": "Entrez votre clé API"
      }
    }
  }
}
```

#### 9. Dil Seçim Mantığı

Sistem şu sırayla dil seçer:
1. Kullanıcının profil dil tercihi kontrol edilir
2. Plugin bu dili destekliyorsa kullanılır
3. Desteklemiyorsa fallback sırası: `tr` → `de` → `en`
4. Hiçbiri yoksa varsayılan dil: `en`

#### 10. Test ve Doğrulama

```bash
# Çevirileri kontrol et
cd /home/jonh/Desktop/ophiron
source venv/bin/activate

# Eksik çevirileri bul
python manage.py makemessages --all --no-obsolete

# Fuzzy çevirileri kontrol et (belirsiz çeviriler)
grep -r "fuzzy" plugins/my_plugin/locale/

# Derleme hatalarını kontrol et
python manage.py compilemessages --verbosity 3
```

#### 11. i18n En İyi Pratikleri

**✅ YAPILMASI GEREKENLER:**
- Her zaman en az `en` (İngilizce) çevirisi sağlayın
- Çevirileri kısa ve net tutun
- Teknik terimleri tutarlı kullanın
- Değişkenler için `%(name)s` formatı kullanın
- Çoğul formlar için `msgid_plural` kullanın
- Çevirileri düzenli derleyin

**❌ YAPILMAMASI GEREKENLER:**
- Hard-coded metinler yazmayın, her zaman `{% trans %}` kullanın
- HTML tag'leri çeviri içine koymayın
- Çok uzun metinler yazmayın (satır sınırı ~80 karakter)
- Çevirileri derlemeden test etmeyin
- Context olmadan aynı kelimeyi farklı anlamlarda kullanmayın

#### 12. Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| Çeviriler görünmüyor | `compilemessages` çalıştırın, Django'yu restart edin |
| Yanlış dil gösteriliyor | Kullanıcı profil dilini ve `supported_languages` kontrol edin |
| `.mo` dosyası yok | `compilemessages` komutu hata vermiş olabilir, kontrol edin |
| Fuzzy çeviriler | `.po` dosyasında `#, fuzzy` satırlarını bulup düzeltin |
| Çoğul çalışmıyor | `msgid_plural` ve `msgstr[0]`, `msgstr[1]` kullanın |

---

## Plugin Ayarları (Settings) ve Güvenli Veri Yönetimi

### Ayar Tanımlama
- `plugin.json` içindeki `settings` nesnesi.
- Tipler: `string`, `integer`, `boolean`, `choice`, `text`.
- Çoklu dil açıklamalar, placeholder, min/max.

### Ayar Okuma/Yazma
```python
from plugins.utils import get_plugin_setting, set_plugin_setting

api_key = get_plugin_setting('url_scanner', 'api_key', user=request.user, default='')
set_plugin_setting('url_scanner', 'api_key', 'new-key', user=request.user)
```

### Go Backend'de Ayar Kullanma
- API key `req.APIKey` alanından gelir.
- Diğer ayarlar `req.Data` içinde gönderilebilir.

### Gizli Veriler
- API key gibi veriler DB'de şifrelenir.
- Loglara yazarken maskeleme yapın.

---

## Test, Paketleme ve Dağıtım

### Go Testleri
```bash
cd plugins/url_scanner/go
go test -v ./...
go test -v -coverprofile=coverage.out ./...
```

### Manual Embedded Test
```bash
cd go
MODE=embedded ./url_scanner <<'EOF'
{"method":"GET","endpoint":"/api/health","data":{}}
EOF
```

### Django Tarafı
```bash
cd /home/jonh/Desktop/ophiron
source venv/bin/activate
python manage.py collectstatic --noinput
python manage.py compilemessages
sudo systemctl restart ophiron
```

### Paketleme

**Temel Paketleme:**
```bash
cd plugins/url_scanner
make package
# dist/url_scanner-1.0.0.zip oluşur
```

**Tüm Platformlar için Paketleme:**
```bash
make package-all
# dist/url_scanner-1.0.0-linux-amd64.zip
# dist/url_scanner-1.0.0-linux-arm64.zip
# dist/url_scanner-1.0.0-darwin-amd64.zip
# dist/url_scanner-1.0.0-darwin-arm64.zip
# dist/url_scanner-1.0.0-windows-amd64.zip
```

**Paket İçeriği:**
```
url_scanner-1.0.0.zip
├── plugin.json          # Metadata
├── go/url_scanner       # Binary (Linux)
├── templates/           # Django templates
├── static/              # CSS, JS, images
├── locale/              # i18n çevirileri
├── README.md            # Dokümantasyon
└── CHANGELOG.md         # Versiyon geçmişi
```

**Makefile Package Komutları:**
```makefile
# Package for current platform
package: build-prod
	@mkdir -p dist
	@zip -r dist/$(PLUGIN_NAME)-$(VERSION).zip \
		plugin.json \
		go/$(BINARY_NAME) \
		templates/ \
		static/ \
		locale/ \
		README.md \
		-x "*.git*" "*.DS_Store" "*.swp"

# Package for all platforms
package-all: build-all
	@mkdir -p dist
	@for os in linux darwin windows; do \
		for arch in amd64 arm64; do \
			zip -r dist/$(PLUGIN_NAME)-$(VERSION)-$$os-$$arch.zip \
				plugin.json \
				dist/binaries/$(BINARY_NAME)-$$os-$$arch* \
				templates/ \
				static/ \
				locale/ \
				README.md; \
		done; \
	done
```

### Plugin Yükleme ve Marketplace

**Manuel Yükleme:**
```bash
# 1. Zip dosyasını plugins/ dizinine kopyala
cp url_scanner-1.0.0.zip /home/jonh/Desktop/ophiron/plugins/

# 2. Unzip
cd /home/jonh/Desktop/ophiron/plugins
unzip url_scanner-1.0.0.zip

# 3. Binary'yi executable yap
chmod +x url_scanner/go/url_scanner

# 4. Dependencies yükle
cd url_scanner/go
go mod download

# 5. Django'ya entegre et
cd /home/jonh/Desktop/ophiron
source venv/bin/activate
python manage.py collectstatic --noinput
python manage.py compilemessages
sudo systemctl restart ophiron
```

**SDK ile Yükleme (Planlanan):**
```bash
# Local zip dosyasından
ophiron-sdk install --from ./url_scanner-1.0.0.zip

# GitHub'dan
ophiron-sdk install --from github.com/username/url_scanner

# Marketplace'den
ophiron-sdk install url_scanner
```

**Marketplace Özellikleri (Planlanan):**
- Plugin arama ve keşfetme
- Versiyon yönetimi ve güncelleme
- Dependency otomatik yükleme
- Rating ve review sistemi
- Güvenlik taraması ve doğrulama
- Otomatik kurulum ve konfigürasyon

**Plugin Silme:**
```bash
# Manuel
rm -rf /home/jonh/Desktop/ophiron/plugins/url_scanner
sudo systemctl restart ophiron

# SDK ile (planlanan)
ophiron-sdk uninstall url_scanner
```

---

## Sorun Giderme, En İyi Pratikler ve Kontrol Listeleri

### Yaygın Sorunlar
| Sorun | Çözüm |
|-------|-------|
| Plugin görünmüyor | Dizini `plugins/` altında, `plugin.json` valid, `python manage.py collectstatic`, restart |
| CSRF 403 | Template'de `window.CSRF_TOKEN`, fetch header `X-CSRFToken` |
| JSON parse error | Go backend sadece JSON döndürmeli, HTML log yok |
| Embedded timeout | `timeout` parametresini arttırın, Go tarafında context kullanın |
| Static dosya yüklenmedi | `collectstatic`, izinler, URL kontrolü |

### En İyi Pratikler
- **Embedded mode** varsayılanı kullanın (daha güvenli).
- API key gerektiren pluginlerde settings zorunlu yapın.
- Logları stderr'e yazın, stdout sadece JSON.
- `build-all` ile cross-platform binary üretin.
- `validate` komutu ile yayın öncesi kontrol edin.
- Sudo gerekiyorsa `sudo_reason` doldurun.

### Hazırlık Kontrol Listesi
1. `ophiron-sdk create ...` ile plugin oluşturuldu.
2. `plugin.json` metadata + settings + sandbox doğru.
3. Makefile metadata blokları dolduruldu.
4. Go backend health endpoint'i çalışıyor.
5. Django `views/urls/templates` tamamlandı.
6. i18n `.po` dosyaları güncel, `compilemessages` koştu.
7. `make test`, `make build`, `make package` başarılı.
8. Dokümantasyon ve README güncel.

---

## Hızlı Referans (Cheat Sheet)

### SDK Kurulumu (İlk Kez)
```bash
# Sistem geneli (önerilen)
cd sdk
sudo make install

# Kullanıcı dizini (sudo olmadan)
cd sdk
make build
mkdir -p ~/.local/bin
cp bin/ophiron-sdk ~/.local/bin/
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc
```

### Plugin Oluşturma ve Yönetim
```bash
# Plugin oluştur (SDK kurulu olmalı)
cd plugins
ophiron-sdk create \
  --name demo_plugin \
  --author "Dev" \
  --email "dev@example.com" \
  --developer-github "https://github.com/dev" \
  --project-github "https://github.com/dev/demo_plugin" \
  --category other \
  --languages "en,tr" \
  --os-support "linux" \
  --version "1.0.0"

# Dil ekle
ophiron-sdk add-language --plugin demo_plugin --language fr

# Validasyon
ophiron-sdk validate --plugin demo_plugin
```

### Django Komutları
```bash
source venv/bin/activate

# Static dosyalar
python manage.py collectstatic --noinput

# i18n çevirileri derle
python manage.py compilemessages
python manage.py compilemessages --locale=tr
python manage.py compilemessages --locale=de

# Eksik çevirileri bul
python manage.py makemessages --all --no-obsolete

# Plugin registry kontrol
python manage.py shell -c "from plugins.registry import PluginRegistry as R; r = R(); r.load_all_plugins(); print(r.get_enabled_plugins())"

# Django restart
sudo systemctl restart ophiron
```

### Go / Makefile
```bash
make deps
make build
make run
make test
make fmt
make lint
make build-all
make package
```

### Scheduled Tasks (Zamanlanmış Görevler)

Plugin'ler `plugin.json` içinde otomatik zamanlanmış görevler tanımlayabilir:

```json
{
  "scheduled_tasks": [
    {
      "endpoint": "/api/scan/url",
      "schedule_type": "daily",
      "schedule_time": "06:00",
      "data": {"url": "example.com"},
      "enabled": true,
      "requires_api_key": true
    }
  ]
}
```

**Zamanlama Türleri:**
- `daily`: Her gün belirli saatte
- `weekly`: Haftalık (`schedule_days`: `"0,2,4"` Pazartesi, Çarşamba, Cuma)
- `monthly`: Aylık (`schedule_day`: 1-31)
- `custom`: Cron ifadesi (`schedule_cron`: `"0 6 * * *"`)

**Parametreler:**
- `endpoint`: Çağrılacak API endpoint
- `data`: Request JSON data
- `enabled`: Görev aktif mi?
- `requires_api_key`: API key gerekiyor mu?

Görevler plugin yüklendiğinde otomatik oluşturulur ve sistem tarafından yönetilir.

### Frontend Tasarım Rehberi - Detaylı Kılavuz

Ophiron minimal ve modern bir tasarım sistemi kullanır. Plugin geliştirirken bu standartlara uymanız kullanıcı deneyimini tutarlı tutar.

#### 1. Tasarım Felsefesi

**Temel Prensipler:**
- **Minimalizm**: Gereksiz görsel karmaşıklıktan kaçınma
- **Konsistenslik**: Tüm modüllerde tutarlı tasarım dili
- **Kullanılabilirlik**: Net ve anlaşılır navigasyon
- **Performans**: Hafif ve hızlı yüklenen arayüzler
- **Erişilebilirlik**: Tüm kullanıcılar için erişilebilir (WCAG 2.1 AA)

**Tasarım Kararları:**
- Siyah-Beyaz temel: Header ve navigasyon siyah, içerik beyaz kartlar
- Gri arka plan: Ana içerik alanı açık gri (#f8f9fa)
- Mavi vurgu: Aktif durumlar ve aksiyonlar için
- Yumuşak gölgeler: Derinlik hissi için hafif shadow'lar

#### 2. Renk Sistemi (CSS Variables)

**Ana Renkler:**
```css
:root {
  /* Primary Colors */
  --primary-black: #000000;      /* Header ve navigasyon */
  --primary-white: #ffffff;      /* Kartlar ve içerik */
  --primary-gray: #f8f9fa;       /* Ana sayfa arka planı */
  --primary-dark: #1a202c;       /* Ana metin */
  --primary-medium: #4a5568;     /* İkincil metin */
  --primary-light: #718096;      /* Açıklama metinleri */
}
```

**Vurgu Renkleri (Accent):**
```css
:root {
  --accent-red: #ff6b6b;         /* Hata, silme */
  --accent-green: #28a745;       /* Başarı */
  --accent-blue: #007bff;        /* Birincil aksiyon */
  --accent-yellow: #ffc107;      /* Uyarılar */
  --accent-cyan: #17a2b8;        /* Bilgi */
  --accent-purple: #6f42c1;      /* Özel durumlar */
  --accent-orange: #fd7e14;      /* İkincil uyarı */
}
```

**Arka Plan ve Metin:**
```css
:root {
  /* Backgrounds */
  --bg-primary: #ffffff;
  --bg-secondary: #f8f9fa;
  --bg-dark: #000000;
  
  /* Text Colors */
  --text-primary: #1a202c;
  --text-secondary: #4a5568;
  --text-light: #718096;
  --text-white: #ffffff;
  
  /* Borders */
  --border-light: #e2e8f0;
  --border-medium: #cbd5e0;
  --border-dark: #a0aec0;
}
```

#### 3. Tipografi Sistemi

**Font Aileleri:**
```css
:root {
  --font-primary: 'Inter', 'Segoe UI', 'Roboto', sans-serif;
  --font-mono: 'Fira Code', 'Monaco', 'Consolas', monospace;
}
```

**Font Boyutları:**
```css
:root {
  --text-xs: 0.75rem;      /* 12px - Küçük etiketler */
  --text-sm: 0.875rem;     /* 14px - Standart metin */
  --text-base: 1rem;       /* 16px - Body */
  --text-lg: 1.125rem;     /* 18px - Alt başlıklar */
  --text-xl: 1.25rem;      /* 20px - Bölüm başlıkları */
  --text-2xl: 1.5rem;      /* 24px - Sayfa alt başlıkları */
  --text-3xl: 1.875rem;    /* 30px - Modül başlıkları */
}
```

**Font Ağırlıkları:**
- `300`: Light - Çok hafif metinler
- `400`: Regular - Normal metin
- `500`: Medium - Butonlar, linkler
- `600`: Semi-bold - Alt başlıklar
- `700`: Bold - Başlıklar
- `800`: Extra-bold - Logo, ana başlıklar

#### 4. Spacing Sistemi (4px Grid)

```css
:root {
  --space-1: 0.25rem;      /* 4px */
  --space-2: 0.5rem;       /* 8px */
  --space-3: 0.75rem;      /* 12px */
  --space-4: 1rem;         /* 16px - Standart */
  --space-5: 1.25rem;      /* 20px */
  --space-6: 1.5rem;       /* 24px */
  --space-8: 2rem;         /* 32px */
  --space-10: 2.5rem;      /* 40px */
  --space-12: 3rem;        /* 48px */
}
```

**Border Radius:**
```css
:root {
  --radius-sm: 0.25rem;    /* 4px - Küçük butonlar */
  --radius-md: 0.5rem;     /* 8px - Kartlar */
  --radius-lg: 0.75rem;    /* 12px - Büyük kartlar */
  --radius-xl: 1rem;       /* 16px - Modal'lar */
  --radius-full: 9999px;   /* Tam yuvarlak */
}
```

**Transitions:**
```css
:root {
  --transition-fast: 0.15s ease;
  --transition-normal: 0.3s ease;
  --transition-slow: 0.5s ease;
}
```

#### 5. Plugin Template Yapısı

**Temel HTML Yapısı:**
```html
{% extends 'plugins/base.html' %}
{% load i18n static %}

{% block plugin_title %}{% trans "My Plugin" %}{% endblock %}

{% block plugin_styles %}
<link rel="stylesheet" href="{% static 'plugins/my_plugin/css/style.css' %}">
{% endblock %}

{% block plugin_content %}
<div class="plugin-container">
    <!-- Header -->
    <div class="plugin-header">
        <h1>
            <i class="fas fa-shield-alt"></i>
            {% trans "My Plugin" %}
        </h1>
        <p class="plugin-subtitle">{% trans "Plugin description" %}</p>
    </div>

    <!-- Content -->
    <div class="plugin-content">
        <!-- Kartlar -->
        <div class="plugin-card">
            <div class="card-header">
                <h3>{% trans "Section Title" %}</h3>
            </div>
            <div class="card-body">
                <!-- İçerik -->
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block plugin_scripts %}
<script src="{% static 'plugins/my_plugin/js/main.js' %}"></script>
{% endblock %}
```

**CSS Yapısı:**
```css
/* plugins/my_plugin/static/plugins/my_plugin/css/style.css */

/* CSS Variables */
:root {
    --plugin-primary: #007bff;
    --plugin-danger: #ff6b6b;
}

/* Container */
.plugin-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: var(--space-10);
    background: var(--bg-secondary);
    min-height: 100vh;
}

/* Header */
.plugin-header {
    margin-bottom: var(--space-8);
    text-align: center;
}

.plugin-header h1 {
    font-size: var(--text-3xl);
    font-weight: 800;
    color: var(--text-primary);
    margin-bottom: var(--space-2);
}

.plugin-header h1 i {
    color: var(--plugin-primary);
    margin-right: var(--space-3);
}

.plugin-subtitle {
    font-size: var(--text-base);
    color: var(--text-secondary);
}

/* Cards */
.plugin-card {
    background: var(--bg-primary);
    border-radius: var(--radius-md);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: var(--space-6);
    overflow: hidden;
}

.card-header {
    padding: var(--space-6);
    border-bottom: 1px solid var(--border-light);
}

.card-header h3 {
    font-size: var(--text-xl);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
}

.card-body {
    padding: var(--space-6);
}

/* Buttons */
.btn {
    padding: var(--space-3) var(--space-6);
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
    font-weight: 600;
    cursor: pointer;
    transition: var(--transition-fast);
    border: none;
}

.btn-primary {
    background: var(--accent-blue);
    color: var(--text-white);
}

.btn-primary:hover {
    background: #0056b3;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
}

.btn-danger {
    background: var(--accent-red);
    color: var(--text-white);
}

/* Forms */
.form-group {
    margin-bottom: var(--space-5);
}

.form-label {
    display: block;
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--space-2);
}

.form-control {
    width: 100%;
    padding: var(--space-3) var(--space-4);
    border: 2px solid var(--border-light);
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
    transition: var(--transition-fast);
}

.form-control:focus {
    outline: none;
    border-color: var(--accent-blue);
    box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}
```

#### 6. Responsive Tasarım

**Breakpoint'ler:**
```css
/* Mobil */
@media (max-width: 480px) {
    .plugin-container {
        padding: var(--space-4);
    }
    
    .plugin-header h1 {
        font-size: var(--text-xl);
    }
}

/* Tablet */
@media (max-width: 768px) {
    .plugin-container {
        padding: var(--space-6);
    }
}

/* Desktop */
@media (max-width: 1024px) {
    .plugin-container {
        max-width: 100%;
    }
}
```

**Responsive Kuralları:**
- Mobile-first yaklaşım (önce mobil, sonra büyük ekranlar)
- Touch-friendly buton boyutları (min 44x44px)
- Yatay scroll yerine vertical scroll
- Flexbox ve Grid kullanımı

#### 7. Komponent Örnekleri

**Loading Indicator:**
```html
<div class="loading-indicator">
    <i class="fas fa-spinner fa-spin"></i>
    <span>{% trans "Loading..." %}</span>
</div>
```

```css
.loading-indicator {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-6);
    color: var(--text-secondary);
}
```

**Alert Messages:**
```html
<div class="alert alert-success">
    <i class="fas fa-check-circle"></i>
    <span>{% trans "Operation successful!" %}</span>
</div>
```

```css
.alert {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-4);
    border-radius: var(--radius-md);
    margin-bottom: var(--space-4);
}

.alert-success {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
}

.alert-error {
    background: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
}
```

**Data Table:**
```html
<table class="data-table">
    <thead>
        <tr>
            <th>{% trans "Name" %}</th>
            <th>{% trans "Status" %}</th>
            <th>{% trans "Actions" %}</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Item 1</td>
            <td><span class="badge badge-success">Active</span></td>
            <td>
                <button class="btn-icon"><i class="fas fa-edit"></i></button>
                <button class="btn-icon"><i class="fas fa-trash"></i></button>
            </td>
        </tr>
    </tbody>
</table>
```

```css
.data-table {
    width: 100%;
    border-collapse: collapse;
}

.data-table th {
    background: var(--bg-secondary);
    padding: var(--space-3) var(--space-4);
    text-align: left;
    font-weight: 600;
    color: var(--text-primary);
    border-bottom: 2px solid var(--border-medium);
}

.data-table td {
    padding: var(--space-3) var(--space-4);
    border-bottom: 1px solid var(--border-light);
}

.badge {
    padding: var(--space-1) var(--space-3);
    border-radius: var(--radius-full);
    font-size: var(--text-xs);
    font-weight: 600;
}

.badge-success {
    background: var(--accent-green);
    color: white;
}
```

#### 8. Best Practices

**✅ YAPILMASI GEREKENLER:**
- CSS değişkenlerini kullan (`:root` seviyesinde)
- Tutarlı spacing kullan (4px grid sistemi)
- Semantic HTML kullan (`<header>`, `<main>`, `<section>`)
- ARIA attribute'ları ekle (erişilebilirlik)
- Responsive tasarım yap
- Loading states göster
- Error handling yap

**❌ YAPILMAMASI GEREKENLER:**
- Hard-coded renk değerleri kullanma
- Inline style kullanma
- Çok fazla nested selector
- !important kullanma (gerekmedikçe)
- Pixel-perfect obsession (esnek ol)
- Flash of Unstyled Content (FOUC)

#### 9. Performans Optimizasyonu

**CSS:**
- Minimize et ve bundle'la
- Critical CSS inline ekle
- Unused CSS'i temizle
- CSS Grid/Flexbox kullan (float yerine)

**JavaScript:**
- Defer veya async yükle
- Event delegation kullan
- Debounce/throttle işlemler
- Lazy loading uygula

**Images:**
- WebP format kullan
- Lazy loading
- Responsive images (`srcset`)
- SVG icon'lar tercih et

---

## 🎯 Özet ve Sonraki Adımlar

Bu dokümantasyon, Ophiron Plugin SDK'sının tüm yönlerini kapsamaktadır:

✅ **Tamamladığınız:**
- SDK CLI kullanımı ve plugin şablon oluşturma
- Plugin.json şeması ve metadata yönetimi
- Go backend geliştirme (Embedded/Port Mode)
- Django entegrasyonu (views, urls, templates)
- Frontend tasarımı ve i18n desteği
- Makefile standartları ve build süreci
- Plugin ayarları ve güvenli veri yönetimi
- Zamanlanmış görevler
- Paketleme ve dağıtım

📚 **Öğrendiğiniz Temel Kavramlar:**
- **Registry Sistemi**: Otomatik plugin keşfi ve URL routing
- **Embedded Mode**: Her istek için izole Go process (önerilen)
- **Port Mode**: Sürekli çalışan HTTP server (hızlı response)
- **Sandbox Metadata**: CPU, RAM, dosya ve ağ erişim limitleri
- **Django Signals**: Plugin lifecycle yönetimi
- **i18n**: Çok dilli plugin desteği
- **Auto Scheduler**: Plugin.json'dan otomatik zamanlanmış görevler

🚀 **Sonraki Adımlar:**
1. SDK'yı kurun: `cd sdk && make install`
2. İlk plugin'inizi oluşturun: `ophiron-sdk create --name ...`
3. Go backend'i geliştirin: API endpoint'leri ekleyin
4. Django views ve frontend UI tasarlayın
5. i18n desteği ekleyin: `ophiron-sdk add-language`
6. Test edin: `make test` ve tarayıcıda manuel test
7. Paketleyin: `make package`
8. Marketplace'e yükleyin (gelecek özellik)

📖 **Ek Kaynaklar:**
- Mevcut plugin örnekleri: `plugins/downloader/url_scanner`, `plugins/downloader/advanced_reporting`
- SDK kaynak kodu: `sdk/`
- Registry implementasyonu: `plugins/registry.py`
- Bridge implementasyonları: `plugins/embedded_bridge.py`, `plugins/go_bridge.py`

💡 **En İyi Pratikler Özeti:**
- Embedded mode tercih edin (güvenlik ve izolasyon)
- API key'leri settings sistemi ile yönetin
- Go backend'de panic recovery ekleyin
- CSRF token kullanın
- i18n desteği ekleyin (çok dilli kullanıcılar için)
- Sandbox limitlerini makul tutun
- Dokümantasyon yazın (README.md)
- Zamanlanmış görevler için `scheduled_tasks` kullanın
