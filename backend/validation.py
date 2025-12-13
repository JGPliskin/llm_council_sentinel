import sys
import os
import asyncio
from typing import List, Optional, Dict

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


async def select_active_council(pool: List[Dict[str, str]], count: int = COUNCIL_SIZE) -> List[Dict[str, str]]:
    """
    Select the first 'count' healthy councilors from the pool.

    Args:
        pool: List of councilor definitions in order of preference
        count: Number of councilors to select

    Returns:
        List of selected councilor definitions
    """
    active_council: List[Dict[str, str]] = []

    for councilor in pool:
        if len(active_council) >= count:
            break

        model = councilor.get("model")
        print(f"Checking health of {model}...")
        is_healthy = await check_model_health(model)

        if is_healthy:
            print(f"Model {model} is HEALTHY")
            active_council.append(councilor)
        else:
            print(f"Model {model} is UNHEALTHY - skipping")

    if len(active_council) == 0:
        print("WARNING: No healthy council models found!")

    # Fallback: return top N even if unhealthy
    return active_council or pool[:count]


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
