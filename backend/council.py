"""3-stage LLM Council orchestration with persona-driven prompts."""

from typing import List, Dict, Any, Tuple, Optional, Callable
import json
import asyncio
import re
import sys
import os
import time

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openrouter import query_model, stream_model
from persona_loader import fetch_persona
from config import (
    DEFAULT_CONCURRENCY_STAGE1,
    DEFAULT_CONCURRENCY_STAGE2,
    DEFAULT_STAGE1_TIMEOUT,
    DEFAULT_STAGE2_TIMEOUT,
    STAGE1_DEADLINE,
    STAGE2_DEADLINE,
    STAGE1_DEADLINE,
    STAGE2_DEADLINE,
    COUNCILOR_MAP,
    GLOBAL_MODEL_MAP,
    SPEED_ROUTE_SWITCH_ABS_MS,
    SPEED_ROUTE_SWITCH_REL_PCT,
)
from health import health_manager
from logger import log_request_timing

THINKING_TOOL_DEF = [
    {
        "type": "function",
        "function": {
            "name": "emit_thinking",
            "description": "Emit a thinking step payload for UI display.",
            "parameters": {
                "type": "object",
                "properties": {
                    "bullet_id": {
                        "type": "string",
                        "description": "Unique identifier of the thinking step."
                    },
                    "title": {
                        "type": "string",
                        "description": "Concise title of the thinking step (6-18 chars)."
                    },
                    "detail": {
                        "type": "string",
                        "description": "1-3 lines of public-facing detail."
                    },
                    "op": {
                        "type": "string",
                        "enum": ["append", "update"],
                        "description": "append to add, update to modify a prior step."
                    }
                },
                "required": ["title"]
            }
        }
    }
]

# Persona cache is injected at startup by the application
PERSONA_CACHE: Dict[str, str] = {}


def set_persona_cache(cache: Dict[str, str]):
    global PERSONA_CACHE
    PERSONA_CACHE = cache


