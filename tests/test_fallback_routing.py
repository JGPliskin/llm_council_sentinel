import sys
from unittest.mock import MagicMock

# Mock httpx to avoid import error in Py3.7/Trio
sys.modules["httpx"] = MagicMock()
sys.modules["httpcore"] = MagicMock()

import os
import pytest
from unittest.mock import patch, MagicMock
import asyncio

# Setup path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path setup
# Import after path setup
from backend.council import select_best_model, _request_stage1_bounded, ModelConcurrencyManager, health_manager
from backend.config import DEFAULT_STAGE1_TIMEOUT

@pytest.fixture
def mock_health_reset():
    # Reset health manager internal state
    health_manager._records = {}
    return health_manager

def test_select_best_model_basic(mock_health_reset):
    async def run():
        # Setup
        candidates = ["model_A", "model_B", "model_C"]
        
        # All unknown -> None (strict)
        assert select_best_model(candidates, set()) is None
        
        # A healthy
        mock_health_reset.update_status("model_A", True)
        
        
        assert select_best_model(candidates, set()) == "model_A"
        
        # A excluded
        assert select_best_model(candidates, {"model_A"}) is None
        
        # B healthy
        mock_health_reset.update_status("model_B", True)
        assert select_best_model(candidates, {"model_A"}) == "model_B"
    
    asyncio.run(run())

def test_request_stage1_fallback(mock_health_reset):
    async def run():
        # Setup
        councilor = {
            "id": "test_c",
            "name": "Test Councilor",
            "model": "model_primary",
            "model_candidates": ["model_primary", "model_backup"],
            "persona_path": "backend/personas/immanuel_kant.md", 
            "stage_limits": {"stage1": {"timeout": 1.0}}
        }
        
        # Mock Persona
        with patch("backend.council.fetch_persona", return_value="You are a test persona."):
            
            # Scenario: Primary Fails (Network), Backup Succeeds
            # Pre-seed healthy status (otherwise select_best_model returns None)
            mock_health_reset.update_status("model_primary", True)
            mock_health_reset.update_status("model_backup", True)
            
            async def side_effect(model, *args, **kwargs):
                if model == "model_primary":
                    return {"error": True, "content": "Network Fail", "status_code": 500}
                if model == "model_backup":
                    return {"status": "ok", "content": "Backup Answer", "model": "model_backup"}
                return None

            with patch("backend.council.stream_model", side_effect=side_effect) as mock_stream:
                semaphore = asyncio.Semaphore(10)
                
                res = await _request_stage1_bounded(semaphore, councilor, "Hello")
                
                assert res["status"] == "ok"
                assert res["model"] == "model_backup"
                assert res["fallback_used"] is True
                assert "model_primary" in res["attempted_models"]
                assert "model_backup" in res["attempted_models"]
                
                # Verify status updates
                h_primary = mock_health_reset.get_status("model_primary")
                assert h_primary["health_status"] != "healthy" # Should be unhealthy/cooldown
                
                h_backup = mock_health_reset.get_status("model_backup")
                assert h_backup["health_status"] == "healthy"
    
    asyncio.run(run())

def test_request_stage1_streams_answer_delta(mock_health_reset):
    async def run():
         # Setup
        councilor = {
            "id": "test_c",
            "name": "Test Councilor",
            "model": "model_smart",
            "model_candidates": ["model_smart"],
            "persona_path": "backend/personas/immanuel_kant.md",
        }
        
        with patch("backend.council.fetch_persona", return_value="You are a test persona."):
            mock_health_reset.update_status("model_smart", True)

            captured = []

            async def side_effect(model, messages, on_content=None, **kwargs):
                if on_content:
                    await on_content("Streamed ")
                    await on_content("Answer")
                return {"status": "ok", "content": "Streamed Answer", "model": "model_smart"}

            async def on_delta(cid, delta):
                captured.append((cid, delta))

            with patch("backend.council.stream_model", side_effect=side_effect):
                semaphore = asyncio.Semaphore(10)
                res = await _request_stage1_bounded(semaphore, councilor, "Hello", on_answer_delta=on_delta)

                assert res["status"] == "ok"
                assert res["answer_markdown"] == "Streamed Answer"
                assert captured == [("test_c", "Streamed "), ("test_c", "Answer")]
    
    asyncio.run(run())
