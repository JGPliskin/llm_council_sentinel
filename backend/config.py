"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Councilor catalog (public fields only)
COUNCILORS = [
    {
        "id": "c-longcat",
        "name": "Longcat",
        "model": "meituan/longcat-flash-chat:free",
        "active": True,
    },
    {
        "id": "c-nemotron",
        "name": "Nemotron",
        "model": "nvidia/nemotron-nano-9b-v2:free",
        "active": True,
    },
    {
        "id": "c-kat",
        "name": "Kat Coder",
        "model": "kwaipilot/kat-coder-pro:free",
        "active": True,
    },
    {
        "id": "c-trinity",
        "name": "Trinity Mini",
        "model": "arcee-ai/trinity-mini:free",
        "active": True,
    },
    {
        "id": "c-chimera",
        "name": "Chimera",
        "model": "tngtech/tng-r1t-chimera:free",
        "active": True,
    },
]

CHAIRMAN = {
    "id": "chair-nova",
    "name": "Nova Chair",
    "model": "amazon/nova-2-lite-v1:free",
    "active": True,
}

# Number of active council members to select
COUNCIL_SIZE = 3

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"

# Schema version for stored conversations
SCHEMA_VERSION = 2