def strip_json_fences(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", cleaned, flags=re.MULTILINE)
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        return match.group(0)
    return cleaned


def extract_thinking_from_content(content: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    从 content 中提取 emit_thinking JSON，返回 (thinking_list, cleaned_answer)。
    
    某些模型不正确使用 tool calls，而是直接把 thinking JSON 输出到 content 中，例如：
    { "name": "emit_thinking", "arguments": {"bullet_id": "1", ...} } { ... } 回答内容
    
    这个函数会：
    1. 找到所有 JSON 对象
    2. 过滤出 emit_thinking 相关的
    3. 提取 thinking 信息
    4. 从 content 中移除这些 JSON，返回干净的回答
    """
    thinking_list = []
    json_spans = []  # [(start, end), ...]
    
    # 逐字符扫描，找到所有顶层 {} 对象
    i = 0
    while i < len(content):
        if content[i] == '{':
            # 找到开始，计算匹配的结束位置
            depth = 1
            start = i
            i += 1
            in_string = False
            escape_next = False
            
            while i < len(content) and depth > 0:
                char = content[i]
                if escape_next:
                    escape_next = False
                elif char == '\\':
                    escape_next = True
                elif char == '"':
                    in_string = not in_string
                elif not in_string:
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                i += 1
            
            if depth == 0:
                json_str = content[start:i]
                try:
                    obj = json.loads(json_str)
                    # 检查是否是 emit_thinking
                    if isinstance(obj, dict) and obj.get("name") == "emit_thinking":
                        args = obj.get("arguments", {})
                        if isinstance(args, dict) and args.get("title"):
                            thinking_list.append({
                                "bullet_id": args.get("bullet_id", f"extracted_{len(thinking_list)}"),
                                "title": args.get("title", ""),
                                "detail": args.get("detail", ""),
                                "op": args.get("op", "append")
                            })
                            json_spans.append((start, i))
                except json.JSONDecodeError:
                    pass
        else:
            i += 1
    
    # 从后往前移除所有匹配的 JSON（避免索引偏移问题）
    cleaned_content = content
    for start, end in reversed(json_spans):
        cleaned_content = cleaned_content[:start] + cleaned_content[end:]
    
    # 清理多余的空白和换行
    cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)
    cleaned_content = re.sub(r'[ \t]+', ' ', cleaned_content)
    cleaned_content = cleaned_content.strip()
    
    # 如果回答以 "回答" 开头，移除这个标记
    cleaned_content = re.sub(r'^回答[:：]?\s*', '', cleaned_content)
    
    return thinking_list, cleaned_content





def is_retryable_error(response_dict: Optional[Dict[str, Any]]) -> bool:
    """Check if the response indicates a retryable failure (Network/RateLimit)."""
    if not response_dict:
        return True  # No response usually implies timeout/network error
    
    # Check for explicit 'error' flag from openrouter.py
    if response_dict.get("error"):
        content = response_dict.get("content", "")
        status = response_dict.get("status_code")
        
        # Explicit Non-Retryable
        if status in [401, 403]:
            return False
            
        # Retryable HTTP Codes
        if status in [408, 429, 500, 502, 503, 504]:
            return True
            
        # Inspect Error Payload for OpenRouter codes
        payload = response_dict.get("error_payload")
        if isinstance(payload, dict):
            err_obj = payload.get("error", {})
            # Example OpenRouter/Provider codes
            code = err_obj.get("code")
            msg = err_obj.get("message", "").lower()
            if code in [429, 502, 503] or "rate limit" in msg or "unavailable" in msg:
                return True
                
        # Fallback: Treat generic network exception strings as retryable
        # This is loose, but usually safer to retry once than fail
        return True
        
    return False


def get_retry_after(response_dict: Optional[Dict[str, Any]]) -> Optional[float]:
    """Parse Retry-After header if present."""
    if not response_dict:
        return None
    headers = response_dict.get("headers", {})
    val = headers.get("retry-after")
    if val:
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    return None



# -------------------------------------------------------------------------
# Concurrency & Routing Helpers
# -------------------------------------------------------------------------

class ModelConcurrencyManager:
    """Manages per-model concurrency semantics."""
    def __init__(self):
        self._semaphores: Dict[str, asyncio.Semaphore] = {}
        self._lock = asyncio.Lock()

    async def get_semaphore(self, model_id: str) -> asyncio.Semaphore:
        # Fast path
        if model_id in self._semaphores:
            return self._semaphores[model_id]
            
        async with self._lock:
            if model_id not in self._semaphores:
                # Look up limit from Global Pool, default to 3
                # If model not in pool, default to 3
                cfg = GLOBAL_MODEL_MAP.get(model_id, {})
                limit = cfg.get("concurrency_limit", 3)
                self._semaphores[model_id] = asyncio.Semaphore(limit)
            return self._semaphores[model_id]

model_concurrency_manager = ModelConcurrencyManager()


# 内存态：每个 councilor 的“当前首选模型”
_current_model_by_councilor: Dict[str, str] = {}


def select_best_model(
    candidates: List[str], 
    excluded: set,
    councilor_id: str = None,
    auto_route_by_speed: bool = True
) -> Optional[str]:
    """
    服务于 Stage1 的模型选择函数。
    
    - auto_route_by_speed=True: 按 TTFT 速度排序选最快 (+ 双阈值防抖)
    - auto_route_by_speed=False: 按 candidates 顺序选第一个健康
    """
    # 1. 过滤出可用的候选模型 (healthy 或 unknown)
    # unknown 状态表示尚未检查，允许参与选择以支持夜间等跳过健康检查的场景
    healthy_candidates = []
    for mid in candidates:
        if mid in excluded:
            continue
        status = health_manager.get_status(mid)
        health_status = status.get("health_status")
        # 允许 healthy 和 unknown 状态
        if health_status in ("healthy", "unknown"):
            healthy_candidates.append(mid)
    
    if not healthy_candidates:
        return None
    
    if len(healthy_candidates) == 1:
        return healthy_candidates[0]
    
    # 2. 如果禁用自动选路，返回第一个健康模型 (按 candidates 原始顺序)
    if not auto_route_by_speed:
        return healthy_candidates[0]
    
    # 3. 自动速度排序模式
    # 获取每个候选的 TTFT
    ttft_map = {}
    for mid in healthy_candidates:
        record = health_manager._records.get(mid)
        if record:
            ttft = record.get_effective_ttft()
            ttft_map[mid] = ttft  # 可能是 None
        else:
            ttft_map[mid] = None
    
    # 按 TTFT 排序 (None 排最后，同 TTFT 按 candidates 顺序保持稳定)
    def sort_key(mid: str) -> Tuple[int, float, int]:
        ttft = ttft_map.get(mid)
        # (has_ttft, ttft_value, original_order)
        # has_ttft: 0=有, 1=无 (无排最后)
        # original_order: candidates 中的索引 (tie-breaker)
        try:
            orig_idx = candidates.index(mid)
        except ValueError:
            orig_idx = 9999
        if ttft is not None:
            return (0, ttft, orig_idx)
        else:
            return (1, 0, orig_idx)
    
    sorted_candidates = sorted(healthy_candidates, key=sort_key)
    top = sorted_candidates[0]
    top_ttft = ttft_map.get(top)
    
    # 4. 双阈值防抖切换
    if councilor_id:
        current = _current_model_by_councilor.get(councilor_id)
        
        # 如果 current 不存在/不健康/TTFT缺失，直接选 top
        if current and current in healthy_candidates:
            current_ttft = ttft_map.get(current)
            
            if current == top:
                # 保持不变
                return current
            
            if current_ttft is not None and top_ttft is not None:
                # 计算差异
                abs_diff = current_ttft - top_ttft
                rel_diff = abs_diff / current_ttft if current_ttft > 0 else 0
                
                # 双阈值: 绝对差 >= 800ms AND 相对差 >= 30%
                if abs_diff >= SPEED_ROUTE_SWITCH_ABS_MS and rel_diff >= SPEED_ROUTE_SWITCH_REL_PCT:
                    # 满足切换条件，切换到 top
                    _current_model_by_councilor[councilor_id] = top
                    return top
                else:
                    # 不满足阈值，保持 current
                    return current
            else:
                # TTFT 缺失，回退到 top
                _current_model_by_councilor[councilor_id] = top
                return top
        else:
            # current 不可用，选 top
            _current_model_by_councilor[councilor_id] = top
            return top
    
    # 无 councilor_id，直接返回最快
    return top

def get_candidates(obj: Dict[str, Any]) -> List[str]:
    """Helper to get candidates from councilor/chairman object."""
    c = obj.get("model_candidates", [])
    if not c and obj.get("model"):
        c = [obj["model"]]
    return c


# Redefining _request_stage1 to handle the loop + semaphore
async def _request_stage1_bounded(
    semaphore: asyncio.Semaphore,
    councilor: Dict[str, Any],
    user_query: str,
    on_thinking: Optional[Callable[[str, str, Any, str], Any]] = None,
    on_answer_delta: Optional[Callable[[str, str], Any]] = None,
    enable_thinking: bool = True
) -> Dict[str, Any]:
    
    # 计时开始
    t_start = time.time()
    t_model_select = None
    
    persona = fetch_persona(PERSONA_CACHE, councilor.get("persona_path", ""))
    stage_limits = councilor.get("stage_limits", {}).get("stage1", {})
    timeout = stage_limits.get("timeout", DEFAULT_STAGE1_TIMEOUT)
    max_tokens = stage_limits.get("max_output_tokens", 800)

    # 基础 persona 提示
    base_instructions = (
        "严格遵守：\n"
        "- 回答语言需与用户问题保持一致。\n"
        "- 不自我介绍，不复述问题，不写模板化客套。\n"
        "- 直接输出 Markdown 格式答案（不要 JSON）。\n"
        "- 内容尽量自然、像人类表达，但不要空洞铺陈。\n"
    )

    if enable_thinking:
        # 参照测试代码的写法，更明确地强调使用 tool calls
        thinking_instructions = """
## 思考规则
1. 在回答问题前，你必须先调用 `emit_thinking` 工具来展示你的思考过程
2. 每个思考步骤都要调用一次 `emit_thinking`，至少调用 2-3 次
3. `title` 必须是 6-12 个词的简短摘要（像 bullet point）
4. `detail` 必须是 1-3 行的解释说明

## 回答规则
1. 思考完成后，直接在 content 中输出最终答案（Markdown 格式）
2. 绝对不要在最终答案中包含任何 thinking 文本或 JSON
3. 思考只能通过 `emit_thinking` 工具发送，不要把 JSON 输出到回答中

## 示例思考流程
- emit_thinking(title="分析问题的核心要素")
- emit_thinking(title="考虑可能的解决方案")  
- emit_thinking(title="评估最佳答案")
- 输出最终答案（纯 Markdown，无 JSON）
"""
        system_prompt = f"{persona}\n\n{base_instructions}\n{thinking_instructions}"
    else:
        system_prompt = f"{persona}\n\n{base_instructions}"

    user_message = (
        f"用户问题：{user_query}\n"
        "请依据 persona 直接作答。"
    )


    candidates = get_candidates(councilor)
    excluded_models = set()
    attempted_models = [] # Track for metadata/history

    last_error = None
    
    # Outer Loop: Candidate Selection
    while True:
        # A. Select Model (Stage1 使用速度选路)
        auto_route = councilor.get("auto_route_by_speed", True)
        
        # 记录模型选择开始时间（仅第一次）
        t_select_start = time.time() if t_model_select is None else None
        
        selected_model = select_best_model(
            candidates, 
            excluded_models, 
            councilor_id=councilor["id"],
            auto_route_by_speed=auto_route
        )
        
        # 记录模型选择结束时间（仅第一次）
        if t_model_select is None:
            t_model_select = time.time() - t_select_start  # 直接存储耗时（秒）
        
        if not selected_model:
            # No healthy models available
            # If we haven't tried anything yet, and maybe all are "unknown" but we are strict?
            # Or if we exhausted all.
            # We fail.
            break
            
        model_sem = await model_concurrency_manager.get_semaphore(selected_model)
        
        model_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        response = None
        answer_chunks: List[str] = []
        try:
            # Double Locking
            async with semaphore: # Stage Limit
                async with model_sem: # Model Limit
                    # Check Capabilities
                    model_cfg = GLOBAL_MODEL_MAP.get(selected_model, {})
                    caps = model_cfg.get("capabilities", {})

                    can_think = caps.get("thinking", False)
                    use_tools = enable_thinking and can_think and on_thinking

                    async def _think_cb(payload: Any):
                        if not on_thinking:
                            return
                        if isinstance(payload, dict):
                            thinking_payload = payload
                        else:
                            thinking_payload = {"title": str(payload)}
                        await on_thinking(councilor["id"], "stage1", thinking_payload, selected_model)

                    async def _content_cb(delta: str):
                        answer_chunks.append(delta)
                        if on_answer_delta:
                            if asyncio.iscoroutinefunction(on_answer_delta):
                                await on_answer_delta(councilor["id"], delta)
                            else:
                                on_answer_delta(councilor["id"], delta)

                    response = await stream_model(
                        selected_model,
                        model_messages,
                        on_thinking=_think_cb if use_tools else None,
                        on_content=_content_cb,
                        timeout=timeout,
                        max_output_tokens=max_tokens,
                        tools=THINKING_TOOL_DEF if use_tools else None
                    )
        except asyncio.CancelledError:
            raise
        except Exception as e:
            # Fallback for unexpected exceptions
            response = {"error": True, "content": str(e)}

        if selected_model not in attempted_models:
            attempted_models.append(selected_model)

        if response and not response.get("error"):
            # Network Success
            health_manager.update_status(selected_model, True, source="runtime")

            answer = response.get("content", "")
            if not answer and answer_chunks:
                answer = "".join(answer_chunks)

            # 后处理：从 content 中提取被错误输出的 thinking JSON
            extracted_thinking, cleaned_answer = extract_thinking_from_content(answer or "")
            
            # 如果提取到了 thinking，触发回调
            if extracted_thinking and on_thinking:
                for thinking_item in extracted_thinking:
                    try:
                        if asyncio.iscoroutinefunction(on_thinking):
                            await on_thinking(councilor["id"], "stage1", thinking_item, selected_model)
                        else:
                            on_thinking(councilor["id"], "stage1", thinking_item, selected_model)
                    except Exception:
                        pass

            # 计算耗时并输出日志
            t_end = time.time()
            ttft_ms = response.get("ttft_ms")
            model_select_ms = int(t_model_select * 1000) if t_model_select else 0  # t_model_select 已经是耗时（秒）
            total_ms = int((t_end - t_start) * 1000)
            generation_ms = total_ms - (ttft_ms or 0) - model_select_ms
            
            # 需求3 4.4: 检查是否需要触发紧急探测
            if ttft_ms is not None:
                # 延迟导入以避免循环依赖
                from validation import check_model_health_probe
                from config import (
                    EMERGENCY_PROBE_TTFT_THRESHOLD,
                    EMERGENCY_PROBE_TTFT_MULTIPLIER,
                    EMERGENCY_PROBE_COOLDOWN_MINUTES
                )
                
                is_slow = health_manager.is_ttft_slow(
                    selected_model, 
                    ttft_ms, 
                    threshold=EMERGENCY_PROBE_TTFT_THRESHOLD, 
                    multiplier=EMERGENCY_PROBE_TTFT_MULTIPLIER
                )
                
                if is_slow:
                    # 触发紧急探测 (Fire-and-forget)
                    # 范围：刷新当前 councilor 的所有候选模型
                    # 注意：trigger_emergency_refresh 内部会检查每个 model 的 cooling down
                    asyncio.create_task(
                        health_manager.trigger_emergency_refresh(
                            candidates, 
                            check_model_health_probe, 
                            cooldown_minutes=EMERGENCY_PROBE_COOLDOWN_MINUTES
                        )
                    )

            log_request_timing(
                stage="stage1",
                councilor_id=councilor["id"],
                councilor_name=councilor.get("name", ""),
                model=response.get("model", selected_model),
                timing={
                    "total_ms": total_ms,
                    "model_select_ms": model_select_ms,
                    "ttft_ms": ttft_ms,
                    "generation_ms": max(0, generation_ms)
                },
                status="ok"
            )

            return {
                "councilor_id": councilor["id"],
                "councilor_name": councilor.get("name"),
                "model": response.get("model", selected_model),
                "status": "ok",
                "answer_markdown": cleaned_answer,
                "attempted_models": attempted_models,
                "fallback_used": (selected_model != candidates[0]),
                "extracted_thinking_count": len(extracted_thinking)
            }


        # Network Failure
        err_msg = response.get('content') if response else 'No response'
        last_error = f"Network Error ({selected_model}): {err_msg}"
        status_code = response.get('status_code') if response else None

        health_manager.update_status(selected_model, False, err_msg, status_code, source="runtime")
        excluded_models.add(selected_model) # In-Flight Exclusion
        continue
        
        # End of Inner Loop
        # If we are here, we either succeeded (returned already) or failed (break)
        # If failed, we seek next candidate in Outer Loop
            
    # If we exited without returning
    # 记录失败日志
    t_end = time.time()
    model_select_ms = int(t_model_select * 1000) if t_model_select else 0  # t_model_select 已经是耗时（秒）
    total_ms = int((t_end - t_start) * 1000)
    
    log_request_timing(
        stage="stage1",
        councilor_id=councilor["id"],
        councilor_name=councilor.get("name", ""),
        model=councilor["model"],
        timing={
            "total_ms": total_ms,
            "model_select_ms": model_select_ms,
            "ttft_ms": None,
            "generation_ms": 0
        },
        status="failed",
        error=str(last_error or "All candidates failed")
    )
    
    return {
        "councilor_id": councilor["id"],
        "councilor_name": councilor.get("name"),
        "model": councilor["model"], # Default requested
        "status": "failed",
        "error": {
            "code": "EXECUTION_ERROR",
            "message": str(last_error or "All candidates failed"),
            "retryable": True
        },
        "answer_markdown": "",
        "attempted_models": attempted_models
    }


async def stage1_collect_responses(
    user_query: str, 
    councilors: List[Dict[str, Any]],
    on_result: Optional[Callable[[Dict[str, Any]], Any]] = None,
    on_thinking: Optional[Callable[[str, str, Any, str], Any]] = None,
    on_answer_delta: Optional[Callable[[str, str], Any]] = None,
    on_answer_done: Optional[Callable[[str], Any]] = None,
    enable_thinking: bool = True
) -> List[Dict[str, Any]]:
    """Stage 1: Collect initial responses from all councilors with strict control."""
    semaphore = asyncio.Semaphore(DEFAULT_CONCURRENCY_STAGE1)
    
    # Create Tasks
    # We must start them. `asyncio.create_task` schedules them.
    # Note: Using a mapping to track who is who is safer if order matters, 
    # but `gather` preserves order of input tasks.
    tasks = [
        asyncio.create_task(
            _request_stage1_bounded(
                semaphore,
                c,
                user_query,
                on_thinking,
                on_answer_delta,
                enable_thinking
            )
        )
        for c in councilors
    ]
    
    # Wait with Deadline
    if STAGE1_DEADLINE:
        done, pending = await asyncio.wait(tasks, timeout=STAGE1_DEADLINE)
        
        # Cancel pending tasks
        for t in pending:
            t.cancel()
        
        # Safe await for cleanup
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
            
        # Replace pending results with Failure Objects
        # We need to map tasks back to councilors. 
        # Since `tasks` is ordered list, we can check `tick.done()`.
        results = []
        for i, task in enumerate(tasks):
            if task in done:
                # Task finished (could be success or normal failure)
                # handle exceptions if any
                try:
                    res = task.result()
                    results.append(res)
                    if on_result:
                        if asyncio.iscoroutinefunction(on_result):
                            await on_result(res)
                        else:
                            on_result(res)
                    if on_answer_done and res.get("councilor_id"):
                        if asyncio.iscoroutinefunction(on_answer_done):
                            await on_answer_done(res["councilor_id"])
                        else:
                            on_answer_done(res["councilor_id"])
                except Exception as e:
                    # Should verify if this happens; _request_stage1_bounded handles most.
                    err_res = {
                        "councilor_id": councilors[i]["id"],
                        "status": "failed",
                        "error": {"code": "UNEXPECTED_ERROR", "message": str(e)}
                    }
                    results.append(err_res)
                    if on_result:
                        if asyncio.iscoroutinefunction(on_result):
                             await on_result(err_res)
                        else:
                             on_result(err_res)
                    if on_answer_done and err_res.get("councilor_id"):
                        if asyncio.iscoroutinefunction(on_answer_done):
                            await on_answer_done(err_res["councilor_id"])
                        else:
                            on_answer_done(err_res["councilor_id"])
            else:
                # Task was pending and cancelled
                results.append({
                    "councilor_id": councilors[i]["id"],
                    "councilor_name": councilors[i].get("name"),
                    "model": councilors[i]["model"],
                    "status": "failed",
                    "error": {
                        "code": "STAGE_DEADLINE", 
                        "message": "Stage deadline exceeded."
                    },
                     "answer_markdown": "",
                })
                if on_answer_done:
                    cid = councilors[i]["id"]
                    if asyncio.iscoroutinefunction(on_answer_done):
                        await on_answer_done(cid)
                    else:
                        on_answer_done(cid)
        return results
        
    else:
        # No strict stage deadline, just gather all
        # To support streaming, we can't just use gather(*tasks).
        # We need as_completed or similar, OR just attach callbacks to the tasks?
        # But we also need to respect the list order for the final return.
        # Let's use as_completed for the side effects, but gather for the final list?
        # Actually, if we use gather, we wait for all.
        # To stream, we must process as they finish.
        # We can use `asyncio.as_completed` but mapping back to ID is tricky if we lose index.
        # Better: Wrap the task to call the callback itself?
        # Or iterate as_completed.
        # Let's wrap the coroutine with a reporter helper?
        # No, let's just use `asyncio.as_completed` to fire events, and `gather` to get final ordered list.
        # Note: `as_completed` returns an iterator of futures.
        
        # Parallel strategy: yield via callback as they complete
        if on_result:
             for f in asyncio.as_completed(tasks):
                 try:
                     res = await f
                     if asyncio.iscoroutinefunction(on_result):
                         await on_result(res)
                     else:
                         on_result(res)
                     if on_answer_done and res.get("councilor_id"):
                         if asyncio.iscoroutinefunction(on_answer_done):
                             await on_answer_done(res["councilor_id"])
                         else:
                             on_answer_done(res["councilor_id"])
                 except Exception as e:
                     # This exception comes from the task itself
                     # But _request_stage1_bounded handles exceptions internally and returns dict.
                     # So strictly, this shouldn't raise unless cancellation or bug.
                     # We can't identify WHO failed easily here without mapping.
                     # But wait, `res` IS the result dict containing councilor_id.
                     # If generic exception, we don't have ID. 
                     # _request_stage1_bounded guarantees dict return.
                     pass 
        
        # Now gather for final ordered list (all should be done)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        final_results = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                err_res = {
                    "councilor_id": councilors[i]["id"],
                    "status": "failed",
                    "error": {"code": "UNHANDLED_EXCEPTION", "message": str(res)}
                }
                final_results.append(err_res)
                if on_answer_done:
                    cid = councilors[i]["id"]
                    if asyncio.iscoroutinefunction(on_answer_done):
                        await on_answer_done(cid)
                    else:
                        on_answer_done(cid)
                # Note: if on_result was used, this exception might have been swallowed or raised during as_completed loop?
                # If as_completed raised, we might have missed calling on_result for this one.
                # Let's ensure strictness: _request_stage1_bounded should NOT raise.
            else:
                final_results.append(res)
        return final_results


def _build_stage2_candidates(stage1_results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """Create anonymized candidate payloads for ranking."""
    candidates = []
    anon_to_councilor_id = {}
    
    # We iterate and assign anon_ids. 
    # To keep anon_ids consistent across debugs, we could sort, but input order is presumed stable.
    
    count = 1
    for result in stage1_results:
        if result.get("status") != "ok":
            continue
            
        anon_id = f"anon_{count}"
        count += 1
        
        # Strict Requirement: anon_map maps anon_id -> councilor_id
        councilor_id = result.get("councilor_id")
        
        anon_to_councilor_id[anon_id] = councilor_id

        payload = {
            "answer_markdown": result.get("answer_markdown", "")
        }

        candidates.append(
            {
                "anon_id": anon_id,
                "payload": payload
            }
        )

    return candidates, anon_to_councilor_id


def _build_ranking_messages(
    user_query: str, 
    candidates: List[Dict[str, Any]],
    persona_text: str,
    rubric_text: str
) -> List[Dict[str, str]]:
    """
    Build messages using 3-layer system prompt:
    1. Judge Persona
    2. Judge Rubric
    3. JSON Guard
    """
    
    # Layer 3: JSON Guard (Strictest)
    json_guard = (
        "HARD CONSTRAINTS (MUST FOLLOW):\n"
        "1) Output EXACTLY ONE JSON object and nothing else.\n"
        "2) NO markdown fences, NO commentary.\n"
        "3) Allowed top-level fields ONLY: ranking, scores, rationale, per_candidate_comments.\n"
        "4) 'ranking' field is REQUIRED. It must include ALL anon_ids exactly once.\n"
        "5) 'scores' (optional) must be 1-10 integers keyed by anon_id only.\n"
        "6) 'rationale' (optional) must be a string.\n"
        "7) 'per_candidate_comments' (REQUIRED) must be a dictionary mapped by anon_id, with string values (max 200 chars each).\n"
        "ANY extra keys at top level = INVALID."
    )
    
    # Combine Systems
    # persona_text from caching logic
    full_system_prompt = (
        f"--- ROLE ---\n{persona_text}\n\n"
        f"--- RUBRIC ---\n{rubric_text}\n\n"
        f"--- FORMAT ---\n{json_guard}"
    )

    ranking_instructions = {
        "task": "rank_responses",
        "question": user_query,
        "candidates": candidates,
    }

    messages = [
        {
            "role": "system",
            "content": full_system_prompt,
        },
        {
            "role": "user",
            "content": json.dumps(ranking_instructions, ensure_ascii=False),
        },
    ]
    return messages


def _parse_ranking_response(
    response_text: str, expected_anon_ids: List[str]
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Parse and validate a ranking response from a judge."""
    try:
        data = json.loads(strip_json_fences(response_text))
    except Exception as exc:
        return None, f"Invalid JSON: {exc}"

    if not isinstance(data, dict):
        return None, "Top-level response must be a JSON object"

    ranking = data.get("ranking")
    if not isinstance(ranking, list):
        return None, "`ranking` must be an array"

    ranking_strs = [str(x) for x in ranking]
    if len(set(ranking_strs)) != len(ranking_strs):
        return None, "Duplicate anon_ids in ranking"
    
    expected_set = set(expected_anon_ids)
    ranking_set = set(ranking_strs)
    
    if ranking_set != expected_set:
        missing = sorted(list(expected_set - ranking_set))
        extra = sorted(list(ranking_set - expected_set))
        return None, f"Ranking mismatch. Missing: {missing}, Extra: {extra}"

    scores = data.get("scores", {})
    filtered_scores = {}
    if isinstance(scores, dict):
        for anon_id, score in scores.items():
            if anon_id in expected_set:
                try:
                    s_val = int(score)
                    if 1 <= s_val <= 10:
                        filtered_scores[anon_id] = s_val
                except (ValueError, TypeError):
                    pass 

    rationale = data.get("rationale")

    per_candidate_comments = data.get("per_candidate_comments", {})
    filtered_comments = {}
    if isinstance(per_candidate_comments, dict):
        for anon_id, comment in per_candidate_comments.items():
            if anon_id in expected_set and isinstance(comment, str):
                filtered_comments[anon_id] = comment[:200] # Truncate

    parsed = {
        "ranking": ranking_strs,
        "scores": filtered_scores,
        "rationale": rationale,
        "per_candidate_comments": filtered_comments
    }
    
    # Strict Key Validation: Subset check
    # Top keys must be subset of allowed
    current_keys = set(data.keys())
    allowed_keys = {"ranking", "scores", "rationale", "per_candidate_comments"}
    if not current_keys.issubset(allowed_keys):
        extra = current_keys - allowed_keys
        return None, f"Invalid extra keys found: {extra}"

    # Truncate rationale if present
    if parsed["rationale"]:
        parsed["rationale"] = str(parsed["rationale"])[:600]

    return parsed, None


async def _collect_single_ranking_bounded(
    semaphore: asyncio.Semaphore,
    councilor_id: str,
    councilor_name: str,
    councilor_obj: Dict[str, Any],
    default_model: str, # Renamed for clarity
    user_query: str,
    candidates: List[Dict[str, Any]],
    expected_anon_ids: List[str],
    timeout: float,
    on_thinking: Optional[Callable[[str, str, Any, str], Any]] = None,
    enable_thinking: bool = True
) -> Dict[str, Any]:
    """Collect ranking with fallback routing."""
    
    # Fetch Persona & Rubric
    persona_path = councilor_obj.get("judge_persona_path") or councilor_obj.get("persona_path")
    persona_text = fetch_persona(PERSONA_CACHE, persona_path)
    rubric_text = councilor_obj.get("judge_system_prompt", "")
    rubric_text += "\n\n评审要求：忽略文风，仅评可行性与有效性。"
    
    # Limits
    stage_limits = councilor_obj.get("stage_limits", {}).get("stage2", {})
    max_tokens = stage_limits.get("max_output_tokens", 360)

    if enable_thinking:
        rubric_text += (
            "\n\nIMPORTANT: You MUST call the `emit_thinking` tool MULTIPLE times "
            "before outputting your JSON to explain your ranking logic."
        )

    messages = _build_ranking_messages(user_query, candidates, persona_text, rubric_text)
    
    candidates = get_candidates(councilor_obj)
    excluded_models = set()
    attempted_models = []

    last_error = None
    
    while True: # Outer Loop: Candidates
        selected_model = select_best_model(candidates, excluded_models)
        if not selected_model:
            break
            
        model_sem = await model_concurrency_manager.get_semaphore(selected_model)
        
        current_messages = messages # Start fresh for this model (though logically same)
        
        # Inner Loop: Logic Retry
        for logic_attempt in range(2):
            response = None
            try:
                async with semaphore:
                    async with model_sem:
                        # Check Capabilities
                        model_cfg = GLOBAL_MODEL_MAP.get(selected_model, {})
                        caps = model_cfg.get("capabilities", {})
                        can_think = caps.get("thinking", False)
                        
                        if can_think and on_thinking:
                            async def _think_cb(payload: Any):
                                if on_thinking:
                                    if isinstance(payload, dict):
                                        thinking_payload = payload
                                    else:
                                        thinking_payload = {"title": str(payload)}
                                    await on_thinking(councilor_id, "stage2", thinking_payload, selected_model)
                                    
                            response = await stream_model(
                                selected_model, 
                                current_messages, 
                                on_thinking=_think_cb, 
                                timeout=timeout, 
                                max_output_tokens=max_tokens,
                                tools=THINKING_TOOL_DEF
                            )
                        else:
                            response = await query_model(selected_model, current_messages, timeout=timeout, max_output_tokens=max_tokens)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                response = {"error": True, "content": str(e)}

            if selected_model not in attempted_models:
                attempted_models.append(selected_model)

            # Validation
            success = False
            parsed_result = None
            should_retry_json = False
            
            attempt_res = {
                "judge_councilor_id": councilor_id,
                "judge_councilor_name": councilor_name,
                "model": response.get("model", selected_model) if response else selected_model,
                "raw_response": response.get("content", "") if response else ""
            }
            
            if response and not response.get("error"):
                # Network OK
                health_manager.update_status(selected_model, True, source="runtime")
                
                parsed, error = _parse_ranking_response(attempt_res["raw_response"], expected_anon_ids)
                if error:
                    last_error = f"JSON/Usage Error ({selected_model}): {error}"
                    should_retry_json = True
                else:
                    attempt_res.update(parsed)
                    attempt_res["fallback_used"] = (selected_model != candidates[0])
                    parsed_result = attempt_res
                    success = True
            else:
                # Network Fail
                err_msg = response.get('content') if response else 'No response'
                last_error = f"Network Error ({selected_model}): {err_msg}"
                status_code = response.get('status_code') if response else None 
                health_manager.update_status(selected_model, False, err_msg, status_code, source="runtime")
                excluded_models.add(selected_model)
                break # Break inner, next candidate
                
            if success:
                return parsed_result
                
            if should_retry_json:
                if logic_attempt == 0:
                   # Repair
                   retry_msg = {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "error": last_error,
                                "instruction": f"Your previous reply was invalid. Reply again with ONLY the JSON object. You must include these anon_ids exactly once: {expected_anon_ids}",
                            },
                            ensure_ascii=False,
                        ),
                    }
                   # Append to NEW list to avoid mutating shared `messages`
                   current_messages = messages + [retry_msg]
                else:
                   # 2nd fail
                   excluded_models.add(selected_model)
                   break
            
    # Fail
    return {
        "judge_councilor_id": councilor_id,
        "model": default_model,
        "error": {
            "code": "EXECUTION_ERROR",
            "message": str(last_error or "All candidates failed"),
            "retryable": True
        },
        "attempted_models": attempted_models
    }


