"""3-stage LLM Council orchestration with persona-driven prompts."""

from typing import List, Dict, Any, Tuple, Optional
import sys
import os
import json
import re
import asyncio

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
        # Final fallback: trim from the end while keeping structure
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
    max_tokens = stage_limits.get("max_output_tokens")

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

    response = await query_model(
        councilor["model"], messages, timeout=timeout, max_output_tokens=max_tokens
    )
    if response is None:
        return None

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
            raw_text = "" if response is None else response.get("content", "")

    return None


async def stage1_collect_responses(user_query: str, councilors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tasks = [_request_stage1(councilor, user_query) for councilor in councilors]
    results = await asyncio.gather(*tasks)
    return [res for res in results if res]


def build_anonymized_judge_cards(stage1_results: List[Dict[str, Any]]):
    labels = [chr(65 + i) for i in range(len(stage1_results))]
    label_to_councilor = {
        f"Response {label}": result["councilor_id"] for label, result in zip(labels, stage1_results)
    }
    anonymized_cards = []
    for label, result in zip(labels, stage1_results):
        anonymized_cards.append(
            {
                "label": f"Response {label}",
                "judge_card": result.get("judge_card", {}),
            }
        )
    return anonymized_cards, label_to_councilor


def parse_stage2_json(text: str) -> Dict[str, Any]:
    cleaned = strip_json_fences(text)
    return json.loads(cleaned)


async def _request_stage2(
    councilor: Dict[str, Any],
    user_query: str,
    anonymized_cards: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    judge_persona = fetch_persona(PERSONA_CACHE, councilor.get("judge_persona_path", ""))
    stage_limits = councilor.get("stage_limits", {}).get("stage2", {})
    timeout = stage_limits.get("timeout", 90.0)
    max_tokens = stage_limits.get("max_output_tokens")

    system_prompt = (
        f"{judge_persona}\n"
        f"{councilor.get('judge_system_prompt', '')}\n"
        "你仅可依据提供的匿名 judge_card 进行评估，不可使用原始回答。"
        "保持 persona 语气。输出 JSON，无需代码块：\n"
        "{\n"
        "  \"councilor_id\": <string>,\n"
        "  \"ranking\": [<Response labels 按优先级从好到差>],\n"
        "  \"scores\": [\n"
        "    {\"label\": <Response X>, \"score\": <0-10 number>, \"rationale\": <<=80字>}, ...\n"
        "  ]\n"
        "}\n"
        "保持 JSON 简洁，避免多余描述。"
    )

    cards_text = json.dumps(anonymized_cards, ensure_ascii=False, separators=(",", ":"))
    user_prompt = (
        f"用户问题：{user_query}\n"
        "以下为匿名化的 judge_card 列表：\n"
        f"{cards_text}\n"
        "请输出排序与打分。"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response = await query_model(
        councilor["model"], messages, timeout=timeout, max_output_tokens=max_tokens
    )
    if response is None:
        return None

    raw_text = response.get("content", "")

    for attempt in range(2):
        try:
            parsed = parse_stage2_json(raw_text)
            ranking = parsed.get("ranking") or []
            scores = parsed.get("scores") or []
            # Normalize ranking from scores if missing
            if not ranking and scores:
                ranking = [entry.get("label") for entry in sorted(scores, key=lambda e: float(e.get("score", 0)), reverse=True) if entry.get("label")]
            parsed["ranking"] = [label for label in ranking if label]
            parsed["scores"] = [
                {
                    "label": score.get("label"),
                    "score": float(score.get("score", 0)),
                    "rationale": truncate_item(score.get("rationale", ""), 80),
                }
                for score in scores
                if score.get("label")
            ]
            parsed["councilor_id"] = parsed.get("councilor_id") or councilor["id"]
            parsed["model"] = response.get("model", councilor["model"])
            parsed["councilor_name"] = councilor.get("name")
            return parsed
        except Exception:
            if attempt == 1:
                break
            repair_prompt = (
                "输出无法解析为 JSON，请直接返回符合要求的 JSON，对rationale保持80字内，"
                "不要添加解释或代码围栏。"
            )
            messages.append({"role": "user", "content": repair_prompt})
            response = await query_model(
                councilor["model"],
                messages,
                timeout=timeout,
                max_output_tokens=max_tokens,
            )
            raw_text = "" if response is None else response.get("content", "")

    return None


async def stage2_collect_rankings(
    user_query: str, stage1_results: List[Dict[str, Any]], councilors: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    anonymized_cards, label_to_councilor = build_anonymized_judge_cards(stage1_results)
    tasks = [
        _request_stage2(councilor, user_query, anonymized_cards) for councilor in councilors
    ]
    results = await asyncio.gather(*tasks)
    return [res for res in results if res], label_to_councilor


def calculate_aggregate_rankings(
    stage2_results: List[Dict[str, Any]], label_to_councilor: Dict[str, str]
) -> List[Dict[str, Any]]:
    from collections import defaultdict

    model_positions = defaultdict(list)

    for result in stage2_results:
        ranking = result.get("ranking") or []
        for position, label in enumerate(ranking):
            councilor_id = label_to_councilor.get(label)
            if councilor_id:
                model_positions[councilor_id].append(position + 1)

    aggregate = []
    for councilor_id, positions in model_positions.items():
        average_rank = sum(positions) / len(positions)
        aggregate.append(
            {
                "councilor_id": councilor_id,
                "average_rank": average_rank,
                "rankings_count": len(positions),
            }
        )

    aggregate.sort(key=lambda x: x["average_rank"])
    return aggregate


async def stage3_synthesize_final(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    chairman: Dict[str, Any],
) -> Dict[str, Any]:
    persona = fetch_persona(PERSONA_CACHE, chairman.get("persona_path", ""))
    stage_limits = chairman.get("stage_limits", {}).get("stage3", {})
    timeout = stage_limits.get("timeout", 90.0)
    max_tokens = stage_limits.get("max_output_tokens")

    stage1_text = "\n\n".join(
        [
            f"{result.get('councilor_name')} ({result.get('model')}):\n{result.get('answer_markdown')}\n评审卡: {json.dumps(result.get('judge_card', {}), ensure_ascii=False)}"
            for result in stage1_results
        ]
    )

    stage2_text = "\n\n".join(
        [
            f"{result.get('councilor_name')} 排序: {', '.join(result.get('ranking', []))}\n打分: {json.dumps(result.get('scores', []), ensure_ascii=False)}"
            for result in stage2_results
        ]
    )

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

    response = await query_model(
        chairman["model"], messages, timeout=timeout, max_output_tokens=max_tokens
    )

    if response is None:
        return {
            "model": "error",
            "response": "Error: Unable to generate final synthesis.",
        }

    actual_model = response.get("model", chairman["model"])
    return {"model": actual_model, "response": response.get("content", "")}


def parse_ranking_from_text(ranking_text: str) -> List[str]:
    # Deprecated but kept for compatibility
    matches = re.findall(r"Response [A-Z]", ranking_text)
    return matches


def calculate_conversation_title_prompt(user_query: str) -> str:
    return f"""Generate a very short title (3-5 words maximum) that summarizes the following question.
The title should be concise and descriptive. Do not use quotes or punctuation in the title.
IMPORTANT: Generate the title in the SAME LANGUAGE as the question below.

Question: {user_query}

Title:"""


async def generate_conversation_title(user_query: str) -> str:
    title_prompt = calculate_conversation_title_prompt(user_query)
    messages = [{"role": "user", "content": title_prompt}]

    response = await query_model("google/gemini-2.5-flash", messages, timeout=30.0)

    if response is None:
        return "New Conversation"

    title = response.get("content", "New Conversation").strip()
    title = title.strip("\"'")
    if len(title) > 50:
        title = title[:47] + "..."

    return title


async def run_full_council(
    user_query: str, councilors: List[Dict[str, Any]], chairman: Dict[str, Any]
) -> Tuple[List, List, Dict, Dict]:
    stage1_results = await stage1_collect_responses(user_query, councilors)

    if not stage1_results:
        return (
            [],
            [],
            {
                "model": "error",
                "response": "All models failed to respond. Please try again.",
            },
            {},
        )

    stage2_results, label_to_councilor = await stage2_collect_rankings(
        user_query, stage1_results, councilors
    )

    aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_councilor)

    stage3_result = await stage3_synthesize_final(
        user_query, stage1_results, stage2_results, chairman
    )

    metadata = {
        "label_to_councilor": label_to_councilor,
        "aggregate_rankings": aggregate_rankings,
    }

    return stage1_results, stage2_results, stage3_result, metadata
