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

# NIM API key (comma-separated for multiple keys)
NIM_API_KEYS = os.getenv("NIM_API_KEYS", "")

# NIM API endpoint
NIM_API_BASE = os.getenv("NIM_API_BASE", "https://integrate.api.nvidia.com/v1")

# NIM requests per minute per key (rate limiting)
NIM_RPM_PER_KEY = int(os.getenv("NIM_RPM_PER_KEY", "40"))

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
STAGE1_DEADLINE = 180.0
STAGE2_DEADLINE = 180.0
STAGE3_DEADLINE = 180.0

# ----------------------------
# 400 错误分类（Fallback Retry）
# ----------------------------
# 请求错误 code（不回退）
REQUEST_ERROR_CODES = {"context_length_exceeded", "invalid_request", "invalid_api_key"}
# 请求错误关键词（不回退）
REQUEST_ERROR_KEYWORDS = [
    "context",
    "token limit",
    "invalid request",
    "invalid json",
    "tool",
    "function",
    "bad request",
]
# 模型错误关键词（可回退）
MODEL_ERROR_KEYWORDS = [
    "not found",
    "unavailable",
    "permission",
    "unauthorized",
    "disabled",
    "provider",
]

# ----------------------------
# Global Model Pool & Routing
# ----------------------------
GLOBAL_MODEL_POOL = [
    {
        "id": "openrouter:xiaomi/mimo-v2-flash:free",
        "name": "Mimo V2 Flash (Free)",
        "provider": "openrouter",
        "concurrency_limit": 5,
        "category": "fast",
        "capabilities": {"thinking": True, "mode": "tool"},
    },
    {
        "id": "openrouter:nvidia/nemotron-nano-9b-v2:free",
        "name": "Nemotron Nano 9B V2 (Free)",
        "provider": "openrouter",
        "concurrency_limit": 5,
        "category": "fast",
        "capabilities": {"thinking": True, "mode": "tool"},
    },
    {
        "id": "openrouter:nvidia/nemotron-3-nano-30b-a3b:free",
        "name": "Nemotron 3 Nano 30B (Free)",
        "provider": "openrouter",
        "concurrency_limit": 3,
        "category": "reasoning",
        "capabilities": {"thinking": True, "mode": "tool"},
    },
    {
        "id": "openrouter:nvidia/nemotron-nano-12b-v2-vl:free",
        "name": "Nemotron Nano 12B VL (Free)",
        "provider": "openrouter",
        "concurrency_limit": 4,
        "category": "reasoning",
        "capabilities": {"thinking": True, "mode": "tool"},
    },
    {
        "id": "openrouter:tngtech/tng-r1t-chimera:free",
        "name": "TNG R1T Chimera (Free)",
        "provider": "openrouter",
        "concurrency_limit": 3,
        "category": "reasoning",
        "capabilities": {"thinking": True, "mode": "tool"},
    },
    {
        "id": "openrouter:mistralai/devstral-2512:free",
        "name": "Devstral 2512 (Free)",
        "provider": "openrouter",
        "concurrency_limit": 5,
        "category": "fast",
        "capabilities": {"thinking": False, "mode": "standard"},
    },
    {
        "id": "openrouter:z-ai/glm-4.5-air:free",
        "name": "GLM-4.5 Air (Free)",
        "provider": "openrouter",
        "concurrency_limit": 5,
        "category": "fast",
        "capabilities": {"thinking": False, "mode": "standard"},
    },
    {
        "id": "openrouter:qwen/qwen3-coder:free",
        "name": "Qwen3 Coder (Free)",
        "provider": "openrouter",
        "concurrency_limit": 5,
        "category": "fast",
        "capabilities": {"thinking": False, "mode": "standard"},
    },
    {
        "id": "openrouter:deepseek/deepseek-v3.2",
        "name": "DeepSeek V3.2",
        "provider": "openrouter",
        "concurrency_limit": 5,
        "category": "reasoning",
        "capabilities": {"thinking": True, "mode": "tool"},
    },
    {
        "id": "openrouter:x-ai/grok-4.1-fast",
        "name": "Grok 4.1 Fast",
        "provider": "openrouter",
        "concurrency_limit": 5,
        "category": "fast",
        "capabilities": {"thinking": True, "mode": "tool"},
    },
    {
        "id": "nim:deepseek-ai/deepseek-v3.1",
        "name": "DeepSeek V3.1 (NIM)",
        "provider": "nim",
        "concurrency_limit": 3,
        "category": "reasoning",
        "capabilities": {"thinking": True, "mode": "tool"},
    },
    {
        "id": "nim:deepseek-ai/deepseek-v3.1-terminus",
        "name": "DeepSeek V3.1 Terminus (NIM)",
        "provider": "nim",
        "concurrency_limit": 3,
        "category": "reasoning",
        "capabilities": {"thinking": True, "mode": "tool"},
    },
    {
        "id": "nim:openai/gpt-oss-120b",
        "name": "GPT OSS 120B (NIM)",
        "provider": "nim",
        "concurrency_limit": 3,
        "category": "reasoning",
        "capabilities": {"thinking": True, "mode": "tool"},
    },
    {
        "id": "nim:z-ai/glm4.7",
        "name": "GLM4.7 (NIM)",
        "provider": "nim",
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
        "model": "openrouter:xiaomi/mimo-v2-flash:free",
        "model_candidates": [
            "openrouter:xiaomi/mimo-v2-flash:free",
            "openrouter:nvidia/nemotron-nano-9b-v2:free",
            "openrouter:nvidia/nemotron-3-nano-30b-a3b:free",
            "openrouter:nvidia/nemotron-nano-12b-v2-vl:free",
            "openrouter:tngtech/tng-r1t-chimera:free",
            "nim:deepseek-ai/deepseek-v3.1",
            "nim:openai/gpt-oss-120b",
            "nim:deepseek-ai/deepseek-v3.1-terminus",
            "nim:z-ai/glm4.7",
            "openrouter:z-ai/glm-4.5-air:free",
            "openrouter:mistralai/devstral-2512:free",
            "openrouter:deepseek/deepseek-v3.2",
            "openrouter:x-ai/grok-4.1-fast",
        ],
        "avatar": "/avatars/kant.png",
        "role": "Ethics Guardian",
        "description": "严谨的逻辑审查者。擅长运用绝对律令（Categorical Imperative）扫描提案，精准捕捉潜在的道德风险与逻辑谬误，确保决策符合普世伦理框架。",
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
        "model": "openrouter:xiaomi/mimo-v2-flash:free",
        "model_candidates": [
            "openrouter:xiaomi/mimo-v2-flash:free",
            "openrouter:nvidia/nemotron-nano-9b-v2:free",
            "openrouter:nvidia/nemotron-3-nano-30b-a3b:free",
            "openrouter:nvidia/nemotron-nano-12b-v2-vl:free",
            "openrouter:tngtech/tng-r1t-chimera:free",
            "nim:deepseek-ai/deepseek-v3.1",
            "nim:openai/gpt-oss-120b",
            "nim:deepseek-ai/deepseek-v3.1-terminus",
            "nim:z-ai/glm4.7",
            "openrouter:z-ai/glm-4.5-air:free",
            "openrouter:mistralai/devstral-2512:free",
            "openrouter:deepseek/deepseek-v3.2",
            "openrouter:x-ai/grok-4.1-fast",
        ],
        "avatar": "/avatars/trump.png",
        "role": "Market Strategist",
        "description": "敏锐的直觉主义者。蔑视教条，专注于市场情绪捕捉与高风险博弈。通过非传统视角重构局势，提供极具破坏力与不对称优势的行动方案。",
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
        "model": "openrouter:xiaomi/mimo-v2-flash:free",
        "model_candidates": [
            "openrouter:xiaomi/mimo-v2-flash:free",
            "openrouter:nvidia/nemotron-nano-9b-v2:free",
            "openrouter:nvidia/nemotron-3-nano-30b-a3b:free",
            "openrouter:nvidia/nemotron-nano-12b-v2-vl:free",
            "openrouter:tngtech/tng-r1t-chimera:free",
            "nim:deepseek-ai/deepseek-v3.1",
            "nim:openai/gpt-oss-120b",
            "nim:deepseek-ai/deepseek-v3.1-terminus",
            "nim:z-ai/glm4.7",
            "openrouter:z-ai/glm-4.5-air:free",
            "openrouter:mistralai/devstral-2512:free",
            "openrouter:deepseek/deepseek-v3.2",
            "openrouter:x-ai/grok-4.1-fast",
        ],
        "avatar": "/avatars/kojima.png",
        "role": "Narrative Weaver",
        "description": "深邃的模因构建者。能够解构复杂的信息流，将其编织为具有电影质感与哲学深度的连贯叙事，赋予枯燥数据以情感共鸣与文化穿透力。",
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
    "model": "openrouter:xiaomi/mimo-v2-flash:free",
    "model_candidates": [
        "openrouter:xiaomi/mimo-v2-flash:free",
        "openrouter:nvidia/nemotron-nano-9b-v2:free",
        "openrouter:nvidia/nemotron-3-nano-30b-a3b:free",
        "openrouter:nvidia/nemotron-nano-12b-v2-vl:free",
        "openrouter:tngtech/tng-r1t-chimera:free",
        "nim:deepseek-ai/deepseek-v3.1",
        "nim:openai/gpt-oss-120b",
        "nim:deepseek-ai/deepseek-v3.1-terminus",
        "nim:z-ai/glm4.7",
        "openrouter:z-ai/glm-4.5-air:free",
        "openrouter:mistralai/devstral-2512:free",
        "openrouter:deepseek/deepseek-v3.2",
        "openrouter:x-ai/grok-4.1-fast",
    ],
    "avatar": "/avatars/chairman.png",
    "role": "Consensus Arbiter",
    "description": "系统的最终校准器。负责在激烈的多方辩论中提取最大公约数，消除由于立场偏见产生的噪音，输出具备最高可执行性的融合指令。",
    "persona_path": "backend/personas/chairman.md",
    "judge_system_prompt": (
        "以平实、公允的口吻综合各方论证，突出共识与冲突点，优先给出清晰、可落地的建议。"
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
HEALTH_CHECK_START_HOUR = 10  # 早上 10 点开始
HEALTH_CHECK_END_HOUR = 24  # 午夜 24 点结束 (即 0 点)
HEALTH_CHECK_INTERVAL = 7200  # 每 2 小时 = 7200 秒
HEALTH_CHECK_TIMEZONE = "Asia/Shanghai"

# ----------------------------
# 速度自动选路 (需求3)
# ----------------------------
SPEED_ROUTE_SWITCH_ABS_MS = 800  # 切换绝对阈值 (ms)
SPEED_ROUTE_SWITCH_REL_PCT = 0.30  # 切换相对阈值 (30%)
EMERGENCY_PROBE_TTFT_THRESHOLD = 20000  # 紧急探测触发阈值 (ms)
EMERGENCY_PROBE_TTFT_MULTIPLIER = 3  # 紧急探测触发: TTFT >= EMA * 此值
EMERGENCY_PROBE_COOLDOWN_MINUTES = 30  # 紧急探测冷却 (分钟，per-model)

# ----------------------------
# ETA 进度预估配置 (冷启动默认值)
# ----------------------------
DEFAULT_ETA_CONFIG = {
    "default_ttft_ms": 2000,  # 默认首 token 时间 (ms)
    "default_generation_ms": 5000,  # 默认生成时间 (ms)
    "default_queue_wait_ms": 1000,  # 默认队列等待时间 (ms)
    "warmup_sample_count": 3,  # EMA 启动所需最小样本数
}

# ----------------------------
# Session Summary Models
# ----------------------------
SUMMARY_MODEL_CANDIDATES = [
    "openrouter:xiaomi/mimo-v2-flash:free",
    "openrouter:mistralai/devstral-2512:free",
    "openrouter:z-ai/glm-4.5-air:free",
    "openrouter:qwen/qwen3-coder:free",
]