async def stage2_collect_rankings(
    user_query: str, 
    stage1_results: List[Dict[str, Any]], 
    councilors: List[Dict[str, Any]],
    on_result: Optional[Callable[[Dict[str, Any]], Any]] = None,
    on_thinking: Optional[Callable[[str, str, Any, str], Any]] = None,
    enable_thinking: bool = True
) -> Dict[str, Any]:
    """
    Stage 2: Each model ranks the anonymized responses.
    Strict concurrency, deadlines, and candidate validation.
    """
    
    # Phase 1: Filter Valid Candidates
    valid_candidates = [r for r in stage1_results if r.get("status") == "ok"]
    
    base_response = {
        "skipped": False,
        "skipped_reason": None,
        "reviews": [],
        "anon_map": {},
        "judge_failures": []
    }

    if len(valid_candidates) < 2:
        base_response["skipped"] = True
        base_response["skipped_reason"] = "insufficient_candidates" # Covers 0 or 1
        return base_response

    # Phase 2: Execution
    candidates, anon_map_ids = _build_stage2_candidates(valid_candidates)
    base_response["anon_map"] = anon_map_ids
    
    # Should not happen given check above, but consistency
    if len(candidates) < 2:
         base_response["skipped"] = True
         base_response["skipped_reason"] = "insufficient_candidates"
         return base_response
         
    anon_ids = [card["anon_id"] for card in candidates]
    
    semaphore = asyncio.Semaphore(DEFAULT_CONCURRENCY_STAGE2)
    tasks = []
    
    # We need to map tasks to models for failure accounting
    # Use councilor objects to get timeouts
    for councilor in councilors:
        model = councilor["model"]
        limits = councilor.get("stage_limits", {}).get("stage2", {})
        timeout = limits.get("timeout", DEFAULT_STAGE2_TIMEOUT)
        
        t = asyncio.create_task(
            _collect_single_ranking_bounded(
                semaphore, 
                councilor["id"],
                councilor.get("name"),
                councilor, # Pass full councilor object to access persona/rubric
                model, 
                user_query, 
                candidates, 
                anon_ids, 
                timeout,
                on_thinking,
                enable_thinking
            )
        )
        tasks.append((councilor, t))
        
    raw_tasks = [t for _, t in tasks]
    
    # Deadline Logic
    completed_results = []
    
    if STAGE2_DEADLINE:
        done, pending = await asyncio.wait(raw_tasks, timeout=STAGE2_DEADLINE)
        for p in pending:
            p.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
            
        for councilor, task in tasks:
            if task in done:
                try:
                    res = task.result()
                    completed_results.append(res)
                    if on_result:
                        if asyncio.iscoroutinefunction(on_result):
                            await on_result(res)
                        else:
                            on_result(res)
                except Exception as e:
                    err = {
                        "judge_councilor_id": councilor["id"],
                        "model": councilor["model"],
                        "error": str(e) # Simplified error structure for Stage2 raw list
                    }
                    completed_results.append(err)
                    if on_result:
                        if asyncio.iscoroutinefunction(on_result):
                             await on_result(err)
                        else:
                             on_result(err)
            else:
                 completed_results.append({
                     "judge_councilor_id": councilor["id"],
                     "model": councilor["model"],
                     "error": {
                         "code": "STAGE_DEADLINE",
                         "message": "Stage 2 deadline exceeded"
                     }
                 })
    else:
        # Callback logic for loose mode
        if on_result:
             for f in asyncio.as_completed(raw_tasks):
                 try:
                     res = await f
                     if asyncio.iscoroutinefunction(on_result):
                         await on_result(res)
                     else:
                         on_result(res)
                 except: pass # handled in gather below

        results = await asyncio.gather(*raw_tasks, return_exceptions=True)
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                completed_results.append({
                    "judge_councilor_id": councilors[i]["id"],
                    "model": councilors[i]["model"],
                    "error": str(res)
                })
            else:
                completed_results.append(res)
    
    reviews = []
    judge_failures = []

    for res in completed_results:
        # Check if internal error field exists or if it's a bare exception string (from catch-all)
        if isinstance(res.get("error"), (str, dict)) or res.get("error") is True:
             judge_failures.append({
                "judge_councilor_id": res.get("judge_councilor_id") or res.get("model"),
                "model": res.get("model"),
                "error": res.get("error") if isinstance(res.get("error"), dict) else {
                    "code": "JUDGE_EXECUTION_ERROR",
                    "message": str(res.get("error")),
                    "retryable": False
                }
            })
        else:
             reviews.append(res)

    base_response["judge_failures"] = judge_failures

    if not reviews:
        base_response["skipped"] = True
        base_response["skipped_reason"] = "all_judges_failed"
    else:
        base_response["skipped"] = False
        base_response["reviews"] = reviews

    return base_response


