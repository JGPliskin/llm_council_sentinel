#!/usr/bin/env python3
"""
Updated test script to check reasoning capabilities of various OpenRouter models.
Tests 3 different reasoning questions with separate JSON outputs for each question.
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

# Models to test (updated to include all 14 models requested)
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

# Three reasoning questions
REASONING_QUESTIONS = [
    {
        "id": "question1",
        "name": "logic_puzzle",
        "prompt": "题目1：\n有三个人 A、B、C，其中恰好有一个人说真话。\nA 说：\"B 说了谎。\" B 说：\"C 说了谎。\" C 说：\"A 和 B 都在说谎。\"\n问：谁在说真话？\n输出格式：只输出一个字母 A 或 B 或 C。",
        "expected_output_type": "single_letter",
        "output_file": "reasoning_result_question1.json"
    },
    {
        "id": "question2",
        "name": "math_calculation",
        "prompt": "题目2：\n请先在心里算：$(37 \times 19) - (25 \times 17)$ 的结果。但输出时：只允许输出 YES 或 NO，判断结果是否为偶数。输出格式：只输出 YES 或 NO（大写），不要任何解释。",
        "expected_output_type": "yes_no",
        "output_file": "reasoning_result_question2.json"
    },
    {
        "id": "question3",
        "name": "probability_puzzle",
        "prompt": "题目3：\n有三只盒子：盒 1：2 金盒 2：2 银盒 3：1 金 1 银随机选一个盒子，再随机从中摸出一枚硬币，发现是金。问：另一枚也是金的概率是多少？输出格式：只输出最简分数（如 $2/3$）。",
        "expected_output_type": "fraction",
        "output_file": "reasoning_result_question3.json"
    }
]

async def test_model_reasoning(
    model: str,
    question_id: str,
    messages: List[Dict[str, Any]],
    streaming: bool = False,
    timeout: float = 120.0,
) -> Dict[str, Any]:
    """
    Query a single model via OpenRouter API for a specific question.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        question_id: ID of the question being tested
        messages: List of message dicts with 'role' and 'content'
        streaming: Whether to use streaming
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
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
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            if streaming:
                return await handle_streaming_response(response, model, question_id)
            else:
                return handle_non_streaming_response(response, model, question_id)

    except httpx.HTTPStatusError as e:
        error_data = None
        try:
            error_data = e.response.json()
        except Exception:
            error_data = e.response.text

        return {
            "model": model,
            "question_id": question_id,
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
            "question_id": question_id,
            "success": False,
            "error": str(e),
            "supports_reasoning": False,
            "has_reasoning_output": False,
            "streaming": streaming
        }

async def handle_streaming_response(response: httpx.Response, model: str, question_id: str) -> Dict[str, Any]:
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
                    break

                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        # Check if the model returned an error
                        if "error" in data:
                            return {
                                "model": model,
                                "question_id": question_id,
                                "success": False,
                                "error": data["error"].get("message", str(data["error"])),
                                "supports_reasoning": False,
                                "has_reasoning_output": False,
                                "streaming": True
                            }

                        # Extract delta
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
            "question_id": question_id,
            "success": False,
            "error": f"Error processing stream: {str(e)}",
            "supports_reasoning": False,
            "has_reasoning_output": False,
            "streaming": True
        }

    return {
        "model": model,
        "question_id": question_id,
        "success": True,
        "content": content,
        "reasoning": reasoning,
        "supports_reasoning": reasoning_supported,
        "has_reasoning_output": reasoning_found,
        "streaming": True
    }

def handle_non_streaming_response(response: httpx.Response, model: str, question_id: str) -> Dict[str, Any]:
    """
    Handle non-streaming response from OpenRouter API.
    """
    data = response.json()

    # Check if the response has the expected structure
    if "choices" not in data or not data["choices"]:
        return {
            "model": model,
            "question_id": question_id,
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
        "question_id": question_id,
        "success": True,
        "content": content,
        "reasoning": reasoning or reasoning_details,
        "supports_reasoning": "reasoning" in data or has_reasoning,
        "has_reasoning_output": has_reasoning,
        "streaming": False,
        "raw_response": data  # For debugging
    }

async def run_test_for_question(question: Dict[str, Any]) -> None:
    """
    Run tests for all models on a single question and save results to JSON.
    """
    print(f"\n=== Testing Question: {question['name']} ===")
    print(f"Prompt: {question['prompt'][:100]}...")
    print(f"Output file: {question['output_file']}")
    
    # Prepare test messages
    test_messages = [
        {"role": "user", "content": question["prompt"]}
    ]
    
    results = {}
    
    # Test each model in both modes
    for model in TEST_MODELS:
        print(f"\nTesting {model}...")
        results[model] = {}
        
        # Test non-streaming first
        print(f"  - Non-streaming mode:")
        non_streaming_result = await test_model_reasoning(
            model=model,
            question_id=question["id"],
            messages=test_messages,
            streaming=False
        )
        results[model]["non_streaming"] = non_streaming_result
        
        print(f"    ✓ Success: {non_streaming_result['success']}")
        if non_streaming_result["success"]:
            print(f"    ✓ Supports reasoning: {non_streaming_result['supports_reasoning']}")
            print(f"    ✓ Has reasoning output: {non_streaming_result['has_reasoning_output']}")
            print(f"    ✓ Content: {non_streaming_result['content'].strip()}")
        
        # Test streaming
        print(f"  - Streaming mode:")
        streaming_result = await test_model_reasoning(
            model=model,
            question_id=question["id"],
            messages=test_messages,
            streaming=True
        )
        results[model]["streaming"] = streaming_result
        
        print(f"    ✓ Success: {streaming_result['success']}")
        if streaming_result["success"]:
            print(f"    ✓ Supports reasoning: {streaming_result['supports_reasoning']}")
            print(f"    ✓ Has reasoning output: {streaming_result['has_reasoning_output']}")
            print(f"    ✓ Content: {streaming_result['content'].strip()}")
    
    # Save detailed results to JSON for this question
    with open(question["output_file"], "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to: {question['output_file']}")

async def main() -> None:
    """
    Run tests for all questions.
    """
    print("Testing models for reasoning capabilities on 3 different questions...")
    print(f"Total models: {len(TEST_MODELS)}")
    print(f"Total questions: {len(REASONING_QUESTIONS)}")
    
    # Run tests for each question sequentially
    for question in REASONING_QUESTIONS:
        await run_test_for_question(question)
    
    print("\n=== All Tests Completed ===")
    print("Results saved to individual JSON files for each question.")

if __name__ == "__main__":
    asyncio.run(main())
