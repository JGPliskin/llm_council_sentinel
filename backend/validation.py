import sys
import os
import asyncio
from typing import List, Optional, Dict, Any, Tuple

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openrouter import query_model
from config import COUNCIL_SIZE, PROBE_TIMEOUT_SECONDS, GLOBAL_MODEL_POOL
from health import health_manager


import time


async def check_model_health_probe(model_id: str) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Probe function to be passed to HealthManager.
    Returns: (success, error_message, status_code)
    
    Side effect: 如果探测成功，会自动更新 HealthRecord 中的 TTFT 统计数据。
    """
    messages = [{"role": "user", "content": "Reply OK"}]
    
    # 记录开始时间 (用于计算 TTFT)
    t_start = time.time()
    ttft_ms = None
    
    try:
        # We assume openrouter.query_model returns dict with 'error', 'status_code' etc.
        # based on our previous observation of openrouter.py
        response = await query_model(
            model_id, 
            messages, 
            timeout=PROBE_TIMEOUT_SECONDS,
            max_output_tokens=5
        )
        
        # 计算 TTFT (探测场景下，整个响应时间就是 TTFT)
        ttft_ms = int((time.time() - t_start) * 1000)
        
        if not response:
             return False, "No response", 500
             
        if response.get('error'):
             return False, response.get('content', 'Unknown error'), response.get('status_code')
        
        # 成功时更新 TTFT 统计
        record = health_manager._records.get(model_id)
        if record and ttft_ms is not None:
            record.update_ttft(ttft_ms)
             
        return True, None, 200
        
    except Exception as e:
        return False, str(e), 500


async def validate_council_health(
    pool: List[Dict[str, str]], 
    count: int = COUNCIL_SIZE, 
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Validate health using HealthManager.
    
    Returns:
        Dict containing:
        - councilors: List[Dict] (annotated)
        - meta: Dict (refresh info)
    """
    models_to_check = [c["model"] for c in pool]
    
    # 1. Trigger Refresh if requested
    refresh_meta = {}
    if force_refresh:
        print(f"Force refreshing health for {len(models_to_check)} models...", flush=True)
        refresh_meta = await health_manager.refresh_all(models_to_check, check_model_health_probe, force=True)
    
    # 2. Build Result List from Cache
    annotated_pool = []
    for councilor in pool:
        c = councilor.copy()
        model = c.get("model")
        
        status = health_manager.get_status(model)
        
        c.update(status) # Merge all health fields
        annotated_pool.append(c)

    return {
        "councilors": annotated_pool,
        "meta": refresh_meta
    }

# Backward compatibility wrapper if needed, but we should update main.py to usage new signature
# Or keep signature but return list (dropping meta)?
# main.py expects List[Dict]. Let's keep it compatible for now but update main to use new function if possible.
# Actually, main.py does: ACTIVE_COUNCIL = await validate_council_health(...)
# So we should probably return List and handle meta separately or side-effect.
# But distinct 'refresh' call in main.py is better.

# Let's change this function to ONLY return list, and leave explicit refresh to a new function or strict force_refresh param behavior.


def get_council_health_status(pool: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Read-only view of health status.
    Aggregates health: Councilor is healthy if ANY candidate is healthy.
    """
    annotated_pool = []
    for councilor in pool:
        c = councilor.copy()
        
        # Determine candidates
        candidates = c.get("model_candidates", [])
        if not candidates and c.get("model"):
            candidates = [c["model"]]
            
        # Check if any candidate is healthy
        is_any_healthy = False
        healthiest_record = None
        
        # We also want to expose which model is likely to be picked (the first healthy one)
        active_model = None
        
        for mid in candidates:
            status = health_manager.get_status(mid)
            if status.get("health_status") == "healthy":
                is_any_healthy = True
                if not active_model:
                    active_model = mid
                # If we found a healthy one, we can stop checking for "is_any_healthy"
                # but we might want to capture the status of the *active* one for display details
                healthiest_record = status
                break
            
            # Keep the last one just in case all fail, so we have something to show
            if healthiest_record is None:
                healthiest_record = status
        
        if not healthiest_record:
             # Should not happen if candidates list is not empty
             healthiest_record = {"health_status": "unknown", "healthy": False}

        # If any is healthy, mark overall as healthy (or use the active model's status)
        # If all fail, use the last checked model's status (likely unhealthy/cooldown)
        
        c.update(healthiest_record)
        
        # Override status if we found a healthy one (though healthiest_record should handle it)
        # Explicitly set active model Metadata
        if active_model:
            c["active_model"] = active_model
        else:
             c["active_model"] = candidates[0] if candidates else None
             
        annotated_pool.append(c)
    return annotated_pool

async def refresh_council_health(pool: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Force refresh ALL models in the Global Pool.
    The 'pool' argument is kept for compatibility but ignored for the refresh scope.
    """
    # We refresh EVERYTHING in the GLOBAL_MODEL_POOL to ensure availability
    models = [m["id"] for m in GLOBAL_MODEL_POOL]
    return await health_manager.refresh_all(models, check_model_health_probe, force=True)


def select_active_chairman(chairman: Dict[str, str]) -> Dict[str, str]:
    """
    Get chairman status.
    Uses cached status unless unknown/stale? 
    For chairman, we might want to ensure at least one check on startup if unknown.
    """
    model = chairman.get("model")
    status = health_manager.get_status(model)
    
    # If status is unknown, maybe we should probe?
    # But user said "Startup default to unknown".
    # So we just return strict status.
    
    c = chairman.copy()
    
    candidates = c.get("model_candidates", [])
    if not candidates and c.get("model"):
        candidates = [c["model"]]
        
    # Same aggregation logic
    healthiest_record = None
    active_model = None
    
    for mid in candidates:
        status = health_manager.get_status(mid)
        if status.get("health_status") == "healthy":
            healthiest_record = status
            active_model = mid
            break
        if healthiest_record is None:
             healthiest_record = status
             
    if not healthiest_record:
         healthiest_record = {"health_status": "unknown", "healthy": False}
         
    c.update(healthiest_record)
    if active_model:
        c["active_model"] = active_model
    else:
        c["active_model"] = candidates[0] if candidates else None

    return c
