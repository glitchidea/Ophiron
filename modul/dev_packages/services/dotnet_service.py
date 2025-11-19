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
    env['DOTNET_CLI_TELEMETRY_OPTOUT'] = '1'
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=30, cwd=cwd)
    except Exception as exc:
        return subprocess.CompletedProcess(cmd, 1, '', str(exc))


def detect() -> bool:
    return which('dotnet')


def list_installed(scope: str = 'global') -> List[Dict[str, str]]:
    if not detect():
        return []
    
    # For global scope, list globally installed tools
    if scope == 'global':
        # dotnet tool list -g shows globally installed tools
        cp = run_cmd(['dotnet', 'tool', 'list', '-g'])
        if cp.returncode != 0:
            return []
        
        items: List[Dict[str, str]] = []
        lines = cp.stdout.splitlines()
        
        # Skip header lines and parse tool entries
        for line in lines[2:]:  # Skip "Package Id" and "Version" headers
            line = line.strip()
            if not line or line.startswith('-'):
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                version = parts[1]
                items.append({'name': name, 'version': version})
        
        return items
    
    # For project scope, check for .NET project files
    project_files = []
    for root, dirs, files in os.walk(os.getcwd()):
        for file in files:
            if file.endswith(('.csproj', '.fsproj', '.vbproj')):
                project_files.append(os.path.join(root, file))
    
    if not project_files:
        return []
    
    items: List[Dict[str, str]] = []
    
    # Parse each project file for package references
    for project_file in project_files:
        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple XML parsing for PackageReference elements
            import re
            package_refs = re.findall(r'<PackageReference\s+Include="([^"]+)"\s+Version="([^"]+)"', content)
            for name, version in package_refs:
                items.append({'name': name, 'version': version})
        except Exception:
            continue
    
    return items


def get_details(name: str) -> Dict[str, Any]:
    if not detect():
        return {'name': name, 'fields': {}, 'dependencies': []}
    
    # Try to get package info using dotnet add package --help or nuget search
    # For now, we'll use a basic approach
    info: Dict[str, Any] = {}
    
    # Try to get info from nuget.org API
    try:
        import urllib.request
        import urllib.parse
        
        # Search for package on nuget.org
        search_url = f"https://api.nuget.org/v3-flatcontainer/{urllib.parse.quote(name)}/index.json"
        with urllib.request.urlopen(search_url, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if 'versions' in data and data['versions']:
                latest_version = data['versions'][-1]
                info = {
                    'name': name,
                    'version': latest_version,
                    'description': f'.NET package: {name}',
                    'homepage': f'https://www.nuget.org/packages/{name}',
                }
    except Exception:
        pass
    
    fields: Dict[str, Any] = {
        'Name': info.get('name') or name,
        'Version': info.get('version') or '',
        'Description': info.get('description') or f'.NET package: {name}',
        'Homepage': info.get('homepage') or f'https://www.nuget.org/packages/{name}',
        'Repository': info.get('repository') or '',
        'License': info.get('license') or '',
        'Type': '.NET Package',
    }
    
    # For .NET packages, dependencies are complex to determine without the actual package
    # We'll return empty dependencies for now
    dependencies = []
    
    return {'name': name, 'fields': fields, 'dependencies': dependencies}
