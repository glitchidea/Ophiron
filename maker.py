#!/usr/bin/env python3
"""

 Ophiron Maker
 A setup tool will be created to automate the installation of Celery, Redis, and Django. 
 It will be deployed in a production environment
 
"""

import os
import sys
import subprocess
import shutil
import shlex
import json
from pathlib import Path


def find_python():
    """Find Python executable"""
    # Try python3 first
    python_cmd = shutil.which('python3')
    if python_cmd:
        return python_cmd
    
    # Then try python
    python_cmd = shutil.which('python')
    if python_cmd:
        return python_cmd
    
    # If neither found, use current python
    return sys.executable


def run_command(cmd, check=True, shell=False, cwd=None):
    """Run command and return result"""
    # For Linux compatibility: Show command as string or join if list
    cmd_display = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)
    print(f"🔄 Running: {cmd_display}")
    try:
        if isinstance(cmd, str) and not shell:
            # shlex.split safely parses on Linux
            cmd = shlex.split(cmd)
        
        result = subprocess.run(
            cmd,
            check=check,
            shell=shell,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',  # Use UTF-8 encoding on Linux
            errors='replace'  # Replace on encoding errors
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        if check:
            raise
        return e
    except FileNotFoundError as e:
        print(f"❌ Command not found: {e}")
        if check:
            raise
        return e


def check_docker_installed():
    """Check if Docker is installed"""
    try:
        result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Docker found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Docker not found. Please install Docker.")
    return False


def check_redis_container():
    """Check if Redis container is running"""
    try:
        result = subprocess.run(
            ['docker', 'ps', '-a', '--filter', 'name=redis', '--format', '{{.Names}}'],
            capture_output=True,
            text=True
        )
        if 'redis' in result.stdout:
            # Container exists, check if it's running
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=redis', '--format', '{{.Names}}'],
                capture_output=True,
                text=True
            )
            if 'redis' in result.stdout:
                print("✅ Redis container already running")
                return True
            else:
                print("🔄 Redis container found but not running, starting...")
                run_command(['docker', 'start', 'redis'], check=False)
                return True
        return False
    except Exception as e:
        print(f"⚠️ Error checking Redis: {e}")
        return False


def setup_redis():
    """Start Redis in Docker"""
    if not check_docker_installed():
        return False
    
    if check_redis_container():
        return True
    
    print("🔄 Creating and starting Redis container...")
    try:
        run_command([
            'docker', 'run', '-d',
            '--name', 'redis',
            '-p', '6379:6379',
            '--restart', 'unless-stopped',
            'redis:latest'
        ], check=True)
        print("✅ Redis started successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to start Redis: {e}")
        return False


def setup_venv(python_cmd):
    """Create virtual environment"""
    venv_path = Path('venv')
    
    if venv_path.exists():
        print("⚠️ venv already exists, skipping...")
        return True
    
    print("🔄 Creating virtual environment...")
    try:
        run_command([python_cmd, '-m', 'venv', 'venv'], check=True)
        print("✅ Virtual environment created")
        return True
    except Exception as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False


def get_venv_python():
    """Return Python path inside venv"""
    # Standard path for Linux and Unix systems
    if sys.platform == 'win32':
        return Path('venv/Scripts/python.exe')
    else:
        # For Linux, macOS and other Unix systems
        return Path('venv/bin/python')


