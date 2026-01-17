"""Unified LLM client router for dual provider support (OpenRouter + NIM)."""

from typing import List, Dict, Any, Optional, Callable
from openrouter import stream_model as or_stream_model

# Import nim module to avoid circular import
import nim as nim_module
from config import GLOBAL_MODEL_MAP


def _nim_stream_model_wrapper(*args, **kwargs):
    """Wrapper to call nim.stream_model."""
    return nim_module.stream_model(*args, **kwargs)


def _get_provider(model_id: str) -> str:
    """
    Determine provider from model_id with strict priority.

    Priority 1: Check explicit provider field in GLOBAL_MODEL_MAP
    Priority 2: Check model_id prefix (nim: / openrouter:)
    Priority 3: Default to OpenRouter

    Args:
        model_id: Model identifier (may include prefix)

    Returns:
        Provider name: "nim" or "openrouter"
    """
    # Priority 1: Check explicit provider field in GLOBAL_MODEL_MAP
    if model_id in GLOBAL_MODEL_MAP:
        provider = GLOBAL_MODEL_MAP[model_id].get("provider")
        if provider:
            return provider.lower()

    # Priority 2: Check model_id prefix
    if model_id.startswith("nim:"):
        return "nim"
    if model_id.startswith("openrouter:"):
        return "openrouter"

    # Priority 3: Default to OpenRouter
    return "openrouter"


def _strip_prefix(model_id: str, provider: str) -> str:
    """
    Remove provider prefix from model_id.

    Args:
        model_id: Model identifier (may include prefix)
        provider: Provider name ("nim" or "openrouter")

    Returns:
        Clean model identifier without prefix
    """
    if provider == "nim" and model_id.startswith("nim:"):
        return model_id[4:]
    if provider == "openrouter" and model_id.startswith("openrouter:"):
        return model_id[11:]  # "openrouter:" is 11 characters
    return model_id


async def stream_model(
    model: str,
    messages: List[Dict[str, str]],
    on_thinking: Optional[Callable[[Dict[str, Any]], Any]] = None,
    on_content: Optional[Callable[[str], Any]] = None,
    timeout: float = 120.0,
    max_output_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Unified streaming interface - routes to appropriate provider.

    Routes to nim.py or openrouter.py based on provider determination.
    Strips provider prefix from model_id before calling respective client.

    Args:
        model: Model identifier (may include nim: or openrouter: prefix)
        messages: List of message dicts
        on_thinking: Callback for thinking payload (arg: dict)
        on_content: Callback for streamed content delta (arg: delta string)
        timeout: Request timeout
        max_output_tokens: Optional max output tokens
        tools: Optional list of tool definitions

    Returns:
        Response dict with content, error, status_code, model, ttft_ms, etc.
        Matches openrouter.py response format for seamless integration.
    """
    provider = _get_provider(model)
    clean_model = _strip_prefix(model, provider)

    # Route to appropriate client
    if provider == "nim":
        return await _nim_stream_model_wrapper(
            model=clean_model,
            messages=messages,
            on_thinking=on_thinking,
            on_content=on_content,
            timeout=timeout,
            max_output_tokens=max_output_tokens,
            tools=tools,
        )
    else:  # openrouter (default)
        return await or_stream_model(
            model=clean_model,
            messages=messages,
            on_thinking=on_thinking,
            on_content=on_content,
            timeout=timeout,
            max_output_tokens=max_output_tokens,
            tools=tools,
        )


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
    max_output_tokens: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Non-streaming query wrapper.

    Delegates to stream_model without callbacks for complete response.

    Args:
        model: Model identifier (may include nim: or openrouter: prefix)
        messages: List of message dicts
        timeout: Request timeout
        max_output_tokens: Optional max output tokens

    Returns:
        Response dict with content, error, status_code, model, ttft_ms, etc.
    """
    return await stream_model(
        model=model,
        messages=messages,
        timeout=timeout,
        max_output_tokens=max_output_tokens,
    )
