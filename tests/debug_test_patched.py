
import sys
import os
import unittest
import traceback
import typing

# Monkey patch NoReturn for Python 3.7 compatibility
# The issue is specifically strict checks in typing.py on 3.7.0-3.7.1
# We replace NoReturn with something valid or disable the check if we could.
# Easier hack: Mock NoReturn to behave like a class that passes valid checks?
# Or just accept that trio is broken and we mock httpx entirely?

# Wait, we need httpx for logic? 
# The application code uses httpx.
# However, we are running tests. Our tests use `unittest.mock` to mock `query_model`'s internals.
# But `council.py` imports `openrouter` which imports `httpx`.
# So the import fails before mocking.

# Hack: Mock `httpx` and `openrouter` in sys.modules BEFORE importing council?
# Yes, because our tests mock `query_model` ANYWAY. We don't need real httpx for unit tests.
# This avoids the environment issue entirely.

sys.modules["httpx"] = unittest.mock.MagicMock()
sys.modules["httpcore"] = unittest.mock.MagicMock()

log_file = "debug_output.txt"

with open(log_file, "w", encoding="utf-8") as f:
    try:
        sys.path.append(os.path.abspath("backend"))
        sys.path.append(os.path.abspath("tests"))
        
        # Now we import our code. 
        # openrouter.py imports httpx, but it will get our Mock now.
        import council
        f.write("Council imported with mocked httpx\n")
        
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
