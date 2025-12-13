"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council member model pool (ordered by preference)
COUNCIL_MODEL_POOL = [
    "meituan/longcat-flash-chat:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "kwaipilot/kat-coder-pro:free",
    "arcee-ai/trinity-mini:free",  # Added as backup
    "tngtech/tng-r1t-chimera:free", # Added as backup
]

# Chairman model pool (ordered by preference)
CHAIRMAN_MODEL_POOL = [
    "amazon/nova-2-lite-v1:free",
    "moonshotai/kimi-k2:free", # Backup chairman
    "tngtech/deepseek-r1t2-chimera:free", # Backup chairman
]

# Number of active council members to select
COUNCIL_SIZE = 3

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"

# Default stage limits (timeouts in seconds, concurrency counts)
DEFAULT_STAGE_LIMITS = {
    "stage1": {"timeout": 120.0, "concurrency": 6},
    "stage2": {"timeout": 180.0, "concurrency": 4},
}

# Optional per-councilor overrides for stage behavior
# Example:
# COUNCILOR_STAGE_OVERRIDES = {
#     "some/model": {
#         "stage1_timeout": 90.0,
#         "stage2_timeout": 150.0,
#         "stage1_concurrency": 2,
#         "stage2_concurrency": 3,
#     }
# }
COUNCILOR_STAGE_OVERRIDES = {}

# Backoff configuration for transient failures
RATE_LIMIT_BACKOFF_SECONDS = 2
