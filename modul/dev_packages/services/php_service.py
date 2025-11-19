import os
import json
import shutil
import subprocess
from typing import List, Dict, Any


def which(bin_name: str) -> bool:
    return shutil.which(bin_name) is not None


def run_cmd(cmd: List[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env['LC_ALL'] = 'C'
    env['COMPOSER_NO_INTERACTION'] = '1'
    env['COMPOSER_DISABLE_XDEBUG_WARN'] = '1'
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=30, cwd=cwd)
    except Exception as exc:
        return subprocess.CompletedProcess(cmd, 1, '', str(exc))


def detect() -> bool:
    return which('composer')


def list_installed(scope: str = 'global') -> List[Dict[str, str]]:
    if not detect():
        return []
    # We default to global packages for developer tools
    if scope != 'global':
        # Optional: parse composer.lock in cwd if needed
        lock_path = os.path.join(os.getcwd(), 'composer.lock')
        if os.path.isfile(lock_path):
            try:
                with open(lock_path, 'r', encoding='utf-8') as f:
                    lock = json.load(f)
                pkgs = lock.get('packages', [])
                return [{'name': p.get('name', ''), 'version': p.get('version', '')} for p in pkgs if p.get('name')]
            except Exception:
                return []
        return []

    # Global scope
    # composer global show --format=json is supported in Composer v2
    cp = run_cmd(['composer', 'global', 'show', '--format=json'])
    try:
        data = json.loads(cp.stdout or '{}')
    except Exception:
        data = {}
    packages = data.get('installed') or data.get('packages') or []
    items: List[Dict[str, str]] = []
    # Fallback: if JSON didn't include packages, try plain output parsing
    if not packages and cp.stdout:
        for line in cp.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith(('{', '}', 'Changed', '<warning')):
                continue
            parts = line.split()
            if len(parts) >= 2 and '/' in parts[0]:
                items.append({'name': parts[0], 'version': parts[1]})
        return items
    for p in packages:
        name = p.get('name') or p.get('package')
        version = p.get('version') or ''
        if name:
            items.append({'name': name, 'version': version})
    return items


def get_details(name: str) -> Dict[str, Any]:
    if not detect():
        return {'name': name, 'fields': {}, 'dependencies': []}
    cp = run_cmd(['composer', 'show', name, '--format=json'])
    info: Dict[str, Any]
    try:
        info = json.loads(cp.stdout or '{}')
    except Exception:
        info = {}
    # Composer show json may return {"name":..., "version":..., "description":..., "license":[...], "homepage":..., "requires":{...}}
    fields: Dict[str, Any] = {
        'Name': info.get('name') or name,
        'Version': info.get('version') or '',
        'Description': info.get('description') or '',
        'Homepage': info.get('homepage') or '',
        'License': ', '.join(info.get('license') or []) if isinstance(info.get('license'), list) else (info.get('license') or ''),
        'Source': (info.get('source', {}) or {}).get('url', ''),
    }
    requires = info.get('requires') if isinstance(info.get('requires'), dict) else {}
    dependencies = list(requires.keys())
    return {'name': name, 'fields': fields, 'dependencies': dependencies}


