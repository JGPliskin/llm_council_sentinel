"""3-stage LLM Council orchestration with persona-driven prompts."""

from typing import List, Dict, Any, Tuple, Optional
import json
import asyncio
import re
import sys
import os

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openrouter import query_model
from persona_loader import fetch_persona

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


async def _request_stage1(councilor: Dict[str, Any], user_query: str) -> Optional[Dict[str, Any]]:
    persona = fetch_persona(PERSONA_CACHE, councilor.get("persona_path", ""))
    stage_limits = councilor.get("stage_limits", {}).get("stage1", {})
    timeout = stage_limits.get("timeout", 90.0)
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
        "    \"judge_card\": {\n"
        "      \"stance\": <string>,\n"
        "      \"core_reasons\": <list, 至少2条>,\n"
        "      \"assumptions\": <list>,\n"
        "      \"risks\": <list>,\n"
        "      \"actionables\": <list>\n"
        "    }\n"
        "  }\n"
        "- 列表每项不超过50个中文字符。\n"
        "- judge_card 整体序列化长度需<=600字符，若超出请合并/抽象信息后再压缩，不要生硬截断。"
    )

    user_message = (
        f"用户问题：{user_query}\n"
        "请依据 persona 直接作答，并填充 judge_card。"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    try:
        response = await query_model(
            councilor["model"], messages, timeout=timeout, max_output_tokens=max_tokens
        )
        if response is None:
            raise ValueError("No response from model (timeout or network error)")

        raw_text = response.get("content", "")

        for attempt in range(2):
            try:
                parsed = parse_stage1_json(raw_text)
                judge_card = enforce_judge_card_constraints(parsed.get("judge_card", {}))
                parsed["judge_card"] = judge_card
                parsed["councilor_id"] = parsed.get("councilor_id") or councilor["id"]
                parsed["answer_markdown"] = parsed.get("answer_markdown", "").strip()
                parsed["model"] = response.get("model", councilor["model"])
                parsed["councilor_name"] = councilor.get("name")
                parsed["status"] = "ok"
                return parsed
            except Exception:
                if attempt == 1:
                    break
                repair_prompt = (
                    "上一轮输出未提供可解析的 JSON，请直接输出符合约束的 JSON 对象，"
                    "不要添加多余文字或代码块。确保 core_reasons 至少两条、列表项<=50字、judge_card 长度<=600。"
                )
                messages.append({"role": "user", "content": repair_prompt})
                response = await query_model(
                    councilor["model"],
                    messages,
                    timeout=timeout,
                    max_output_tokens=max_tokens,
                )
                if response is None:
                     raise ValueError("No response from model on retry")
                raw_text = response.get("content", "")

        raise ValueError("Failed to parse JSON after retries")

    except Exception as e:
        # Strict error schema return
        return {
            "councilor_id": councilor["id"],
            "councilor_name": councilor.get("name"),
            "model": councilor["model"],
            "status": "failed",
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
                "retryable": True
            },
            "answer_markdown": "",
            # judge_card is omitted on failure
        }


