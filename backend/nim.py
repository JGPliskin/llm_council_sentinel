"""NVIDIA NIM API client with key management and rate limiting."""

import httpx
import json
import time
import asyncio
import logging
import re
import inspect
from typing import List, Dict, Any, Optional, Callable
from config import NIM_API_KEYS, NIM_RPM_PER_KEY, NIM_API_BASE

logger = logging.getLogger("nim")


class NIMKeyManager:
    """
    Manages NIM API keys with token bucket rate limiting.

    Uses token bucket algorithm per key for RPM (requests per minute) control.
    Keys in cooldown are skipped during selection.
    """

    def __init__(self):
        """
        Initialize key manager with token buckets.

        Parses NIM_API_KEYS comma-separated string and initializes
        token buckets for each key.
        """
        # Parse comma-separated keys
        self.api_keys = [k.strip() for k in NIM_API_KEYS.split(",") if k.strip()]
        self.rpm_per_key = NIM_RPM_PER_KEY

        # Initialize token buckets for each key
        # Each bucket: {capacity, tokens, refill_rate, last_refill, cooldown_until}
        self.key_buckets = {}
        for key in self.api_keys:
            capacity = self.rpm_per_key
            refill_rate = capacity / 60.0  # tokens per second
            self.key_buckets[key] = {
                "capacity": capacity,
                "tokens": capacity,
                "refill_rate": refill_rate,
                "last_refill": time.time(),
                "cooldown_until": None,
            }

        self._lock = asyncio.Lock()

    def _refill_bucket(self, bucket: Dict[str, Any]) -> None:
        """
        Refill tokens based on elapsed time.

        Args:
            bucket: Token bucket dict with capacity, tokens, refill_rate, last_refill
        """
        now = time.time()
        elapsed = now - bucket["last_refill"]
        new_tokens = elapsed * bucket["refill_rate"]
        bucket["tokens"] = min(bucket["capacity"], bucket["tokens"] + new_tokens)
        bucket["last_refill"] = now

    async def acquire_key(self) -> Optional[str]:
        """
        Acquire a key with available tokens (load-balanced by most tokens).

        Selects the key with the most available tokens from non-cooled keys.
        Skips keys in cooldown and keys with no tokens.

        Returns:
            API key string if available, None if all keys exhausted.
        """
        async with self._lock:
            now = time.time()
            best_key = None
            max_tokens = -1

            for key, bucket in self.key_buckets.items():
                # Skip keys in cooldown
                if bucket["cooldown_until"] and now < bucket["cooldown_until"]:
                    continue

                # Refill bucket
                self._refill_bucket(bucket)

                # Debug: log token state
                logger.debug(
                    f"Key {key[:8]}...: tokens={bucket['tokens']}, cooldown={bucket['cooldown_until']}"
                )

                # Select key with most available tokens (load balancing)
                if bucket["tokens"] > 0 and bucket["tokens"] > max_tokens:
                    max_tokens = bucket["tokens"]
                    best_key = key

            if best_key:
                # Consume one token
                self.key_buckets[best_key]["tokens"] -= 1
                logger.debug(
                    f"Acquired key {best_key[:8]}..., tokens left: {self.key_buckets[best_key]['tokens']}"
                )
                return best_key

            # No keys available - provide detailed diagnostics
            now = time.time()
            diagnostics = []
            for key, bucket in self.key_buckets.items():
                key_short = key[:8] + "..."
                if bucket["cooldown_until"] and now < bucket["cooldown_until"]:
                    remaining = int(bucket["cooldown_until"] - now)
                    diagnostics.append(f"{key_short}: cooldown ({remaining}s remaining)")
                else:
                    diagnostics.append(f"{key_short}: tokens={bucket['tokens']:.1f}")
            
            logger.warning(
                f"No NIM keys available! Diagnostics: {'; '.join(diagnostics)}"
            )
            return None

    async def release_key(self, key: str, success: bool = True) -> None:
        """
        Release key after request completion.

        On success: token is consumed (no action needed - token was already deducted on acquire)
        On failure: marks key as temporarily cooled (1 minute) and optionally returns token.

        Note: Token consumption happens at acquire_key() time, not release.
        Refill happens automatically based on elapsed time.

        Args:
            key: API key string
            success: True if request succeeded, False otherwise
        """
        async with self._lock:
            if key not in self.key_buckets:
                return

            if not success:
                # Mark key as temporarily cooled on failure
                bucket = self.key_buckets[key]
                bucket["cooldown_until"] = time.time() + 60  # 1 min cooldown
                logger.warning(f"Key {key[:8]}... set to cooldown due to failure (60s)")

    async def mark_key_failed(
        self, key: str, status_code: Optional[int] = None
    ) -> None:
        """
        Mark key as failed with appropriate cooldown.

        Different status codes trigger different cooldown durations:
        - 429 (rate limit): 2 minute cooldown
        - 401 (auth error): 5 minute cooldown
        - Other: 1 minute cooldown

        Args:
            key: API key string
            status_code: HTTP status code if available
        """
        async with self._lock:
            if key not in self.key_buckets:
                return

            bucket = self.key_buckets[key]
            cooldown_time = 60  # Default 1 min

            if status_code == 429:
                # Rate limit: longer cooldown
                cooldown_time = 120
            elif status_code == 401:
                # Auth error: long cooldown
                cooldown_time = 300

            bucket["cooldown_until"] = time.time() + cooldown_time
            logger.warning(f"Key {key[:8]}... marked failed with status_code={status_code}, cooldown={cooldown_time}s")


