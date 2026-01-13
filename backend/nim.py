"""NIM API client for making LLM requests."""

import asyncio
import json
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable

import httpx

from config import NIM_API_BASE, NIM_API_KEYS, NIM_RPM_PER_KEY

NIM_API_URL = f"{NIM_API_BASE}/chat/completions"
DEFAULT_TIMEOUT = 120.0
KEY_COOLDOWN_SECONDS = 10


class ProviderRateLimitError(Exception):
    """Raised when no NIM API key is available."""


@dataclass
class _KeyState:
    key: str
    tokens: float
    last_refill: float
    cooldown_until: float = 0.0


class NIMKeyManager:
    """Manage multi-key rotation and per-key token bucket."""

    def __init__(self, keys: List[str], rpm_per_key: int, cooldown_seconds: int = KEY_COOLDOWN_SECONDS):
        self._capacity = max(1, int(rpm_per_key))
        self._refill_rate = self._capacity / 60.0
        now = time.monotonic()
        self._keys = [
            _KeyState(key=k, tokens=float(self._capacity), last_refill=now) for k in keys
        ]
        self._cooldown_seconds = cooldown_seconds
        self._lock = asyncio.Lock()

    def _refill(self, state: _KeyState, now: float) -> None:
        elapsed = now - state.last_refill
        if elapsed <= 0:
            return
        state.tokens = min(self._capacity, state.tokens + elapsed * self._refill_rate)
        state.last_refill = now

    async def acquire_key(self) -> str:
        if not self._keys:
            raise ProviderRateLimitError("no_keys")
        async with self._lock:
            now = time.monotonic()
            for state in self._keys:
                self._refill(state, now)
            candidates = [
                state
                for state in self._keys
                if state.cooldown_until <= now and state.tokens >= 1.0
            ]
            if not candidates:
                raise ProviderRateLimitError("keys_exhausted")
            selected = max(candidates, key=lambda s: s.tokens)
            selected.tokens -= 1.0
            return selected.key

    async def mark_cooldown(self, key: str) -> None:
        async with self._lock:
            now = time.monotonic()
            for state in self._keys:
                if state.key == key:
                    state.cooldown_until = max(state.cooldown_until, now + self._cooldown_seconds)
                    break

    def has_keys(self) -> bool:
        return bool(self._keys)


_key_manager = NIMKeyManager(NIM_API_KEYS, NIM_RPM_PER_KEY)


def _parse_error_body_bytes(raw: bytes) -> Dict[str, Any]:
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        try:
            return {"raw_text": raw.decode("utf-8", errors="replace")}
        except Exception:
            return {"raw_text": str(raw)}


def _build_error_response(
    model: str,
    message: str,
    status_code: Optional[int] = None,
    error_code: Optional[str] = None,
    headers: Optional[Dict[str, Any]] = None,
    error_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "error": True,
        "content": message,
        "status_code": status_code,
        "headers": headers or {},
        "error_payload": error_payload,
        "model": model,
        "provider": "nim",
        "error_code": error_code,
    }