async def stage3_synthesize_final(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_result: Dict[str, Any], # Changed to Dict
    chairman: Dict[str, Any],
    on_thinking: Optional[Callable[[str, str, Any, str], Any]] = None,
    on_answer_delta: Optional[Callable[[str], Any]] = None,
    enable_thinking: bool = True
) -> Dict[str, Any]:
    persona = fetch_persona(PERSONA_CACHE, chairman.get("persona_path", ""))
    stage_limits = chairman.get("stage_limits", {}).get("stage3", {})
    timeout = stage_limits.get("timeout", 90.0)
    max_tokens = stage_limits.get("max_output_tokens", 900)

    # Filter Valid Stage 1 inputs
    valid_stage1 = [r for r in stage1_results if r.get("status") == "ok"]
    
    if not valid_stage1:
        return {
            "status": "failed",
            "model": "system",
            "response": "所有模型在第一阶段均未能生成有效回答，无法进行总结。",
            "error": {"code": "ALL_STAGE1_FAILED", "message": "No valid stage 1 answers"}
        }

    stage1_text = "\n\n".join(
        [
            f"{result.get('councilor_name')} ({result.get('model')}):\n{result.get('answer_markdown')}"
            for result in valid_stage1
        ]
    )

    stage2_text = ""
    skipped_reason_map = {
        "all_stage1_failed": "所有模型第一阶段均失败（理论上不应运行到此）",
        "insufficient_candidates": "有效候选方案少于2个，无需排序",
        "all_judges_failed": "所有评审员在排序阶段均运行失败"
    }

    if stage2_result.get("skipped"):
        reason_code = stage2_result.get("skipped_reason")
        reason_text = skipped_reason_map.get(reason_code, reason_code)
        stage2_text = f"（阶段二已跳过：{reason_text}，请直接基于阶段一回答进行总结）"
    else:
        # Process Reviews
        reviews_text_parts = []
        for result in stage2_result.get("reviews", []):
            ranking_summary = " > ".join(result.get("ranking", []))
            scores_summary = result.get("scores") if result.get("scores") else "None"
            rationale_summary = result.get("rationale") if result.get("rationale") else "None"
            reviews_text_parts.append(
                f"Model: {result['model']}\nRanking: {ranking_summary}\nScores: {scores_summary}\nRationale: {rationale_summary}"
            )
        stage2_text = "\n\n".join(reviews_text_parts)

    system_prompt = (
        f"{persona}\n"
        f"{chairman.get('judge_system_prompt', '')}\n"
        "保持简洁、公允，无需自我介绍或复述问题。"
    )

    if enable_thinking:
        system_prompt += (
            "\n\nIMPORTANT: You MUST call the `emit_thinking` tool MULTIPLE times (3-5 times) "
            "before your final synthesis to explain how you are weighing the different opinions."
        )

    chairman_prompt = f"""
用户问题：{user_query}

阶段一答案与评审卡：
{stage1_text}

阶段二匿名排序与打分：
{stage2_text}

请综合给出精炼的最终回答，可列出关键行动要点与风险提示，保持原问题语言。
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": chairman_prompt},
    ]

    candidates = get_candidates(chairman)
    excluded_models = set()
    attempted_models = []
    
    last_error = None

    while True: # Outer Loop: Candidates
        selected_model = select_best_model(candidates, excluded_models)
        if not selected_model:
            break
            
        model_sem = await model_concurrency_manager.get_semaphore(selected_model)
        
        # Inner Loop: Retry (Simple retries for Stage 3, usually logic errors are rare here as it's freeform text, 
        # but network errors are common. JSON not strict here.)
        # Actually Stage 3 output is text, no JSON guard.
        # So we just try once or retry network?
        # Let's do 2 attempts for network robustness.
        
        for attempt in range(2):
            response = None
            try:
                # Double Locking
                # No stage limit semaphore passed to stage3? 
                # stage3_synthesize_final is usually run alone.
                # But we should respect model concurrency.
                async with model_sem:
                    # Check Capabilities
                    model_cfg = GLOBAL_MODEL_MAP.get(selected_model, {})
                    caps = model_cfg.get("capabilities", {})
                    can_think = caps.get("thinking", False)

                    use_tools = enable_thinking and can_think and on_thinking
                    use_stream = use_tools or on_answer_delta

                    async def _content_cb(delta: str):
                        if not on_answer_delta:
                            return
                        if asyncio.iscoroutinefunction(on_answer_delta):
                            await on_answer_delta(delta)
                        else:
                            on_answer_delta(delta)

                    if use_stream:
                        async def _think_cb(payload: Any):
                            if not use_tools or not on_thinking:
                                return
                            if isinstance(payload, dict):
                                thinking_payload = payload
                            else:
                                thinking_payload = {"title": str(payload)}
                            await on_thinking(chairman["id"], "stage3", thinking_payload, selected_model)

                        response = await stream_model(
                            selected_model,
                            messages,
                            on_thinking=_think_cb if use_tools else None,
                            on_content=_content_cb if on_answer_delta else None,
                            timeout=timeout,
                            max_output_tokens=max_tokens,
                            tools=THINKING_TOOL_DEF if use_tools else None
                        )
                    else:
                        response = await query_model(
                            selected_model, messages, timeout=timeout, max_output_tokens=max_tokens
                        )
            except Exception as e:
                response = {"error": True, "content": str(e)}

            if selected_model not in attempted_models:
                attempted_models.append(selected_model)

            if response and not response.get('error'):
                 health_manager.update_status(selected_model, True, source="runtime")
                 
                 actual_model = response.get("model", selected_model)
                 return {
                    "status": "ok",
                    "model": actual_model, 
                    "response": response.get("content", ""),
                    "attempted_models": attempted_models,
                    "fallback_used": (selected_model != candidates[0])
                 }
            else:
                 error_msg = response.get("content") if response else "No response from chairman"
                 last_error = f"{selected_model}: {error_msg}"
                 status_code = response.get('status_code') if response else None
                 health_manager.update_status(selected_model, False, last_error, status_code, source="runtime")
                 
                 # Network Retry Logic
                 if attempt == 0 and is_retryable_error(response):
                     retry_after = get_retry_after(response)
                     delay = retry_after if retry_after else 1.0
                     await asyncio.sleep(delay)
                     continue # Retry inner
                 else:
                     # 2nd fail or fatal
                     excluded_models.add(selected_model)
                     break # Break inner
                     
    return {
        "status": "failed",
        "model": chairman["model"],
        "response": f"最终总结生成失败: {str(last_error)}",
        "error": {"code": "CHAIRMAN_FAILED", "message": str(last_error)},
        "attempted_models": attempted_models
    }


def calculate_aggregate_rankings(
    stage2_results: List[Dict[str, Any]], anon_to_councilor: Dict[str, str]
) -> List[Dict[str, Any]]:
    from collections import defaultdict
    model_positions = defaultdict(list)

    for ranking in stage2_results:
        ranking_list = ranking.get("ranking")
        if not ranking_list or ranking.get("error"):
            continue

        for position, anon_id in enumerate(ranking_list, start=1):
            if anon_id in anon_to_councilor:
                model_name = anon_to_councilor[anon_id]
                model_positions[model_name].append(position)

    aggregate = []
    for model, positions in model_positions.items():
        if positions:
            avg_rank = sum(positions) / len(positions)
            aggregate.append(
                {
                    "councilor_id": model,
                    "average_rank": round(avg_rank, 2),
                    "rankings_count": len(positions),
                }
            )

    aggregate.sort(key=lambda x: x["average_rank"])
    return aggregate


def calculate_conversation_title_prompt(user_query: str) -> str:
     return f"""Generate a very short title (3-5 words maximum) that summarizes the following question.