def install_requirements(python_cmd):
    """Install requirements.txt"""
    print("🔄 Installing requirements...")
    try:
        # Upgrade pip
        run_command([str(python_cmd), '-m', 'pip', 'install', '--upgrade', 'pip'], check=False)
        
        # Install requirements
        requirements_file = Path('requirements.txt')
        if not requirements_file.exists():
            print("❌ requirements.txt not found!")
            return False
        
        run_command([str(python_cmd), '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Requirements installed successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to install requirements: {e}")
        return False


def check_celery_container():
    """Check if Celery container is running"""
    try:
        result = subprocess.run(
            ['docker', 'ps', '-a', '--filter', 'name=celery', '--format', '{{.Names}}'],
            capture_output=True,
            text=True
        )
        if 'celery' in result.stdout:
            # Container exists, check if it's running
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=celery', '--format', '{{.Names}}'],
                capture_output=True,
                text=True
            )
            if 'celery' in result.stdout:
                print("✅ Celery container already running")
                return True
            else:
                print("🔄 Celery container found but not running, starting...")
                run_command(['docker', 'start', 'celery'], check=False)
                return True
        return False
    except Exception as e:
        print(f"⚠️ Error checking Celery: {e}")
        return False


def start_celery_worker(python_cmd):
    """Start Celery worker in Docker"""
    if not check_docker_installed():
        return False
    
    if check_celery_container():
        return True
    
    print("🔄 Creating and starting Celery container...")
    
    # Get project directory
    project_root = Path(__file__).parent.absolute()
    
    try:
        # For Linux compatibility: Try network host first, fallback to bridge network
        # Create Celery container using Python image
        # Mount project directory, install requirements and run celery
        
        # Use more general Python version (3-slim instead of 3.11)
        # Use python:3-slim to be available on all Linux distributions
        docker_cmd = [
            'docker', 'run', '-d',
            '--name', 'celery',
            '--network', 'host',  # To access Redis on Linux
            '--restart', 'unless-stopped',
            '-v', f'{project_root}:/app',
            '-w', '/app',
            'python:3-slim',  # More general, available on all Linux
            'sh', '-c',
            'pip install --no-cache-dir -q -r requirements.txt && celery -A core worker --loglevel=info --pool=solo'
        ]
        
        run_command(docker_cmd, check=True)
        print("✅ Celery container started successfully")
        print("💡 To view Celery logs: docker logs -f celery")
        return True
    except Exception as e:
        print(f"❌ Failed to start Celery container: {e}")
        print("⚠️ Trying to run locally as fallback...")
        # Fallback: Try running locally
        # Note: On Linux, host network usually works, this fallback is rarely needed
        return start_celery_worker_local(python_cmd)


def start_celery_worker_local(python_cmd):
    """Start Celery worker locally (fallback)"""
    print("🔄 Starting Celery worker locally...")
    
    celery_cmd = None
    if sys.platform == 'win32':
        celery_cmd = Path('venv/Scripts/celery.exe')
    else:
        celery_cmd = Path('venv/bin/celery')
    
    if not celery_cmd.exists():
        print("⚠️ Celery command not found, check requirements installation")
        return False
    
    try:
        # Start Celery worker in background
        celery_process = subprocess.Popen(
            [
                str(celery_cmd),
                '-A', 'core', 'worker',
                '--loglevel=info',
                '--pool=solo'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"✅ Celery worker started (PID: {celery_process.pid})")
        print("⚠️ Celery worker is running in background. You can use the PID to stop it.")
        return True
    except Exception as e:
        print(f"❌ Failed to start Celery worker: {e}")
        return False


def create_superuser(python_cmd):
    """Create superuser"""
    print("\n" + "="*50)
    print("👤 Create Superuser")
    print("="*50)
    
    username = input("Username: ").strip()
    if not username:
        print("❌ Username cannot be empty!")
        return False
    
    email = input("Email (optional, can be left blank): ").strip()
    # Email is optional, can be left blank
    
    password = input("Password: ").strip()
    if not password:
        print("❌ Password cannot be empty!")
        return False
    
    password_confirm = input("Password (confirm): ").strip()
    if password != password_confirm:
        print("❌ Passwords do not match!")
        return False
    
    print("\n🔄 Creating superuser...")
    
    try:
        # Create superuser using Django shell
        # If email is empty, pass empty string
        # For Linux compatibility: Escape special characters
        email_value = email if email else ''
        
        # Security: Escape special characters (against SQL injection-like attacks)
        username_escaped = json.dumps(username)
        email_escaped = json.dumps(email_value)
        password_escaped = json.dumps(password)
        
        create_user_script = f"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

username = {username_escaped}
email = {email_escaped}
password = {password_escaped}

if User.objects.filter(username=username).exists():
    print('⚠️ This username already exists!')
else:
    User.objects.create_superuser(username, email, password)
    print('✅ Superuser created successfully!')
"""
        
        result = run_command(
            [str(python_cmd), 'manage.py', 'shell', '-c', create_user_script],
            check=False
        )
        
        if result.returncode == 0:
            print("✅ Superuser created successfully!")
            return True
        else:
            print("❌ Failed to create superuser!")
            return False
            
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
        return False


def run_migrations(python_cmd):
    """Create and run Django migrations"""
    print("🔄 Running makemigrations...")
    try:
        # First run makemigrations
        result = run_command([str(python_cmd), 'manage.py', 'makemigrations'], check=False)
        if result.returncode == 0:
            print("✅ Makemigrations completed")
        else:
            print("⚠️ Warning during makemigrations (may be no new migrations)")
    except Exception as e:
        print(f"⚠️ Error during makemigrations: {e}")
    
    print("🔄 Running migrate...")
    try:
        # Then run migrate
        run_command([str(python_cmd), 'manage.py', 'migrate'], check=True)
        print("✅ Migrations completed successfully")
        return True
    except Exception as e:
        print(f"❌ Migrations failed: {e}")
        return False


def main():
    """Main setup function"""
    print("="*50)
    print("🚀 Starting Ophiron Setup")
    print("="*50)
    print()
    
    # Change to project directory
    project_root = Path(__file__).parent.absolute()
    os.chdir(project_root)
    print(f"📁 Working directory: {project_root}")
    print()
    
    # Find Python
    python_cmd = find_python()
    print(f"🐍 Python found: {python_cmd}")
    print()
    
    # 1. Create virtual environment
    if not setup_venv(python_cmd):
        print("❌ Setup failed: Could not create virtual environment")
        sys.exit(1)
    print()
    
    # 2. Use Python from venv
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("❌ Venv Python not found!")
        sys.exit(1)
    
    print(f"🐍 Venv Python: {venv_python}")
    print()
    
    # 3. Install requirements
    if not install_requirements(venv_python):
        print("❌ Setup failed: Could not install requirements")
        sys.exit(1)
    print()
    
    # 4. Run makemigrations and migrate
    if not run_migrations(venv_python):
        print("⚠️ Migrations failed, continuing...")
    print()
    
    # 5. Start Redis
    if not setup_redis():
        print("⚠️ Failed to start Redis, continuing...")
    print()
    
    # 6. Start Celery worker
    if not start_celery_worker(venv_python):
        print("⚠️ Failed to start Celery worker, continuing...")
    print()
    
    # 7. Create superuser
    if not create_superuser(venv_python):
        print("⚠️ Failed to create superuser, you can create it later with 'python manage.py createsuperuser'")
    print()
    
    print("="*50)
    print("✅ Setup completed!")
    print("="*50)
    print()
    print("📝 Next steps:")
    print("  1. To start Django application:")
    print(f"     {venv_python} manage.py runserver 0.0.0.0:8000")
    print()
    print("  2. Or for production:")
    print(f"     {Path('venv/bin/gunicorn' if sys.platform != 'win32' else 'venv/Scripts/gunicorn.exe')} core.wsgi:application --bind 0.0.0.0:8000 --workers 4")
    print()


if __name__ == '__main__':
    main()
