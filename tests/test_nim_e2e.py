"""E2E tests for NIM integration in Stage1/2/3 workflows."""

import pytest
import asyncio
import json
import os
from unittest.mock import AsyncMock, patch, Mock
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from council import (
    stage1_collect_responses,
    _collect_single_ranking_bounded,
    stage3_synthesize_final,
)
from config import COUNCILORS, CHAIRMAN, GLOBAL_MODEL_MAP


# =============================================================================
# Mock helpers
# =============================================================================


def create_mock_llm_response(model, content, thinking_steps=None):
    """Create mock LLM response."""
    response = {
        "content": content,
        "error": False,
        "model": model,
        "provider": "nim" if model.startswith("nim:") else "openrouter",
        "ttft_ms": 1000,
        "tool_calls": [],
    }
    if thinking_steps:
        response["tool_calls"] = thinking_steps
    return response


def create_mock_health_record():
    """Create a mock health record."""
    record = Mock()
    record.get_effective_ttft.return_value = 1000.0
    return record


# =============================================================================
# Pytest fixtures for comprehensive mocking
# =============================================================================


@pytest.fixture
def mock_providers():
    """Mock both NIM and OpenRouter providers."""
    # Create a callable that will be used by both stream_model functions
    call_tracker = {"count": 0, "responses": []}

    async def mock_nim_stream(*args, **kwargs):
        model = kwargs.get("model", args[0] if args else "unknown")
        # Return standard NIM response
        return create_mock_llm_response(
            f"nim:{model}",
            content=f"这是NIM模型 {model} 的回答。",
            thinking_steps=[
                {
                    "id": f"call_{call_tracker['count']}",
                    "function": {
                        "name": "emit_thinking",
                        "arguments": json.dumps(
                            {
                                "bullet_id": str(call_tracker["count"]),
                                "title": "思考步骤",
                                "detail": "NIM思考过程",
                            }
                        ),
                    },
                }
            ],
        )

    async def mock_openrouter_stream(*args, **kwargs):
        model = kwargs.get("model", args[0] if args else "unknown")
        return create_mock_llm_response(
            model, content=f"这是OpenRouter模型 {model} 的回答。"
        )

    with patch("nim.stream_model", new_callable=AsyncMock) as mock_nim:
        mock_nim.side_effect = mock_nim_stream

        with patch("openrouter.stream_model", new_callable=AsyncMock) as mock_or:
            mock_or.side_effect = mock_openrouter_stream

            yield mock_nim, mock_or


@pytest.fixture
def mock_health_with_records():
    """Mock health manager with proper record structure."""
    mock_health = Mock()
    mock_health.get_status.return_value = {"health_status": "healthy"}

    # Create mock records for all models
    records = {}
    for model_id in GLOBAL_MODEL_MAP.keys():
        records[model_id] = create_mock_health_record()
    mock_health._records = records

    return mock_health


# =============================================================================
# Test Stage1 with NIM models
# =============================================================================


class TestStage1WithNIM:
    """Test Stage1 execution using NIM models."""

    @pytest.mark.asyncio
    async def test_stage1_nim_councilor_response(
        self, mock_providers, mock_health_with_records
    ):
        """Stage1: Single councilor using NIM model."""
        councilor = COUNCILORS[0].copy()
        councilor["model_candidates"] = ["nim:deepseek-ai/deepseek-v3.1"]
        councilor["model"] = "nim:deepseek-ai/deepseek-v3.1"

        with patch("council.health_manager", mock_health_with_records):
            results = await stage1_collect_responses(
                user_query="测试问题", councilors=[councilor]
            )

            # Verify response
            assert len(results) == 1
            assert results[0]["status"] == "ok"
            assert "回答" in results[0]["answer_markdown"]
            assert results[0]["model"].startswith("nim:")

    @pytest.mark.asyncio
    async def test_stage1_mixed_providers(
        self, mock_providers, mock_health_with_records
    ):
        """Stage1: Mixed OpenRouter and NIM models."""
        results = await stage1_collect_responses(
            user_query="测试问题",
            councilors=[
                {
                    "id": "c1",
                    "name": "Councilor 1",
                    "model": "xiaomi/mimo-v2-flash:free",
                    "avatar": "🧠",
                },
                {
                    "id": "c2",
                    "name": "Councilor 2",
                    "model": "nim:deepseek-ai/deepseek-v3.1",
                    "avatar": "🧠",
                },
            ],
        )

        # Both should succeed
        assert len(results) == 2
        assert all(r["status"] == "ok" for r in results)
        assert any(r["model"].startswith("nim:") for r in results)

    @pytest.mark.asyncio
    async def test_stage1_nim_with_thinking(
        self, mock_providers, mock_health_with_records
    ):
        """Stage1: NIM model with thinking steps."""
        results = await stage1_collect_responses(
            user_query="测试问题",
            councilors=[
                {
                    "id": "c1",
                    "name": "Councilor 1",
                    "model": "nim:deepseek-ai/deepseek-v3.1",
                    "avatar": "🧠",
                }
            ],
        )

        assert len(results) == 1
        assert results[0]["status"] == "ok"
        assert results[0]["model"] == "nim:deepseek-ai/deepseek-v3.1"


