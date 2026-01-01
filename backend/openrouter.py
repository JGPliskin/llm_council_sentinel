"""OpenRouter API client for making LLM requests."""

import httpx
import json
import inspect
from typing import List, Dict, Any, Optional, Callable
from config import OPENROUTER_API_KEY, OPENROUTER_API_URL


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
    Query a model with streaming enabled, handling thinking tool calls.
    
    核心循环（参考 streaming_thinking_backend.py）：
    1. 发送请求，流式接收响应
    2. 如果收到 tool_calls（emit_thinking），先 yield thinking 事件
    3. 然后回传 tool result，继续循环
    4. 直到获得最终 content（finish_reason == "stop"）

    Args:
        model: OpenRouter model identifier
        messages: List of message dicts
        on_thinking: Callback for thinking payload (arg: dict)
        on_content: Callback for streamed content delta (arg: delta string)
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

    # 复制消息列表，用于多轮对话
    conversation_messages = list(messages)
    
    # Buffer for final content reconstruction
    full_content = []
    
    # State tracking
    response_model = model
    max_rounds = 10  # 防止无限循环

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
                if max_output_tokens is not None:
                    payload["max_output_tokens"] = max_output_tokens
                if tools:
                    payload["tools"] = tools

                # 本轮的缓冲区
                content_buffer = []
                tool_call_buffer = {}  # index -> {id, name, arguments, emitted}
                finish_reason = None
                
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
                        
                        choice = chunk.get("choices", [{}])[0]
                        delta = choice.get("delta", {})
                        
                        # 检查 finish_reason
                        if choice.get("finish_reason"):
                            finish_reason = choice["finish_reason"]
                        
                        # 1. Handle Content（流式输出最终答案）
                        if "content" in delta and delta["content"]:
                            content_buffer.append(delta["content"])
                            full_content.append(delta["content"])
                            if on_content:
                                if inspect.iscoroutinefunction(on_content):
                                    await on_content(delta["content"])
                                else:
                                    on_content(delta["content"])
                            
                        # 2. Handle Tool Calls (Thinking)
                        if "tool_calls" in delta and delta["tool_calls"]:
                            for tc in delta["tool_calls"]:
                                idx = tc.get("index", 0)
                                
                                if idx not in tool_call_buffer:
                                    tool_call_buffer[idx] = {
                                        "id": tc.get("id", f"call_{idx}"),
                                        "name": "",
                                        "arguments": "",
                                        "emitted": False
                                    }
                                
                                if "id" in tc and tc["id"]:
                                    tool_call_buffer[idx]["id"] = tc["id"]
                                
                                if "function" in tc:
                                    fn = tc["function"]
                                    if "name" in fn:
                                        tool_call_buffer[idx]["name"] = fn["name"]
                                    if "arguments" in fn:
                                        tool_call_buffer[idx]["arguments"] += fn["arguments"]
                                
                                # 尝试实时解析 emit_thinking 并触发回调
                                if tool_call_buffer[idx]["name"] == "emit_thinking":
                                    args_str = tool_call_buffer[idx]["arguments"]
                                    if args_str.strip():
                                        try:
                                            args_json = json.loads(args_str)
                                            # 检查是否已经触发过回调
                                            if not tool_call_buffer[idx]["emitted"] and "title" in args_json:
                                                tool_call_buffer[idx]["emitted"] = True
                                                if on_thinking:
                                                    if inspect.iscoroutinefunction(on_thinking):
                                                        await on_thinking(args_json)
                                                    else:
                                                        on_thinking(args_json)
                                        except json.JSONDecodeError:
                                            # JSON 还不完整，继续等待
                                            pass
                
                # 本轮流结束，检查结果
                # 情况1：正常结束（stop）或有 content 且无 pending tool calls
                if finish_reason == "stop" or (full_content and finish_reason != "tool_calls"):
                    # 正常结束，有最终答案
                    return {
                        'content': "".join(full_content),
                        'reasoning_details': None, 
                        'model': response_model,
                        'tool_calls': [
                            {**v, "arguments": v["arguments"]} for k,v in tool_call_buffer.items()
                        ]
                    }
                
                # 情况2：收到 tool_calls，需要回传 tool result 并继续
                if finish_reason == "tool_calls" and tool_call_buffer:
                    # 构建 assistant 消息（包含 tool_calls）
                    assistant_msg = {
                        "role": "assistant",
                        "content": "".join(content_buffer) if content_buffer else None,
                        "tool_calls": []
                    }
                    
                    for idx, tc_data in sorted(tool_call_buffer.items()):
                        assistant_msg["tool_calls"].append({
                            "id": tc_data["id"],
                            "type": "function",
                            "function": {
                                "name": tc_data["name"],
                                "arguments": tc_data["arguments"]
                            }
                        })
                    
                    conversation_messages.append(assistant_msg)
                    
                    # 为每个 tool call 生成 tool result
                    for idx, tc_data in sorted(tool_call_buffer.items()):
                        if tc_data["name"] == "emit_thinking":
                            # 虚拟工具：不执行任何操作，直接返回成功
                            tool_result = {
                                "role": "tool",
                                "tool_call_id": tc_data["id"],
                                "content": json.dumps({"ok": True})
                            }
                            conversation_messages.append(tool_result)
                        else:
                            # 其他工具（如果有的话）
                            tool_result = {
                                "role": "tool", 
                                "tool_call_id": tc_data["id"],
                                "content": json.dumps({"error": "Unknown tool"})
                            }
                            conversation_messages.append(tool_result)
                    
                    # 继续下一轮
                    continue
                
                # 情况3：流结束但没有明确的 finish_reason，检查是否有内容
                if full_content:
                    return {
                        'content': "".join(full_content),
                        'reasoning_details': None,
                        'model': response_model,
                        'finish_reason': finish_reason,
                        'tool_calls': [
                            {**v, "arguments": v["arguments"]} for k,v in tool_call_buffer.items()
                        ]
                    }
                
                # 情况4：其他情况（如 length 超限），直接结束
                return {
                    'content': "".join(full_content),
                    'reasoning_details': None,
                    'model': response_model,
                    'finish_reason': finish_reason,
                    'tool_calls': [
                        {**v, "arguments": v["arguments"]} for k,v in tool_call_buffer.items()
                    ]
                }

            
            # 超过最大轮数
            return {
                'content': "".join(full_content),
                'reasoning_details': None,
                'model': response_model,
                'error': True,
                'error_message': 'Max rounds exceeded'
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
