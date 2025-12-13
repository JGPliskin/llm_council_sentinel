import sys
import os
import asyncio
from typing import List, Optional, Dict, Any, Tuple

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openrouter import query_model
from config import COUNCIL_SIZE, PROBE_TIMEOUT_SECONDS
from health import health_manager


async def check_model_health_probe(model_id: str) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Probe function to be passed to HealthManager.
    Returns: (success, error_message, status_code)
    """
    messages = [{"role": "user", "content": "Reply OK"}]
    
    try:
        # We assume openrouter.query_model returns dict with 'error', 'status_code' etc.
        # based on our previous observation of openrouter.py
        response = await query_model(
            model_id, 
            messages, 
            timeout=PROBE_TIMEOUT_SECONDS,
            max_output_tokens=5
        )
        
        if not response:
             return False, "No response", 500
             
        if response.get('error'):
             return False, response.get('content', 'Unknown error'), response.get('status_code')
             
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

def get_council_health_status(pool: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Read-only view of health status."""
    annotated_pool = []
    for councilor in pool:
        c = councilor.copy()
        status = health_manager.get_status(c["model"])
        c.update(status)
        annotated_pool.append(c)
    return annotated_pool

async def refresh_council_health(pool: List[Dict[str, str]]) -> Dict[str, Any]:
    """Force refresh and return meta."""
    models = [c["model"] for c in pool]
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
    c.update(status)
    return c
