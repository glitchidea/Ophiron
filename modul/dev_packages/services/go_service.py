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
    env['GO111MODULE'] = 'on'
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=30, cwd=cwd)
    except Exception as exc:
        return subprocess.CompletedProcess(cmd, 1, '', str(exc))


def detect() -> bool:
    return which('go')


def list_installed(scope: str = 'global') -> List[Dict[str, str]]:
    if not detect():
        return []
    
    # For global scope, list globally installed packages
    if scope == 'global':
        # go list -m all shows all modules in the current module
        # For global packages, we need to check GOPATH/bin or go install list
        items: List[Dict[str, str]] = []
        
        # Method 1: Check GOPATH/bin for installed binaries
        gopath = os.environ.get('GOPATH', os.path.expanduser('~/go'))
        bin_dir = os.path.join(gopath, 'bin')
        if os.path.isdir(bin_dir):
            for filename in os.listdir(bin_dir):
                if os.path.isfile(os.path.join(bin_dir, filename)):
                    # Try to get version info if it's a Go binary
                    try:
                        cp = run_cmd([os.path.join(bin_dir, filename), '--version'])
                        if cp.returncode == 0:
                            version = cp.stdout.strip()
                        else:
                            version = 'unknown'
                    except Exception:
                        version = 'unknown'
                    items.append({'name': filename, 'version': version})
        
        # Method 2: Use go list to get installed packages
        try:
            cp = run_cmd(['go', 'list', '-m', 'all'])
            if cp.returncode == 0:
                for line in cp.stdout.splitlines():
                    line = line.strip()
                    if line and ' ' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            name = parts[0]
                            version = parts[1]
                            # Skip indirect dependencies (marked with indentation)
                            if not line.startswith(' '):
                                items.append({'name': name, 'version': version})
        except Exception:
            pass
        
        return items
    
    # For project scope, check go.mod and go.sum
    go_mod_path = os.path.join(os.getcwd(), 'go.mod')
    if os.path.isfile(go_mod_path):
        try:
            cp = run_cmd(['go', 'list', '-m', 'all'])
            if cp.returncode == 0:
                items: List[Dict[str, str]] = []
                for line in cp.stdout.splitlines():
                    line = line.strip()
                    if line and ' ' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            name = parts[0]
                            version = parts[1]
                            items.append({'name': name, 'version': version})
                return items
        except Exception:
            pass
    
    return []


def get_details(name: str) -> Dict[str, Any]:
    if not detect():
        return {'name': name, 'fields': {}, 'dependencies': []}
    
    # Try to get package info using go list
    cp = run_cmd(['go', 'list', '-m', '-json', name])
    info: Dict[str, Any] = {}
    
    try:
        info = json.loads(cp.stdout or '{}')
    except Exception:
        # Fallback: try to get basic info
        cp = run_cmd(['go', 'list', '-m', name])
        if cp.returncode == 0 and cp.stdout.strip():
            parts = cp.stdout.strip().split()
            if len(parts) >= 2:
                info = {'Path': parts[0], 'Version': parts[1]}
    
    fields: Dict[str, Any] = {
        'Name': info.get('Path') or name,
        'Version': info.get('Version') or '',
        'Description': info.get('Dir', ''),
        'Homepage': info.get('Homepage') or '',
        'Repository': info.get('Dir', ''),
        'License': info.get('License') or '',
        'Module': info.get('Module', {}).get('Path', '') if isinstance(info.get('Module'), dict) else '',
    }
    
    # Get dependencies
    dependencies = []
    try:
        cp = run_cmd(['go', 'list', '-m', '-json', name])
        if cp.returncode == 0:
            data = json.loads(cp.stdout or '{}')
            if 'Require' in data:
                for req in data['Require']:
                    if isinstance(req, dict) and 'Path' in req:
                        dependencies.append(req['Path'])
    except Exception:
        pass
    
    return {'name': name, 'fields': fields, 'dependencies': dependencies}