# Global key manager instance
_nim_key_manager = None


def get_nim_key_manager() -> NIMKeyManager:
    """
    Get or create global NIM key manager instance.

    Returns:
        NIMKeyManager singleton instance
    """
    global _nim_key_manager
    if _nim_key_manager is None:
        _nim_key_manager = NIMKeyManager()
    return _nim_key_manager


def _parse_error_body(response: httpx.Response) -> Dict[str, Any]:
    """
    Parse HTTP error response body, try to extract JSON format error info.

    Returns:
        Parsed JSON dict, or dict with raw text if parsing fails.
    """
    try:
        return response.json()
    except (json.JSONDecodeError, ValueError):
        return {"raw_text": response.text}

def _looks_like_emit_thinking(args_str: str) -> bool:
    """Check if arguments string looks like it belongs to emit_thinking."""
    if not args_str:
        return False
    return "title" in args_str or "bullet_id" in args_str


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
    NIM API streaming call with tool calling support.

    Implements:
    - NIMKeyManager for key rotation and rate limiting
    - Token bucket rate limiting per key
    - Tool calls (emit_thinking) parsing and callback
    - Stage2 target_anon_id validation (drop if missing)
    - TTFT tracking
    - provider_rate_limited error when all keys exhausted

    Args:
        model: NIM model identifier (without nim: prefix)
        messages: List of message dicts
        on_thinking: Callback for thinking payload (arg: dict)
        on_content: Callback for streamed content delta (arg: delta string)
        timeout: Request timeout
        max_output_tokens: Optional max output tokens
        tools: Optional list of tool definitions (must include emit_thinking)

    Returns:
        Response dict matching openrouter.py format:
        {
            "content": "...",
            "error": False/True,
            "error_code": None or "provider_rate_limited",
            "model": "...",
            "ttft_ms": 1234,
            "provider": "nim",
        }
    """
    # Get key from NIMKeyManager
    key_manager = get_nim_key_manager()
    api_key = await key_manager.acquire_key()

    if not api_key:
        # No keys available - return provider_rate_limited error
        return {
            "error": True,
            "error_code": "provider_rate_limited",
            "content": "All NIM API keys exhausted (rate limit)",
            "model": model,
            "provider": "nim",
            "status_code": 429,
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Copy messages for multi-round conversation
    conversation_messages = list(messages)

    # Buffer for final content reconstruction
    full_content = []

    # State tracking
    response_model = model
    max_rounds = 10

    # TTFT (Time-to-First-Token) recording
    request_start_time = time.time()
    ttft_recorded = False
    ttft_ms = None

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            round_count = 0

            while round_count < max_rounds:
                round_count += 1

                payload: Dict[str, Any] = {
                    "model": model,
                    "messages": conversation_messages,
                    "stream": True,
                }

                if "deepseek" in model:
                     # Match settings from working test script
                     payload["temperature"] = payload.get("temperature", 0.6)
                     payload["top_p"] = payload.get("top_p", 0.7)
                     if max_output_tokens is None:
                         payload["max_tokens"] = 4096

                if max_output_tokens is not None:
                    payload["max_tokens"] = max_output_tokens
                if tools:
                    payload["tools"] = tools
                    payload["tool_choice"] = "auto"  # NIM only uses tool calling

                # Round-specific buffers
                content_buffer = []
                tool_call_buffer = {}  # index -> {id, name, arguments, emitted}
                finish_reason = None

                try:
                    async with client.stream(
                        "POST",
                        f"{NIM_API_BASE}/chat/completions",
                        headers=headers,
                        json=payload,
                    ) as response:
                        # Check for HTTP errors before reading stream
                        if response.status_code >= 400:
                            # Must read body before accessing content in streaming context
                            await response.aread()
                            error_payload = _parse_error_body(response)
                            status_code = response.status_code
                            
                            # Log detailed error info
                            error_msg = error_payload.get('error', {}).get('message') or error_payload.get('detail') or str(error_payload)
                            logger.error(f"NIM HTTP {status_code} for model={model}: {error_msg}")
                            # Debug: Log full payload on 400 errors to diagnose unexpected end of data
                            if status_code == 400:
                                try:
                                    logger.error(f"Failed Payload (trunc 2000 chars): {json.dumps(payload)[:2000]}")
                                except Exception:
                                    pass
                            
                            # Handle rate limit (429) - mark key as failed
                            if status_code == 429:
                                await key_manager.mark_key_failed(api_key, status_code=429)
                            elif status_code in [401, 403]:
                                await key_manager.mark_key_failed(api_key, status_code=status_code)
                            
                            return {
                                "error": True,
                                "status_code": status_code,
                                "headers": dict(response.headers),
                                "error_payload": error_payload,
                                "content": f"HTTP {status_code}: {error_msg}",
                                "model": model,
                                "provider": "nim",
                            }

                        async for line in response.aiter_lines():
                            if not line.startswith("data: "):
                                continue

                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break

                            try:
                                chunk = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue

                            if "model" in chunk:
                                response_model = chunk["model"]

                            choices = chunk.get("choices", [])
                            if not choices:
                                continue  # Skip chunks with empty choices
                            choice = choices[0]
                            delta = choice.get("delta", {})

                            # Check finish_reason
                            if choice.get("finish_reason"):
                                finish_reason = choice["finish_reason"]

                            # 1. Handle Content (final answer streaming)
                            if "content" in delta and delta["content"]:
                                # Record TTFT
                                if not ttft_recorded:
                                    ttft_ms = int(
                                        (time.time() - request_start_time) * 1000
                                    )
                                    ttft_recorded = True

                                content_buffer.append(delta["content"])
                                full_content.append(delta["content"])
                                if on_content:
                                    if inspect.iscoroutinefunction(on_content):
                                        await on_content(delta["content"])
                                    else:
                                        on_content(delta["content"])

                            # 2. Handle Tool Calls (emit_thinking)
                            if "tool_calls" in delta and delta["tool_calls"]:
                                # Record TTFT (might arrive first)
                                if not ttft_recorded:
                                    ttft_ms = int(
                                        (time.time() - request_start_time) * 1000
                                    )
                                    ttft_recorded = True

                                for tc in delta["tool_calls"]:
                                    idx = tc.get("index", 0)

                                    if idx not in tool_call_buffer:
                                        tool_call_buffer[idx] = {
                                            "id": tc.get("id", f"call_{idx}"),
                                            "name": "",
                                            "arguments": "",
                                            "emitted": False,
                                        }

                                    if "id" in tc and tc["id"]:
                                        tool_call_buffer[idx]["id"] = tc["id"]

                                    if "function" in tc:
                                        fn = tc["function"]
                                        if "name" in fn:
                                            tool_call_buffer[idx]["name"] = fn["name"]
                                        if "arguments" in fn:
                                            tool_call_buffer[idx]["arguments"] += fn[
                                                "arguments"
                                            ]

                                    # Try to parse emit_thinking and trigger callback
                                    # FIX: Check if name is emit_thinking OR matches heuristic (for DeepSeek)
                                    current_name = tool_call_buffer[idx]["name"]
                                    args_str = tool_call_buffer[idx]["arguments"]
                                    
                                    is_thinking = (current_name == "emit_thinking") or \
                                                  (not current_name and _looks_like_emit_thinking(args_str))

                                    if is_thinking:
                                        if args_str.strip():
                                            try:
                                                args_json = json.loads(args_str)

                                                # Stage2: Check target_anon_id requirement
                                                # If missing, try regex extraction from title/detail
                                                target_anon_id = args_json.get(
                                                    "target_anon_id"
                                                )
                                                if not target_anon_id:
                                                    # Light regex fallback: look for anon_\d+ pattern
                                                    title = args_json.get("title", "")
                                                    detail = args_json.get("detail", "")
                                                    combined = f"{title} {detail}"
                                                    match = re.search(
                                                        r"anon_\d+", combined
                                                    )
                                                    if match:
                                                        target_anon_id = match.group(0)

                                                # Only emit if we have valid thinking with title
                                                # Frontend will filter Stage2 thinking without target_anon_id
                                                if "title" in args_json:
                                                    if not tool_call_buffer[idx][
                                                        "emitted"
                                                    ]:
                                                        tool_call_buffer[idx][
                                                            "emitted"
                                                        ] = True
                                                        if on_thinking:
                                                            if inspect.iscoroutinefunction(
                                                                on_thinking
                                                            ):
                                                                await on_thinking(
                                                                    args_json
                                                                )
                                                            else:
                                                                on_thinking(args_json)
                                            except json.JSONDecodeError:
                                                pass  # JSON incomplete, wait for more

                except httpx.HTTPStatusError as e:
                    error_payload = _parse_error_body(e.response)
                    status_code = e.response.status_code

                    # Handle rate limit (429) - mark key as failed
                    if status_code == 429:
                        await key_manager.mark_key_failed(api_key, status_code=429)
                    elif status_code in [401, 403]:
                        await key_manager.mark_key_failed(
                            api_key, status_code=status_code
                        )

                    # Return error response
                    return {
                        "error": True,
                        "status_code": status_code,
                        "headers": dict(e.response.headers),
                        "error_payload": error_payload,
                        "content": f"HTTP {status_code}: {error_payload.get('error', {}).get('message', str(e))}",
                        "model": model,
                        "provider": "nim",
                    }

                # Round complete: check result

                # Case 1: Normal end (stop) or content without pending tool calls
                if finish_reason == "stop" or (
                    full_content and finish_reason != "tool_calls"
                ):
                    # Release key (success)
                    await key_manager.release_key(api_key, success=True)
                    return {
                        "content": "".join(full_content),
                        "reasoning_details": None,
                        "model": response_model,
                        "provider": "nim",
                        "ttft_ms": ttft_ms,
                        "error": False,
                        "tool_calls": [
                            {**v, "arguments": v["arguments"]}
                            for k, v in tool_call_buffer.items()
                        ],
                    }

                # Case 2: Tool calls received, need to send tool result and continue
                if finish_reason == "tool_calls" and tool_call_buffer:
                    # Build assistant message (including tool_calls)
                    assistant_msg = {
                        "role": "assistant",
                        "content": "".join(content_buffer) if content_buffer else None,
                        "tool_calls": [],
                    }

                    for idx, tc_data in sorted(tool_call_buffer.items()):
                        # FIX: Ensure name is not None or empty
                        tool_name = tc_data["name"]
                        if not tool_name:
                            # Heuristic: if we parsed emit_thinking arguments successfully, use that name
                            # Or default to emit_thinking if it looks like one
                            if _looks_like_emit_thinking(tc_data["arguments"]):
                                tool_name = "emit_thinking"
                            else:
                                tool_name = "emit_thinking" # Default fallback to avoid 500 error
                            # Persist fallback name so the tool result loop uses it correctly
                            tc_data["name"] = tool_name

                        assistant_msg["tool_calls"].append(
                            {
                                "id": tc_data["id"],
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": tc_data["arguments"],
                                },
                            }
                        )

                    conversation_messages.append(assistant_msg)

                    # Send tool results for each tool call
                    for idx, tc_data in sorted(tool_call_buffer.items()):
                        if tc_data["name"] == "emit_thinking":
                            # Virtual tool: no execution, just return success
                            tool_result = {
                                "role": "tool",
                                "tool_call_id": tc_data["id"],
                                "content": json.dumps({"ok": True}),
                            }
                            conversation_messages.append(tool_result)
                        else:
                            # Other tools (if any)
                            tool_result = {
                                "role": "tool",
                                "tool_call_id": tc_data["id"],
                                "content": json.dumps({"error": "Unknown tool"}),
                            }
                            conversation_messages.append(tool_result)

                    # Continue to next round
                    continue

                # Case 3: Stream ended but no explicit finish_reason, check content
                if full_content:
                    await key_manager.release_key(api_key, success=True)
                    return {
                        "content": "".join(full_content),
                        "reasoning_details": None,
                        "model": response_model,
                        "provider": "nim",
                        "finish_reason": finish_reason,
                        "ttft_ms": ttft_ms,
                        "error": False,
                        "tool_calls": [
                            {**v, "arguments": v["arguments"]}
                            for k, v in tool_call_buffer.items()
                        ],
                    }

                # Case 4: Other cases (length exceeded, etc.)
                await key_manager.release_key(api_key, success=True)
                return {
                    "content": "".join(full_content),
                    "reasoning_details": None,
                    "model": response_model,
                    "provider": "nim",
                    "finish_reason": finish_reason,
                    "ttft_ms": ttft_ms,
                    "error": False,
                    "tool_calls": [
                        {**v, "arguments": v["arguments"]}
                        for k, v in tool_call_buffer.items()
                    ],
                }

            # Max rounds exceeded
            await key_manager.release_key(api_key, success=True)
            return {
                "content": "".join(full_content),
                "reasoning_details": None,
                "model": response_model,
                "error": True,
                "error_message": "Max rounds exceeded",
                "ttft_ms": ttft_ms,
                "provider": "nim",
            }

    except httpx.HTTPStatusError as e:
        # HTTP errors (4xx, 5xx)
        error_payload = _parse_error_body(e.response)
        await key_manager.mark_key_failed(api_key, status_code=e.response.status_code)

        return {
            "error": True,
            "status_code": e.response.status_code,
            "headers": dict(e.response.headers),
            "error_payload": error_payload,
            "content": str(e),
            "model": model,
            "provider": "nim",
        }

    except Exception as e:
        # Other errors (network timeout, connection failure, etc.)
        logger.error(f"NIM stream_model exception: {type(e).__name__}: {e}")
        if api_key:
            await key_manager.release_key(api_key, success=False)

        return {
            "error": True,
            "status_code": None,
            "content": str(e),
            "model": model,
            "provider": "nim",
        }


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
    max_output_tokens: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Non-streaming query wrapper.

    Delegates to stream_model for consistency.

    Args:
        model: NIM model identifier (without nim: prefix)
        messages: List of message dicts
        timeout: Request timeout
        max_output_tokens: Optional max output tokens

    Returns:
        Response dict matching openrouter.py format
    """
    return await stream_model(
        model=model,
        messages=messages,
        timeout=timeout,
        max_output_tokens=max_output_tokens,
    )
