# scripts/setup.py
#!/usr/bin/env python3
"""
AFS Assessment Framework - Initial Setup Script
Handles environment setup, dependency installation, and initial configuration.
"""

import os
import sys
import subprocess
import shutil
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import secrets
import platform

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('setup.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

class AFSSetup:
    """Main setup class for AFS Assessment Framework"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.required_python_version = (3, 11)
        self.required_dirs = [
            'app', 'templates', 'static', 'data', 'config', 'logs', 
            'backups', 'static/dist', 'static/assets/images',
            'static/assets/fonts', 'static/uploads/temp'
        ]
        self.env_file = self.project_root / '.env'
        
    def run_setup(self) -> bool:
        """Execute complete setup process"""
        logger.info("Starting AFS Assessment Framework Setup...")
        
        try:
            self._check_system_requirements()
            self._create_directory_structure()
            self._setup_virtual_environment()
            self._install_dependencies()
            self._create_environment_config()
            self._initialize_static_assets()
            self._run_database_setup()
            self._create_startup_scripts()
            self._validate_installation()
            
            logger.info("Setup completed successfully!")
            self._print_next_steps()
            return True
            
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            return False
    
    def _check_system_requirements(self) -> None:
        """Validate system requirements"""
        logger.info("Checking system requirements...")
        
        # Check Python version
        current_version = sys.version_info[:2]
        if current_version < self.required_python_version:
            raise RuntimeError(
                f"Python {self.required_python_version[0]}.{self.required_python_version[1]}+ required. "
                f"Current: {current_version[0]}.{current_version[1]}"
            )
        
        # Check for required system tools
        required_tools = ['git', 'curl']
        missing_tools = []
        
        for tool in required_tools:
            if not shutil.which(tool):
                missing_tools.append(tool)
        
        if missing_tools:
            logger.warning(f"Missing optional tools: {', '.join(missing_tools)}")
        
        # Check available disk space (minimum 1GB)
        if platform.system() != 'Windows':
            statvfs = os.statvfs(self.project_root)
            free_bytes = statvfs.f_frsize * statvfs.f_bavail
            if free_bytes < 1024 * 1024 * 1024:  # 1GB
                logger.warning("Less than 1GB free disk space available")
        
        logger.info("System requirements check passed")
    
    def _create_directory_structure(self) -> None:
        """Create required directory structure"""
        logger.info("Creating directory structure...")
        
        for dir_path in self.required_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {full_path}")
        
        # Create .gitkeep files for empty directories
        empty_dirs = ['logs', 'backups', 'static/uploads/temp']
        for dir_path in empty_dirs:
            gitkeep_path = self.project_root / dir_path / '.gitkeep'
            gitkeep_path.touch()
    
    def _setup_virtual_environment(self) -> None:
        """Setup Python virtual environment"""
        logger.info("Setting up virtual environment...")
        
        venv_path = self.project_root / 'venv'
        
        if venv_path.exists():
            logger.info("Virtual environment already exists")
            return
        
        # Create virtual environment
        subprocess.run([
            sys.executable, '-m', 'venv', str(venv_path)
        ], check=True)
        
        logger.info("Virtual environment created successfully")
    
    def _install_dependencies(self) -> None:
        """Install Python dependencies"""
        logger.info("Installing Python dependencies...")
        
        venv_python = self._get_venv_python()
        requirements_file = self.project_root / 'requirements.txt'
        
        if not requirements_file.exists():
            logger.warning("requirements.txt not found, creating minimal version")
            self._create_requirements_file()
        
        # Upgrade pip first
        subprocess.run([
            venv_python, '-m', 'pip', 'install', '--upgrade', 'pip'
        ], check=True)
        
        # Install requirements
        subprocess.run([
            venv_python, '-m', 'pip', 'install', '-r', str(requirements_file)
        ], check=True)
        
        logger.info("Dependencies installed successfully")
    
    def _create_requirements_file(self) -> None:
        """Create basic requirements.txt if it doesn't exist"""
        requirements_content = """
Flask==2.3.3
Jinja2==3.1.2
SQLAlchemy==2.0.21
JayDeBeApi==1.2.3
python-dotenv==1.0.0
marshmallow==3.20.1
Flask-SQLAlchemy==3.0.5
gunicorn==21.2.0
psycopg2-binary==2.9.7
pymysql==1.1.0
pytest==7.4.2
coverage==7.3.2
click==8.1.7
"""
        
        requirements_file = self.project_root / 'requirements.txt'
        requirements_file.write_text(requirements_content.strip())
    
    def _create_environment_config(self) -> None:
        """Create .env configuration file"""
        logger.info("Creating environment configuration...")
        
        if self.env_file.exists():
            logger.info(".env file already exists")
            return
        
        # Generate secure secret key
        secret_key = secrets.token_urlsafe(32)
        
        env_content = f"""# AFS Assessment Framework Configuration
# Flask Settings
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY={secret_key}
DEBUG=True

# Database Settings  
DATABASE_TYPE=h2
DATABASE_URL=h2:file:./data/afs_assessment
DATABASE_POOL_SIZE=5
DATABASE_POOL_TIMEOUT=20

# Application Settings
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=static/uploads
EXPORT_FOLDER=data/exports

# Security Settings
SESSION_LIFETIME=7200
RATELIMIT_ENABLED=False

# Logging Settings
LOG_LEVEL=INFO
LOG_FILE=logs/afs_audit.log

# Analytics Settings
ANALYTICS_ENABLED=True
ANALYTICS_RETENTION_DAYS=365

# Performance Settings
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=300

# Development Settings (remove in production)
FLASK_DEBUG_TB_ENABLED=False
"""
        
        self.env_file.write_text(env_content)
        logger.info("Environment configuration created")
    
    def _initialize_static_assets(self) -> None:
        """Initialize static asset structure"""
        logger.info("Initializing static assets...")
        
        # Create basic CSS structure
        css_dir = self.project_root / 'static' / 'dist' / 'css'
        css_dir.mkdir(parents=True, exist_ok=True)
        
        # Create placeholder CSS file
        basic_css = """/* AFS Assessment Framework - Basic Styles */
:root {
    --primary-color: #3b82f6;
    --secondary-color: #64748b;
    --success-color: #059669;
    --warning-color: #d97706;
    --danger-color: #dc2626;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.assessment-card {
    border-left: 4px solid var(--primary-color);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
"""
        
        css_file = css_dir / 'main.css'
        if not css_file.exists():
            css_file.write_text(basic_css)
        
        # Create basic favicon
        favicon_content = self._create_basic_favicon()
        favicon_path = self.project_root / 'static' / 'assets' / 'images' / 'favicon.ico'
        favicon_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("Static assets initialized")
    
    def _create_basic_favicon(self) -> bytes:
        """Create a basic favicon (placeholder)"""
        # This would normally create a proper favicon
        # For now, return empty bytes - replace with actual favicon generation
        return b''
    
    def _run_database_setup(self) -> None:
        """Run database initialization"""
        logger.info("Initializing database...")
        
        try:
            # Import and run seed_database script
            sys.path.append(str(self.project_root / 'scripts'))
            from seed_database import DatabaseSeeder
            
            seeder = DatabaseSeeder()
            success = seeder.seed_database()
            
            if success:
                logger.info("Database initialized successfully")
            else:
                raise RuntimeError("Database initialization failed")
                
        except ImportError as e:
            logger.warning(f"Could not import database seeder: {e}")
            logger.info("Database setup will need to be run manually")
            logger.info("Run: python scripts/seed_database.py")
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
            logger.info("You can initialize the database manually later with:")
            logger.info("python scripts/seed_database.py")
    
    def _create_startup_scripts(self) -> None:
        """Create startup scripts for different environments"""
        logger.info("Creating startup scripts...")
        
        # Development startup script
        dev_script_content = """#!/bin/bash
# AFS Assessment Framework - Development Startup
cd "$(dirname "$0")"
source venv/bin/activate
export FLASK_ENV=development
export FLASK_DEBUG=1
python run.py
"""
        
        dev_script_path = self.project_root / 'start_dev.sh'
        dev_script_path.write_text(dev_script_content)
        dev_script_path.chmod(0o755)
        
        # Production startup script  
        prod_script_content = """#!/bin/bash
# AFS Assessment Framework - Production Startup
cd "$(dirname "$0")"
source venv/bin/activate
export FLASK_ENV=production
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 run:app
"""
        
        prod_script_path = self.project_root / 'start_prod.sh'
        prod_script_path.write_text(prod_script_content)
        prod_script_path.chmod(0o755)
        
        # Windows batch files
        dev_bat_content = """@echo off
cd /d "%~dp0"
call venv\\Scripts\\activate.bat
set FLASK_ENV=development
set FLASK_DEBUG=1
python run.py
"""
        
        dev_bat_path = self.project_root / 'start_dev.bat'
        dev_bat_path.write_text(dev_bat_content)
    
    def _validate_installation(self) -> None:
        """Validate the installation"""
        logger.info("Validating installation...")
        
        # Check required files exist
        required_files = [
            'run.py', 'requirements.txt', '.env',
            'app/__init__.py', 'config/__init__.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.warning(f"Missing files: {', '.join(missing_files)}")
        
        # Test Python environment
        venv_python = self._get_venv_python()
        result = subprocess.run([
            venv_python, '-c', 'import flask; print("Flask import successful")'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError("Flask import test failed")
        
        logger.info("Installation validation passed")
    
    def _get_venv_python(self) -> str:
        """Get path to virtual environment Python executable"""
        if platform.system() == 'Windows':
            return str(self.project_root / 'venv' / 'Scripts' / 'python.exe')
        else:
            return str(self.project_root / 'venv' / 'bin' / 'python')
    
    def _print_next_steps(self) -> None:
        """Print next steps for user"""
        print("\n" + "="*60)
        print("🎉 AFS Assessment Framework Setup Complete!")
        print("="*60)
        print("\nNext Steps:")
        print("1. Activate virtual environment:")
        if platform.system() == 'Windows':
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        
        print("\n2. Start development server:")
        print("   python run.py")
        print("   OR")
        print("   ./start_dev.sh")
        
        print("\n3. Access the application:")
        print("   http://localhost:5000")
        
        print("\n4. For production deployment:")
        print("   ./start_prod.sh")
        
        print("\nConfiguration file: .env")
        print("Logs directory: logs/")
        print("Setup log: setup.log")
        print("\n" + "="*60)

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("AFS Assessment Framework Setup Script")
        print("Usage: python scripts/setup.py")
        print("\nThis script will:")
        print("- Check system requirements")
        print("- Create directory structure")
        print("- Setup virtual environment")
        print("- Install dependencies")
        print("- Create configuration files")
        print("- Initialize database")
        return
    
    setup = AFSSetup()
    success = setup.run_setup()
    
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()