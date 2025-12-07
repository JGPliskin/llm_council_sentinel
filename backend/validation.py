"""Model validation and selection logic."""

import sys
import os
import asyncio
from typing import List, Optional

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
    messages = [{"role": "user", "content": "hi"}]
    
    # Set a short timeout for health checks to avoid delaying startup
    try:
        response = await query_model(model_id, messages, timeout=10.0)
        return response is not None and not response.get('error')
    except Exception:
        return False

async def select_active_council(pool: List[str], count: int = COUNCIL_SIZE) -> List[str]:
    """
    Select the first 'count' healthy models from the pool.
    
    Args:
        pool: List of model identifiers in order of preference
        count: Number of models to select
        
    Returns:
        List of selected active model identifiers
    """
    active_models = []
    
    # Check models sequentially until we fill the council
    # Note: We could do this in parallel, but we want to prioritize the top of the list
    for model in pool:
        if len(active_models) >= count:
            break
            
        print(f"Checking health of {model}...")
        is_healthy = await check_model_health(model)
        
        if is_healthy:
            print(f"Model {model} is HEALTHY")
            active_models.append(model)
        else:
            print(f"Model {model} is UNHEALTHY - skipping")
            
    # If we couldn't find enough models, just return what we have
    # (or potentially fall back to the first ones even if they failed, depending on policy)
    if len(active_models) == 0:
         print("WARNING: No healthy council models found!")
         
    return active_models

async def select_active_chairman(pool: List[str]) -> str:
    """
    Select the first healthy chairman model from the pool.
    
    Args:
        pool: List of model identifiers in order of preference
        
    Returns:
        The selected active chairman model identifier, or the first one if all fail
    """
    for model in pool:
        print(f"Checking health of chairman candidate {model}...")
        is_healthy = await check_model_health(model)
        
        if is_healthy:
            print(f"Chairman {model} is HEALTHY")
            return model
        else:
            print(f"Chairman {model} is UNHEALTHY - skipping")
            
    print("WARNING: No healthy chairman models found! Defaulting to first in pool.")
    return pool[0] if pool else "amazon/nova-2-lite-v1:free"
