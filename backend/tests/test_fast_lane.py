
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os
import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from health import HealthManager, HealthRecord
from council import select_best_model, _request_stage1_bounded
from config import SPEED_ROUTE_SWITCH_ABS_MS, SPEED_ROUTE_SWITCH_REL_PCT

# -------------------------------------------------------------------------
# Unit Tests: Health Logic & Sorting
# -------------------------------------------------------------------------

@pytest.fixture
def health_manager():
    return HealthManager()

def test_is_ttft_slow(health_manager):
    record = HealthRecord()
    # Case 1: Absolute Threshold
    assert record.is_slow(current_ttft_ms=6000, threshold_ms=5000, multiplier=3) is True
    assert record.is_slow(current_ttft_ms=3000, threshold_ms=5000, multiplier=3) is False

    # Case 2: Relative Threshold (EMA)
    record.ema_ttft_ms = 1000.0
    # 3 * 1000 = 3000
    assert record.is_slow(current_ttft_ms=3500, threshold_ms=9000, multiplier=3) is True
    assert record.is_slow(current_ttft_ms=2500, threshold_ms=9000, multiplier=3) is False

def test_health_record_p50_logic():
    record = HealthRecord()
    # Add 4 samples
    for i in [100, 200, 300, 400]:
        record.update_ttft(i)
    
    # Not enough samples for p50
    assert record.p50_ttft_ms is None
    # EMA calc: 
    # 100
    # 0.3*200 + 0.7*100 = 60+70=130
    # 0.3*300 + 0.7*130 = 90+91=181
    # 0.3*400 + 0.7*181 = 120+126.7=246.7
    assert abs(record.get_effective_ttft() - 246.7) < 0.1
    
    # Add 5th sample
    record.update_ttft(500)
    # Samples: [100, 200, 300, 400, 500] -> Median 300
    assert record.p50_ttft_ms == 300.0
    assert record.get_effective_ttft() == 300.0
    
    # Add 6th sample (sliding window)
    record.update_ttft(1000) 
    # Samples: [200, 300, 400, 500, 1000] -> Median 400
    assert record.p50_ttft_ms == 400.0

@patch('council.health_manager')
def test_select_best_model_sorting(mock_hm):
    # Setup 3 models
    # M1: 100ms
    # M2: 500ms
    # M3: None (missing)
    
    candidates = ["m1", "m2", "m3"]
    
    # Mock records
    r1 = MagicMock(spec=HealthRecord)
    r1.get_effective_ttft.return_value = 100
    r1.get_effective_status.return_value = "healthy"
    
    r2 = MagicMock(spec=HealthRecord)
    r2.get_effective_ttft.return_value = 500
    r2.get_effective_status.return_value = "healthy"
    
    r3 = MagicMock(spec=HealthRecord)
    r3.get_effective_ttft.return_value = None
    r3.get_effective_status.return_value = "healthy"
    
    mock_hm.get_status.return_value = {"health_status": "healthy"}
    mock_hm._records = {"m1": r1, "m2": r2, "m3": r3}
    
    # Test auto route
    best = select_best_model(candidates, excluded=set(), auto_route_by_speed=True)
    assert best == "m1"
    
    # Test strict order (disable auto route)
    # m2 is slower, but if it were first in list...
    candidates_reordered = ["m2", "m1"]
    best_strict = select_best_model(candidates_reordered, excluded=set(), auto_route_by_speed=False)
    assert best_strict == "m2"

@patch('council.health_manager')
@patch('council._current_model_by_councilor', new_callable=dict) # Reset state
def test_anti_shake_switch(mock_state, mock_hm):
    councilor_id = "test_c"
    candidates = ["fast", "slow"]
    
    # Mock Records
    r_fast = MagicMock()
    r_fast.get_effective_ttft.return_value = 1000
    r_fast.get_effective_status.return_value = "healthy"
    
    r_slow = MagicMock()
    r_slow.get_effective_ttft.return_value = 2000
    r_slow.get_effective_status.return_value = "healthy"
    
    mock_hm._records = {"fast": r_fast, "slow": r_slow}
    mock_hm.get_status.return_value = {"health_status": "healthy"}

    # Setup: Current is SLOW
    mock_state[councilor_id] = "slow"
    
    # Scenario 1: Diff = 1000ms, Rel = 50%. (Threshold: 800ms, 30%) -> Should Switch
    best = select_best_model(candidates, excluded=set(), councilor_id=councilor_id, auto_route_by_speed=True)
    assert best == "fast"
    assert mock_state[councilor_id] == "fast"

    # Scenario 2: Small Diff
    mock_state[councilor_id] = "slow"
    # Make fast model slower (1500ms) -> Diff 500ms -> No Switch
    r_fast.get_effective_ttft.return_value = 1500
    
    best = select_best_model(candidates, excluded=set(), councilor_id=councilor_id, auto_route_by_speed=True)
    assert best == "slow" # Stick to current
    assert mock_state[councilor_id] == "slow"


