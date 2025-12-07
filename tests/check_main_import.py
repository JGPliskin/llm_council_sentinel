import sys
import os

# Add global path
sys.path.append(os.path.join(os.path.dirname(__file__)))

try:
    from backend import main
    print("Successfully imported backend.main")
except ImportError as e:
    print(f"Failed to import backend.main: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Failed with error: {e}")
    sys.exit(1)
