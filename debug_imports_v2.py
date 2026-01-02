import sys
import os

# 把当前目录加入 path
sys.path.append(os.getcwd())

print("Attempting to import backend.main...")
try:
    import backend.main
    print("Import successful!")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
