"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"

# Admin Token for protected endpoints
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "secret-token")

# ----------------------------
# Concurrency & Timeouts
# ----------------------------
DEFAULT_CONCURRENCY_STAGE1 = 6
DEFAULT_CONCURRENCY_STAGE2 = 4

# Per-call timeouts (seconds)
DEFAULT_STAGE1_TIMEOUT = 120.0
DEFAULT_STAGE2_TIMEOUT = 180.0

# Stage-level deadlines (seconds). None = Disabled by default.
# Can be enabled if desired (e.g. 180.0, 240.0)
STAGE1_DEADLINE = None
STAGE2_DEADLINE = None

# ----------------------------
# Global Model Pool & Routing
# ----------------------------
GLOBAL_MODEL_POOL = [
    {
        "id": "openai/gpt-oss-20b:free",
        "name": "GPT-OSS 20B (Free)",
        "concurrency_limit": 4,
        "category": "general"
    },
    {
        "id": "tngtech/tng-r1t-chimera:free",
        "name": "TNG R1T Chimera (Free)",
        "concurrency_limit": 3,
        "category": "reasoning"
    },
    {
        "id": "tngtech/deepseek-r1t2-chimera:free",
        "name": "DeepSeek R1T2 Chimera (Free)",
        "concurrency_limit": 3,
        "category": "reasoning"
    },
    {
        "id": "nvidia/nemotron-nano-9b-v2:free",
        "name": "Nemotron Nano 9B (Free)",
        "concurrency_limit": 5,
        "category": "fast"
    },
    {
        "id": "z-ai/glm-4.5-air:free",
        "name": "GLM 4.5 Air (Free)",
        "concurrency_limit": 3,
        "category": "general"
    },
    {
        "id": "amazon/nova-2-lite-v1:free",
        "name": "Amazon Nova 2 Lite (Free)",
        "concurrency_limit": 3,
        "category": "fast"
    },
    {
        "id": "alibaba/tongyi-deepresearch-30b-a3b:free",
        "name": "Tongyi DeepResearch 30B (Free)",
        "concurrency_limit": 2,
        "category": "research"
    },
]

GLOBAL_MODEL_MAP = {m["id"]: m for m in GLOBAL_MODEL_POOL}

# Councilor definitions with personas and stage limits
COUNCILORS = [
    {
        "id": "immanuel_kant",
        "name": "康德",
        "model": "openai/gpt-oss-20b:free",
        "model_candidates": [
            "openai/gpt-oss-20b:free",
            "tngtech/tng-r1t-chimera:free",
            "tngtech/deepseek-r1t2-chimera:free",
            "nvidia/nemotron-nano-9b-v2:free",
            "z-ai/glm-4.5-air:free",
        ],
        "avatar": "🧠",
        "persona_path": "backend/personas/immanuel_kant.md",
        "judge_persona_path": "backend/personas/immanuel_kant_judge.md",
        "judge_system_prompt": (
            "保持冷静的政策分析腔调，重视结构化推理与证据透明度，"
            "在比较选项时更关注长期稳健性而非短期噱头。"
        ),
        "stage_limits": {
            "stage1": {"max_output_tokens": 800, "timeout": DEFAULT_STAGE1_TIMEOUT},
            "stage2": {"max_output_tokens": 360, "timeout": 75.0},  # Custom overrides can remain
        },
    },
    {
        "id": "donald_trump",
        "name": "特朗普",
        "model": "openai/gpt-oss-20b:free",
        "model_candidates": [
            "openai/gpt-oss-20b:free",
            "tngtech/tng-r1t-chimera:free",
            "tngtech/deepseek-r1t2-chimera:free",
            "nvidia/nemotron-nano-9b-v2:free",
            "z-ai/glm-4.5-air:free",
        ],
        "avatar": "🧱",
        "persona_path": "backend/personas/donald_trump.md",
        "judge_persona_path": "backend/personas/donald_trump_judge.md",
        "judge_system_prompt": (
            "以一线工程复盘的语气点评，突出可执行性、风险隔离与资源约束，"
            "避免夸张修辞，保持克制、精确。"
        ),
        "stage_limits": {
            "stage1": {"max_output_tokens": 820, "timeout": DEFAULT_STAGE1_TIMEOUT},
            "stage2": {"max_output_tokens": 360, "timeout": 75.0},
        },
    },
    {
        "id": "hideo_kojima",
        "name": "小岛秀夫",
        "model": "openai/gpt-oss-20b:free",
        "model_candidates": [
            "openai/gpt-oss-20b:free",
            "tngtech/tng-r1t-chimera:free",
            "tngtech/deepseek-r1t2-chimera:free",
            "nvidia/nemotron-nano-9b-v2:free",
            "z-ai/glm-4.5-air:free",
        ],
        "avatar": "🎮",
        "persona_path": "backend/personas/hideo_kojima.md",
        "judge_persona_path": "backend/personas/hideo_kojima_judge.md",
        "judge_system_prompt": (
            "保持学术审慎与可验证性，强调论据来源、假设条件与潜在偏误，"
            "用简洁中文表达，避免抒情或模板化寒暄。"
        ),
        "stage_limits": {
            "stage1": {"max_output_tokens": 820, "timeout": DEFAULT_STAGE1_TIMEOUT},
            "stage2": {"max_output_tokens": 360, "timeout": 75.0},
        },
    },
]

CHAIRMAN = {
    "id": "chairman",
    "name": "共识主席",
    "model": "amazon/nova-2-lite-v1:free",
    "model_candidates": [
        "amazon/nova-2-lite-v1:free",
        "alibaba/tongyi-deepresearch-30b-a3b:free",
        "openai/gpt-oss-20b:free",
        "tngtech/tng-r1t-chimera:free",
        "tngtech/deepseek-r1t2-chimera:free",
        "nvidia/nemotron-nano-9b-v2:free",
        "z-ai/glm-4.5-air:free",
    ],
    "avatar": "🪶",
    "persona_path": "backend/personas/chairman.md",
    "judge_system_prompt": (
        "以平实、公允的口吻综合各方论证，突出共识与冲突点，"
        "优先给出清晰、可落地的建议。"
    ),
    "stage_limits": {
        "stage3": {"max_output_tokens": 900, "timeout": 90.0},
    },
}

COUNCIL_SIZE = 3

COUNCILOR_MAP = {c["id"]: c for c in COUNCILORS}

# ----------------------------
# Health Check & Circuit Breaker
# ----------------------------
HEALTH_TTL_SECONDS = 3600
REFRESH_COOLDOWN_SECONDS = 60
FAILURE_THRESHOLD = 2
BACKOFF_SECONDS = [120, 300, 900, 3600]
HEALTH_STARTUP_CHECK = False
PROBE_TIMEOUT_SECONDS = 25.0
HEALTH_PROBE_CONCURRENCY = 4

# Error Classification
HARD_FAILURE_CODES = {401, 403, 404}
HARD_FAILURE_PATTERNS = [
    "does not exist",
    "not found",
    "permission denied",
    "unauthorized",
    "disabled",
]
