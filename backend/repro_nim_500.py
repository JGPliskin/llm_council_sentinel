
import asyncio
import httpx
import json

API_KEY = "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"
API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
# MODEL = "deepseek-ai/deepseek-v3.1"
MODEL = "deepseek-ai/deepseek-v3.1-terminus"

async def test_nim(content_value):
    print(f"Testing with content={repr(content_value)}")
    
    assistant_msg = {
        "role": "assistant",
        "tool_calls": [
            {
                "id": "call_test_123",
                "type": "function",
                "function": {
                    "name": "emit_thinking",
                    "arguments": "{\"title\": \"Thinking\", \"detail\": \"Process started\"}"
                }
            }
        ]
    }
    
    # Handle content key
    if content_value is not ...:
        assistant_msg["content"] = content_value
    
    messages = [
        {"role": "user", "content": "Hello"},
        assistant_msg,
        {
            "role": "tool",
            "tool_call_id": "call_test_123",
            "content": json.dumps({"status": "recorded"})
        }
    ]
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "max_tokens": 100
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(API_URL, json=payload, headers=headers, timeout=30.0)
            if resp.status_code != 200:
                print(f"FAILED {resp.status_code}: {resp.text}")
            else:
                print(f"SUCCESS 200: {resp.text[:100]}...")
        except Exception as e:
            print(f"EXCEPTION: {e}")

async def main():
    print("--- Test 1: content='' ---")
    await test_nim("")
    
    print("\n--- Test 2: content=None ---")
    await test_nim(None)
    
    # print("\n--- Test 3: Omitted content ---")
    # await test_nim(...)
    
    print("\n--- Test 4: content='Thinking...' ---")
    await test_nim("Thinking...")

if __name__ == "__main__":
    asyncio.run(main())
