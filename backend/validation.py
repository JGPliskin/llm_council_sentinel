import sys
import os
import asyncio
from typing import List, Optional, Dict, Any

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openrouter import query_model
from config import COUNCIL_SIZE


async def check_model_health(model_id: str) -> bool:
    """
    Check if a model is available by sending a minimal request.

    Args:
        model_id: The model identifier to check

    Returns:
        True if the model responds successfully, False otherwise
    """
    # "hi" sometimes gets filtered by strict safety models or is too short.
    messages = [{"role": "user", "content": "Hello"}]

    # Increase timeout for free-tier models which can be slow (cold start)
    try:
        response = await query_model(model_id, messages, timeout=25.0)
        
        if response and not response.get('error'):
            return True
        
        print(f"Health check failed for {model_id}: {response.get('content') if response else 'No response'}", flush=True)
        return False
    except Exception as e:
        print(f"Health check exception for {model_id}: {e}", flush=True)
        return False


async def validate_council_health(pool: List[Dict[str, str]], count: int = COUNCIL_SIZE, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Validate health of all councilors in the pool.
    Returns the FULL list with 'healthy', 'health_error', and 'health_checked_at' fields.
    
    Args:
        pool: List of councilor definitions
        count: (Unused but kept for sig compat) - we validate ALL
        force_refresh: Whether to force re-check
        
    Returns:
        Annotated list of councilors
    """
    import datetime
    
    annotated_pool = []
    
    # We check ALL, not just first 'count', because user wants to see unavailable ones
    for councilor in pool:
        # Create a copy to annotate
        c = councilor.copy()
        
        # Determine if we need to check (simple logic: always check if not checked recently?)
        # For this implementation, we check on startup/request.
        model = c.get("model")
        print(f"Checking health of {model}...", flush=True)
        
        try:
            is_healthy = await check_model_health(model)
            c["healthy"] = is_healthy
            c["health_error"] = None if is_healthy else "Health check failed"
            if is_healthy:
                 print(f"Model {model} is HEALTHY", flush=True)
            else:
                 print(f"Model {model} is UNHEALTHY", flush=True)
        except Exception as e:
            c["healthy"] = False
            c["health_error"] = str(e)
            print(f"Model {model} error: {e}", flush=True)
            
        c["health_checked_at"] = datetime.datetime.now().isoformat()
        annotated_pool.append(c)

    return annotated_pool


async def select_active_chairman(chairman: Dict[str, str]) -> Dict[str, str]:
    """
    Select a healthy chairman definition, falling back to the provided one.

    Args:
        chairman: Chairman definition dict

    Returns:
        The chosen chairman definition
    """
    model = chairman.get("model")
    print(f"Checking health of chairman candidate {model}...")
    is_healthy = await check_model_health(model)

    if is_healthy:
        print(f"Chairman {model} is HEALTHY")
        return chairman

    print("WARNING: Chairman model unhealthy, falling back to declared definition.")
    return chairman
