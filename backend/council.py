"""3-stage LLM Council orchestration with persona-driven prompts."""

from typing import List, Dict, Any, Tuple, Optional, Callable
import json
import asyncio
import re
import sys
import os
import random
import httpx

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openrouter import query_model
from persona_loader import fetch_persona
from config import (
    DEFAULT_CONCURRENCY_STAGE1,
    DEFAULT_CONCURRENCY_STAGE2,
    DEFAULT_STAGE1_TIMEOUT,
    DEFAULT_STAGE2_TIMEOUT,
    STAGE1_DEADLINE,
    STAGE2_DEADLINE,
    COUNCILOR_MAP,
)
from health import health_manager

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


def truncate_item(text: str, limit: int = 50) -> str:
    if text is None:
        return ""
    text = str(text).strip()
    return text[:limit]


def enforce_judge_card_constraints(judge_card: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {
        "stance": str(judge_card.get("stance", "")).strip(),
        "core_reasons": judge_card.get("core_reasons") or [],
        "assumptions": judge_card.get("assumptions") or [],
        "risks": judge_card.get("risks") or [],
        "actionables": judge_card.get("actionables") or [],
    }

    # Enforce per-item length and minimum core reasons
    normalized["core_reasons"] = [truncate_item(item) for item in normalized["core_reasons"] if str(item).strip()]
    if len(normalized["core_reasons"]) < 2:
        filler = "补充要点：概括主要论据"
        normalized["core_reasons"].append(filler)
        if len(normalized["core_reasons"]) < 2:
            normalized["core_reasons"].append("补充要点：再凝练一条")

    for key in ["assumptions", "risks", "actionables"]:
        items = [truncate_item(item) for item in normalized[key] if str(item).strip()]
        normalized[key] = items

    # Compress to meet 600 char limit if necessary
    serialized = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
    if len(serialized) <= 600:
        return normalized

    def compress_list(values: List[str]) -> List[str]:
        if len(values) <= 1:
            return values
        merged: List[str] = []
        buffer = ""
        for value in values:
            candidate = (buffer + "；" if buffer else "") + value
            if len(candidate) <= 45:
                buffer = candidate
            else:
                if buffer:
                    merged.append(buffer)
                buffer = value[:45]
        if buffer:
            merged.append(buffer)
        return merged

    compressed = normalized.copy()
    for key in ["core_reasons", "assumptions", "risks", "actionables"]:
        compressed[key] = compress_list(compressed[key])

    serialized = json.dumps(compressed, ensure_ascii=False, separators=(",", ":"))
    if len(serialized) > 600:
        list_order = ["actionables", "risks", "assumptions", "core_reasons"]
        while len(serialized) > 600:
            trimmed = False
            for key in list_order:
                if compressed.get(key):
                    compressed[key].pop()
                    trimmed = True
                    break
            if not trimmed:
                break
            serialized = json.dumps(compressed, ensure_ascii=False, separators=(",", ":"))
    return compressed


def parse_stage1_json(text: str) -> Dict[str, Any]:
    cleaned = strip_json_fences(text)
    return json.loads(cleaned)


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


async def _bounded_query(
    semaphore: asyncio.Semaphore,
    query_fn: Callable[..., Any],
    *args,
) -> Dict[str, Any]:
    """
    Execute a query with strict semaphore acquisition per attempt.
    Handles max 2 attempts (1 initial + 1 retry) across both network and logic failures.
    """
    
    last_result = None
    
    # Total attempts = 2
    for attempt in range(2):
        try:
            async with semaphore:
                # Execute the wrapped function (which includes logic + optional internal JSON retry if needed,
                # but here we unify the retry logic so query_fn should perform ONE shot)
                # Actually, to support "Different Prompt on Retry", query_fn needs to know the attempt number or context.
                # However, the requirement is "Total 2 attempts". 
                # So we pass 'attempt' and 'last_result' to query_fn if we want logic inside.
                # Simplification: We move the "query + validate" logic completely inside here? No, too coupled.
                # Better: query_fn handles the API call + Validation. If it returns a "Success" dict, we stop.
                # If it returns a "Failure" dict, we decide to retry.
                
                # To support changing prompts (repair), we can ask query_fn to handle the "make call" part
                # but we need to control the loop here.
                # Let's trust query_fn to do ONE request.
                
                # We need to construct the args potentially differently on retry (repair prompt).
                # This suggests the caller should pass a 'factory' or we handle the logic inline.
                # Given strict requirements, let's keep logic inline in _request_stage1 but bounded here?
                # No, _bounded_query is best as a generic wrapper if we just pass a coroutine.
                # But we can't pass a coroutine because it's already created. We need a factory.
                
                pass # Placeholder for thought, resuming implementation below.
            
            # Since we need to modify args (add repair prompt) on retry, `_bounded_query` is best utilized 
            # as a "Slot Manager". The complexities of "JSON Repair" vs "Network Retry" suggest
            # we should implement the loop inside `_request_stage1` and strictly acquire semaphore there.
            # But the requirement says "Semaphore context manager must wrap the entire retry loop... wait, no, 
            # User said: 'Acquire semaphore per attempt... Release ... before backoff'".
            
            # So, `_bounded_query` isn't generic enough if the prompt changes.
            # I will inline the semaphore usage into `_request_stage1` and `_collect_single_ranking` macros.
            # This is cleaner.
            pass

        except asyncio.CancelledError:
            raise

    return {} # Should not be reached logic-wise if inlined.


# Redefining _request_stage1 to handle the loop + semaphore
async def _request_stage1_bounded(
    semaphore: asyncio.Semaphore,
    councilor: Dict[str, Any],
    user_query: str
) -> Dict[str, Any]:
    
    persona = fetch_persona(PERSONA_CACHE, councilor.get("persona_path", ""))
    stage_limits = councilor.get("stage_limits", {}).get("stage1", {})
    timeout = stage_limits.get("timeout", DEFAULT_STAGE1_TIMEOUT)
    max_tokens = stage_limits.get("max_output_tokens", 800)

    system_prompt = (
        f"{persona}\n\n"
        "严格遵守：\n"
        "- 回答语言需与用户问题保持一致。\n"
        "- 不自我介绍，不复述问题，不写模板化客套。\n"
        "- 用紧凑 Markdown 表达答案，避免空洞铺陈。\n"
        "- 仅返回 JSON，对象格式如下（不要附带说明或代码块）：\n"
        "  {\n"
        "    \"councilor_id\": <string>,\n"
        "    \"answer_markdown\": <string>,\n"
        "    \"answer_summary\": <string, 纯文本摘要, 500字以内>,\n"
        "    \"judge_card\": {\n"
        "      \"stance\": <string>,\n"
        "      \"core_reasons\": <list, 至少2条>,\n"
        "      \"assumptions\": <list>,\n"
        "      \"risks\": <list>,\n"
        "      \"actionables\": <list>\n"
        "    }\n"
        "  }\n"
        "- 列表每项不超过50个中文字符。\n"
        "- judge_card 整体序列化长度需<=600字符，若超出请合并/抽象信息后再压缩，不要生硬截断。\n"
        "- answer_summary 必须是对回答的客观陈述，不包含立场评判，严格控制在500字以内。"
    )

    user_message = (
        f"用户问题：{user_query}\n"
        "请依据 persona 直接作答，并填充 judge_card。"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    last_error = None
    
    for attempt in range(2):
        # 1. Acquire Semaphore & Execute
        response = None
        try:
            async with semaphore:
                # Check cancellation immediately upon entering
                # (although `async with` doesn't pause, `await query_model` does)
                response = await query_model(
                    councilor["model"], messages, timeout=timeout, max_output_tokens=max_tokens
                )
        except asyncio.CancelledError:
            raise # Strict Exit
        except Exception:
            # Should not happen as query_model returns dict, but just in case
            pass

        # 2. Validation Logic
        success = False
        parsed_result = None
        
        should_retry_network = False
        should_retry_json = False
        
        if response and not response.get("error"):
            # Try parsing
            raw_text = response.get("content", "")
            try:
                parsed = parse_stage1_json(raw_text)
                judge_card = enforce_judge_card_constraints(parsed.get("judge_card", {}))
                parsed["judge_card"] = judge_card
                # STRICT: Always overwrite councilor_id with our authoritative ID.
                # Do not trust the model to know its own internal system ID.
                parsed["councilor_id"] = councilor["id"]
                parsed["answer_markdown"] = parsed.get("answer_markdown", "").strip()
                
                # Summary Logic
                am = parsed.get("answer_markdown", "")
                summary = parsed.get("answer_summary", "")
                
                if not summary and am:
                    # Fallback logic: truncate markdown
                    # Remove markdown symbols for cleaner summary if possible (simple approach)
                    # Just truncate for stability
                    summary = am[:500]
                
                # Strict Truncation
                if summary:
                    summary = str(summary)[:500]
                
                parsed["answer_summary"] = summary

                parsed["model"] = response.get("model", councilor["model"])
                parsed["councilor_name"] = councilor.get("name")
                parsed["status"] = "ok"
                parsed_result = parsed
                success = True
                
                # Runtime Health: Success
                # Note: We update status even if parsing failed? No, parsing is logic, not model health.
                # However, model returning bad JSON might be "unhealthy" (degraded)?
                # Spec: "A. Transient ... Network ... B. Determine ... 404".
                # Bad JSON is arguably "execution success, validation failure".
                # Let's count it as success for *connection* health (it replied).
                # So we update success=True immediately if network was fine.
                health_manager.update_status(councilor["model"], True, source="runtime")
                
            except Exception as e:
                # JSON/Validation Failure
                last_error = f"JSON Parse/Validation Error: {str(e)}"
                should_retry_json = True
                # Still consider healthy backend
                health_manager.update_status(councilor["model"], True, source="runtime")
                
        else:
            # Network/API Failure
            last_error = f"Network/API Error: {response.get('content') if response else 'No response'}"
            status_code = response.get('status_code') if response else None
            # Runtime Health: Failure
            health_manager.update_status(councilor["model"], False, last_error, status_code, source="runtime")
            should_retry_network = True

        # 3. Decision
        if success:
            return parsed_result
        
        # If last attempt, we are done
        if attempt == 1:
            break
            
        # 4. Prepare Logic for Next Attempt (if allowed)
        if should_retry_network:
            if not is_retryable_error(response):
                # Fatal error (e.g. 401), stop immediately
                break
            # Backoff for network
            retry_after = get_retry_after(response)
            delay = retry_after if retry_after else random.uniform(0.8, 2.0)
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                raise
            # Messages remain same for network retry

        elif should_retry_json:
            # No sleep needed for logic retry (or maybe tiny yield), but usually it's fine to proceed.
            # User comment: "Exception: JSON-repair retry can reuse the same slot if no backoff is needed (optional)."
            # Implementation: We released slot. We re-acquire. This is safer for fairness.
            
            # Update messages with repair prompt
            repair_prompt = (
                "上一轮输出未提供可解析的 JSON，请直接输出符合约束的 JSON 对象，"
                "不要添加多余文字或代码块。确保 core_reasons 至少两条、列表项<=50字、judge_card 长度<=600。"
            )
            # Remove previous repair attempts if any (though loop is max 2 so simple append works)
            messages.append({"role": "user", "content": repair_prompt})
            
    # If we exited loop without success
    return {
        "councilor_id": councilor["id"],
        "councilor_name": councilor.get("name"),
        "model": councilor["model"],
        "status": "failed",
        "error": {
            "code": "EXECUTION_ERROR",
            "message": str(last_error or "Unknown error"),
            "retryable": True # Marked as retryable for upstream, though we exhausted retries here
        },
        "answer_markdown": "",
    }


async def stage1_collect_responses(
    user_query: str, 
    councilors: List[Dict[str, Any]],
    on_result: Optional[Callable[[Dict[str, Any]], Any]] = None
) -> List[Dict[str, Any]]:
    """Stage 1: Collect initial responses from all councilors with strict control."""
    semaphore = asyncio.Semaphore(DEFAULT_CONCURRENCY_STAGE1)
    
    # Create Tasks
    # We must start them. `asyncio.create_task` schedules them.
    # Note: Using a mapping to track who is who is safer if order matters, 
    # but `gather` preserves order of input tasks.
    tasks = [
        asyncio.create_task(_request_stage1_bounded(semaphore, c, user_query))
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
                 # Note: if on_result was used, this exception might have been swallowed or raised during as_completed loop?
                 # If as_completed raised, we might have missed calling on_result for this one.
                 # Let's ensure strictness: _request_stage1_bounded should NOT raise.
             else:
                 final_results.append(res)
        return final_results


def _build_judge_cards(stage1_results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """Create anonymized judge cards for ranking. Only distinct valid results should be passed here."""
    judge_cards = []
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

        # New Payload Structure: Summary + Card
        payload = {
            "answer_summary": result.get("answer_summary", ""),
            "judge_card": result.get("judge_card", {})
        }

        judge_cards.append(
            {
                "anon_id": anon_id,
                "payload": payload
            }
        )

    return judge_cards, anon_to_councilor_id


def _build_ranking_messages(
    user_query: str, 
    judge_cards: List[Dict[str, Any]],
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
        "3) Allowed top-level fields ONLY: ranking, scores, rationale.\n"
        "4) 'ranking' field is REQUIRED. It must include ALL anon_ids exactly once.\n"
        "5) 'scores' (optional) must be 1-10 integers keyed by anon_id only.\n"
        "6) 'rationale' (optional) must be a string.\n"
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
        "candidates": judge_cards, # Changed key to generic 'candidates' or keep judge_cards? logic used judge_cards.
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

    parsed = {
        "ranking": ranking_strs,
        "scores": filtered_scores,
        "rationale": rationale,
    }
    
    # Strict Key Validation: Subset check
    # Top keys must be subset of allowed
    current_keys = set(data.keys())
    allowed_keys = {"ranking", "scores", "rationale"}
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
    councilor_obj: Dict[str, Any], # Added
    model: str,
    user_query: str,
    judge_cards: List[Dict[str, Any]],
    expected_anon_ids: List[str],
    timeout: float
) -> Dict[str, Any]:
    """Collect ranking with semaphore, retry, and backoff."""
    
    # Fetch Persona & Rubric
    persona_path = councilor_obj.get("judge_persona_path") or councilor_obj.get("persona_path")
    persona_text = fetch_persona(PERSONA_CACHE, persona_path)
    rubric_text = councilor_obj.get("judge_system_prompt", "")
    
    # Limits
    stage_limits = councilor_obj.get("stage_limits", {}).get("stage2", {})
    max_tokens = stage_limits.get("max_output_tokens", 360)

    messages = _build_ranking_messages(user_query, judge_cards, persona_text, rubric_text)
    
    last_error = None
    
    for attempt in range(2):
        # 1. Acquire & Execute
        response = None
        try:
            async with semaphore:
                response = await query_model(model, messages, timeout=timeout, max_output_tokens=max_tokens)
        except asyncio.CancelledError:
            raise
        except Exception:
            pass
            
        # 2. Validation
        success = False
        parsed_result = None
        should_retry_network = False
        should_retry_json = False
        
        attempt_res = {
            "judge_councilor_id": councilor_id,
            "judge_councilor_name": councilor_name,
            "model": response.get("model", model) if response else model,
            "raw_response": response.get("content", "") if response else ""
        }
        
        if response and not response.get("error"):
            parsed, error = _parse_ranking_response(attempt_res["raw_response"], expected_anon_ids)
            if error:
                last_error = f"JSON/Usage Error: {error}"
                should_retry_json = True
                # Logic error but network success
                health_manager.update_status(model, True, source="runtime")
            else:
                attempt_res.update(parsed)
                parsed_result = attempt_res
                success = True
                health_manager.update_status(model, True, source="runtime")
        else:
            last_error = f"Network/API Error: {response.get('content') if response else 'No response'}"
            status_code = response.get('status_code') if response else None
            health_manager.update_status(model, False, last_error, status_code, source="runtime")
            should_retry_network = True
            
        # 3. Decision
        if success:
            return parsed_result
            
        if attempt == 1:
            break
            
        # 4. Retry Setup
        if should_retry_network:
            if not is_retryable_error(response):
                break
            # Backoff
            retry_after = get_retry_after(response)
            delay = retry_after if retry_after else random.uniform(0.8, 2.0)
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                raise
        elif should_retry_json:
            # JSON Repair
            retry_messages = messages + [
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "error": last_error,
                            "instruction": f"Your previous reply was invalid. Reply again with ONLY the JSON object. You must include these anon_ids exactly once: {expected_anon_ids}",
                        },
                        ensure_ascii=False,
                    ),
                }
            ]
            messages = retry_messages
            # Re-acquire semaphore in next loop
            
    # Fail
    return {
        "judge_councilor_id": councilor_id,
        "model": model,
        "error": {
            "code": "EXECUTION_ERROR",
            "message": str(last_error),
            "retryable": True
        }
    }


async def stage2_collect_rankings(
    user_query: str, 
    stage1_results: List[Dict[str, Any]], 
    councilors: List[Dict[str, Any]],
    on_result: Optional[Callable[[Dict[str, Any]], Any]] = None
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
    # Note: _build_judge_cards now returns anon_id -> councilor_id
    judge_cards, anon_map_ids = _build_judge_cards(valid_candidates)
    base_response["anon_map"] = anon_map_ids
    
    # Should not happen given check above, but consistency
    if len(judge_cards) < 2:
         base_response["skipped"] = True
         base_response["skipped_reason"] = "insufficient_candidates"
         return base_response
         
    anon_ids = [card["anon_id"] for card in judge_cards]
    
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
                judge_cards, 
                anon_ids, 
                timeout
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
            f"{result.get('councilor_name')} ({result.get('model')}):\n{result.get('answer_markdown')}\n评审卡: {json.dumps(result.get('judge_card', {}), ensure_ascii=False)}"
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

    try:
        response = await query_model(
            chairman["model"], messages, timeout=timeout, max_output_tokens=max_tokens
        )
    
        if response and not response.get('error'):
             health_manager.update_status(chairman["model"], True, source="runtime")
             
             actual_model = response.get("model", chairman["model"])
             return {
                "status": "ok",
                "model": actual_model, 
                "response": response.get("content", "")
             }
        else:
             error_msg = response.get("content") if response else "No response from chairman"
             status_code = response.get('status_code') if response else None
             health_manager.update_status(chairman["model"], False, error_msg, status_code, source="runtime")
             raise ValueError(error_msg)

    except Exception as e:
        return {
            "status": "failed",
            "model": chairman["model"],
            "response": f"最终总结生成失败: {str(e)}",
            "error": {"code": "CHAIRMAN_FAILED", "message": str(e)}
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
    user_query: str, councilors: List[Dict[str, Any]], chairman: Dict[str, Any]
) -> Tuple[List, Dict, Dict, Dict]:
    # Stage 1
    stage1_results = await stage1_collect_responses(user_query, councilors)

    # Use active models for ranking (using councilors models)
    # Note: stage2_collect_rankings now expects full councilor objects to read timeouts
    
    # Stage 2 (Unified Dict)
    stage2_result = await stage2_collect_rankings(
        user_query, stage1_results, councilors
    )

    # Aggregate Rankings (if not skipped)
    aggregate_rankings = []
    if not stage2_result.get("skipped"):
         aggregate_rankings = calculate_aggregate_rankings(
            stage2_result.get("reviews", []), stage2_result.get("anon_map", {})
        )

    # Stage 3
    stage3_result = await stage3_synthesize_final(
        user_query, stage1_results, stage2_result, chairman
    )

    metadata = {
        "anon_to_councilor": stage2_result.get("anon_map", {}),
        "aggregate_rankings": aggregate_rankings,
    }

    return stage1_results, stage2_result, stage3_result, metadata
