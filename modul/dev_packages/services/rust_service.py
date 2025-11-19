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
    env['CARGO_TERM_COLOR'] = 'never'
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=30, cwd=cwd)
    except Exception as exc:
        return subprocess.CompletedProcess(cmd, 1, '', str(exc))


def detect() -> bool:
    return which('cargo')


def list_installed(scope: str = 'global') -> List[Dict[str, str]]:
    if not detect():
        return []
    
    # For global scope, list globally installed binaries
    if scope == 'global':
        # cargo install --list shows globally installed packages
        cp = run_cmd(['cargo', 'install', '--list'])
        if cp.returncode != 0:
            return []
        
        items: List[Dict[str, str]] = []
        current_package = None
        
        for line in cp.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            
            # Package name line (e.g., "cargo-edit v0.12.0:")
            if ' v' in line and line.endswith(':'):
                current_package = line.split(' v')[0].strip()
                version_part = line.split(' v')[1].rstrip(':')
                if current_package and version_part:
                    items.append({'name': current_package, 'version': version_part})
            # Binary name line (e.g., "    cargo-add")
            elif line.startswith('    ') and current_package:
                binary_name = line.strip()
                if binary_name and binary_name != current_package:
                    # This is a binary from the current package
                    items.append({'name': f"{current_package} ({binary_name})", 'version': ''})
        
        return items
    
    # For project scope, parse Cargo.lock if it exists
    lock_path = os.path.join(os.getcwd(), 'Cargo.lock')
    if os.path.isfile(lock_path):
        try:
            with open(lock_path, 'r', encoding='utf-8') as f:
                lock = json.load(f)
            packages = lock.get('package', [])
            items: List[Dict[str, str]] = []
            for pkg in packages:
                name = pkg.get('name', '')
                version = pkg.get('version', '')
                if name and version:
                    items.append({'name': name, 'version': version})
            return items
        except Exception:
            return []
    
    return []


def get_details(name: str) -> Dict[str, Any]:
    if not detect():
        return {'name': name, 'fields': {}, 'dependencies': []}
    
    # Try to get package info from crates.io
    cp = run_cmd(['cargo', 'search', name, '--limit', '1', '--format', 'json'])
    info: Dict[str, Any] = {}
    
    try:
        # cargo search returns one JSON object per line
        for line in cp.stdout.splitlines():
            if line.strip():
                data = json.loads(line)
                if data.get('name') == name:
                    info = data
                    break
    except Exception:
        pass
    
    fields: Dict[str, Any] = {
        'Name': info.get('name') or name,
        'Version': info.get('max_version') or info.get('version') or '',
        'Description': info.get('description') or '',
        'Homepage': info.get('homepage') or '',
        'Repository': info.get('repository') or '',
        'License': info.get('license') or '',
        'Downloads': info.get('downloads') or '',
    }
    
    # Get dependencies from Cargo.toml if available
    dependencies = []
    try:
        # Try to find Cargo.toml in common locations
        for path in ['.', os.path.expanduser('~/.cargo/registry')]:
            toml_path = os.path.join(path, 'Cargo.toml')
            if os.path.isfile(toml_path):
                # This is a simplified approach - in reality, we'd need to parse TOML
                # For now, we'll return empty dependencies
                break
    except Exception:
        pass
    
    return {'name': name, 'fields': fields, 'dependencies': dependencies}
