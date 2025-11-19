<div align="center">

<img src="../static/images/ophiron.svg" alt="Ophiron Logo" width="140">

# Ophiron

Erweiterte Plattform für Systemüberwachung und Sicherheitsmanagement

[Webseite](https://ophiron.glitchidea.com/) • [Issue melden](https://github.com/glitchidea/Ophiron/issues) • [Community](https://github.com/glitchidea/Ophiron/discussions)

</div>

---

## Über

Ophiron unterstützt die Echtzeitverwaltung von Linux-Servern mit Modulen für Monitoring, Sicherheitsscans, Servicemanagement und Docker.

### 🎯 Funktionen

#### 📊 Dashboard
- **Echtzeit-Metriken**: CPU, RAM, Disk, Netzwerkauslastung (WebSocket)
- **Systemstatus**: Laufende Dienste, aktive Benutzer, Systemlast, Betriebszeit
- **Diagramme**: CPU/RAM/Disk/Netzwerk-Nutzungsdiagramme
- **Schnellzugriff**: Letzte Operationen, kritische Warnungen, Modulzugriff-Schaltflächen

#### 🔒 Security (Sicherheit)
- **Paket-Manager**: Unterstützung für apt, pacman, yay, flatpak, dnf, zypper, snap
- **Developer-Pakete**: Python (pip, pipx, conda, poetry), Node.js (npm, yarn, pnpm), PHP (composer), Ruby (gem), Rust (cargo), Go, .NET
- **CVE-Scanner**: CVE-Scanning für Arch, Fedora, Debian, Ubuntu; Batch-Verarbeitung, Schwachstellenerkennung

#### 🌐 Network (Netzwerk)
- **Process Monitor**: Live-Prozessüberwachung via WebSocket, Port- und Netzwerkverbindungen, PID/Port/IP-Gruppierung, PDF-Berichterstattung
- **Service Monitor**: Systemd-Dienste starten/stoppen/neustarten, kategoriebasierte Filterung
- **Service Builder**: Systemd-Service-Dateien erstellen, Vorlagenunterstützung (Python, Node.js, PHP, Ruby, Rust, Go, .NET), Port-Validierung

#### 🖥️ System
- **Process Topology**: Visualisierung von Prozessbeziehungen, Parent-Child-Beziehungen, Snapshot-Speicherung
- **System Logs**: Syslog-, Kernel-, Auth-, Daemon-, Boot-, Cron-Logs; journalctl-Integration, Filterung, Suche, Export
- **User Management**: Systembenutzer, Gruppenmitgliedschaften, Aktivitätsverlauf, Sitzungsverwaltung
- **Firewall**: UFW- und iptables-Verwaltung, Regeln hinzufügen/löschen/bearbeiten
- **System Information**: CPU-, RAM-, Disk-, Netzwerk-Informationen; Live-Modus-Unterstützung
- **Docker Manager**: Container-, Image-, Volume-Verwaltung; Docker Hub-Integration, Logs, Terminalzugriff

#### ⚙️ Settings (Einstellungen)
- **Profil**: Profilbild, Sprachauswahl (TR/EN/DE), Zeitzone
- **Sicherheit**: Passwortwechsel, 2FA (QR-Code/manuell), Backup-Codes
- **Moduleinstellungen**: Live-Modus-Einstellungen für Process Monitor, System Information, Service Monitoring
- **Log-Verwaltung**: Logs pro Modul aktivieren/deaktivieren
- **SMTP**: E-Mail-Konfiguration, CVE-E-Mail-Automatisierung (täglich/wöchentlich/monatlich/cron)

#### 🔐 Sicherheit & Zugriff
- **Authentifizierung**: Benutzername/Passwort, 2FA-Unterstützung
- **Sitzungsverwaltung**: Sichere Tokens, Timeout, Sitzungsverlauf
- **Aktivitätsverfolgung**: Benutzeraktivitätsprotokolle, IP-Tracking
- **Zugriffskontrolle**: Rollenbasierter Zugriff, Berechtigungsverwaltung

#### 🌍 Internationalisierung
- Vollständige UI-Unterstützung für Türkisch, Englisch, Deutsch
- Alle Module unterstützen mehrere Sprachen

#### 🏗️ Infrastruktur
- **Backend**: Django (Python), Gunicorn/Daphne
- **Task Queue**: Redis + Celery
- **Reverse Proxy**: Nginx
- **Echtzeit**: WebSocket-Unterstützung

---

## Installation

### Entwicklung (Lokal)
```bash
git clone https://github.com/glitchidea/Ophiron.git
cd Ophiron
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Produktion (Kurz)
- `collectstatic` ausführen; mit Gunicorn/Daphne bereitstellen
- Nginx Reverse Proxy + HTTPS empfohlen

```bash
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## Anwendung starten

Um Ophiron zu starten, befolgen Sie diese Schritte:

### 1. Redis starten

Redis wird als Message-Broker für Celery benötigt. Starten Sie Redis mit Docker:

```bash
docker run -d --name redis -p 6379:6379 redis:latest
```

Alternativ können Sie, wenn Sie docker-compose verwenden, einen Redis-Service zu Ihrer docker-compose.yml-Datei hinzufügen.

### 2. Celery Worker starten

Celery wird zur Verarbeitung von Hintergrundaufgaben verwendet. Führen Sie den folgenden Befehl in einem neuen Terminalfenster aus:

```bash
celery -A core worker --loglevel=info --pool=solo
```

**Celery Worker mit Root-Benutzer:**
```bash
sudo venv/bin/celery -A core worker --loglevel=info --pool=solo
```

**Hinweis:** Der Parameter `--pool=solo` ist unter Windows und in einigen Entwicklungsumgebungen erforderlich. In der Produktion wird normalerweise `--pool=prefork` verwendet.

### 3. Django-Anwendung starten

Starten Sie die Hauptanwendung:

**Für Entwicklungsumgebung:**
```bash
python manage.py runserver 0.0.0.0:8000
```

**Mit Root-Benutzer starten (für Vorgänge, die sudo erfordern):**
```bash
sudo venv/bin/python manage.py runserver 0.0.0.0:8000
```

**Für Produktionsumgebung:**
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

**Produktion mit Root-Benutzer:**
```bash
sudo venv/bin/gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Vollständige Startsequenz

1. Redis starten (mit Docker)
2. Celery Worker starten (in einem separaten Terminal)
3. Django-Anwendung starten

Sobald alle Dienste laufen, können Sie auf die Anwendung über Ihren Browser zugreifen.

---

## Lizenz und kommerzielle Nutzung

### Anforderung für kommerzielle/unternehmerische Nutzung

Wenn Sie dieses Projekt für **kommerzielle Zwecke** oder in einer **Unternehmensumgebung** verwenden möchten, besteht eine **Pflicht zur Lizenzierung und Genehmigung** für folgende Szenarien:

- ✅ **Direkte oder indirekte Einnahmen** werden aus diesem Projekt generiert
- ✅ Wird in einer **unternehmerischen/kommerziellen** Umgebung verwendet
- ✅ Wird **als Dienstleistung** für Kunden angeboten
- ✅ Wird als Teil eines **kommerziellen Produkts oder einer Dienstleistung** verwendet

### Benachrichtigungs- und Genehmigungsprozess

Wenn eines der oben genannten Szenarien auf Sie zutrifft, müssen Sie **vor Beginn der Nutzung** eine E-Mail mit folgenden Informationen senden:

**E-Mail-Adresse:** info@glitchidea.com

**Erforderliche Informationen in der E-Mail:**
- Firmen-/Organisationsname
- Zweck und Umfang der Nutzung
- Erwartete Anzahl der Benutzer
- Nutzungsdauer
- Kontaktinformationen

Kommerzielle/unternehmerische Nutzung ohne vorherige Genehmigung stellt eine **Lizenzverletzung** dar.

### Persönliche/Forschungsnutzung

Für persönliche Projekte, Bildungszwecke und Open-Source-Forschungsprojekte besteht keine Lizenzanforderung.

---

