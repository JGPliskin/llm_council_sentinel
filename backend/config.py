"""Configuration for the LLM Council."""

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
        "id": "xiaomi/mimo-v2-flash:free",
        "name": "Mimo V2 Flash (Free)",
        "concurrency_limit": 5,
        "category": "fast",
        "capabilities": {"thinking": True, "mode": "standard"},
    },
    {
        "id": "nvidia/nemotron-nano-9b-v2:free",
        "name": "Nemotron Nano 9B V2 (Free)",
        "concurrency_limit": 5,
        "category": "fast",
        "capabilities": {"thinking": True, "mode": "tool"},
    },
    {
        "id": "nvidia/nemotron-3-nano-30b-a3b:free",
        "name": "Nemotron 3 Nano 30B (Free)",
        "concurrency_limit": 3,
        "category": "reasoning",
        "capabilities": {"thinking": True, "mode": "tool"},
    },
    {
        "id": "nvidia/nemotron-nano-12b-v2-vl:free",
        "name": "Nemotron Nano 12B VL (Free)",
        "concurrency_limit": 4,
        "category": "reasoning",
        "capabilities": {"thinking": True, "mode": "tool"},
    },
    {
        "id": "tngtech/tng-r1t-chimera:free",
        "name": "TNG R1T Chimera (Free)",
        "concurrency_limit": 3,
        "category": "reasoning",
        "capabilities": {"thinking": True, "mode": "tool"},
    },
]

GLOBAL_MODEL_MAP = {m["id"]: m for m in GLOBAL_MODEL_POOL}

# Councilor definitions with personas and stage limits
COUNCILORS = [
    {
        "id": "immanuel_kant",
        "name": "康德",
        "model": "xiaomi/mimo-v2-flash:free",
        "model_candidates": [
            "xiaomi/mimo-v2-flash:free",
            "nvidia/nemotron-nano-9b-v2:free",
            "nvidia/nemotron-3-nano-30b-a3b:free",
            "nvidia/nemotron-nano-12b-v2-vl:free",
            "tngtech/tng-r1t-chimera:free",
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
            "stage2": {"max_output_tokens": 360, "timeout": 75.0},
        },
        "auto_route_by_speed": True,  # 是否启用速度自动选路
    },
    {
        "id": "donald_trump",
        "name": "特朗普",
        "model": "xiaomi/mimo-v2-flash:free",
        "model_candidates": [
            "xiaomi/mimo-v2-flash:free",
            "nvidia/nemotron-nano-9b-v2:free",
            "nvidia/nemotron-3-nano-30b-a3b:free",
            "nvidia/nemotron-nano-12b-v2-vl:free",
            "tngtech/tng-r1t-chimera:free",
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
        "auto_route_by_speed": True,
    },
    {
        "id": "hideo_kojima",
        "name": "小岛秀夫",
        "model": "xiaomi/mimo-v2-flash:free",
        "model_candidates": [
            "xiaomi/mimo-v2-flash:free",
            "nvidia/nemotron-nano-9b-v2:free",
            "nvidia/nemotron-3-nano-30b-a3b:free",
            "nvidia/nemotron-nano-12b-v2-vl:free",
            "tngtech/tng-r1t-chimera:free",
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
        "auto_route_by_speed": True,
    },
]

CHAIRMAN = {
    "id": "chairman",
    "name": "共识主席",
    "model": "xiaomi/mimo-v2-flash:free",
    "model_candidates": [
        "xiaomi/mimo-v2-flash:free",
        "nvidia/nemotron-nano-9b-v2:free",
        "nvidia/nemotron-3-nano-30b-a3b:free",
        "nvidia/nemotron-nano-12b-v2-vl:free",
        "tngtech/tng-r1t-chimera:free",
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

# ----------------------------
HEALTH_CHECK_START_HOUR = 10   # 早上 10 点开始
HEALTH_CHECK_END_HOUR = 24     # 午夜 24 点结束 (即 0 点)
HEALTH_CHECK_INTERVAL = 7200   # 每 2 小时 = 7200 秒
HEALTH_CHECK_TIMEZONE = "Asia/Shanghai"

# ----------------------------
# 速度自动选路 (需求3)
# ----------------------------
SPEED_ROUTE_SWITCH_ABS_MS = 800      # 切换绝对阈值 (ms)
SPEED_ROUTE_SWITCH_REL_PCT = 0.30    # 切换相对阈值 (30%)
EMERGENCY_PROBE_TTFT_THRESHOLD = 5000  # 紧急探测触发阈值 (ms)
EMERGENCY_PROBE_TTFT_MULTIPLIER = 3    # 紧急探测触发: TTFT >= EMA * 此值
EMERGENCY_PROBE_COOLDOWN_MINUTES = 10  # 紧急探测冷却 (分钟，per-model)