# =============================================================================
# Test Stage2 with NIM models
# =============================================================================


class TestStage2WithNIM:
    """Test Stage2 evaluation using NIM models."""

    @pytest.mark.asyncio
    async def test_stage2_nim_judge(self, mock_providers, mock_health_with_records):
        """Stage2: Single judge using NIM model."""
        stage1_results = [
            {"councilor_id": "c1", "answer_markdown": "回答1", "status": "ok"},
            {"councilor_id": "c2", "answer_markdown": "回答2", "status": "ok"},
        ]

        result = await _collect_single_ranking_bounded(
            semaphore=asyncio.Semaphore(1),
            councilor_id="judge",
            councilor_name="Judge",
            councilor_obj={"id": "judge", "name": "Judge", "judge_persona_path": ""},
            default_model="nim:deepseek-ai/deepseek-v3.1",
            user_query="测试问题",
            candidates=[
                {"anon_id": "anon_1", "payload": {"answer_markdown": "回答1"}},
                {"anon_id": "anon_2", "payload": {"answer_markdown": "回答2"}},
            ],
            expected_anon_ids=["anon_1", "anon_2"],
            timeout=60.0,
            enable_thinking=True,
        )

        # Verify Stage2 response structure
        assert result["judge_councilor_id"] == "judge"
        assert result["model"].startswith("nim:")
        assert "ranking" in result
        assert result["ranking"] == ["anon_1", "anon_2"]

    @pytest.mark.asyncio
    async def test_stage2_nim_with_scores_and_comments(
        self, mock_providers, mock_health_with_records
    ):
        """Stage2: NIM judge with detailed scores and comments."""
        result = await _collect_single_ranking_bounded(
            semaphore=asyncio.Semaphore(1),
            councilor_id="judge1",
            councilor_name="Judge 1",
            councilor_obj={"id": "judge1", "name": "Judge 1", "judge_persona_path": ""},
            default_model="nim:deepseek-ai/deepseek-v3.1",
            user_query="测试问题",
            candidates=[
                {"anon_id": "anon_1", "payload": {"answer_markdown": "方案1"}},
                {"anon_id": "anon_2", "payload": {"answer_markdown": "方案2"}},
                {"anon_id": "anon_3", "payload": {"answer_markdown": "方案3"}},
            ],
            expected_anon_ids=["anon_1", "anon_2", "anon_3"],
            timeout=60.0,
            enable_thinking=True,
        )

        # Check that we got the expected structure
        assert result["judge_councilor_id"] == "judge1"
        # The response should contain ranking, scores, etc.
        assert "ranking" in result or "raw_response" in result


# =============================================================================
# Test Stage3 with NIM models
# =============================================================================


class TestStage3WithNIM:
    """Test Stage3 chairman using NIM models."""

    @pytest.mark.asyncio
    async def test_stage3_chairman_with_nim(
        self, mock_providers, mock_health_with_records
    ):
        """Stage3: Chairman using NIM model."""
        # Prepare stage data
        stage1_results = [
            {
                "councilor_id": "c1",
                "answer_markdown": "方案1的内容",
                "status": "ok",
                "model": "nim:deepseek-ai/deepseek-v3.1",
            }
        ]

        stage2_result = {
            "skipped": False,
            "reviews": [
                {
                    "judge_councilor_id": "judge1",
                    "raw_response": {
                        "ranking": ["anon_1"],
                        "scores": {"anon_1": 8},
                        "rationale": "方案优秀",
                    },
                }
            ],
            "anon_map": {"anon_1": "c1"},
        }

        result = await stage3_synthesize_final(
            user_query="测试问题",
            stage1_results=stage1_results,
            stage2_result=stage2_result,
            chairman=CHAIRMAN,
            on_thinking=None,
            on_answer_delta=None,
            enable_thinking=True,
            fixed_model="nim:deepseek-ai/deepseek-v3.1",
        )

        # Verify chairman response
        assert result["error"] is False
        assert result["model"] == "nim:deepseek-ai/deepseek-v3.1"
        assert "回答" in result["content"] or "综合" in result["content"]


