
import sys
import os
import unittest
from unittest.mock import MagicMock
import traceback

# log file
log_file = "debug_output_patched.txt"

with open(log_file, "w", encoding="utf-8") as f:
    f.write("Starting patched runner...\n")
    try:
        # Pre-emptive patching of sys.modules to prevent httpx/trio import
        # This bypasses the Python 3.7 typing issue in trio
        sys.modules["httpx"] = MagicMock()
        sys.modules["httpcore"] = MagicMock()
        sys.modules["trio"] = MagicMock()
        
        f.write("Modules patched. Importing backend...\n")
        
        sys.path.append(os.path.abspath("backend"))
        sys.path.append(os.path.abspath("tests"))
        
        # Verify patch
        import httpx
        f.write(f"httpx is mocked: {isinstance(httpx, MagicMock)}\n")

        import council
        f.write("Council imported.\n")
        
        import test_concurrency_logic
        f.write("Test module imported.\n")

        suite = unittest.TestLoader().loadTestsFromModule(test_concurrency_logic)
        f.write(f"Running {suite.countTestCases()} tests...\n")
        
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        result = runner.run(suite)
        
        if not result.wasSuccessful():
            f.write("TESTS FAILED\n")
            sys.exit(1)
            
        f.write("TESTS PASSED\n")

    except Exception:
        f.write("RUNNER SCULL: \n")
        f.write(traceback.format_exc())
        sys.exit(1)
