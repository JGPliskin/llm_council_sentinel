"""Persona loading and caching utilities."""

import os
from typing import Dict, Iterable

PersonaCache = Dict[str, str]


def load_persona_file(path: str) -> str:
    """Load a persona file with UTF-8 encoding."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def preload_personas(definitions: Iterable[dict]) -> PersonaCache:
    """Preload persona and judge persona content based on definitions."""
    cache: PersonaCache = {}
    for definition in definitions:
        persona_path = definition.get("persona_path")
        if persona_path and persona_path not in cache and os.path.exists(persona_path):
            cache[persona_path] = load_persona_file(persona_path)
        judge_path = definition.get("judge_persona_path")
        if judge_path and judge_path not in cache and os.path.exists(judge_path):
            cache[judge_path] = load_persona_file(judge_path)
    return cache


def fetch_persona(cache: PersonaCache, path: str) -> str:
    """Retrieve cached persona content safely."""
    return cache.get(path, "")