# =============================================================================
# Test provider_rate_limited handling
# =============================================================================


class TestProviderRateLimitedE2E:
    """Test provider_rate_limited triggers in full workflow."""

    @pytest.mark.asyncio
    async def test_all_models_rate_limited(
        self, mock_providers, mock_health_with_records
    ):
        """Stage1: All models provider_rate_limited should return error."""

        # Override mock to return errors
        async def error_response(*args, **kwargs):
            model = kwargs.get("model", args[0] if args else "unknown")
            return {
                "error": True,
                "error_code": "provider_rate_limited",
                "content": "All providers rate limited",
                "model": model,
                "status_code": 429,
                "provider": "nim" if model.startswith("nim:") else "openrouter",
            }

        with patch("nim.stream_model", new_callable=AsyncMock) as mock_nim:
            mock_nim.side_effect = error_response

            with patch("openrouter.stream_model", new_callable=AsyncMock) as mock_or:
                mock_or.side_effect = error_response

                councilor = COUNCILORS[0].copy()
                councilor["model_candidates"] = [
                    "nim:deepseek-ai/deepseek-v3.1",
                    "xiaomi/mimo-v2-flash:free",
                ]

                with patch("council.health_manager", mock_health_with_records):
                    results = await stage1_collect_responses(
                        user_query="测试问题", councilors=[councilor]
                    )

                    # Should fail after exhausting all candidates
                    assert len(results) == 1
                    assert results[0]["status"] == "failed"
                    assert "error" in results[0]


# =============================================================================
# Test mixed OpenRouter/NIM councilors
# =============================================================================


class TestMixedProvidersE2E:
    """Test mixed OpenRouter and NIM providers in full workflow."""

    @pytest.mark.asyncio
    async def test_councilors_use_different_providers(
        self, mock_providers, mock_health_with_records
    ):
        """Councilors can use different providers simultaneously."""
        results = await stage1_collect_responses(
            user_query="测试问题",
            councilors=[
                {
                    "id": "c1",
                    "name": "OpenRouter Councilor",
                    "model": "xiaomi/mimo-v2-flash:free",
                    "avatar": "🧠",
                },
                {
                    "id": "c2",
                    "name": "NIM Councilor",
                    "model": "nim:deepseek-ai/deepseek-v3.1",
                    "avatar": "🧠",
                },
                {
                    "id": "c3",
                    "name": "Another OpenRouter",
                    "model": "nvidia/nemotron-nano-9b-v2:free",
                    "avatar": "🧠",
                },
            ],
        )

        assert len(results) == 3
        assert all(r["status"] == "ok" for r in results)
        # Check that we have mixed providers
        providers = set()
        for r in results:
            if r["model"].startswith("nim:"):
                providers.add("nim")
            else:
                providers.add("openrouter")
        assert "nim" in providers and "openrouter" in providers

    @pytest.mark.asyncio
    async def test_stage2_judges_mixed_providers(
        self, mock_providers, mock_health_with_records
    ):
        """Stage2: Multiple judges using different providers."""
        judge_models = [
            "nim:deepseek-ai/deepseek-v3.1",
            "xiaomi/mimo-v2-flash:free",
            "nim:openai/gpt-oss-120b",
        ]

        results = []
        for i, model in enumerate(judge_models):
            result = await _collect_single_ranking_bounded(
                semaphore=asyncio.Semaphore(1),
                councilor_id=f"judge{i}",
                councilor_name=f"Judge {i}",
                councilor_obj={
                    "id": f"judge{i}",
                    "name": f"Judge {i}",
                    "model_candidates": [model],
                    "judge_persona_path": "",
                },
                default_model=model,
                user_query="测试问题",
                candidates=[
                    {"anon_id": "anon_1", "payload": {"answer_markdown": "回答1"}},
                    {"anon_id": "anon_2", "payload": {"answer_markdown": "回答2"}},
                ],
                expected_anon_ids=["anon_1", "anon_2"],
                timeout=60.0,
                enable_thinking=True,
            )
            results.append(result)

        assert len(results) == 3
        # Verify mixed providers
        nim_count = sum(1 for r in results if r["model"].startswith("nim:"))
        openrouter_count = sum(1 for r in results if not r["model"].startswith("nim:"))
        assert nim_count == 2
        assert openrouter_count == 1


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
