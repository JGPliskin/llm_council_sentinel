#!/usr/bin/env python3
"""
Test script to check reasoning capabilities of various OpenRouter models.
Tests if models support reasoning parameters and can return reasoning details in both streaming and non-streaming modes.
"""

import asyncio
import httpx
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Models to test
TEST_MODELS = [
    "amazon/nova-2-lite-v1:free",  # Amazon: Nova 2 Lite (free)
    "arcee-ai/trinity-mini:free",   # Arcee AI: Trinity Mini (free)
    "tngtech/tng-r1t-chimera:free",  # TNG: R1T Chimera (free)
    "allenai/olmo-3-32b-think:free",  # AllenAI: Olmo 3 32B Think (free)
    "nvidia/nemotron-nano-12b-v2-vl:free",  # NVIDIA: Nemotron Nano 12B 2 VL (free)
    "alibaba/tongyi-deepresearch-30b-a3b:free",  # Tongyi DeepResearch 30B A3B (free)
    "nvidia/nemotron-nano-9b-v2:free",  # NVIDIA: Nemotron Nano 9B V2 (free)
    "openai/gpt-oss-120b:free",  # OpenAI: gpt-oss-120b (free)
    "openai/gpt-oss-20b:free",  # OpenAI: gpt-oss-20b (free)
    "z-ai/glm-4.5-air:free",  # Z.AI: GLM 4.5 Air (free)
    "tngtech/deepseek-r1t2-chimera:free",  # TNG: DeepSeek R1T2 Chimera (free)
    "qwen/qwen3-4b:free",  # Qwen: Qwen3 4B (free)
    "qwen/qwen3-235b-a22b:free",  # Qwen: Qwen3 235B A22B (free)
    "tngtech/deepseek-r1t-chimera:free"  # TNG: DeepSeek R1T Chimera (free)
]

# Test prompt that requires reasoning
test_prompt = """解决这个问题，一步一步来：
如果一辆火车以每小时60英里的速度行驶2小时，然后将速度提高到每小时80英里行驶1.5小时，
最后减速到每小时40英里行驶最后30分钟，那么它总共行驶了多少距离？
"""

