"""OpenRouter API client for making LLM requests."""

import httpx
import json
from typing import List, Dict, Any, Optional, Callable
from backend.config import OPENROUTER_API_KEY, OPENROUTER_API_URL

async def stream_model(
    model: str,
    messages: List[Dict[str, str]],
    on_thinking: Optional[Callable[[str], Any]] = None,
    timeout: float = 120.0,
    max_output_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Query a model with streaming enabled, handling thinking tool calls.

    Args:
        model: OpenRouter model identifier
        messages: List of message dicts
        on_thinking: Callback for thinking titles (arg: title_string)
        timeout: Request timeout
        max_output_tokens: Optional max output tokens
        tools: Optional list of tool definitions

    Returns:
        Constructed response dict compatible with query_model, or None if failed.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Starttoaster/llm-council-sentinel",
        "X-Title": "LLM Council Sentinel",
    }

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    if max_output_tokens is not None:
        payload["max_output_tokens"] = max_output_tokens
    if tools:
        payload["tools"] = tools

    # Buffer for final content reconstruction
    full_content = []
    # Buffer for tool calls: index -> {name, arguments, id}
    tool_call_buffer = {}
    
    # State tracking
    response_model = model

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", OPENROUTER_API_URL, headers=headers, json=payload) as response:
                response.raise_for_status()
                
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
                        
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    
                    # 1. Handle Content
                    if "content" in delta and delta["content"]:
                        full_content.append(delta["content"])
                        
                    # 2. Handle Tool Calls (Thinking)
                    if "tool_calls" in delta and delta["tool_calls"]:
                        for tc in delta["tool_calls"]:
                            idx = tc.get("index")
                            if idx not in tool_call_buffer:
                                tool_call_buffer[idx] = {"name": "", "arguments": "", "id": tc.get("id")}
                            
                            if "function" in tc:
                                fn = tc["function"]
                                if "name" in fn:
                                    tool_call_buffer[idx]["name"] = fn["name"]
                                if "arguments" in fn:
                                    tool_call_buffer[idx]["arguments"] += fn["arguments"]

                            # Robust Parsing of nested JSON in arguments
                            # Arguments build up over time: "{" -> "{"title":..."
                            # We only try to parse if we have a closing brace or seemingly complete JSON structure
                            # Actually, standard is to wait for finish, but we want streaming titles.
                            # So we try to parse what we have.
                            args_str = tool_call_buffer[idx]["arguments"]
                            if args_str.strip():
                                try:
                                    # Attempt partial repair if needed? 
                                    # For specific thinking pattern `{"title": "..."}`
                                    # If it ends with quote, maybe it's complete string value?
                                    # Simple attempt:
                                    args_json = None
                                    try:
                                        args_json = json.loads(args_str)
                                    except json.JSONDecodeError:
                                        # If failed, maybe it's because it's incomplete. 
                                        # We ignore incomplete JSON until next chunk.
                                        pass
                                    
                                    if args_json and "title" in args_json and on_thinking:
                                        if not tool_call_buffer[idx].get("emitted"):
                                            # Found a title, emit it!
                                            import inspect
                                            if inspect.iscoroutinefunction(on_thinking):
                                                await on_thinking(args_json["title"])
                                            else:
                                                on_thinking(args_json["title"])
                                            tool_call_buffer[idx]["emitted"] = True
                                except Exception:
                                    pass

        return {
            'content': "".join(full_content),
            'reasoning_details': None, 
            'model': response_model,
            'tool_calls': [
                {**v, "arguments": v["arguments"]} for k,v in tool_call_buffer.items()
            ]
        }

    except Exception as e:
        print(f"Error streaming model {model}: {e}")
        return {
            'content': f"Error: {str(e)}",
            'error': True,
            'model': model
        }

async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
    max_output_tokens: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Non-streaming query wrapper.
    """
    return await stream_model(
        model=model,
        messages=messages,
        timeout=timeout,
        max_output_tokens=max_output_tokens
    )

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
