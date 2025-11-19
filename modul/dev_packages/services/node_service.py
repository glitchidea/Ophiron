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
    env['NO_COLOR'] = '1'
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=30, cwd=cwd)
    except Exception as exc:
        return subprocess.CompletedProcess(cmd, 1, '', str(exc))


def detect() -> bool:
    return which('npm')


def list_installed(scope: str = 'project') -> List[Dict[str, str]]:
    if not detect():
        return []
    # Use npm ls with depth 0 to get top-level dependencies
    args = ['npm', 'ls', '--depth=0', '--json', '--long=false']
    cp = run_cmd(args if scope == 'project' else ['npm', 'ls', '-g', '--depth=0', '--json', '--long=false'])
    if cp.returncode not in (0, 1):  # npm ls returns 1 when unmet deps; still output JSON
        # still try to parse
        pass
    try:
        data = json.loads(cp.stdout or '{}')
    except Exception:
        return []
    deps = (data.get('dependencies') or {})
    items: List[Dict[str, str]] = []
    for name, info in deps.items():
        version = info.get('version') or ''
        if name:
            items.append({'name': name, 'version': version})
    # For global scope, npm prefixes with empty project; already handled via -g
    return items


def get_details(name: str) -> Dict[str, Any]:
    if not detect():
        return {'name': name, 'fields': {}, 'dependencies': []}
    cp = run_cmd(['npm', 'view', name, '--json'])
    try:
        info = json.loads(cp.stdout or '{}')
    except Exception:
        info = {}
    fields: Dict[str, Any] = {
        'Name': info.get('name') or name,
        'Version': info.get('version') or '',
        'Description': info.get('description') or '',
        'Homepage': (info.get('homepage') or ''),
        'License': (info.get('license') or ''),
        'Repository': (info.get('repository', {}).get('url') if isinstance(info.get('repository'), dict) else info.get('repository') or ''),
    }
    deps_dict = info.get('dependencies') or {}
    dependencies = list(deps_dict.keys()) if isinstance(deps_dict, dict) else []
    return {'name': name, 'fields': fields, 'dependencies': dependencies}


