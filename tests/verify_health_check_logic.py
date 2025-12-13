
import asyncio
import sys
import os
try:
    from unittest.mock import AsyncMock, patch
except ImportError:
    # Polyfill for Python < 3.8
    from unittest.mock import MagicMock, patch
    
    class AsyncMock(MagicMock):
        async def __call__(self, *args, **kwargs):
            return super(AsyncMock, self).__call__(*args, **kwargs)

try:
    # Adjust path to import backend modules
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

    # MOCK openrouter BEFORE importing validation AND slowapi for main
    from unittest.mock import MagicMock
    mock_openrouter = MagicMock()
    sys.modules["openrouter"] = mock_openrouter
    sys.modules["backend.openrouter"] = mock_openrouter
    
    mock_slowapi = MagicMock()
    sys.modules["slowapi"] = mock_slowapi
    sys.modules["slowapi.util"] = MagicMock()
    sys.modules["slowapi.errors"] = MagicMock()
    
    msg_mock = MagicMock()
    sys.modules["council"] = msg_mock
    
    # Now safe to import
    from validation import validate_council_health
    from main import resolve_target_councilors, app
    from config import COUNCILORS, COUNCILOR_MAP
except Exception as e:
    print(f"Import Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

async def test_health_check_logic():
    print("--- Testing Health Check Logic ---")
    
    # Mock COUNCILORS for testing
    test_councilors = [
        {"id": "c1", "model": "model-1", "active": True},
        {"id": "c2", "model": "model-2", "active": True},
        {"id": "c3", "model": "model-3", "active": True},
    ]
    
    # patch check_model_health to return False for model-2
    with patch("validation.check_model_health", new_callable=AsyncMock) as mock_check:
        mock_check.side_effect = lambda model: model != "model-2"
        
        results = await validate_council_health(test_councilors, count=3)
        
        print("\n[Checked Results]")
        for c in results:
            print(f"ID: {c['id']}, Healthy: {c.get('healthy')}, Error: {c.get('health_error')}")
            
        # Assertions
        assert results[0]['healthy'] == True
        assert results[1]['healthy'] == False
        assert results[2]['healthy'] == True
        assert results[1]['health_error'] == "Health check failed"
        print("[OK] validate_council_health logic correct")
        
        return results

def test_resolve_logic(annotated_council):
    print("\n--- Testing Execution Filtering Logic ---")
    
    
    # Create map for test councilors
    test_map = {c["id"]: c for c in annotated_council}

    # Mock ACTIVE_COUNCIL AND COUNCILOR_MAP in main.py
    with patch("main.ACTIVE_COUNCIL", annotated_council), \
         patch("main.COUNCILOR_MAP", test_map):
        
        # Case 1: Request all (including unhealthy c2)
        print("Testing Case 1: Requesting [c1, c2, c3]")
        resolved, needs_migration, ignored = resolve_target_councilors(["c1", "c2", "c3"], {})
        
        resolved_ids = [c['id'] for c in resolved]
        print(f"Resolved: {resolved_ids}")
        print(f"Ignored: {ignored}")
        
        assert "c1" in resolved_ids
        assert "c2" not in resolved_ids # SHOULD BE FILTERED
        assert "c3" in resolved_ids
        assert "c2" in ignored
        print("[OK] Unhealthy councilor c2 strictly ignored")

        # Case 2: Verification of API structure (Partial)
        # We can't easily spin up full FastAPI here without client, but we verified the logic units.

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    annotated = loop.run_until_complete(test_health_check_logic())
    test_resolve_logic(annotated)
    print("\n[OK] All logic checks passed!")
