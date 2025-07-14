#!/usr/bin/env python3
"""
DevSecrin Setup Script
Automated setup for DevSecrin Developer Context Engine
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path
import json
import time
from packages.config import get_config

# Load configuration
config = get_config()

class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text, color=Colors.ENDC):
    print(f"{color}{text}{Colors.ENDC}")

def print_header(text):
    print_colored(f"\n{'='*60}", Colors.BLUE)
    print_colored(f"🚀 {text}", Colors.BLUE + Colors.BOLD)
    print_colored(f"{'='*60}", Colors.BLUE)

def print_step(text):
    print_colored(f"\n📋 {text}", Colors.YELLOW)

def print_success(text):
    print_colored(f"✅ {text}", Colors.GREEN)

def print_error(text):
    print_colored(f"❌ {text}", Colors.RED)

def run_command(cmd, cwd=None, check=True):
    """Run a command and handle errors gracefully"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True,
            check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, "", str(e)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python {version.major}.{version.minor} is not supported. Please upgrade to Python 3.8+")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_node_version():
    """Check if Node.js version is compatible"""
    success, stdout, stderr = run_command("node --version", check=False)
    if not success:
        print_error("Node.js is not installed. Please install Node.js 20+")
        return False
    
    version_str = stdout.strip().replace('v', '')
    major_version = int(version_str.split('.')[0])
    
    if major_version < 20:
        print_error(f"Node.js {version_str} is too old. Please upgrade to Node.js 20+")
        return False
    
    print_success(f"Node.js {version_str} is compatible")
    return True

def check_pnpm():
    """Check if pnpm is installed"""
    success, stdout, stderr = run_command("pnpm --version", check=False)
    if not success:
        print_error("pnpm is not installed. Installing pnpm...")
        success, _, _ = run_command("npm install -g pnpm")
        if success:
            print_success("pnpm installed successfully")
            return True
        else:
            print_error("Failed to install pnpm")
            return False
    print_success(f"pnpm {stdout.strip()} is available")
    return True

def check_ollama():
    """Check if Ollama is installed and running"""
    success, stdout, stderr = run_command("ollama --version", check=False)
    if not success:
        print_error("Ollama is not installed. Please install Ollama from https://ollama.ai")
        return False
    
    print_success(f"Ollama is installed")
    
    # Check if Ollama service is running
    success, _, _ = run_command("ollama list", check=False)
    if not success:
        print_error("Ollama service is not running. Please start Ollama service")
        return False
    
    print_success("Ollama service is running")
    return True

def install_ollama_model():
    """Install required Ollama model"""
    print_step(f"Installing {config.ollama_model} model...")
    
    # Check if model is already installed
    success, stdout, stderr = run_command("ollama list")
    if config.ollama_model in stdout:
        print_success(f"{config.ollama_model} model is already installed")
        return True
    
    print_colored(f"📥 Downloading {config.ollama_model} model (this may take a while)...", Colors.YELLOW)
    success, stdout, stderr = run_command(f"ollama pull {config.ollama_model}")
    
    if success:
        print_success(f"{config.ollama_model} model installed successfully")
        return True
    else:
        print_error(f"Failed to install {config.ollama_model} model: {stderr}")
        return False

def create_virtual_environment():
    """Create and activate Python virtual environment"""
    print_step("Creating Python virtual environment...")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print_colored("Virtual environment already exists. Removing old one...", Colors.YELLOW)
        shutil.rmtree(venv_path)
    
    success, stdout, stderr = run_command("python3 -m venv venv")
    if success:
        print_success("Virtual environment created successfully")
        return True
    else:
        print_error(f"Failed to create virtual environment: {stderr}")
        return False

def install_python_dependencies():
    """Install Python dependencies"""
    print_step("Installing Python dependencies...")
    
    # Determine the correct pip path based on OS
    if platform.system() == "Windows":
        pip_cmd = "venv\\Scripts\\pip"
    else:
        pip_cmd = "venv/bin/pip"
    
    # Upgrade pip first
    run_command(f"{pip_cmd} install --upgrade pip")
    
    # Install dependencies
    success, stdout, stderr = run_command(f"{pip_cmd} install -r requirements.txt")
    if success:
        print_success("Python dependencies installed successfully")
        return True
    else:
        print_error(f"Failed to install Python dependencies: {stderr}")
        return False

def install_node_dependencies():
    """Install Node.js dependencies"""
    print_step("Installing Node.js dependencies...")
    
    success, stdout, stderr = run_command("pnpm install")
    if success:
        print_success("Node.js dependencies installed successfully")
        return True
    else:
        print_error(f"Failed to install Node.js dependencies: {stderr}")
        return False

