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
    timeout: float = 120.0
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

    def build_error_response(error: Exception) -> Dict[str, Any]:
        """Create a standardized error response structure."""
        code = "unknown_error"
        message = str(error)

        if isinstance(error, httpx.HTTPStatusError):
            code = f"http_{error.response.status_code}"
            message = error.response.text or str(error)
        elif isinstance(error, httpx.TimeoutException):
            code = "timeout"

        return {
            "content": f"Error: {message}",
            "error": {"code": code, "message": message},
            "model": model,  # Keep original model on error
        }

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
        if isinstance(e, httpx.HTTPStatusError):
            print(f"Response body: {e.response.text}")
        return build_error_response(e)


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]]
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
    tasks = [query_model(model, messages) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}
