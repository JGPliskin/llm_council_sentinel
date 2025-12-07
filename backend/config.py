"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council members - list of Model identifiers
COUNCIL_MODELS = [
    "meituan/longcat-flash-chat:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "kwaipilot/kat-coder-pro:free",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "amazon/nova-2-lite-v1:free"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
