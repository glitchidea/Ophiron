import os
import re
import shutil
import subprocess
from typing import List, Dict, Any


def which(bin_name: str) -> bool:
    return shutil.which(bin_name) is not None


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env['LC_ALL'] = 'C'
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=30)
    except Exception as exc:
        return subprocess.CompletedProcess(cmd, 1, '', str(exc))


def detect() -> bool:
    return which('gem')


def list_installed(scope: str = 'project') -> List[Dict[str, str]]:
    if not detect():
        return []
    # project scope: parse Gemfile.lock if exists in CWD
    if scope == 'project' and os.path.isfile('Gemfile.lock'):
        try:
            with open('Gemfile.lock', 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            specs_section = text.split('GEM\n')[1] if 'GEM\n' in text else ''
            # lines like:    rake (13.1.0)
            items: List[Dict[str, str]] = []
            for line in specs_section.splitlines():
                m = re.match(r"\s{2,}([a-zA-Z0-9_\-]+) \(([^\)]+)\)", line)
                if m:
                    items.append({'name': m.group(1), 'version': m.group(2)})
            return items
        except Exception:
            pass
    # global scope or fallback: gem list --local
    cp = run_cmd(['gem', 'list', '--local'])
    items: List[Dict[str, str]] = []
    for line in (cp.stdout or '').splitlines():
        # example: rake (13.1.0)
        m = re.match(r"^([a-zA-Z0-9_\-]+) \(([^\)]+)\)", line.strip())
        if m:
            # take first version if multiple
            ver = m.group(2).split(',')[0].strip()
            items.append({'name': m.group(1), 'version': ver})
    return items


def get_details(name: str) -> Dict[str, Any]:
    if not detect():
        return {'name': name, 'fields': {}, 'dependencies': []}
    cp = run_cmd(['gem', 'specification', name, '--local'])
    fields: Dict[str, Any] = {}
    deps: List[str] = []
    text = cp.stdout or ''
    # crude parsing from gemspec YAML-ish output
    def get_field(key: str) -> str:
        m = re.search(rf"^{key}:\s*(.*)$", text, flags=re.MULTILINE)
        return (m.group(1).strip() if m else '')

    fields['Name'] = get_field('name') or name
    fields['Version'] = get_field('version')
    fields['Summary'] = get_field('summary')
    fields['Homepage'] = get_field('homepage')
    fields['License'] = get_field('license') or get_field('licenses')

    # dependencies: lines like - !ruby/object:Gem::Dependency name: rake
    for m in re.finditer(r"name:\s*([a-zA-Z0-9_\-]+)", text):
        dep = m.group(1)
        if dep and dep.lower() != name.lower() and dep not in deps:
            deps.append(dep)

    return {
        'name': name,
        'fields': fields,
        'dependencies': deps,
    }


