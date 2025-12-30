"""
流式思考显示测试后端

核心思路（OpenAI 方案）：
1. 使用 `emit_thinking` 虚拟工具传输"提纲/展开说明"
2. 后端收到后不去外部执行，只把它当 UI 事件推给前端
3. 然后立刻回一个空的 tool result 让模型继续

这样可以实现：一边思考，一边返回思考过程
"""

import os
import sys
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

# 加载项目根目录的 .env 文件
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, ".env")
load_dotenv(env_path)

app = FastAPI(title="流式思考测试服务")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenRouter 配置
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b:free"  # 支持 thinking 的模型

# 虚拟工具定义
EMIT_THINKING_TOOL = {
    "type": "function",
    "function": {
        "name": "emit_thinking",
        "description": "输出当前思考步骤的标题和详细说明。每次调用外部工具前必须先调用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "bullet_id": {
                    "type": "string",
                    "description": "思考步骤的唯一标识符"
                },
                "title": {
                    "type": "string", 
                    "description": "思考步骤的标题（6-12个词）"
                },
                "detail": {
                    "type": "string",
                    "description": "思考步骤的详细说明（1-3行）"
                },
                "op": {
                    "type": "string",
                    "enum": ["append", "update"],
                    "description": "操作类型：append=新增，update=更新"
                }
            },
            "required": ["title"]
        }
    }
}

# 系统提示词
SYSTEM_PROMPT = """你是一个拥有深度思考能力的 AI 助手。

## 思考规则
1. 在回答问题前，你必须先调用 `emit_thinking` 工具来展示你的思考过程
2. 每个思考步骤都要调用一次 `emit_thinking`，至少调用 2-3 次
3. `title` 必须是 6-12 个词的简短摘要（像 bullet point）
4. `detail` 必须是 1-3 行的解释说明

## 回答规则
1. 思考完成后，直接在 content 中输出最终答案
2. 不要在最终答案中包含任何 thinking 文本
3. 思考只能通过 `emit_thinking` 工具发送

## 示例思考流程
- emit_thinking(title="分析问题的核心要素")
- emit_thinking(title="考虑可能的解决方案")  
- emit_thinking(title="评估最佳答案")
- 输出最终答案
"""


async def stream_chat_with_thinking(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL
):
    """
    流式调用 OpenRouter API，处理 emit_thinking 虚拟工具。
    
    核心循环：
    1. 发送请求，流式接收响应
    2. 如果收到 tool_calls，判断是否为 emit_thinking
    3. 如果是 emit_thinking，yield 思考事件，然后回传 tool result
    4. 继续循环直到获得最终 content
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/llm-council-test",
        "X-Title": "Streaming Thinking Test",
    }
    
    conversation_messages = list(messages)  # 复制消息列表
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        round_count = 0
        max_rounds = 10  # 防止无限循环
        
        while round_count < max_rounds:
            round_count += 1
            
            payload = {
                "model": model,
                "messages": conversation_messages,
                "tools": [EMIT_THINKING_TOOL],
                "stream": True,
            }
            
            # 用于缓冲流式数据
            content_buffer = []
            tool_call_buffer = {}  # index -> {id, name, arguments}
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
                    
                    choice = chunk.get("choices", [{}])[0]
                    delta = choice.get("delta", {})
                    
                    # 检查 finish_reason
                    if choice.get("finish_reason"):
                        finish_reason = choice["finish_reason"]
                    
                    # 处理普通 content（流式输出最终答案）
                    if "content" in delta and delta["content"]:
                        content_buffer.append(delta["content"])
                        # 流式 yield 最终答案片段
                        yield {
                            "type": "content",
                            "delta": delta["content"]
                        }
                    
                    # 处理 tool_calls
                    if "tool_calls" in delta and delta["tool_calls"]:
                        for tc in delta["tool_calls"]:
                            idx = tc.get("index", 0)
                            
                            if idx not in tool_call_buffer:
                                tool_call_buffer[idx] = {
                                    "id": tc.get("id", f"call_{idx}"),
                                    "name": "",
                                    "arguments": ""
                                }
                            
                            if "id" in tc and tc["id"]:
                                tool_call_buffer[idx]["id"] = tc["id"]
                            
                            if "function" in tc:
                                fn = tc["function"]
                                if "name" in fn:
                                    tool_call_buffer[idx]["name"] = fn["name"]
                                if "arguments" in fn:
                                    tool_call_buffer[idx]["arguments"] += fn["arguments"]
                            
                            # 尝试实时解析 emit_thinking
                            if tool_call_buffer[idx]["name"] == "emit_thinking":
                                args_str = tool_call_buffer[idx]["arguments"]
                                try:
                                    args = json.loads(args_str)
                                    # 检查是否已经 yield 过
                                    if not tool_call_buffer[idx].get("emitted"):
                                        tool_call_buffer[idx]["emitted"] = True
                                        yield {
                                            "type": "thinking",
                                            "op": args.get("op", "append"),
                                            "bullet_id": args.get("bullet_id", f"bullet_{idx}_{round_count}"),
                                            "title": args.get("title", ""),
                                            "detail": args.get("detail", "")
                                        }
                                except json.JSONDecodeError:
                                    # JSON 还不完整，继续等待
                                    pass
            
            # 这一轮流结束，检查结果
            if finish_reason == "stop" or (content_buffer and not tool_call_buffer):
                # 正常结束，有最终答案
                yield {"type": "done"}
                return
            
            if finish_reason == "tool_calls" and tool_call_buffer:
                # 收到 tool_calls，需要处理
                
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
            
            # 其他情况（如 length 超限），直接结束
            yield {"type": "done", "finish_reason": finish_reason}
            return
        
        # 超过最大轮数
        yield {"type": "error", "message": "Max rounds exceeded"}


@app.get("/")
async def index():
    """返回测试前端页面"""
    html_path = os.path.join(os.path.dirname(__file__), "streaming_thinking_frontend.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>请创建 streaming_thinking_frontend.html</h1>")


@app.post("/api/chat/stream")
async def chat_stream(request: Request):
    """
    流式聊天 API
    
    请求体：
    {
        "message": "用户消息",
        "model": "模型ID（可选）"
    }
    
    响应：SSE 流
    - type: "thinking" - 思考步骤
    - type: "content" - 最终答案片段
    - type: "done" - 完成
    - type: "error" - 错误
    """
    body = await request.json()
    user_message = body.get("message", "")
    model = body.get("model", DEFAULT_MODEL)
    
    if not user_message:
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'error', 'message': 'Empty message'})}\n\n"]),
            media_type="text/event-stream"
        )
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
    
    async def event_generator():
        try:
            async for event in stream_chat_with_thinking(messages, model):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("流式思考测试服务")
    print("=" * 60)
    print(f"前端页面: http://localhost:8020")
    print(f"API 端点: http://localhost:8020/api/chat/stream")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8020)
