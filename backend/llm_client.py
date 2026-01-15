"""Provider routing layer for LLM requests."""

import asyncio
from typing import List, Dict, Any, Optional, Callable, Tuple

from config import GLOBAL_MODEL_MAP
import openrouter
import nim


def _strip_nim_prefix(model_id: str) -> str:
    if model_id.startswith("nim:"):
        return model_id[len("nim:") :]
    return model_id


def _resolve_provider(model_id: str) -> Tuple[str, str]:
    normalized_id = _strip_nim_prefix(model_id)
    cfg = GLOBAL_MODEL_MAP.get(normalized_id) or GLOBAL_MODEL_MAP.get(model_id)
    provider = cfg.get("provider") if cfg else None

    if provider:
        if provider == "nim":
            return provider, normalized_id
        if model_id.startswith("nim:"):
            return provider, normalized_id
        return provider, model_id

    if model_id.startswith("nim:"):
        return "nim", normalized_id

    return "openrouter", model_id


async def stream_model(
    model: str,
    messages: List[Dict[str, str]],
    on_thinking: Optional[Callable[[Dict[str, Any]], Any]] = None,
    on_content: Optional[Callable[[str], Any]] = None,
    timeout: float = 120.0,
    max_output_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    provider, resolved_model = _resolve_provider(model)
    if provider == "nim":
        # Adapter to convert NIM raw stream to Application Thinking Events
        async def _nim_adapter(payload: Dict[str, Any]):
            if not on_thinking:
                return

            if isinstance(payload, dict) and payload.get("type") == "reasoning_delta":
                event = {
                    "title": "Thinking Process",
                    "detail": payload.get("delta", ""),
                    "op": "append",
                }
            elif isinstance(payload, dict):
                event = payload
            else:
                event = {"title": str(payload)}

            if asyncio.iscoroutinefunction(on_thinking):
                await on_thinking(event)
            else:
                on_thinking(event)

        response = await nim.stream_model(
            model=resolved_model,
            messages=messages,
            on_thinking=_nim_adapter if on_thinking else None,
            on_content=on_content,
            timeout=timeout,
            max_output_tokens=max_output_tokens,
            tools=tools,
        )
    else:
        response = await openrouter.stream_model(
            model=resolved_model,
            messages=messages,
            on_thinking=on_thinking,
            on_content=on_content,
            timeout=timeout,
            max_output_tokens=max_output_tokens,
            tools=tools,
        )

    if response is None:
        return None
    response.setdefault("provider", provider)
    return response


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
    max_output_tokens: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    provider, resolved_model = _resolve_provider(model)
    if provider == "nim":
        response = await nim.query_model(
            model=resolved_model,
            messages=messages,
            timeout=timeout,
            max_output_tokens=max_output_tokens,
        )
    else:
        response = await openrouter.query_model(
            model=resolved_model,
            messages=messages,
            timeout=timeout,
            max_output_tokens=max_output_tokens,
        )

    if response is None:
        return None
    response.setdefault("provider", provider)
    return response
