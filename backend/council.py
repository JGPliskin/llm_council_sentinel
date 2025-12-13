"""3-stage LLM Council orchestration."""

from typing import List, Dict, Any, Tuple, Optional
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openrouter import query_models_parallel, query_model


async def stage1_collect_responses(user_query: str, council_models: List[str]) -> List[Dict[str, Any]]:
    """
    Stage 1: Collect individual responses from all council models.

    Args:
        user_query: The user's question
        council_models: List of active council models

    Returns:
        List of dicts with 'model' and 'response' keys
    """
    messages = [
        {
            "role": "system",
            "content": "You must always respond in the exact same language as the user's question. Never translate or switch languages.",
        },
        {"role": "user", "content": user_query},
    ]

    # Query all models in parallel
    responses = await query_models_parallel(council_models, messages)

    # Format results
    stage1_results = []
    for model, response in responses.items():
        if response is not None:  # Only include successful responses
            # Use actual model from response if available (handling fallback), otherwise requested model
            actual_model = response.get("model", model)
            stage1_results.append(
                {"model": actual_model, "response": response.get("content", "")}
            )

    return stage1_results


def _build_judge_cards(stage1_results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, str]], Dict[str, str]]:
    """Create anonymized judge cards for ranking."""

    judge_cards = []
    anon_to_councilor = {}

    for idx, result in enumerate(stage1_results, start=1):
        anon_id = f"anon_{idx}"
        anon_to_councilor[anon_id] = result["model"]
        judge_cards.append(
            {
                "anon_id": anon_id,
                # Pass only anonymized payloads to the judges
                "answer": result["response"],
            }
        )

    return judge_cards, anon_to_councilor


