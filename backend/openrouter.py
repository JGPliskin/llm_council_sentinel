"""OpenRouter API client for making LLM requests."""

import asyncio
import httpx
from typing import List, Dict, Any, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_API_URL,
    RATE_LIMIT_BACKOFF_SECONDS,
)


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
    *,
    max_json_retries: int = 1,
    max_rate_limit_retries: int = 1,
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    async def perform_request(current_messages: List[Dict[str, str]], retrying: bool) -> Optional[Dict[str, Any]]:
        rate_attempts = 0
        while True:
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        OPENROUTER_API_URL,
                        headers=headers,
                        json={"model": model, "messages": current_messages},
                    )

                if response.status_code == 429 and rate_attempts < max_rate_limit_retries:
                    await asyncio.sleep(RATE_LIMIT_BACKOFF_SECONDS)
                    rate_attempts += 1
                    continue

                response.raise_for_status()

                try:
                    data = response.json()
                except ValueError:
                    return None

                message = data["choices"][0]["message"]
                return {
                    "content": message.get("content"),
                    "reasoning_details": message.get("reasoning_details"),
                    "model": data.get("model"),
                }

            except Exception as e:
                print(f"Error querying model {model}: {e}")
                if isinstance(e, httpx.HTTPStatusError):
                    print(f"Response body: {e.response.text}")
                if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 429:
                    # Exhausted rate limit retries
                    return {
                        "content": f"Error: rate limited for model {model}",
                        "error": True,
                        "model": model,
                    }

                if retrying:
                    # Only one retry cycle is allowed
                    return {
                        "content": f"Error: {str(e)}",
                        "error": True,
                        "model": model,
                    }
                raise

    try:
        data = await perform_request(messages, retrying=False)

        json_attempts = 0
        while data is None and json_attempts < max_json_retries:
            strict_messages = messages + [
                {
                    "role": "system",
                    "content": "Return a valid JSON response following the chat completion schema only.",
                }
            ]
            json_attempts += 1
            data = await perform_request(strict_messages, retrying=True)

        return data

    except Exception as e:
        print(f"Error querying model {model}: {e}")
        return {
            "content": f"Error: {str(e)}",
            "error": True,
            "model": model,
        }


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
    *,
    concurrency: int,
    default_timeout: float,
    timeout_overrides: Optional[Dict[str, float]] = None,
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of OpenRouter model identifiers
        messages: List of message dicts to send to each model

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    import asyncio

    timeout_overrides = timeout_overrides or {}
    semaphore = asyncio.Semaphore(concurrency)

    async def run(model: str) -> Optional[Dict[str, Any]]:
        model_timeout = timeout_overrides.get(model, default_timeout)
        async with semaphore:
            return await query_model(model, messages, timeout=model_timeout)

    tasks = [run(model) for model in models]
    responses = await asyncio.gather(*tasks)
    return {model: response for model, response in zip(models, responses)}
