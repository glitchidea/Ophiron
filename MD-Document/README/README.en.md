<div align="center">

<img src="../static/images/ophiron.svg" alt="Ophiron Logo" width="140">

# Ophiron

Advanced System Monitoring and Security Management Platform

[Website](https://ophiron.glitchidea.com/) • [Report Issue](https://github.com/glitchidea/Ophiron/issues) • [Community](https://github.com/glitchidea/Ophiron/discussions)

</div>

---

## About

Ophiron helps you manage Linux servers in real time with modules for monitoring, security scanning, service management, and Docker.

### 🎯 Features

#### 📊 Dashboard
- **Real-time Metrics**: CPU, RAM, Disk, Network usage (WebSocket)
- **System Status**: Running services, active users, system load, uptime
- **Charts**: CPU/RAM/Disk/Network usage graphs
- **Quick Access**: Recent operations, critical alerts, module access buttons

#### 🔒 Security
- **Package Manager**: Support for apt, pacman, yay, flatpak, dnf, zypper, snap
- **Developer Packages**: Python (pip, pipx, conda, poetry), Node.js (npm, yarn, pnpm), PHP (composer), Ruby (gem), Rust (cargo), Go, .NET
- **CVE Scanner**: CVE scanning for Arch, Fedora, Debian, Ubuntu; batch processing, vulnerability detection

#### 🌐 Network
- **Process Monitor**: Live process monitoring via WebSocket, port and network connections, PID/Port/IP grouping, PDF reporting
- **Service Monitor**: Start/stop/restart systemd services, category-based filtering
- **Service Builder**: Create systemd service files, template support (Python, Node.js, PHP, Ruby, Rust, Go, .NET), port validation

#### 🖥️ System
- **Process Topology**: Visualize inter-process relationships, parent-child relations, snapshot saving
- **System Logs**: Syslog, kernel, auth, daemon, boot, cron logs; journalctl integration, filtering, search, export
- **User Management**: System users, group memberships, activity history, session management
- **Firewall**: UFW and iptables management, add/delete/edit rules
- **System Information**: CPU, RAM, disk, network info; live mode support
- **Docker Manager**: Container, image, volume management; Docker Hub integration, logs, terminal access

#### ⚙️ Settings
- **Profile**: Profile picture, language selection (TR/EN/DE), timezone
- **Security**: Password change, 2FA (QR code/manual), backup codes
- **Module Settings**: Live mode settings for Process Monitor, System Information, Service Monitoring
- **Log Management**: Enable/disable logs per module
- **SMTP**: Email configuration, CVE email automation (daily/weekly/monthly/cron)

#### 🔐 Security & Access
- **Authentication**: Username/password, 2FA support
- **Session Management**: Secure tokens, timeout, session history
- **Activity Tracking**: User activity logs, IP tracking
- **Access Control**: Role-based access, permission management

#### 🌍 Internationalization
- Full UI support for Turkish, English, German
- All modules support multiple languages

#### 🏗️ Infrastructure
- **Backend**: Django (Python), Gunicorn/Daphne
- **Task Queue**: Redis + Celery
- **Reverse Proxy**: Nginx
- **Real-time**: WebSocket support

---

## Installation

### Development (Local)
```bash
git clone https://github.com/glitchidea/Ophiron.git
cd Ophiron
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Production (Quick)
- Run `collectstatic`; serve with Gunicorn/Daphne
- Nginx reverse proxy + HTTPS recommended

```bash
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## Running the Application

To run Ophiron, follow these steps:

### 1. Start Redis

Redis is required as a message broker for Celery. Start Redis using Docker:

```bash
docker run -d --name redis -p 6379:6379 redis:latest
```

Alternatively, if you're using docker-compose, you can add a Redis service to your docker-compose.yml file.

### 2. Start Celery Worker

Celery is used to process background tasks. Run the following command in a new terminal window:

```bash
celery -A core worker --loglevel=info --pool=solo
```

**Celery Worker with root user:**
```bash
sudo venv/bin/celery -A core worker --loglevel=info --pool=solo
```

**Note:** The `--pool=solo` parameter is required on Windows and some development environments. In production, `--pool=prefork` is typically used.

### 3. Start Django Application

Start the main application:

**For development environment:**
```bash
python manage.py runserver 0.0.0.0:8000
```

**Start with root user (for operations requiring sudo):**
```bash
sudo venv/bin/python manage.py runserver 0.0.0.0:8000
```

**For production environment:**
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

**Production with root user:**
```bash
sudo venv/bin/gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Complete Startup Sequence

1. Start Redis (using Docker)
2. Start Celery worker (in a separate terminal)
3. Start Django application

Once all services are running, you can access the application from your browser.

---

## License and Commercial Use

### Commercial/Enterprise Use Requirement

If you plan to use this project for **commercial purposes** or in an **enterprise environment**, **license acquisition and approval are mandatory** for the following scenarios:

- ✅ **Direct or indirect revenue** will be generated from this project
- ✅ Will be used in a **corporate/commercial** environment
- ✅ Will be offered **as a service** to customers
- ✅ Will be used as part of a **commercial product or service**

### Notification and Approval Process

If any of the above scenarios apply to you, you **must** send an email with the following information **before starting use**:

**Email Address:** info@glitchidea.com

**Required information in the email:**
- Company/Organization name
- Purpose and scope of use
- Expected number of users
- Duration of use
- Contact information

Commercial/enterprise use without prior approval constitutes a **license violation**.

### Personal/Research Use

No license requirement exists for personal projects, educational use, and open-source research projects.

---