The title should be concise and descriptive. Do not use quotes or punctuation in the title.
IMPORTANT: Generate the title in the SAME LANGUAGE as the question below.

Question: {user_query}

Title:"""


async def generate_conversation_title(user_query: str) -> str:
    title_prompt = calculate_conversation_title_prompt(user_query)
    messages = [{"role": "user", "content": title_prompt}]

    try:
        response = await query_model("kwaipilot/kat-coder-pro:free", messages, timeout=30.0)

        if response is None:
            return "New Conversation"

        title = response.get("content", "New Conversation").strip()
        title = title.strip("\"'")
        if len(title) > 50:
            title = title[:47] + "..."

        return title
    except Exception:
        return "New Conversation"


async def run_full_council(
    user_query: str, 
    councilors: List[Dict[str, Any]], 
    chairman: Dict[str, Any],
    on_thinking: Optional[Callable[[str, str, Any, str], Any]] = None,
    enable_thinking: bool = True
) -> Tuple[List, Dict, Dict, Dict]:
    # Stage 1
    stage1_results = await stage1_collect_responses(
        user_query, councilors, on_thinking=on_thinking, enable_thinking=enable_thinking
    )

    # Use active models for ranking (using councilors models)
    # Note: stage2_collect_rankings now expects full councilor objects to read timeouts
    
    # Stage 2 (Unified Dict)
    stage2_result = await stage2_collect_rankings(
        user_query, stage1_results, councilors, on_thinking=on_thinking, enable_thinking=enable_thinking
    )

    # Aggregate Rankings (if not skipped)
    aggregate_rankings = []
    if not stage2_result.get("skipped"):
         aggregate_rankings = calculate_aggregate_rankings(
            stage2_result.get("reviews", []), stage2_result.get("anon_map", {})
        )

    # Stage 3
    stage3_result = await stage3_synthesize_final(
        user_query, stage1_results, stage2_result, chairman, on_thinking=on_thinking, enable_thinking=enable_thinking
    )

    metadata = {
        "anon_to_councilor": stage2_result.get("anon_map", {}),
        "aggregate_rankings": aggregate_rankings,
    }

    return stage1_results, stage2_result, stage3_result, metadata
