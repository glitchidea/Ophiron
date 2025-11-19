import os
import json
import shlex
import subprocess
import re
from typing import Dict, List, Any


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env['LC_ALL'] = 'C'
    env['NO_COLOR'] = '1'
    env['CLICOLOR'] = '0'
    try:
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            timeout=30,
        )
    except Exception as exc:
        cp = subprocess.CompletedProcess(cmd, 1, '', str(exc))
        return cp


def which(binary: str) -> bool:
    return any(
        os.path.isfile(os.path.join(path, binary)) and os.access(os.path.join(path, binary), os.X_OK)
        for path in os.environ.get('PATH', '').split(os.pathsep)
    )


class PackageScanner:
    def __init__(self) -> None:
        self.managers = self.detect_managers()

    def detect_managers(self) -> List[str]:
        candidates = ['apt', 'pacman', 'yay', 'flatpak', 'dnf', 'zypper', 'snap']
        detected = []
        for c in candidates:
            if which(c):
                detected.append(c)
        return detected

    def get_updates_summary(self) -> Dict[str, Any]:
        summary: Dict[str, Any] = {'managers': {}, 'total_updates': 0}
        for m in self.managers:
            count, critical = self._updates_for_manager(m)
            summary['managers'][m] = {'count': count, 'critical': critical}
            summary['total_updates'] += count
        return summary

    def get_upgradeable_packages(self) -> Dict[str, List[Dict[str, Any]]]:
        result: Dict[str, List[Dict[str, Any]]] = {}
        for m in self.managers:
            result[m] = self._upgradeable_for_manager(m)
        return result

    def _updates_for_manager(self, manager: str) -> (int, int):
        try:
            if manager == 'apt':
                # apt list --upgradeable
                cp = run_cmd(['bash', '-lc', 'apt list --upgradeable 2>/dev/null | tail -n +2'])
                lines = [l for l in cp.stdout.splitlines() if l.strip()]
                # Critical heuristic: security updates include "-security" in origin or version
                critical = sum(1 for l in lines if 'security' in l.lower())
                return len(lines), critical
            if manager == 'pacman':
                cp = run_cmd(['bash', '-lc', 'checkupdates 2>/dev/null || true'])
                lines = [l for l in cp.stdout.splitlines() if l.strip()]
                return len(lines), 0
            if manager == 'yay':
                cp = run_cmd(['bash', '-lc', 'yay -Qua 2>/dev/null || true'])
                lines = [l for l in cp.stdout.splitlines() if l.strip()]
                return len(lines), 0
            if manager == 'flatpak':
                cp = run_cmd(['bash', '-lc', 'flatpak remote-ls --updates 2>/dev/null || true'])
                lines = [l for l in cp.stdout.splitlines() if l.strip()]
                return len(lines), 0
            if manager == 'dnf':
                cp = run_cmd(['bash', '-lc', 'dnf -q check-update --refresh 2>/dev/null | egrep -v "^Last metadata|^$|^Obsoleting|^Security"'])
                lines = [l for l in cp.stdout.splitlines() if l.strip()]
                # Security updates
                cp_sec = run_cmd(['bash', '-lc', 'dnf -q updateinfo list security 2>/dev/null || true'])
                crit = len([l for l in cp_sec.stdout.splitlines() if l.strip()])
                return len(lines), crit
            if manager == 'zypper':
                cp = run_cmd(['bash', '-lc', 'zypper -q lu 2>/dev/null | tail -n +3'])
                lines = [l for l in cp.stdout.splitlines() if l.strip()]
                cp_sec = run_cmd(['bash', '-lc', 'zypper -q lp -g security 2>/dev/null | tail -n +3'])
                crit = len([l for l in cp_sec.stdout.splitlines() if l.strip()])
                return len(lines), crit
            if manager == 'snap':
                cp = run_cmd(['bash', '-lc', 'snap refresh --list 2>/dev/null | tail -n +2'])
                lines = [l for l in cp.stdout.splitlines() if l.strip()]
                return len(lines), 0
        except Exception:
            return 0, 0
        return 0, 0

    def get_installed_packages(self) -> Dict[str, List[Dict[str, Any]]]:
        data: Dict[str, List[Dict[str, Any]]] = {}
        for m in self.managers:
            data[m] = self._installed_for_manager(m)
        return data

    def _installed_for_manager(self, manager: str) -> List[Dict[str, Any]]:
        try:
            if manager == 'apt':
                cp = run_cmd(['bash', '-lc', "dpkg-query -W -f='${Package}\t${Version}\t${Status}\n' 2>/dev/null"]) 
                items = []
                for line in cp.stdout.splitlines():
                    parts = line.split('\t')
                    if len(parts) >= 3 and 'installed' in parts[2]:
                        items.append({'name': parts[0], 'version': parts[1]})
                return items
            if manager == 'pacman':
                # Native repo packages only (exclude AUR/foreign)
                cp = run_cmd(['bash', '-lc', 'pacman -Qn 2>/dev/null'])
                return self._parse_name_version_lines(cp.stdout)
            if manager == 'yay':
                # AUR/foreign packages only
                # Prefer pacman -Qm (works without parsing yay output); fallback to yay -Qm
                cp = run_cmd(['bash', '-lc', 'pacman -Qm 2>/dev/null || yay -Qm 2>/dev/null'])
                return self._parse_name_version_lines(cp.stdout)
            if manager == 'flatpak':
                cp = run_cmd(['bash', '-lc', 'flatpak list --app --columns=application,version 2>/dev/null'])
                items = []
                for line in cp.stdout.splitlines()[1:]:
                    parts = [p.strip() for p in line.split('\t') if p.strip()]
                    if len(parts) >= 1:
                        items.append({'name': parts[0], 'version': parts[1] if len(parts) > 1 else ''})
                return items
            if manager == 'dnf':
                cp = run_cmd(['bash', '-lc', 'rpm -qa --qf "%{NAME} %{VERSION}-%{RELEASE}\n" 2>/dev/null'])
                return self._parse_name_version_lines(cp.stdout)
            if manager == 'zypper':
                cp = run_cmd(['bash', '-lc', 'rpm -qa --qf "%{NAME} %{VERSION}-%{RELEASE}\n" 2>/dev/null'])
                return self._parse_name_version_lines(cp.stdout)
            if manager == 'snap':
                cp = run_cmd(['bash', '-lc', 'snap list 2>/dev/null | tail -n +2'])
                items = []
                for line in cp.stdout.splitlines():
                    cols = [c for c in line.split(' ') if c]
                    if len(cols) >= 2:
                        items.append({'name': cols[0], 'version': cols[1]})
                return items
        except Exception:
            return []
        return []

    def _parse_name_version_lines(self, text: str) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for line in text.splitlines():
            parts = [p for p in line.strip().split(' ') if p]
            if len(parts) >= 2:
                items.append({'name': parts[0], 'version': parts[1]})
        return items

    def get_package_details(self, manager: str, package_name: str) -> Dict[str, Any]:
        if manager not in self.managers:
            return {'error': 'manager_not_found', 'manager': manager}
        try:
            if manager == 'apt':
                cp = run_cmd(['bash', '-lc', f"apt-cache show -- {shlex.quote(package_name)} 2>/dev/null"])
                fields = self._parse_colon_kv(cp.stdout)
                deps = self._split_dep_list(fields.get('Depends') or fields.get('Pre-Depends'))
                return {
                    'manager': manager,
                    'name': package_name,
                    'fields': fields,
                    'dependencies': deps,
                    'raw': cp.stdout,
                }
            if manager == 'pacman':
                cp = run_cmd(['bash', '-lc', f"pacman -Qi -- {shlex.quote(package_name)} 2>/dev/null"])
                fields = self._parse_colon_kv(cp.stdout)
                deps = self._split_dep_list(fields.get('Depends On'))
                return {
                    'manager': manager,
                    'name': package_name,
                    'fields': fields,
                    'dependencies': deps,
                    'raw': cp.stdout,
                }
            if manager == 'yay':
                cp = run_cmd(['bash', '-lc', f"yay -Si -- {shlex.quote(package_name)} 2>/dev/null || yay -Qi -- {shlex.quote(package_name)} 2>/dev/null"])
                fields = self._parse_colon_kv(cp.stdout)
                deps = self._split_dep_list(fields.get('Depends On'))
                return {
                    'manager': manager,
                    'name': package_name,
                    'fields': fields,
                    'dependencies': deps,
                    'raw': cp.stdout,
                }
            if manager == 'flatpak':
                cp = run_cmd(['bash', '-lc', f"flatpak info -- {shlex.quote(package_name)} 2>/dev/null"])
                fields = self._parse_colon_kv(cp.stdout)
                deps: List[str] = []
                return {
                    'manager': manager,
                    'name': package_name,
                    'fields': fields,
                    'dependencies': deps,
                    'raw': cp.stdout,
                }
            if manager == 'dnf':
                cp = run_cmd(['bash', '-lc', f"dnf info -- {shlex.quote(package_name)} 2>/dev/null"])
                fields = self._parse_colon_kv(cp.stdout)
                deps = self._split_dep_list(fields.get('Depends'))
                return {
                    'manager': manager,
                    'name': package_name,
                    'fields': fields,
                    'dependencies': deps,
                    'raw': cp.stdout,
                }
            if manager == 'zypper':
                cp = run_cmd(['bash', '-lc', f"zypper info -- {shlex.quote(package_name)} 2>/dev/null"])
                fields = self._parse_colon_kv(cp.stdout)
                deps = self._split_dep_list(fields.get('Depends') or fields.get('Requires'))
                return {
                    'manager': manager,
                    'name': package_name,
                    'fields': fields,
                    'dependencies': deps,
                    'raw': cp.stdout,
                }
            if manager == 'snap':
                # snap info doesn't always include deps, but provide raw info
                cp = run_cmd(['bash', '-lc', f"snap info -- {shlex.quote(package_name)} 2>/dev/null"])
                fields = self._parse_colon_kv(cp.stdout)
                return {
                    'manager': manager,
                    'name': package_name,
                    'fields': fields,
                    'dependencies': [],
                    'raw': cp.stdout,
                }
        except Exception as exc:
            return {'manager': manager, 'name': package_name, 'error': str(exc)}
        return {'manager': manager, 'name': package_name, 'error': 'unsupported'}

    def _upgradeable_for_manager(self, manager: str) -> List[Dict[str, Any]]:
        try:
            if manager == 'apt':
                cp = run_cmd(['bash', '-lc', 'apt list --upgradeable 2>/dev/null | tail -n +2'])
                items: List[Dict[str, Any]] = []
                for line in cp.stdout.splitlines():
                    line = self._strip_ansi(line)
                    # format: pkg/version arch [upgradable from: old] ...
                    parts = line.split()
                    if not parts:
                        continue
                    name_ver = parts[0]
                    if '/' in name_ver:
                        name, ver = name_ver.split('/', 1)
                    else:
                        name, ver = name_ver, ''
                    critical = 'security' in line.lower()
                    items.append({'name': name, 'new_version': ver, 'critical': critical})
                return items
            if manager == 'pacman':
                cp = run_cmd(['bash', '-lc', 'checkupdates 2>/dev/null || true'])
                items: List[Dict[str, Any]] = []
                for line in cp.stdout.splitlines():
                    line = self._strip_ansi(line).strip()
                    if not line or '->' not in line or line.startswith(('==>', '::')):
                        continue
                    left, right = line.split('->', 1)
                    left = left.strip()
                    right = right.strip()
                    left_parts = [p for p in left.split() if p]
                    if len(left_parts) >= 2 and right:
                        name = left_parts[0]
                        current = left_parts[-1]
                        items.append({'name': name, 'current_version': current, 'new_version': right})
                return items
            if manager == 'yay':
                cp = run_cmd(['bash', '-lc', 'yay -Qua --color never 2>/dev/null || true'])
                items: List[Dict[str, Any]] = []
                for line in cp.stdout.splitlines():
                    raw = self._strip_ansi(line).strip()
                    if not raw or '->' not in raw or raw.startswith(('==>', '::')):
                        continue
                    # expected: name current -> new
                    left, right = raw.split('->', 1)
                    left = left.strip()
                    right = right.strip()
                    left_parts = [p for p in left.split() if p]
                    if len(left_parts) >= 2 and right:
                        name = left_parts[0]
                        current = left_parts[-1]
                        # Filter improbable names like 'root/sudo.' noise
                        if not self._looks_like_pkg_name(name):
                            continue
                        items.append({'name': name, 'current_version': current, 'new_version': right})
                return items
            if manager == 'flatpak':
                cp = run_cmd(['bash', '-lc', 'flatpak remote-ls --updates --columns=application,branch 2>/dev/null || true'])
                items: List[Dict[str, Any]] = []
                for line in cp.stdout.splitlines():
                    line = self._strip_ansi(line)
                    parts = [p for p in line.split('\t') if p]
                    if parts:
                        items.append({'name': parts[0], 'branch': parts[1] if len(parts) > 1 else ''})
                return items
            if manager == 'dnf':
                cp = run_cmd(['bash', '-lc', 'dnf -q check-update --refresh 2>/dev/null'])
                items: List[Dict[str, Any]] = []
                for line in cp.stdout.splitlines():
                    line = self._strip_ansi(line).strip()
                    if not line or line.startswith('Last metadata') or line.startswith('Obsoleting'):
                        continue
                    parts = [p for p in line.split() if p]
                    if len(parts) >= 2:
                        items.append({'name': parts[0], 'new_version': parts[1]})
                return items
            if manager == 'zypper':
                cp = run_cmd(['bash', '-lc', 'zypper -q lu 2>/dev/null | tail -n +3'])
                items: List[Dict[str, Any]] = []
                for line in cp.stdout.splitlines():
                    line = self._strip_ansi(line)
                    parts = [p for p in line.split() if p]
                    if len(parts) >= 2:
                        items.append({'name': parts[0], 'new_version': parts[-1]})
                return items
            if manager == 'snap':
                cp = run_cmd(['bash', '-lc', 'snap refresh --list 2>/dev/null | tail -n +2'])
                items: List[Dict[str, Any]] = []
                for line in cp.stdout.splitlines():
                    line = self._strip_ansi(line)
                    cols = [c for c in line.split(' ') if c]
                    if len(cols) >= 1:
                        items.append({'name': cols[0], 'new_version': cols[2] if len(cols) > 2 else ''})
                return items
        except Exception:
            return []
        return []

    _ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")

    def _strip_ansi(self, s: str) -> str:
        try:
            return self._ANSI_RE.sub('', s)
        except Exception:
            return s

    def _looks_like_pkg_name(self, name: str) -> bool:
        if not name:
            return False
        for ch in name:
            if not (ch.isalnum() or ch in ('@', '.', '+', '-', '_')):
                return False
        return True

    def _parse_colon_kv(self, text: str) -> Dict[str, str]:
        fields: Dict[str, str] = {}
        current_key: str | None = None
        for line in text.splitlines():
            if not line.strip():
                continue
            if ':' in line and (not line.startswith(' ') and not line.startswith('\t')):
                key, val = line.split(':', 1)
                key = key.strip()
                val = val.strip()
                fields[key] = val
                current_key = key
            else:
                if current_key:
                    fields[current_key] = (fields.get(current_key, '') + ' ' + line.strip()).strip()
        return fields

    def _split_dep_list(self, value: Any) -> List[str]:
        if not value:
            return []
        # Split by comma or spaces, clean version constraints
        raw = str(value)
        items: List[str] = []
        for part in raw.replace('>=', ' ').replace('<=', ' ').replace('=', ' ').replace('>', ' ').replace('<', ' ').split(','):
            p = part.strip()
            if not p:
                continue
            # Some lists are space separated
            for token in p.split():
                t = token.strip()
                if t and all(c.isalnum() or c in ('-', '_', '.') for c in t):
                    items.append(t)
        # De-duplicate while preserving order
        seen = set()
        result: List[str] = []
        for it in items:
            if it not in seen:
                seen.add(it)
                result.append(it)
        return result


