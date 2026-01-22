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

async def test_glm(tool_choice_val="auto"):
    print(f"\n--- Testing {MODEL} (tool_choice={tool_choice_val}) ---")
    
    # Actual Chinese system prompt (Immanuel Kant)
    system_prompt = (
        "保持冷静的政策分析腔调，重视结构化推理与证据透明度，"
        "在比较选项时更关注长期稳健性而非短期噱头。"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "分析当前全球地缘政治局势"}
    ]
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 500,
        "stream": True,
        "tools": [tool_definition]
    }
    
    if tool_choice_val is not None:
        payload["tool_choice"] = tool_choice_val

    print(f"Payload keys: {list(payload.keys())}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NIM_API_BASE}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
        
            print(f"Status: {response.status_code}")
            if response.status_code >= 400:
                print(f"Error Body: {response.text}")
                return False
            
            # Read a bit of stream
            async for line in response.aiter_lines():
                if line:
                    print(f"First chunk: {line[:100]}")
                    break
            return True
            
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    # Test with "auto" (what app uses)
    print("Testing with tool_choice='auto'...")
    success_auto = asyncio.run(test_glm(tool_choice_val="auto"))
    
    # Test without tool_choice (implicit)
    print("\nTesting with tool_choice=None (implicit)...")
    success_none = asyncio.run(test_glm(tool_choice_val=None))
    
    if not success_auto and success_none:
        print("\nCONCLUSION: 'tool_choice: auto' causes the error.")
    elif success_auto:
         print("\nCONCLUSION: Both work. Need more complex repro?")
    else:
         print("\nCONCLUSION: Both fail.")