async def stage1_collect_responses(
    user_query: str, councilors: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Stage 1: Collect initial responses from all councilors."""
    tasks = [_request_stage1(c, user_query) for c in councilors]
    results = await asyncio.gather(*tasks)
    # Collect all responses including failures, do not filter None
    return list(results)


def _build_judge_cards(stage1_results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """Create anonymized judge cards for ranking. Only distinct valid results should be passed here."""
    judge_cards = []
    anon_to_councilor = {}

    for idx, result in enumerate(stage1_results, start=1):
        if result.get("status") != "ok":
            continue
            
        anon_id = f"anon_{idx}"
        # We map anon_id to model name for display usually
        model_name = result.get("model", "unknown-model") 
        councilor_name = result.get("councilor_name") or model_name
        
        anon_to_councilor[anon_id] = f"{councilor_name} ({model_name})"

        judge_cards.append(
            {
                "anon_id": anon_id,
                "payload": result["judge_card"]
            }
        )

    return judge_cards, anon_to_councilor


def _build_ranking_messages(user_query: str, judge_cards: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Build messages instructing judges to return structured JSON rankings."""
    # Revised: Update requirements
    ranking_instructions = {
        "task": "rank_responses",
        "question": user_query,
        "judge_cards": judge_cards,
        "response_format": {
            "ranking": "Array of anon_id strings ordered best to worst (required). Include ALL anon_ids exactly once.",
            "scores": "Optional object mapping anon_id to integer 1-10",
            "rationale": "Optional explanation in any format (no length constraints)",
        },
    }

    messages = [
        {
            "role": "system",
            "content": "Always reply with a single JSON object and nothing else. No markdown fences.",
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

    # Revised: Strict coverage and duplicates check
    ranking_strs = [str(x) for x in ranking]
    if len(set(ranking_strs)) != len(ranking_strs):
        return None, "Duplicate anon_ids in ranking"
    
    expected_set = set(expected_anon_ids)
    ranking_set = set(ranking_strs)
    
    if ranking_set != expected_set:
        missing = sorted(list(expected_set - ranking_set))
        extra = sorted(list(ranking_set - expected_set))
        return None, f"Ranking mismatch. Missing: {missing}, Extra: {extra}"

    # Revised: Loose score validation (ignore invalid, don't fail)
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
                    pass # Ignore invalid scores

    rationale = data.get("rationale")

    parsed = {
        "ranking": ranking_strs,
        "scores": filtered_scores,
        "rationale": rationale,
    }
    return parsed, None


async def _collect_single_ranking(
    model: str,
    user_query: str,
    judge_cards: List[Dict[str, Any]],
    expected_anon_ids: List[str],
) -> Dict[str, Any]:
    """Collect and validate a ranking from a single judge with one retry if needed."""
    messages = _build_ranking_messages(user_query, judge_cards)
    response = await query_model(model, messages)
    
    # Handle response failure
    if not response:
        return {"model": model, "error": "No response from model"}

    attempt_results: Dict[str, Any] = {
        "model": response.get("model", model),
        "raw_response": response.get("content", ""),
    }

    parsed, error = _parse_ranking_response(attempt_results["raw_response"], expected_anon_ids)

    if error:
        # Retry once with stricter reminder
        retry_messages = messages + [
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "error": error,
                        "instruction": f"Your previous reply was invalid. Reply again with ONLY the JSON object. You must include these anon_ids exactly once: {expected_anon_ids}",
                    },
                    ensure_ascii=False,
                ),
            }
        ]
        retry_response = await query_model(model, retry_messages)
        if not retry_response:
             attempt_results["error"] = "No response on retry"
             return attempt_results

        attempt_results["retry_raw_response"] = retry_response.get("content", "")
        
        parsed, retry_error = _parse_ranking_response(
            attempt_results.get("retry_raw_response", ""), expected_anon_ids
        )

        if retry_error:
            attempt_results["error"] = retry_error
            return attempt_results

    if parsed is None:
        attempt_results["error"] = error
        return attempt_results

    attempt_results.update(parsed)
    return attempt_results


async def stage2_collect_rankings(
    user_query: str, stage1_results: List[Dict[str, Any]], council_models: List[str]
) -> Dict[str, Any]:
    """
    Stage 2: Each model ranks the anonymized responses.
    Returns Strict Unified Dict.
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

    if len(valid_candidates) == 0:
        base_response["skipped"] = True
        base_response["skipped_reason"] = "all_stage1_failed"
        return base_response

    if len(valid_candidates) == 1:
        base_response["skipped"] = True
        base_response["skipped_reason"] = "insufficient_candidates"
        return base_response

    # Phase 2: Execution
    judge_cards, anon_to_councilor = _build_judge_cards(valid_candidates)
    base_response["anon_map"] = anon_to_councilor
    
    if not judge_cards:
        # Should be covered by valid_candidates check, but safety net
        base_response["skipped"] = True
        base_response["skipped_reason"] = "insufficient_candidates"
        return base_response

    anon_ids = [card["anon_id"] for card in judge_cards]

    tasks = [
         _collect_single_ranking(model, user_query, judge_cards, anon_ids)
         for model in council_models
    ]
    raw_results = await asyncio.gather(*tasks)

    reviews = []
    judge_failures = []

    for res in raw_results:
        if res.get("error"):
            judge_failures.append({
                "judge_councilor_id": res.get("model"), # Using model as ID for now if we don't have mapping
                "model": res.get("model"),
                "error": {
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
        # base_response["reviews"] remains []
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
    
        if response is None:
             raise ValueError("No response from chairman")

        actual_model = response.get("model", chairman["model"])
        return {
            "status": "ok",
            "model": actual_model, 
            "response": response.get("content", "")
        }
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
                    "model": model,
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

    response = await query_model("kwaipilot/kat-coder-pro:free", messages, timeout=30.0)

    if response is None:
        return "New Conversation"

    title = response.get("content", "New Conversation").strip()
    title = title.strip("\"'")
    if len(title) > 50:
        title = title[:47] + "..."

    return title


async def run_full_council(
    user_query: str, councilors: List[Dict[str, Any]], chairman: Dict[str, Any]
) -> Tuple[List, Dict, Dict, Dict]:
    # Stage 1
    stage1_results = await stage1_collect_responses(user_query, councilors)

    # Use active models for ranking (using councilors models)
    council_models = [c["model"] for c in councilors]

    # Stage 2 (Unified Dict)
    stage2_result = await stage2_collect_rankings(
        user_query, stage1_results, council_models
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
