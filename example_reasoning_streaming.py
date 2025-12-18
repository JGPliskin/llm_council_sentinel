#!/usr/bin/env python3
"""
Example script demonstrating how to use the OpenRouter client with reasoning and streaming support.
"""

import asyncio
from typing import List, Dict, Any
from backend.openrouter import query_model, query_model_streaming

# Test configuration
TEST_MODEL = "tngtech/deepseek-r1t2-chimera:free"
TEST_MESSAGES = [
    {
        "role": "user",
        "content": "Solve this problem step by step: If a train travels at 60 mph for the first 2 hours, then increases its speed to 80 mph for the next 1.5 hours, and finally slows down to 40 mph for the last 30 minutes, what is the total distance traveled?"
    }
]
REASONING_CONFIG = {
    "effort": "high",
    "exclude": False
}

async def test_non_streaming_reasoning():
    """Test non-streaming reasoning functionality."""
    print("=== Testing Non-Streaming Reasoning ===")
    print(f"Model: {TEST_MODEL}")
    print("\nQuerying model...")
    
    result = await query_model(
        model=TEST_MODEL,
        messages=TEST_MESSAGES,
        reasoning=REASONING_CONFIG
    )
    
    if result and not result.get('error'):
        print(f"\n✅ Success!")
        print(f"Model used: {result.get('model')}")
        print(f"\n=== Content ===")
        print(result.get('content', ''))
        
        if result.get('reasoning'):
            print(f"\n=== Reasoning ===")
            print(result.get('reasoning', ''))
    else:
        print(f"\n❌ Error: {result.get('content', 'Unknown error')}")

async def test_streaming_reasoning():
    """Test streaming reasoning functionality."""
    print("\n\n=== Testing Streaming Reasoning ===")
    print(f"Model: {TEST_MODEL}")
    print("\nStreaming response...")
    
    full_content = ""
    full_reasoning = ""
    
    async for chunk in query_model_streaming(
        model=TEST_MODEL,
        messages=TEST_MESSAGES,
        reasoning=REASONING_CONFIG
    ):
        if chunk.get('error'):
            print(f"\n❌ Stream Error: {chunk.get('content')}")
            break
        
        # Collect content
        if chunk.get('content'):
            full_content += chunk.get('content')
            print(chunk.get('content'), end="", flush=True)
        
        # Collect reasoning separately (for frontend display)
        if chunk.get('reasoning'):
            full_reasoning += chunk.get('reasoning')
        
        if chunk.get('done'):
            print("\n\n✅ Stream completed!")
            break
    
    if full_reasoning:
        print(f"\n=== Reasoning (Collected Separately) ===")
        print(full_reasoning[:500] + "..." if len(full_reasoning) > 500 else full_reasoning)

async def main():
    """Run all tests."""
    await test_non_streaming_reasoning()
    await test_streaming_reasoning()
    
    print("\n\n=== Integration Example for Frontend ===")
    print("\nTo use this in your frontend, you can:")
    print("1. Create a WebSocket endpoint in your backend")
    print("2. When a client connects, call query_model_streaming()")
    print("3. Send each chunk as a WebSocket message with format:")
    print("   {")
    print("     'type': 'stream_chunk',")
    print("     'content': '<content_chunk>',")
    print("     'reasoning': '<reasoning_chunk>',")
    print("     'done': false,")
    print("     'model': '<model_name>'")
    print("   }")
    print("4. In your frontend, update the UI with each chunk")
    print("5. Display reasoning in a separate section or alongside content")

if __name__ == "__main__":
    asyncio.run(main())
