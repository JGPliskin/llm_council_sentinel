import os
import httpx
import json
import sys
import asyncio

# Load env safely
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

NIM_API_KEYS = os.getenv("NIM_API_KEYS", "").split(",")[0].strip()
NIM_API_BASE = os.getenv("NIM_API_BASE", "https://integrate.api.nvidia.com/v1")

if not NIM_API_KEYS:
    print("Error: NIM_API_KEYS not found in env")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {NIM_API_KEYS}",
    "Content-Type": "application/json"
}

MODEL = "z-ai/glm4.7"

tool_definition = {
    "type": "function",
    "function": {
        "name": "emit_thinking",
        "description": "Emit a thinking process step.",
        "parameters": {
            "type": "object",
            "properties": {
                "bullet_id": {"type": "string"},
                "title": {"type": "string"},
                "detail": {"type": "string"},
                "op": {"type": "string", "enum": ["append", "update"]}
            },
            "required": ["title"]
        }
    }
}

async def test_glm(use_tools=True):
    print(f"\n--- Testing {MODEL} (Tools={use_tools}) ---")
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Hello, who are you?"}],
        "max_tokens": 100,
        "stream": True 
    }
    
    if use_tools:
        payload["tools"] = [tool_definition]
        payload["tool_choice"] = "auto"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NIM_API_BASE}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0
        )
    
        print(f"Status: {response.status_code}")
        print(f"Body: {response.text}")
        return response.status_code == 200

if __name__ == "__main__":
    success_with_tools = asyncio.run(test_glm(use_tools=True))
    success_without_tools = asyncio.run(test_glm(use_tools=False))
    
    if not success_with_tools and success_without_tools:
        print("\nCONCLUSION: Model fails with tools, works without.")
    elif success_with_tools:
        print("\nCONCLUSION: Model works with tools (Could not reproduce?).")
    else:
        print("\nCONCLUSION: Model fails regardless of tools.")