# -------------------------------------------------------------------------
# Integration Tests: Request & Emergency Probe
# -------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_emergency_probe_trigger_integration():
    # Mock dependencies
    councilor = {
        "id": "c1",
        "name": "C1",
        "model": "m1",
        "model_candidates": ["m1", "m2"],
        "auto_route_by_speed": True
    }
    
    
    # Patch all the heavy lifting
    with patch("council.stream_model", new_callable=AsyncMock) as mock_stream, \
         patch("council.health_manager") as mock_hm, \
         patch("council.model_concurrency_manager") as mock_mcm, \
         patch("council.log_request_timing"):  # 禁用日志写入，防止测试数据污染
                # Fix: Mock Async Semaphore properly
                # The semaphore object itself (used in async with)
                fake_sem = MagicMock()
                fake_sem.__aenter__ = AsyncMock(return_value=None)
                fake_sem.__aexit__ = AsyncMock(return_value=None)

                # The get_semaphore method: must be async and return fake_sem
                mock_mcm.get_semaphore = AsyncMock(return_value=fake_sem)

                # Setup mock response with SLOW TTFT
                mock_stream.return_value = {
                    "model": "m1", 
                    "content": "ok", 
                    "ttft_ms": 6000 # > 5000 threshold
                }
                
                # Mock health check returning True for slow check
                mock_hm.is_ttft_slow.return_value = True
                mock_hm.trigger_emergency_refresh = AsyncMock()
                # Also mock get_status for selection
                mock_hm.get_status.return_value = {"health_status": "healthy"}
                # Mock record existence for selection (so it picks m1)
                mock_hm._records = {} 

                # Run specific function
                semaphore = asyncio.Semaphore(1)
                
                await _request_stage1_bounded(
                    semaphore=semaphore,
                    councilor=councilor,
                    user_query="hi",
                    enable_thinking=False
                )
                
                # Verify is_ttft_slow called
                mock_hm.is_ttft_slow.assert_called_with("m1", 6000, threshold=5000, multiplier=3)
                
                # Verify trigger called
                mock_hm.trigger_emergency_refresh.assert_called_once()
                args, kwargs = mock_hm.trigger_emergency_refresh.call_args
                assert set(args[0]) == set(["m1", "m2"]) # candidates

@pytest.mark.asyncio
async def test_no_emergency_trigger_when_fast():
     # Mock dependencies
    councilor = {
        "id": "c1",
        "model": "m1",
        "model_candidates": ["m1"]
    }
    
    
    with patch("council.stream_model", new_callable=AsyncMock) as mock_stream, \
         patch("council.health_manager") as mock_hm, \
         patch("council.model_concurrency_manager") as mock_mcm, \
         patch("council.log_request_timing"):  # 禁用日志写入，防止测试数据污染
                # Fix: Mock Async Semaphore properly
                fake_sem = MagicMock()
                fake_sem.__aenter__ = AsyncMock(return_value=None)
                fake_sem.__aexit__ = AsyncMock(return_value=None)
                mock_mcm.get_semaphore = AsyncMock(return_value=fake_sem)

                mock_stream.return_value = {
                    "model": "m1", 
                    "content": "ok", 
                    "ttft_ms": 200 # Fast
                }
                
                mock_hm.is_ttft_slow.return_value = False
                mock_hm.trigger_emergency_refresh = AsyncMock()
                mock_hm.get_status.return_value = {"health_status": "healthy"}

                semaphore = asyncio.Semaphore(1)
                await _request_stage1_bounded(
                    semaphore=semaphore,
                    councilor=councilor,
                    user_query="hi"
                )
                
                # Verify NOT called
                mock_hm.trigger_emergency_refresh.assert_not_called()
