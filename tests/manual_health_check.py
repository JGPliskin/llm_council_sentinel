
import asyncio
import sys
import os
import json

# Adjust path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from validation import check_model_health, validate_council_health
from config import COUNCILORS, COUNCIL_SIZE

async def debug_health():
    print("--- Debugging Real Health Checks ---")
    for c in COUNCILORS:
        model = c["model"]
        print(f"\nChecking {model}...")
        try:
            # We want to see the RAW response if possible, but check_model_health returns bool.
            # Let's import query_model directly to see why it fails.
            from openrouter import query_model
            
            messages = [{"role": "user", "content": "hi"}]
            response = await query_model(model, messages, timeout=10.0)
            
            print(f"Response: {json.dumps(response, indent=2)}")
            
            is_healthy = response is not None and not response.get('error')
            print(f"Calculated Health: {is_healthy}")
            
        except Exception as e:
            print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(debug_health())
