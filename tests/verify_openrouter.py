import asyncio
import os
from dotenv import load_dotenv

# Load .env manually to ensure we pick up local changes if any
load_dotenv()

# Set dummy key if not present, just to import the module without erroring immediately if it checks on import
# (Though config.py reads it at module level, so we need to validata that)
if not os.getenv("OPENROUTER_API_KEY"):
    print("WARNING: OPENROUTER_API_KEY not found in environment variables.")
    print("Please set it in your .env file or environment.")

from backend.openrouter import query_model
from backend.config import CHAIRMAN_MODEL

async def main():
    print(f"Testing OpenRouter connectivity with model: {CHAIRMAN_MODEL}")
    
    messages = [
        {"role": "user", "content": "Hello! Please reply with a short greeting."}
    ]
    
    try:
        response = await query_model(CHAIRMAN_MODEL, messages)
        
        if response:
            print("\nSUCCESS! Received response:")
            print("-" * 20)
            print(response.get("content"))
            print("-" * 20)
        else:
            print("\nFAILURE: Received None response.")
            
    except Exception as e:
        print(f"\nERROR: Exception occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
