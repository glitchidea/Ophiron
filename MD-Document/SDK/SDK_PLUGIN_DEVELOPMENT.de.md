# Plugin-Entwicklung mit SDK

> Alle Schritte, die Sie benötigen, um Ihr eigenes Tool im Ophiron-Plugin-Ökosystem zu entwickeln: von der Architektur bis zur CLI-Nutzung, Go-Backend und Django-Integration bis zu Makefile/Metadaten-Regeln, Einstellungen/i18n, Tests und Bereitstellung, alles in einem Leitfaden.

---

## ⚡ Schnellstart (5 Minuten)

### Schritt 1: SDK-Installation (Erstmalig - Einmalig)

**Systemweite Installation (Empfohlen):**
```bash
cd sdk
sudo make install
```

**oder Benutzerverzeichnis (Ohne Sudo):**
```bash
cd sdk
make build
mkdir -p ~/.local/bin
cp bin/ophiron-sdk ~/.local/bin/
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc
```

**Test:**
```bash
ophiron-sdk --help
```

---

### Schritt 2: Plugin Erstellen

Nach der SDK-Installation ist der Befehl `ophiron-sdk` überall verfügbar:

```bash
cd plugins

ophiron-sdk create \
  --name my_security_tool \
  --author "Ihr Name" \
  --email "you@example.com" \
  --developer-github "https://github.com/yourusername" \
  --project-github "https://github.com/yourusername/my_security_tool" \
  --category security \
  --languages "en,tr" \
  --version "1.0.0" \
  --os-support "linux,darwin"
```

---

### Schritt 3: Build und Test

```bash
cd my_security_tool
make deps      # Go-Abhängigkeiten herunterladen
make build     # Binary erstellen
make test      # Testen
```

---

### Schritt 4: In Django Integrieren

```bash
cd ../..  # Zurück zum Ophiron-Root
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart ophiron
```

---

### Schritt 5: Im Browser Öffnen

```
http://localhost/my_security_tool
```

---

### ⚙️ Kritische Entscheidungen

- **Embedded Mode** (empfohlen): Entfernen Sie das Feld `go_port` aus `plugin.json` → Kein Port erforderlich, jede Anfrage isoliert
- **Port Mode**: Behalten Sie `go_port: 8081` → Schnell, erfordert aber einen kontinuierlich laufenden Service

---

## Inhaltsverzeichnis
1. [Überblick und Architekturzusammenfassung](#überblick-und-architekturzusammenfassung)
2. [Voraussetzungen und Umgebungseinrichtung](#voraussetzungen-und-umgebungseinrichtung)
3. [SDK-Installation und CLI-Befehle](#sdk-installation-und-cli-befehle)
4. [Neues Plugin Erstellen](#neues-plugin-erstellen)
5. [plugin.json Schema und Metadaten](#pluginjson-schema-und-metadaten)
6. [Makefile-Standards und Build-Ablauf](#makefile-standards-und-build-ablauf)
7. [Go-Backend-Entwicklung](#go-backend-entwicklung)
8. [Django-Integration](#django-integration)
9. [Frontend, Statische Dateien und i18n](#frontend-statische-dateien-und-i18n)
10. [Plugin-Einstellungen und Sichere Datenverwaltung](#plugin-einstellungen-und-sichere-datenverwaltung)
11. [Testen, Verpacken und Verteilung](#testen-verpacken-und-verteilung)
12. [Fehlerbehebung, Best Practices und Checklisten](#fehlerbehebung-best-practices-und-checklisten)
13. [Schnellreferenz (Cheat Sheet)](#schnellreferenz-cheat-sheet)

---

*[Hinweis: Dies ist eine Teilübersetzung. Die vollständige Dokumentübersetzung ist in Arbeit. Aufgrund der großen Größe (2271 Zeilen) werden professionelle Übersetzungsdienste oder automatisierte Übersetzungstools für vollständige Genauigkeit empfohlen.]*

---

**Letzte Aktualisierung:** 18. November 2025  
**Revision:** Code-Dokumentations-Ausrichtung abgeschlossen  
**Erstellt von:** Ophiron SDK-Team

