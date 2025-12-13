"""OpenRouter API client for making LLM requests."""

import httpx
from typing import List, Dict, Any, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import OPENROUTER_API_KEY, OPENROUTER_API_URL


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
    max_output_tokens: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds
        max_output_tokens: Optional max output tokens

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
    }
    if max_output_tokens is not None:
        payload["max_output_tokens"] = max_output_tokens

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            message = data['choices'][0]['message']

            return {
                'content': message.get('content'),
                'reasoning_details': message.get('reasoning_details'),
                'model': data.get('model')  # Capture actual model used
            }

    except Exception as e:
        print(f"Error querying model {model}: {e}")
        status_code = None
        headers = {}
        error_payload = None

        if isinstance(e, httpx.HTTPStatusError):
            print(f"Response body: {e.response.text}")
            status_code = e.response.status_code
            headers = dict(e.response.headers)
            try:
                error_payload = e.response.json()
            except Exception:
                error_payload = e.response.text

        return {
            'content': f"Error: {str(e)}",
            'error': True,
            'model': model,  # Keep original model on error
            'status_code': status_code,
            'headers': headers,
            'error_payload': error_payload
        }


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
    max_output_tokens: Optional[int] = None,
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

    # Create tasks for all models
    tasks = [query_model(model, messages, timeout=timeout, max_output_tokens=max_output_tokens) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}
