"""Verification script for model rotation."""

import asyncio
import sys
import os
from unittest.mock import patch, MagicMock

# Mock dependencies that might be missing in this environment
sys.modules["httpx"] = MagicMock()
sys.modules["dotenv"] = MagicMock() # In case logic uses it

# Add backend to path explicitly and print it
backend_path = os.path.join(os.path.dirname(__file__), "backend")
print(f"Adding to sys.path: {backend_path}", flush=True)
sys.path.append(backend_path)

try:
    from validation import select_active_council, select_active_chairman, check_model_health
    import validation
    print(f"Imported validation from: {validation.__file__}", flush=True)
    from config import COUNCIL_MODEL_POOL, CHAIRMAN_MODEL_POOL, COUNCIL_SIZE
    print("Imports successful.", flush=True)
except ImportError as e:
    print(f"Import failed: {e}", flush=True)
    sys.exit(1)

async def mock_query_model(model, messages, timeout=None):
    """Mock query_model that fails for specific models."""
    print(f"[MOCK] Called for {model}", flush=True)
    # Simulate failure for the first model in each pool
    if model == COUNCIL_MODEL_POOL[0]:
        print(f"[MOCK] Simulating failure result for {model}", flush=True)
        return None
    if model == CHAIRMAN_MODEL_POOL[0]:
        print(f"[MOCK] Simulating failure result for {model}", flush=True)
        return None
        
    print(f"[MOCK] Simulating success result for {model}", flush=True)
    return {"content": "ok"}

async def verify_rotation():
    print("Starting rotation verification...", flush=True)
    
    # Check what we are patching
    print(f"Original query_model in validation: {validation.query_model}", flush=True)

    # Patch the query_model function used in validation
    # We patch 'validation.query_model' because validation.py does 'from openrouter import query_model'
    with patch('validation.query_model', side_effect=mock_query_model) as mock_obj:
        print(f"Patched query_model: {validation.query_model}", flush=True)
        
        print("\n--- Testing Council Rotation ---", flush=True)
        print(f"Pool: {COUNCIL_MODEL_POOL}", flush=True)
        
        # We need to await this
        active_council = await select_active_council(COUNCIL_MODEL_POOL, COUNCIL_SIZE)
        print(f"Selected Council: {active_council}", flush=True)
        
        # Verify that the first model was skipped
        assert COUNCIL_MODEL_POOL[0] not in active_council, "First model should have been skipped"
        assert len(active_council) == COUNCIL_SIZE, f"Should have selected {COUNCIL_SIZE} models"
        assert active_council[0] == COUNCIL_MODEL_POOL[1], "First active model should be the second one in pool"
        
        print("\n--- Testing Chairman Rotation ---", flush=True)
        print(f"Pool: {CHAIRMAN_MODEL_POOL}", flush=True)
        active_chairman = await select_active_chairman(CHAIRMAN_MODEL_POOL)
        print(f"Selected Chairman: {active_chairman}", flush=True)
        
        # Verify that the first chairman was skipped
        assert active_chairman != CHAIRMAN_MODEL_POOL[0], "First chairman should have been skipped"
        assert active_chairman == CHAIRMAN_MODEL_POOL[1], "Active chairman should be the second one in pool"
        
    print("\nVerification PASSED!", flush=True)

if __name__ == "__main__":
    try:
        asyncio.run(verify_rotation())
    except Exception as e:
        print(f"\nFATAL ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
