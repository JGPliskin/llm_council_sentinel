import os
import sys
import subprocess
import urllib.request
import venv
from pathlib import Path

# Configuration
VENV_DIR = Path(".venv")
PYTHON_EXC = VENV_DIR / "Scripts" / "python.exe"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"
REQUIREMENTS = ["openai>=1.0.0", "rich", "python-dotenv"]

def log(msg):
    print(f"[SETUP] {msg}")

def run_cmd(cmd, check=True):
    log(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=check)

def main():
    log("Initializing robust environment setup...")

    # 1. Create Virtual Environment
    if not VENV_DIR.exists():
        log(f"Creating venv at {VENV_DIR}...")
        venv.create(VENV_DIR, with_pip=True)
    
    # 2. Verify Python Executable
    if not PYTHON_EXC.exists():
        log(f"Error: Python executable not found at {PYTHON_EXC}")
        # Try to find it elsewhere or fail
        sys.exit(1)

    # 3. Check for PIP
    pip_check = subprocess.run([str(PYTHON_EXC), "-m", "pip", "--version"], capture_output=True)
    if pip_check.returncode != 0:
        log("PIP is missing in venv (Anaconda issue). Bootstrapping pip...")
        
        # Download get-pip.py
        get_pip_path = Path("get-pip.py")
        try:
            log("Downloading get-pip.py...")
            urllib.request.urlretrieve(GET_PIP_URL, get_pip_path)
            
            log("Installing pip...")
            run_cmd([str(PYTHON_EXC), str(get_pip_path)])
        except Exception as e:
            log(f"Failed to bootstrap pip: {e}")
            sys.exit(1)
        finally:
            if get_pip_path.exists():
                os.remove(get_pip_path)
    
    # 4. Install Dependencies
    log("Installing dependencies...")
    run_cmd([str(PYTHON_EXC), "-m", "pip", "install"] + REQUIREMENTS)

    # 5. Run the target script
    log("Setup complete. Launching Thinking Stream PoC...")
    print("-" * 50)
    
    # Pass through arguments
    target_script = "thinking_stream_test.py"
    cmd = [str(PYTHON_EXC), target_script] + sys.argv[1:]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
