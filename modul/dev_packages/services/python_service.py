import os
import json
import shutil
import subprocess
from typing import List, Dict, Any


def which(bin_name: str) -> bool:
    return shutil.which(bin_name) is not None


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env['LC_ALL'] = 'C'
    env['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=30)
    except Exception as exc:
        return subprocess.CompletedProcess(cmd, 1, '', str(exc))


def detect() -> bool:
    return which('pip') or which('pip3')


def _pip_bin() -> str:
    return shutil.which('pip') or shutil.which('pip3') or 'pip'


def list_installed(scope: str = 'project') -> List[Dict[str, str]]:
    # For now, list global as well; project/global distinction can be refined later
    if not detect():
        return []
    cp = run_cmd([_pip_bin(), 'list', '--format=json'])
    if cp.returncode != 0:
        return []
    try:
        data = json.loads(cp.stdout or '[]')
        return [{ 'name': p.get('name') or '', 'version': p.get('version') or '' } for p in data]
    except Exception:
        return []


def list_outdated(scope: str = 'global') -> List[Dict[str, str]]:
    if not detect():
        return []
    
    # Use pip list --outdated to get packages with available updates
    cp = run_cmd([_pip_bin(), 'list', '--outdated', '--format=json'])
    if cp.returncode != 0:
        return []
    
    try:
        data = json.loads(cp.stdout or '[]')
    except Exception:
        return []
    
    items: List[Dict[str, str]] = []
    for pkg in data:
        name = pkg.get('name', '')
        current = pkg.get('version', '')
        latest = pkg.get('latest_version', '')
        if name and current and latest:
            # Determine if it's critical (major version change)
            is_critical = False
            try:
                current_parts = [int(x) for x in current.split('.')]
                latest_parts = [int(x) for x in latest.split('.')]
                if len(current_parts) > 0 and len(latest_parts) > 0:
                    # Major version change is critical
                    if latest_parts[0] > current_parts[0]:
                        is_critical = True
            except (ValueError, IndexError):
                pass
            
            items.append({
                'name': name,
                'current': current,
                'latest': latest,
                'critical': is_critical
            })
    
    return items


def get_details(name: str) -> Dict[str, Any]:
    # Prefer stdlib metadata to avoid parsing CLI output
    try:
        try:
            from importlib import metadata as importlib_metadata  # Python 3.8+
        except Exception:
            import importlib_metadata  # type: ignore
        dist = importlib_metadata.distribution(name)
        md = dist.metadata or {}
        fields: Dict[str, Any] = {
            'Name': md.get('Name') or name,
            'Version': md.get('Version') or '',
            'Summary': md.get('Summary') or '',
            'Home-page': md.get('Home-page') or md.get('Project-URL') or '',
            'License': md.get('License') or '',
            'Author': md.get('Author') or '',
        }
        # Dependencies
        requires = list(dist.requires or [])
        deps: List[str] = []
        for r in requires:
            # Example: 'requests>=2.0'
            dep = r.split(';', 1)[0].strip()
            if dep:
                # keep only the package token before version specifiers
                token = dep.split(' ', 1)[0]
                deps.append(token)
        return {
            'name': name,
            'fields': fields,
            'dependencies': deps,
        }
    except Exception:
        # Fallback to pip show parsing
        if not detect():
            return {'name': name, 'fields': {}, 'dependencies': []}
        cp = run_cmd([_pip_bin(), 'show', name])
        fields: Dict[str, Any] = {}
        deps_list: List[str] = []
        for line in (cp.stdout or '').splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                k = k.strip()
                v = v.strip()
                fields[k] = v
                if k.lower() in ('requires', 'dependencies') and v:
                    deps_list = [s.strip() for s in v.split(',') if s.strip()]
        return {'name': name, 'fields': fields, 'dependencies': deps_list}


