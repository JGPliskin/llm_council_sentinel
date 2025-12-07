import sys
import os
try:
    print("Attempting import...")
    import backend.main
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
