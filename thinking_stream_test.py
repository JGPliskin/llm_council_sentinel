import os
import sys
# [HOTFIX] Block 'trio' library to prevent Anaconda crash (typing.NoReturn issue)
sys.modules["trio"] = None 

import json
import time
import asyncio
import threading
import argparse
from typing import List, Dict, Optional
from datetime import datetime

# 3rd party imports
try:
    from openai import AsyncOpenAI
    from dotenv import load_dotenv
    from rich.live import Live
    from rich.table import Table
    from rich.text import Text
    from rich.spinner import Spinner
    from rich.panel import Panel
    from rich.console import Console, Group
    from rich.markdown import Markdown
    from rich.layout import Layout
    from rich.style import Style
    from rich import box
    import httpx
except ImportError as e:
    print(f"Error: Missing dependencies. Detail: {e}")
    print("Please run: pip install openai rich python-dotenv")
    sys.exit(1)

# --- Environment Setup (Windows Compatibility) ---
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

load_dotenv()

# --- Configuration ---
# ... (rest of config unchanged) ...
DEFAULT_MODEL = "xiaomi/mimo-v2-flash:free"
FILLER_MESSAGES = [
    "正在分析上下文...",
    "回顾相关知识库...",
    "正在拆解问题逻辑...",
    "正在校验边界条件...",
    "组织语言结构...",
    "思考过于复杂，请稍候...",
    "正在优化输出格式..."
]

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "emit_thinking_title",
            "description": "Report the current thinking step or process title to the user. Use this frequently to show progress.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the thinking step (e.g., 'Analyzing Request', 'Checking constraints'). Keep it concise (under 20 characters)."
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "emit_final",
            "description": "Output the final answer in structured format. Use this OR just output plain content for the final answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "final": {
                        "type": "string",
                        "description": "The final answer content (Markdown supported)."
                    }
                },
                "required": ["final"]
            }
        }
    }
]

SYSTEM_PROMPT = """
你是一个拥有深度思考能力的 AI 助手。
1. **思考阶段**：必须通过调用 `emit_thinking_title` 工具来实时汇报思考进度（至少 1 个步骤，每 3-10 秒一条）。
2. **标题要求**：标题为短语（6-18 字），无标点、无解释。
3. **回答阶段**：最终答案请直接输出在 content 中，不要调用 `emit_final` 工具。
4. **结束标记**：回答完毕必须输出 "over"。
""".strip()

# --- Helpers ---

class ToolArgumentAccumulator:
    """Accumulates streaming tool arguments until valid JSON is formed."""
    def __init__(self):
        self.buffers = {} # call_id -> string buffer

    def add(self, call_id: str, fragment: str):
        if call_id not in self.buffers:
            self.buffers[call_id] = ""
        self.buffers[call_id] += fragment

    def try_parse(self, call_id: str) -> Optional[Dict]:
        if call_id not in self.buffers:
            return None
        try:
            return json.loads(self.buffers[call_id])
        except json.JSONDecodeError:
            return None
            
    def get_buffer(self, call_id: str) -> str:
        return self.buffers.get(call_id, "")

class ThinkingUI:
    """Manages the Rich UI state."""
    def __init__(self, console: Console):
        self.console = console
        self.titles = [] # List[str]
        self.is_thinking = True # True=Thinking/Filler, False=Locked
        self.filler_active = False # True if fillers are being generated
        self.filler_text = ""
        self.stats = {"start_time": time.time(), "titles": 0, "first_token_time": None}
        self.lock = threading.Lock()
        
        self.final_answer = "" # Buffer for final answer text
        self.final_answer_started = False
        self.reasoning_buffer = "" # RAW reasoning buffer
        self.last_title_time = time.time() # For smart filler logic
        
    def generate_view(self) -> Group:
        """Returns the Thinking Table."""
        # 1. Thinking Table
        table = Table(box=box.ROUNDED, expand=True, border_style="blue", title="Thinking Process", title_style="bold blue")
        
        # Add Real Titles
        for t in self.titles:
            table.add_row(f"[green]✔[/green]  [bold]{t}[/bold]")
            
        # Add Filler / Spinner if thinking
        if self.is_thinking:
            if self.titles:
                 table.add_row(f"[cyan]⠋[/cyan]  [dim]Thinking...[/dim]")
            elif self.filler_active:
                 table.add_row(f"[cyan]⠋[/cyan]  [dim][FILLER] {self.filler_text}[/dim]")
            else:
                 table.add_row(f"[cyan]⠋[/cyan]  [dim]Initializing...[/dim]")
        
        items = [table]
        
        # 2. Live Reasoning Panel (if any)
        if self.reasoning_buffer:
            # Show last 3 lines or full? Let's show full but dim, maybe truncated length?
            # User wants to check reasoning match.
            r_text = Text(self.reasoning_buffer, style="dim italic white")
            p = Panel(r_text, title="Reasoning Stream", border_style="dim")
            items.append(p)
            
        return Group(*items)

    def add_title(self, title: str):
        with self.lock:
            if not self.titles and self.stats["first_token_time"] is None:
                self.stats["first_token_time"] = time.time() - self.stats["start_time"]
            
            if self.titles and self.titles[-1] == title:
                return

            self.titles.append(title)
            self.stats["titles"] += 1
            # Reset filler state immediately on new title
            self.filler_active = False 
            self.last_title_time = time.time()
            
    def append_reasoning(self, content: str):
        with self.lock:
            self.reasoning_buffer += content

    def set_filler(self, text: str):
        with self.lock:
            self.filler_text = text
            self.filler_active = True
    
    def freeze(self):
        with self.lock:
            self.is_thinking = False
            self.filler_active = False
            
    def append_final(self, content: str):
        # Legacy: Not used in Hybrid mode stream
        pass