def _build_ranking_messages(user_query: str, judge_cards: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Build messages instructing judges to return structured JSON rankings."""

    ranking_instructions = {
        "task": "rank_responses",
        "question": user_query,
        "judge_cards": judge_cards,
        "response_format": {
            "ranking": "Array of anon_id strings ordered best to worst (required)",
            "scores": "Optional object mapping anon_id to integer 1-10",
            "rationale": "Optional explanation in any format",
        },
    }

    messages = [
        {
            "role": "system",
            "content": "Always reply with a single JSON object and nothing else.",
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
        data = json.loads(response_text)
    except Exception as exc:  # noqa: BLE001
        return None, f"Invalid JSON: {exc}"

    if not isinstance(data, dict):
        return None, "Top-level response must be a JSON object"

    ranking = data.get("ranking")
    if not isinstance(ranking, list) or not all(isinstance(item, str) for item in ranking):
        return None, "`ranking` must be an array of anon_id strings"

    # Validate coverage and duplicates
    expected_set = set(expected_anon_ids)
    ranking_set = set(ranking)
    if ranking_set != expected_set or len(ranking) != len(expected_anon_ids):
        return None, "`ranking` must include each anon_id exactly once"

    scores = data.get("scores", {})
    filtered_scores = {}
    if isinstance(scores, dict):
        for anon_id, score in scores.items():
            if (
                anon_id in expected_set
                and isinstance(score, int)
                and 1 <= score <= 10
            ):
                filtered_scores[anon_id] = score

    rationale = data.get("rationale")

    parsed = {
        "ranking": ranking,
        "scores": filtered_scores,
        "rationale": rationale,
    }
    return parsed, None


async def _collect_single_ranking(
    model: str,
    user_query: str,
    judge_cards: List[Dict[str, str]],
    expected_anon_ids: List[str],
) -> Dict[str, Any]:
    """Collect and validate a ranking from a single judge with one retry if needed."""

    messages = _build_ranking_messages(user_query, judge_cards)
    response = await query_model(model, messages)
    attempt_results: Dict[str, Any] = {
        "model": response.get("model", model) if response else model,
        "raw_response": response.get("content", "") if response else "",
    }

    parsed, error = (
        _parse_ranking_response(attempt_results["raw_response"], expected_anon_ids)
        if response
        else (None, "No response received")
    )

    if error:
        # Retry once with stricter reminder
        retry_messages = messages + [
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "error": error,
                        "instruction": "Your previous reply was invalid. Reply again with ONLY the JSON object described earlier. Use the same anon_id values and include each exactly once in `ranking`.",
                    },
                    ensure_ascii=False,
                ),
            }
        ]
        retry_response = await query_model(model, retry_messages)
        attempt_results["retry_raw_response"] = (
            retry_response.get("content", "") if retry_response else ""
        )
        parsed, retry_error = (
            _parse_ranking_response(
                attempt_results.get("retry_raw_response", ""), expected_anon_ids
            )
            if retry_response
            else (None, "No response received on retry")
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
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Stage 2: Each model ranks the anonymized responses.

    Args:
        user_query: The original user query
        stage1_results: Results from Stage 1
        council_models: List of active council models

    Returns:
        Tuple of (rankings list, anon_to_councilor mapping)
    """

    judge_cards, anon_to_councilor = _build_judge_cards(stage1_results)
    anon_ids = [card["anon_id"] for card in judge_cards]

    # Collect rankings sequentially to allow retries per judge
    stage2_results: List[Dict[str, Any]] = []
    for model in council_models:
        result = await _collect_single_ranking(
            model, user_query, judge_cards, anon_ids
        )
        stage2_results.append(result)

    return stage2_results, anon_to_councilor


async def stage3_synthesize_final(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    chairman_model: str,
) -> Dict[str, Any]:
    """
    Stage 3: Chairman synthesizes final response.

    Args:
        user_query: The original user query
        stage1_results: Individual model responses from Stage 1
        stage2_results: Rankings from Stage 2
        chairman_model: The active chairman model identifier

    Returns:
        Dict with 'model' and 'response' keys
    """
    # Build comprehensive context for chairman
    stage1_text = "\n\n".join(
        [
            f"Model: {result['model']}\nResponse: {result['response']}"
            for result in stage1_results
        ]
    )

    stage2_text_parts = []
    for result in stage2_results:
        if result.get("error"):
            stage2_text_parts.append(
                f"Model: {result['model']}\nRanking: ERROR - {result['error']}"
            )
            continue

        ranking_summary = " > ".join(result.get("ranking", []))
        scores_summary = result.get("scores") if result.get("scores") else "None"
        rationale_summary = result.get("rationale") if result.get("rationale") else "None"
        stage2_text_parts.append(
            f"Model: {result['model']}\nRanking: {ranking_summary}\nScores: {scores_summary}\nRationale: {rationale_summary}"
        )

    stage2_text = "\n\n".join(stage2_text_parts)

    chairman_prompt = f"""You are the Chairman of an LLM Council. Multiple AI models have provided responses to a user's question, and then ranked each other's responses.

Original Question: {user_query}

STAGE 1 - Individual Responses:
{stage1_text}

STAGE 2 - Peer Rankings:
{stage2_text}

Your task as Chairman is to synthesize all of this information into a single, comprehensive, accurate answer to the user's original question. Consider:
- The individual responses and their insights
- The peer rankings and what they reveal about response quality
- Any patterns of agreement or disagreement

Now synthesize your answer to the question above."""

    messages = [
        {
            "role": "system",
            "content": f'You must answer in the exact same language as this question: "{user_query}". The responses you see may be in various languages - ignore their languages and focus only on their content. Your synthesized answer must be in the same language as the original question.',
        },
        {"role": "user", "content": chairman_prompt},
    ]

    # Query the chairman model
    response = await query_model(chairman_model, messages)

    if response is None:
        # Fallback if chairman fails
        return {
            "model": "error",
            "response": "Error: Unable to generate final synthesis.",
        }

    # Use actual model from response if available
    actual_model = response.get("model", chairman_model)
    return {"model": actual_model, "response": response.get("content", "")}


def calculate_aggregate_rankings(
    stage2_results: List[Dict[str, Any]], anon_to_councilor: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Calculate aggregate rankings across all models.

    Args:
        stage2_results: Rankings from each model
        anon_to_councilor: Mapping from anon_id to councilor_id

    Returns:
        List of dicts with model name and average rank, sorted best to worst
    """
    from collections import defaultdict

    # Track positions for each model
    model_positions = defaultdict(list)

    for ranking in stage2_results:
        ranking_list = ranking.get("ranking")

        if not ranking_list or ranking.get("error"):
            continue

        for position, anon_id in enumerate(ranking_list, start=1):
            if anon_id in anon_to_councilor:
                model_name = anon_to_councilor[anon_id]
                model_positions[model_name].append(position)

    # Calculate average position for each model
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

    # Sort by average rank (lower is better)
    aggregate.sort(key=lambda x: x["average_rank"])

    return aggregate


async def generate_conversation_title(user_query: str) -> str:
    """
    Generate a short title for a conversation based on the first user message.

    Args:
        user_query: The first user message

    Returns:
        A short title (3-5 words)
    """
    title_prompt = f"""Generate a very short title (3-5 words maximum) that summarizes the following question.
The title should be concise and descriptive. Do not use quotes or punctuation in the title.
IMPORTANT: Generate the title in the SAME LANGUAGE as the question below.

Question: {user_query}

Title:"""

    messages = [{"role": "user", "content": title_prompt}]

    # Use gemini-2.5-flash for title generation (fast and cheap)
    response = await query_model("google/gemini-2.5-flash", messages, timeout=30.0)

    if response is None:
        # Fallback to a generic title
        return "New Conversation"

    title = response.get("content", "New Conversation").strip()

    # Clean up the title - remove quotes, limit length
    title = title.strip("\"'")

    # Truncate if too long
    if len(title) > 50:
        title = title[:47] + "..."

    return title


async def run_full_council(
    user_query: str, council_models: List[str], chairman_model: str
) -> Tuple[List, List, Dict, Dict]:
    """
    Run the complete 3-stage council process.

    Args:
        user_query: The user's question
        council_models: List of active council models
        chairman_model: The active chairman model identifier

    Returns:
        Tuple of (stage1_results, stage2_results, stage3_result, metadata)
    """
    # Stage 1: Collect individual responses
    stage1_results = await stage1_collect_responses(user_query, council_models)

    # If no models responded successfully, return error
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

    # Stage 2: Collect rankings
    stage2_results, anon_to_councilor = await stage2_collect_rankings(
        user_query, stage1_results, council_models
    )

    # Calculate aggregate rankings
    aggregate_rankings = calculate_aggregate_rankings(
        stage2_results, anon_to_councilor
    )

    # Stage 3: Synthesize final answer
    stage3_result = await stage3_synthesize_final(
        user_query, stage1_results, stage2_results, chairman_model
    )

    # Prepare metadata
    metadata = {
        "anon_to_councilor": anon_to_councilor,
        "aggregate_rankings": aggregate_rankings,
    }

    return stage1_results, stage2_results, stage3_result, metadata
