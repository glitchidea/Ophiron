# Plugin Development with SDK

> All the steps you need to develop your own tool in the Ophiron plugin ecosystem: from architecture to CLI usage, Go backend and Django integration to Makefile/metadata rules, settings/i18n, testing and deployment, all in one guide.

---

## ⚡ Quick Start (5 Minutes)

### Step 1: SDK Installation (First Time - One Time Only)

**System-wide Installation (Recommended):**
```bash
cd sdk
sudo make install
```

**or User Directory (Without Sudo):**
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

### Step 2: Create Plugin

After SDK installation, `ophiron-sdk` command is available everywhere:

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

### Step 3: Build and Test

```bash
cd my_security_tool
make deps      # Download Go dependencies
make build     # Create binary
make test      # Test
```

---

### Step 4: Integrate with Django

```bash
cd ../..  # Return to Ophiron root
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart ophiron
```

---

### Step 5: Open in Browser

```
http://localhost/my_security_tool
```

---

### ⚙️ Critical Decisions

- **Embedded Mode** (recommended): Remove `go_port` field from `plugin.json` → No port needed, each request isolated
- **Port Mode**: Keep `go_port: 8081` → Fast but requires continuously running service

---

## Table of Contents
1. [Overview and Architecture Summary](#overview-and-architecture-summary)
2. [Prerequisites and Environment Setup](#prerequisites-and-environment-setup)
3. [SDK Installation and CLI Commands](#sdk-installation-and-cli-commands)
4. [Creating a New Plugin](#creating-a-new-plugin)
5. [plugin.json Schema and Metadata](#pluginjson-schema-and-metadata)
6. [Makefile Standards and Build Flow](#makefile-standards-and-build-flow)
7. [Go Backend Development](#go-backend-development)
8. [Django Integration](#django-integration)
9. [Frontend, Static Files and i18n](#frontend-static-files-and-i18n)
10. [Plugin Settings and Secure Data Management](#plugin-settings-and-secure-data-management)
11. [Testing, Packaging and Distribution](#testing-packaging-and-distribution)
12. [Troubleshooting, Best Practices and Checklists](#troubleshooting-best-practices-and-checklists)
13. [Quick Reference (Cheat Sheet)](#quick-reference-cheat-sheet)

---

*[Note: This is a partial translation. The full document translation is in progress. Due to the large size (2271 lines), professional translation services or automated translation tools are recommended for complete accuracy.]*

---

**Last Update:** November 18, 2025  
**Revision:** Code-documentation alignment completed  
**Prepared by:** Ophiron SDK Team