def filler_thread_func(ui: ThinkingUI, stop_event: threading.Event):
    """Background thread to update filler text if silence > 3s."""
    idx = 0
    while not stop_event.is_set():
        # Check gap
        now = time.time()
        gap = now - ui.last_title_time
        
        if ui.is_thinking:
            # If gap > 3s AND correct time has passed for next filler update
            if gap > 3.0:
                 if not ui.filler_active:
                     ui.set_filler(FILLER_MESSAGES[idx % len(FILLER_MESSAGES)])
                     idx += 1
                 else:
                     # Rotate filler every 2.5s if already active
                     # (Simple logic: just keep rotating)
                     ui.set_filler(FILLER_MESSAGES[idx % len(FILLER_MESSAGES)])
                     idx += 1
            else:
                # Less than 3s gap, ensure filler is hidden
                with ui.lock:
                    ui.filler_active = False
                
        time.sleep(2.5) 

async def main(args):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("[red]Error: OPENROUTER_API_KEY not found in environment.[/red]")
        print("Please create a .env file or set result in specific environment variables.")
        return

    # [NETWORK FIX: NUCLEAR OPTION]
    # Use a custom httpx client that EXPLICITLY ignores all system proxies.
    if args.debug:
        console.print("[yellow]Debug: Forcing DIRECT CONNECTION (ignoring system proxies/VPN)[/yellow]")
    
    # [FIX]: Increase timeout to 600s
    http_client = httpx.AsyncClient(trust_env=False, timeout=600.0)

    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        http_client=http_client, # Inject custom client
    )

    console = Console()
    ui = ThinkingUI(console)
    acc = ToolArgumentAccumulator()
    stop_filler = threading.Event()
    
    # Start Filler Thread
    t = threading.Thread(target=filler_thread_func, args=(ui, stop_filler), daemon=True)
    t.start()
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": args.question}
    ]

    title_count = 0
    duration = 0
    ttfb = 0
    finish_reason = None
    
    if args.debug:
        console.print(f"[yellow]Debug: Using model {args.model}[/yellow]")

    # Start Live Display
    # HYBRID MODE: "Break-out" Strategy
    
    first_chunk = None
    final_answer_type = None # "content" or "tool"
    
    try:
        start_req_time = time.time()
        
        stream = await client.chat.completions.create(
            model=args.model,
            messages=messages,
            tools=TOOL_DEFINITIONS, # tool_choice auto
            stream=True,
            extra_body={"include_reasoning": True} # Request explicit reasoning if supported
        )
        
        ui.stats["start_time"] = start_req_time

        # PHASE 1: Thinking (Live UI)
        with Live(ui.generate_view(), refresh_per_second=10, console=console) as live:
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].finish_reason:
                     finish_reason = chunk.choices[0].finish_reason
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta: continue

                # Extract Reasoning (Native)
                # handle various provider formats (OpenRouter, DeepSeek, etc)
                reasoning_chunk = getattr(delta, "reasoning", None) 
                if reasoning_chunk:
                     # Update UI with reasoning
                     ui.append_reasoning(reasoning_chunk)
                     live.update(ui.generate_view())

                # Check for Content -> Break to Phase 2
                # Check for Content -> Break to Phase 2
                if delta.content:
                    if not delta.content.strip():
                        continue # Ignore pure whitespace to prevent premature break
                    
                    first_chunk = chunk
                    final_answer_type = "content"
                    ui.freeze()
                    live.update(ui.generate_view())
                    break # Exit Live context

                # Check for Tool Calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if tc.function and tc.function.arguments:
                            acc.add(str(idx), tc.function.arguments)
                            
                            args_obj = acc.try_parse(str(idx))
                            if args_obj:
                                if "title" in args_obj:
                                    ui.add_title(args_obj["title"])
                                    live.update(ui.generate_view())
                                
                                elif "final" in args_obj:
                                    # Tool-based final answer
                                    first_chunk = chunk
                                    final_answer_type = "tool"
                                    ui.freeze()
                                    live.update(ui.generate_view())
                                    break 
                    
                    if final_answer_type: # Break outer loop if found
                        break

        # PHASE 2: Final Answer (Standard Stream)
        stop_filler.set()
        
        if final_answer_type:
            console.print("\n[bold cyan]== Final Answer ==[/bold cyan]")
            
            # Handle the stashed chunk
            if final_answer_type == "content":
                if first_chunk and first_chunk.choices[0].delta.content:
                    console.print(first_chunk.choices[0].delta.content, end="")
                
                # Resume streaming the rest
                async for chunk in stream:
                     if chunk.choices and chunk.choices[0].finish_reason:
                        finish_reason = chunk.choices[0].finish_reason
                     delta = chunk.choices[0].delta if chunk.choices else None
                     if not delta: continue
                     
                     # 1. Handle Content
                     if delta.content:
                         console.print(delta.content, end="")
                     
                     # 2. Handle Native Reasoning (in Final Phase)
                     r = getattr(delta, "reasoning", None)
                     if r:
                         console.print(f"[dim]{r}[/dim]", end="")

                     # 3. Handle Late Tool Calls (e.g. late titles)
                     if delta.tool_calls:
                         for tc in delta.tool_calls:
                             if tc.function and tc.function.arguments:
                                 acc.add(str(tc.index), tc.function.arguments)
                                 obj = acc.try_parse(str(tc.index))
                                 if obj:
                                     if "title" in obj:
                                         # Since UI is frozen, print title as log
                                         console.print(f"\n[green][Step] {obj['title']}[/green]")
                                     elif "final" in obj:
                                         # [FIX]: If model switches to emit_final mid-stream, print it!
                                         # Note: JSON usually parses only at the very end of the tool call.
                                         val = obj['final']
                                         # Avoid duplicating if possible, but prioritization on showing content.
                                         console.print(val) 

            elif final_answer_type == "tool":
                # Resume streaming with full checks
                printed_content = False
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].finish_reason:
                        finish_reason = chunk.choices[0].finish_reason
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if not delta: continue
                    
                    if delta.tool_calls:
                         for tc in delta.tool_calls:
                             if tc.function and tc.function.arguments:
                                 acc.add(str(tc.index), tc.function.arguments)

                    # Also handle content/reasoning mixed in tool mode??
                    # Rare but possible.
                    if delta.content: console.print(delta.content, end="")

        # [POST-LOOP CHECK]: Flush any tool-based final answers
        # Debug: Print what we have in accumulators
        if not final_answer_type and acc.buffers:
             pass

        for idx in acc.buffers:
            obj = acc.try_parse(idx)
            if obj:
                if "final" in obj:
                    val = obj['final']
                    console.print(f"\n[bold cyan]== Final Answer (Tool) ==[/bold cyan]\n{val}")
                # [FIX]: Ignore "title" objects here, they are already handled in Phase 1/2 UI.
                
            else:
                 # [SALVAGE]: If JSON is incomplete/invalid, try to extract "final" value raw.
                 raw = acc.buffers[idx]
                 
                 # Only salvage if it looks like a final answer tool call
                 if "final" in raw:
                     import re
                     match = re.search(r'"final"\s*:\s*"(.*)', raw, re.DOTALL)
                     if match:
                         content = match.group(1)
                         console.print(f"\n[bold red]== Final Answer (Salvaged) ==[/bold red]\n{content}")
                     else:
                         # Fallback for complex failing structure
                         console.print(f"\n[bold red]== Raw Final Output ==[/bold red]\n{raw}")
                 
                 # Hide raw titles to avoid confusion
                 # elif "title" in raw: pass

    except Exception as e:
        stop_filler.set()
        console.print(f"\n[red]Error: {e}[/red]")
        if args.debug:
            import traceback
            traceback.print_exc() 
    
    # Print Stats
    duration = time.time() - start_req_time
    title_count = ui.stats["titles"]
    ttfb = ui.stats["first_token_time"]
    ttfb_str = f"{ttfb:.2f}s" if ttfb else "N/A" 
    
    # Print Stats
    duration = time.time() - start_req_time
    title_count = ui.stats["titles"]
    ttfb = ui.stats["first_token_time"]
    ttfb_str = f"{ttfb:.2f}s" if ttfb else "N/A"
    
    console.print(Panel(
        f"Titles: [bold]{title_count}[/bold] | "
        f"Total Time: [bold]{duration:.2f}s[/bold] | "
        f"1st Title Gap: [bold]{ttfb_str}[/bold] | "
        f"Finish Reason: [bold]{finish_reason}[/bold]",
        title="Session Stats",
        border_style="green"
    ))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Thinking Title Stream PoC")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="OpenRouter Model ID")
    parser.add_argument("--question", type=str, default="我妈和我与我爸同时吵架，你说她是咋回事？不挑一个盟友吗，同时宣战？", help="Question to ask")
    parser.add_argument("--debug", action="store_true", help="Show debug info")
    
    args = parser.parse_args()
    
    if sys.platform == "win32":
        # Windows-specific cleanup or setup if needed
        pass
        
    asyncio.run(main(args))
