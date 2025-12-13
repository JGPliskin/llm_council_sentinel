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

# Councilor definitions with personas and stage limits
COUNCILORS = [
    {
        "id": "hefei-strategist",
        "name": "合肥策略官",
        "model": "meituan/longcat-flash-chat:free",
        "persona_path": "backend/personas/hefei_strategist.md",
        "judge_persona_path": "backend/personas/hefei_strategist_judge.md",
        "judge_system_prompt": (
            "保持冷静的政策分析腔调，重视结构化推理与证据透明度，"
            "在比较选项时更关注长期稳健性而非短期噱头。"
        ),
        "stage_limits": {
            "stage1": {"max_output_tokens": 800, "timeout": DEFAULT_STAGE1_TIMEOUT},
            "stage2": {"max_output_tokens": 360, "timeout": 75.0}, # Custom overrides can remain
        },
    },
    {
        "id": "qinling-engineer",
        "name": "秦岭工程师",
        "model": "nvidia/nemotron-nano-9b-v2:free",
        "persona_path": "backend/personas/qinling_engineer.md",
        "judge_persona_path": "backend/personas/qinling_engineer_judge.md",
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
        "id": "lingnan-researcher",
        "name": "岭南研究员",
        "model": "kwaipilot/kat-coder-pro:free",
        "persona_path": "backend/personas/lingnan_researcher.md",
        "judge_persona_path": "backend/personas/lingnan_researcher_judge.md",
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