def create_env_file():
    """Create .env file with default configuration"""
    print_step("Creating environment configuration...")
    
    env_content = """# DevSecrin Environment Configuration

# Database Configuration
DATABASE_URL=postgresql://localhost/devsecrin
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=devsecrin
DATABASE_USER=devsecrin
DATABASE_PASSWORD=devsecrin

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:1.5b

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY=./chroma_store

# GitHub Integration (Optional - fill in if you want GitHub integration)
GITHUB_TOKEN=your_github_token_here
GITHUB_OWNER=your_github_username
GITHUB_REPO=your_repository_name

# Confluence Integration (Optional - fill in if you want Confluence integration)
CONFLUENCE_URL=your_confluence_url
CONFLUENCE_USERNAME=your_username
CONFLUENCE_API_TOKEN=your_api_token

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print_success("Environment file created at .env")
    print_colored("📝 Please edit .env file to configure your integrations", Colors.YELLOW)

def setup_database():
    """Setup PostgreSQL database"""
    print_step("Setting up database...")
    
    # Check if PostgreSQL is installed
    success, stdout, stderr = run_command("psql --version", check=False)
    if not success:
        print_error("PostgreSQL is not installed. Please install PostgreSQL first.")
        print_colored("Visit: https://www.postgresql.org/download/", Colors.YELLOW)
        return False
    
    print_success("PostgreSQL is installed")
    
    # Run database migrations
    if platform.system() == "Windows":
        python_cmd = "venv\\Scripts\\python"
    else:
        python_cmd = "venv/bin/python"
    
    success, stdout, stderr = run_command(f"{python_cmd} packages/dbup/runner.py")
    if success:
        print_success("Database setup completed")
        return True
    else:
        print_colored("Database setup failed. You may need to create the database manually.", Colors.YELLOW)
        return False

def create_quick_start_script():
    """Create a quick start script for users"""
    if platform.system() == "Windows":
        script_content = """@echo off
echo Starting DevSecrin Developer Context Engine...
echo.

echo Activating virtual environment...
call venv\\Scripts\\activate.bat

echo Starting the application...
pnpm run devsecrin

pause
"""
        with open("start.bat", "w") as f:
            f.write(script_content)
        print_success("Quick start script created: start.bat")
    else:
        script_content = """#!/bin/bash
echo "🚀 Starting DevSecrin Developer Context Engine..."
echo

echo "📦 Activating virtual environment..."
source venv/bin/activate

echo "🚀 Starting the application..."
pnpm run devsecrin
"""
        with open("start.sh", "w") as f:
            f.write(script_content)
        
        # Make it executable
        os.chmod("start.sh", 0o755)
        print_success("Quick start script created: start.sh")

def print_final_instructions():
    """Print final setup instructions"""
    print_header("Setup Complete! 🎉")
    
    print_colored("""
🎯 Next Steps:

1. Configure your integrations in the .env file:
   - Add your GitHub token for repository integration
   - Add Confluence credentials if needed
   - Adjust database settings if necessary

2. Start the application:""", Colors.GREEN)
    
    if platform.system() == "Windows":
        print_colored("   • Double-click start.bat", Colors.GREEN)
    else:
        print_colored("   • Run: ./start.sh", Colors.GREEN)
    
    print_colored("   • Or manually: pnpm run devsecrin", Colors.GREEN)
    
    print_colored("""
3. Open your browser to:
   • Frontend: http://localhost:3000
   • API: http://localhost:8000

4. Start asking questions about your codebase!

📚 Documentation: Check README.md for detailed usage instructions
🐛 Issues: Report problems at your GitHub repository
""", Colors.GREEN)

def main():
    """Main setup function"""
    print_header("DevSecrin Setup Wizard")
    print_colored("Welcome to DevSecrin - Developer Context Engine Setup!", Colors.BLUE)
    
    # Check prerequisites
    print_header("Checking Prerequisites")
    
    if not check_python_version():
        sys.exit(1)
    
    if not check_node_version():
        sys.exit(1)
    
    if not check_pnpm():
        sys.exit(1)
    
    if not check_ollama():
        sys.exit(1)
    
    # Install Ollama model
    if not install_ollama_model():
        print_colored("Warning: Failed to install Ollama model. You may need to install it manually.", Colors.YELLOW)
    
    # Setup project
    print_header("Setting Up Project")
    
    if not create_virtual_environment():
        sys.exit(1)
    
    if not install_python_dependencies():
        sys.exit(1)
    
    if not install_node_dependencies():
        sys.exit(1)
    
    create_env_file()
    
    # Setup database (optional)
    setup_database()
    
    # Create convenience scripts
    create_quick_start_script()
    
    # Final instructions
    print_final_instructions()

if __name__ == "__main__":
    main()
