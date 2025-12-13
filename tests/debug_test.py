
import sys
import os
import unittest
import traceback

log_file = "debug_output.txt"

with open(log_file, "w", encoding="utf-8") as f:
    try:
        sys.path.append(os.path.abspath("backend"))
        sys.path.append(os.path.abspath("tests"))
        
        import httpx
        f.write("httpx imported successfully\n")
        
        # Import the test module
        import test_concurrency_logic
        f.write("Test module imported\n")
        
        # Create a suite
        suite = unittest.TestLoader().loadTestsFromModule(test_concurrency_logic)
        f.write(f"Tests loaded: {suite.countTestCases()}\n")
        
        # Run
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        result = runner.run(suite)
        
        if not result.wasSuccessful():
            sys.exit(1)
            
    except Exception:
        f.write("DRIVER EXCEPTION:\n")
        f.write(traceback.format_exc())
        sys.exit(1)