async def test_model_reasoning(
    model: str, 
    messages: List[Dict[str, Any]],
    streaming: bool = False
) -> Dict[str, Any]:
    """
    Test a model's reasoning capabilities.
    
    Args:
        model: Model identifier
        messages: List of messages
        streaming: Whether to use streaming
    
    Returns:
        Dictionary with test results
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": streaming,
        "reasoning": {
            "effort": "high",
            "exclude": False
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            if streaming:
                return await handle_streaming_response(response, model)
            else:
                return handle_non_streaming_response(response, model)
                
    except httpx.HTTPStatusError as e:
        error_data = None
        try:
            error_data = e.response.json()
        except:
            error_data = e.response.text
        
        return {
            "model": model,
            "success": False,
            "error": str(e),
            "status_code": e.response.status_code,
            "error_details": error_data,
            "supports_reasoning": False,
            "has_reasoning_output": False,
            "streaming": streaming
        }
    except Exception as e:
        return {
            "model": model,
            "success": False,
            "error": str(e),
            "supports_reasoning": False,
            "has_reasoning_output": False,
            "streaming": streaming
        }

async def handle_streaming_response(response: httpx.Response, model: str) -> Dict[str, Any]:
    """
    Handle streaming response from OpenRouter API.
    """
    content = ""
    reasoning = ""
    reasoning_found = False
    reasoning_supported = True
    
    try:
        async for chunk in response.aiter_text():
            # Process each chunk
            for line in chunk.splitlines():
                line = line.strip()
                if not line:
                    continue
                
                if line == "data: [DONE]":
                    continue
                
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        # Check if the model returned an error
                        if "error" in data:
                            return {
                                "model": model,
                                "success": False,
                                "error": data["error"].get("message", str(data["error"])),
                                "supports_reasoning": False,
                                "has_reasoning_output": False,
                                "streaming": True
                            }
                        
                        # Extract content delta
                        choice = data.get("choices", [{}])[0]
                        delta = choice.get("delta", {})
                        
                        # Handle content (could be string or list of content parts)
                        if "content" in delta and delta["content"] is not None:
                            content_value = delta["content"]
                            if isinstance(content_value, str):
                                content += content_value
                            elif isinstance(content_value, list):
                                # Process content parts
                                for part in content_value:
                                    if isinstance(part, dict) and part.get("type") == "text":
                                        content += part.get("text", "")
                        
                        # Check for reasoning (could be string or other types)
                        if "reasoning" in delta and delta["reasoning"] is not None:
                            reasoning_value = delta["reasoning"]
                            reasoning_found = True
                            if isinstance(reasoning_value, str):
                                reasoning += reasoning_value
                            else:
                                # Convert other types to string
                                reasoning += str(reasoning_value)
                        
                        # Check if reasoning_details is in the response
                        if "reasoning_details" in delta and delta["reasoning_details"] is not None:
                            reasoning_details_value = delta["reasoning_details"]
                            reasoning_found = True
                            if isinstance(reasoning_details_value, str):
                                reasoning += reasoning_details_value
                            else:
                                # Convert other types to string
                                reasoning += str(reasoning_details_value)
                            
                    except json.JSONDecodeError:
                        continue
                        
    except Exception as e:
        return {
            "model": model,
            "success": False,
            "error": f"Error processing stream: {str(e)}",
            "supports_reasoning": False,
            "has_reasoning_output": False,
            "streaming": True
        }
    
    return {
        "model": model,
        "success": True,
        "content": content,
        "reasoning": reasoning,
        "supports_reasoning": reasoning_supported,
        "has_reasoning_output": reasoning_found,
        "streaming": True
    }

def handle_non_streaming_response(response: httpx.Response, model: str) -> Dict[str, Any]:
    """
    Handle non-streaming response from OpenRouter API.
    """
    data = response.json()
    
    # Check if the response has the expected structure
    if "choices" not in data or not data["choices"]:
        return {
            "model": model,
            "success": False,
            "error": "Invalid response structure: no choices",
            "supports_reasoning": False,
            "has_reasoning_output": False,
            "streaming": False
        }
    
    message = data["choices"][0]["message"]
    content = message.get("content", "")
    
    # Check for reasoning in different possible fields
    reasoning = message.get("reasoning", "")
    reasoning_details = message.get("reasoning_details", "")
    
    has_reasoning = bool(reasoning or reasoning_details)
    
    return {
        "model": model,
        "success": True,
        "content": content,
        "reasoning": reasoning or reasoning_details,
        "supports_reasoning": "reasoning" in data or has_reasoning,
        "has_reasoning_output": has_reasoning,
        "streaming": False,
        "raw_response": data  # For debugging
    }

async def run_tests() -> None:
    """
    Run tests for all models in both streaming and non-streaming modes.
    """
    print("Testing models for reasoning capabilities...\n")
    
    # Prepare test messages
    test_messages = [
        {"role": "user", "content": test_prompt}
    ]
    
    results = {}
    
    # Test each model in both modes
    for model in TEST_MODELS:
        print(f"Testing {model}...")
        results[model] = {}
        
        # Test non-streaming first
        print(f"  - Non-streaming mode:")
        non_streaming_result = await test_model_reasoning(model, test_messages, streaming=False)
        results[model]["non_streaming"] = non_streaming_result
        
        print(f"    ✓ Success: {non_streaming_result['success']}")
        if non_streaming_result["success"]:
            print(f"    ✓ Supports reasoning: {non_streaming_result['supports_reasoning']}")
            print(f"    ✓ Has reasoning output: {non_streaming_result['has_reasoning_output']}")
        
        # Test streaming
        print(f"  - Streaming mode:")
        streaming_result = await test_model_reasoning(model, test_messages, streaming=True)
        results[model]["streaming"] = streaming_result
        
        print(f"    ✓ Success: {streaming_result['success']}")
        if streaming_result["success"]:
            print(f"    ✓ Supports reasoning: {streaming_result['supports_reasoning']}")
            print(f"    ✓ Has reasoning output: {streaming_result['has_reasoning_output']}")
        
        print()
    
    # Generate summary
    print("=== TEST SUMMARY ===")
    for model, modes in results.items():
        print(f"\nModel: {model}")
        for mode, result in modes.items():
            status = "✓" if result["success"] else "✗"
            reasoning_support = "✓" if result.get("supports_reasoning", False) else "✗"
            reasoning_output = "✓" if result.get("has_reasoning_output", False) else "✗"
            
            print(f"  {mode.replace('_', ' ').title()}: {status}")
            print(f"    Supports reasoning parameter: {reasoning_support}")
            print(f"    Returns reasoning output: {reasoning_output}")
            
            if not result["success"]:
                print(f"    Error: {result.get('error', 'Unknown error')}")
    
    # Save detailed results to JSON
    with open("reasoning_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\nDetailed results saved to reasoning_test_results.json")

if __name__ == "__main__":
    asyncio.run(run_tests())
