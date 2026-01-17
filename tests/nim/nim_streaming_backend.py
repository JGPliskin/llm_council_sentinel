"""
NIM API Streaming Thinking Test Backend (Refined Multi-Strategy)
Handles model-specific quirks with improved text parsing strategies.
"""

import os
import sys
import json
import asyncio
import re
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

# Load env
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, ".env")
load_dotenv(env_path)

app = FastAPI(title="NIM Streaming Thinking Test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NIM Configuration
NIM_API_KEY = os.getenv("NIM_API_KEYS")
if not NIM_API_KEY:
    raise ValueError(f"NIM_API_KEYS not found in .env file at {env_path}")
NIM_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-ai/deepseek-r1"

# === 1. Tool Definition (Strategy: TOOLS) ===
EMIT_THINKING_TOOL = {
    "type": "function",
    "function": {
        "name": "emit_thinking",
        "description": "Output thinking steps. Call this MULTIPLE times BEFORE the final answer.",
        "parameters": {
            "type": "object",
            "properties": {
                "bullet_id": {"type": "string"},
                "title": {"type": "string", "description": "Concise title of thought"},
                "detail": {"type": "string", "description": "Details"},
                "op": {"type": "string", "enum": ["append", "update"]}
            },
            "required": ["title"]
        }
    }
}

SYSTEM_PROMPT_TOOLS = """You are a deep-thinking AI.
RULES:
1. You MUST use the `emit_thinking` tool to structure your reasoning.
2. Call the tool 3-5 times for different steps.
3. AFTER thinking, output the final answer as normal text.
"""

# === 2. Prompt Definition (Strategy: PROMPT) ===
# We use this for models that don't support tools, and parse the output.
SYSTEM_PROMPT_TEXT = """You are a deep-thinking AI.
RULES:
1. First, output your thinking process using this format:
   Thinking Process:
   - [Analysis]: ...
   - [Strategy]: ...
   - [Reflection]: ...
   
2. Then, output your final answer starting with "Final Answer:".
   Final Answer:
   (your answer here)
"""

# === Model Config Registry ===
MODEL_CONFIG = {
    # Working with tools
    "deepseek-ai/deepseek-v3.1": "TOOLS",
    "deepseek-ai/deepseek-v3.1-terminus": "TOOLS",
    "moonshotai/kimi-k2-instruct-0905": "TOOLS", # Kimi tries to use tools, imperfect but works
    "openai/gpt-oss-120b": "TOOLS", 
    "z-ai/glm4.7": "TOOLS",

    # R1: Native
    "deepseek-ai/deepseek-r1": "NATIVE_R1",  # R1 ignores tools usually

    # BROKEN TOOLS -> FORCE PROMPT PARSING
    "nvidia/cosmos-reason2-8b": "PROMPT", 
    "mistralai/mixtral-8x22b-instruct-v0.1": "PROMPT",
    "google/gemma-3-27b-it": "PROMPT",
    "qwen/qwen2.5-coder-32b-instruct": "PROMPT",
    "nvidia/llama-3.3-nemotron-super-49b-v1": "PROMPT",
    "meta/llama-3.3-70b-instruct": "PROMPT", # Was problematic with tools
    "nvidia/nemotron-3-nano-30b-a3b": "PROMPT",

    # Special Parsing
    "minimaxai/minimax-m2.1": "NATIVE_MINIMAX",
}

def get_strategy(model: str) -> str:
    return MODEL_CONFIG.get(model, "PROMPT") # Default to safest PROMPT

async def stream_chat_with_thinking(messages: List[Dict[str, str]], model: str):
    strategy = get_strategy(model)
    print(f"[DEBUG] Model: {model} | Strategy: {strategy}")
    
    headers = {
        "Authorization": f"Bearer {NIM_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "stream": True,
        "temperature": 0.6,
        "max_tokens": 4096
    }
    
    # Configure Payload based on Strategy
    conv_messages = list(messages)
    
    if strategy == "TOOLS":
        # Inject System Prompt
        if not any(m["role"] == "system" for m in conv_messages):
            conv_messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT_TOOLS})
        else:
             for m in conv_messages:
                 if m["role"] == "system": m["content"] = SYSTEM_PROMPT_TOOLS
        
        payload["messages"] = conv_messages
        payload["tools"] = [EMIT_THINKING_TOOL]
        payload["tool_choice"] = "auto" 

    elif strategy in ["PROMPT", "NATIVE_MINIMAX", "NATIVE_R1"]:
        # Text-based prompting
        sys_prompt = SYSTEM_PROMPT_TEXT
        if strategy == "NATIVE_MINIMAX":
             sys_prompt = "You are a helpful assistant. Please show your thinking process using <think> tags before answering."
        elif strategy == "NATIVE_R1":
            # R1 doesn't need prompt forcing, it just does it.
            sys_prompt = "" 
             
        if sys_prompt:
            if not any(m["role"] == "system" for m in conv_messages):
                conv_messages.insert(0, {"role": "system", "content": sys_prompt})
            else:
                for m in conv_messages:
                    if m["role"] == "system": m["content"] = sys_prompt
        
        payload["messages"] = conv_messages
        # NO TOOLS in payload

    # State for PROMPT parsing
    prompt_parser_thinking = True # Start assuming we are in thinking phase
    prompt_buffer = "" 
    
    # State for MiniMax
    minimax_in_think = False
    
    # Validated timeouts and HTTP/1.1 enforcement
    timeout = httpx.Timeout(connect=60.0, read=300.0, write=60.0, pool=60.0)
    
    async with httpx.AsyncClient(timeout=timeout, http2=False) as client:
        round_count = 0
        while round_count < 5:
            round_count += 1
            # Clear buffers for new round
            tool_call_buffer = {}
            content_buffer = []

            try:
                async with client.stream("POST", NIM_API_URL, headers=headers, json=payload) as response:
                     if response.status_code != 200:
                        err_text = await response.aread()
                        yield {"type": "error", "message": f"API Error {response.status_code}: {err_text.decode('utf-8')}"}
                        return

                     async for line in response.aiter_lines():
                        if not line.startswith("data: "): continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]": break
                        try:
                            chunk = json.loads(data_str)
                        except: continue
                        
                        choices = chunk.get("choices", [])
                        if not choices: continue
                        delta = choices[0].get("delta", {})
                        
                        # === STRATEGY: NATIVE R1 ===
                        if strategy == "NATIVE_R1" and "reasoning_content" in delta and delta["reasoning_content"]:
                             yield {
                                "type": "thinking",
                                "op": "update",
                                "bullet_id": "r1_native",
                                "title": "Deep Thinking (R1)",
                                "detail": delta["reasoning_content"] 
                            }
                        
                        # === STRATEGY: TOOLS ===
                        elif strategy == "TOOLS" and "tool_calls" in delta and delta["tool_calls"]:
                             for tc in delta["tool_calls"]:
                                 idx = tc.get("index", 0)
                                 if idx not in tool_call_buffer:
                                     tool_call_buffer[idx] = {
                                         "id": tc.get("id", f"call_{idx}"), 
                                         "name": "", 
                                         "arguments": "",
                                         "emitted": False
                                     }
                                 
                                 if "function" in tc:
                                     if "name" in tc["function"]:
                                         tool_call_buffer[idx]["name"] = tc["function"]["name"]
                                     if "arguments" in tc["function"]:
                                         tool_call_buffer[idx]["arguments"] += tc["function"]["arguments"]
                                 
                                 # Try parsing full buffer
                                 args_str = tool_call_buffer[idx]["arguments"]
                                 try:
                                    if args_str.strip().endswith("}"):
                                        a = json.loads(args_str)
                                        if "title" in a and not tool_call_buffer[idx]["emitted"]:
                                            tool_call_buffer[idx]["emitted"] = True
                                            yield {
                                                "type": "thinking", 
                                                "op": a.get("op", "append"), 
                                                "bullet_id": f"t_{idx}", 
                                                "title": a.get("title"), 
                                                "detail": a.get("detail")
                                            }
                                 except: pass

                        # === GENERIC CONTENT HAS TEXT ===
                        if "content" in delta and delta["content"]:
                            text_chunk = delta["content"]
                            content_buffer.append(text_chunk)
                            
                            # --- 1. PROMPT STRATEGY PARSING ---
                            if strategy == "PROMPT":
                                prompt_buffer += text_chunk
                                
                                # Check for transition marker
                                if prompt_parser_thinking:
                                    lower_buf = prompt_buffer.lower()
                                    if "final answer:" in lower_buf:
                                        # Split!
                                        parts = re.split(r"final answer:", prompt_buffer, flags=re.IGNORECASE, maxsplit=1)
                                        think_part = parts[0]
                                        ans_part = parts[1] if len(parts) > 1 else ""
                                        
                                        # Flush thinking
                                        yield {"type": "thinking", "op": "update", "bullet_id": "prompt_think", "title": "Thinking Process", "detail": think_part}
                                        
                                        # Switch mode
                                        prompt_parser_thinking = False
                                        
                                        # Yield rest as content
                                        if ans_part:
                                            yield {"type": "content", "delta": ans_part}
                                            
                                        prompt_buffer = "" 
                                    else:
                                        # Still thinking, update visual
                                        yield {"type": "thinking", "op": "update", "bullet_id": "prompt_think", "title": "Thinking Process", "detail": prompt_buffer}
                                else:
                                    # Already in content mode, just stream
                                    yield {"type": "content", "delta": text_chunk}
                            
                            # --- 2. MINIMAX STRATEGY PARSING ---
                            elif strategy == "NATIVE_MINIMAX":
                                 # We need to detect tags.
                                 remaining = text_chunk
                                 while remaining:
                                     if not minimax_in_think:
                                         # Looking for <think>
                                         if "<think>" in remaining:
                                             pre, post = remaining.split("<think>", 1)
                                             if pre: yield {"type": "content", "delta": pre}
                                             minimax_in_think = True
                                             remaining = post
                                             yield {"type": "thinking", "op": "append", "bullet_id": "mm_think", "title": "MiniMax Thinking", "detail": ""}
                                         else:
                                             # No tag, just content
                                             yield {"type": "content", "delta": remaining}
                                             remaining = ""
                                     else:
                                         # Inside think, looking for </think>
                                         if "</think>" in remaining:
                                             think_content, post = remaining.split("</think>", 1)
                                             # Flush think content to CURRENT bullet
                                             yield {"type": "thinking", "op": "update", "bullet_id": "mm_think", "title": "MiniMax Thinking", "detail": think_content}
                                             minimax_in_think = False
                                             remaining = post
                                         else:
                                             # All is think content
                                             yield {"type": "thinking", "op": "update", "bullet_id": "mm_think", "title": "MiniMax Thinking", "detail": remaining}
                                             remaining = ""
                            
                            # --- 3. DEFAULT (R1 Content, Tools Content) ---
                            else:
                                yield {"type": "content", "delta": text_chunk}

            except Exception as e:
                yield {"type": "error", "message": f"Stream Error: {str(e)}"}
                return
            
            # === ROUND END Logic ===
            
            # 1. Strategies that don't use multi-turn tools
            if strategy != "TOOLS":
                yield {"type": "done"}
                return

            # 2. TOOLS Strategy: Handle Tool Calls & Loop
            if tool_call_buffer:
                # Construct Tool Calls List
                valid_calls = []
                for idx, tc in tool_call_buffer.items():
                    if not tc["name"]: tc["name"] = "emit_thinking" # Robust Fix
                    valid_calls.append({
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]}
                    })
                
                # Append Assistant Message
                conv_messages.append({
                    "role": "assistant",
                    "content": "".join(content_buffer) or "", # Avoid None, use empty string
                    "tool_calls": valid_calls
                })
                
                # Append Tool Results (Virtual Execution)
                for tc in valid_calls:
                    result_content = json.dumps({"ok": True})
                    conv_messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result_content
                    })
                
                # Update Payload
                payload["messages"] = conv_messages
                
                # Continue to next round (model will now generate answer)
                continue 
            
            # If no tools were called in TOOLS mode, we are done
            yield {"type": "done"}
            return

@app.get("/")
async def index():
    html_path = os.path.join(os.path.dirname(__file__), "nim_streaming_frontend.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Please create nim_streaming_frontend.html</h1>")

@app.post("/api/chat/stream")
async def chat_stream(request: Request):
    body = await request.json()
    user_message = body.get("message", "")
    model = body.get("model", DEFAULT_MODEL)
    
    if not user_message:
         return StreamingResponse(iter([]), media_type="text/event-stream")
    
    # Simple pass-through messages
    messages = [{"role": "user", "content": user_message}]
    
    async def event_generator():
        async for event in stream_chat_with_thinking(messages, model):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("NIM Backend: Refined Multi-Strategy Mode")
    print(f"URL: http://localhost:8022")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=8022)