async def _request_once(
    client: httpx.AsyncClient,
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    stream: bool,
    timeout: float,
    max_output_tokens: Optional[int],
    on_thinking: Optional[Callable[[Dict[str, Any]], Any]],
    on_content: Optional[Callable[[str], Any]],
) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }
    if max_output_tokens is not None:
        payload["max_tokens"] = max_output_tokens

    if not stream:
        start_time = time.time()
        try:
            response = await client.post(
                NIM_API_URL, headers=headers, json=payload, timeout=timeout
            )
        except Exception as exc:
            return _build_error_response(model, str(exc))

        if response.status_code != 200:
            error_payload = _parse_error_body_bytes(response.content)
            return _build_error_response(
                model,
                f"HTTP {response.status_code}: {response.text[:500]}",
                status_code=response.status_code,
                headers=dict(response.headers),
                error_payload=error_payload,
            )

        data = response.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "")
        reasoning = message.get("reasoning_content", "")
        ttft_ms = int((time.time() - start_time) * 1000)

        return {
            "content": content,
            "thinking_content": reasoning,
            "model": data.get("model", model),
            "ttft_ms": ttft_ms,
            "error": False,
            "provider": "nim",
        }

    request_start = time.time()
    ttft_ms = None
    ttft_recorded = False
    response_model = model
    content_buffer: List[str] = []
    reasoning_buffer: List[str] = []
    bullet_id = f"nim_reasoning_{int(request_start * 1000)}"

    async with client.stream(
        "POST", NIM_API_URL, headers=headers, json=payload, timeout=timeout
    ) as response:
        if response.status_code != 200:
            raw = await response.aread()
            error_payload = _parse_error_body_bytes(raw)
            return _build_error_response(
                model,
                f"HTTP {response.status_code}: {response.text[:500]}",
                status_code=response.status_code,
                headers=dict(response.headers),
                error_payload=error_payload,
            )

        async for line in response.aiter_lines():
            if not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            if "model" in chunk:
                response_model = chunk["model"]

            choice = chunk.get("choices", [{}])[0]
            delta = choice.get("delta", {})

            reasoning_delta = delta.get("reasoning_content")
            if reasoning_delta:
                if not ttft_recorded:
                    ttft_ms = int((time.time() - request_start) * 1000)
                    ttft_recorded = True
                reasoning_buffer.append(reasoning_delta)
                if on_thinking:
                    payload = {
                        "bullet_id": bullet_id,
                        "title": "Reasoning",
                        "detail": "".join(reasoning_buffer),
                        "op": "update",
                    }
                    if asyncio.iscoroutinefunction(on_thinking):
                        await on_thinking(payload)
                    else:
                        on_thinking(payload)

            content_delta = delta.get("content")
            if content_delta:
                if not ttft_recorded:
                    ttft_ms = int((time.time() - request_start) * 1000)
                    ttft_recorded = True
                content_buffer.append(content_delta)
                if on_content:
                    if asyncio.iscoroutinefunction(on_content):
                        await on_content(content_delta)
                    else:
                        on_content(content_delta)

    return {
        "content": "".join(content_buffer),
        "thinking_content": "".join(reasoning_buffer),
        "model": response_model,
        "ttft_ms": ttft_ms,
        "error": False,
        "provider": "nim",
    }


async def stream_model(
    model: str,
    messages: List[Dict[str, str]],
    on_thinking: Optional[Callable[[Dict[str, Any]], Any]] = None,
    on_content: Optional[Callable[[str], Any]] = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_output_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    if tools:
        # NIM does not support tool calling in this integration path.
        tools = None

    if not _key_manager.has_keys():
        return _build_error_response(
            model,
            "NIM API keys not configured",
            status_code=429,
            error_code="provider_rate_limited",
        )

    async with httpx.AsyncClient(timeout=timeout) as client:
        attempts = max(1, len(NIM_API_KEYS))
        for _ in range(attempts):
            try:
                api_key = await _key_manager.acquire_key()
            except ProviderRateLimitError:
                return _build_error_response(
                    model,
                    "NIM API keys exhausted",
                    status_code=429,
                    error_code="provider_rate_limited",
                )

            result = await _request_once(
                client=client,
                api_key=api_key,
                model=model,
                messages=messages,
                stream=True,
                timeout=timeout,
                max_output_tokens=max_output_tokens,
                on_thinking=on_thinking,
                on_content=on_content,
            )

            status_code = result.get("status_code")
            if status_code in (401, 403, 429):
                await _key_manager.mark_cooldown(api_key)
                # Try another key if available.
                if status_code == 429:
                    continue

            return result

        return _build_error_response(
            model,
            "NIM API keys exhausted",
            status_code=429,
            error_code="provider_rate_limited",
        )


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = DEFAULT_TIMEOUT,
    max_output_tokens: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    if not _key_manager.has_keys():
        return _build_error_response(
            model,
            "NIM API keys not configured",
            status_code=429,
            error_code="provider_rate_limited",
        )

    async with httpx.AsyncClient(timeout=timeout) as client:
        attempts = max(1, len(NIM_API_KEYS))
        for _ in range(attempts):
            try:
                api_key = await _key_manager.acquire_key()
            except ProviderRateLimitError:
                return _build_error_response(
                    model,
                    "NIM API keys exhausted",
                    status_code=429,
                    error_code="provider_rate_limited",
                )

            result = await _request_once(
                client=client,
                api_key=api_key,
                model=model,
                messages=messages,
                stream=False,
                timeout=timeout,
                max_output_tokens=max_output_tokens,
                on_thinking=None,
                on_content=None,
            )

            status_code = result.get("status_code")
            if status_code in (401, 403, 429):
                await _key_manager.mark_cooldown(api_key)
                if status_code == 429:
                    continue

            return result

        return _build_error_response(
            model,
            "NIM API keys exhausted",
            status_code=429,
            error_code="provider_rate_limited",
        )

