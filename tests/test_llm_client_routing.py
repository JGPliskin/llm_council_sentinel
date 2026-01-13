import pytest

from backend import llm_client


@pytest.mark.asyncio
async def test_llm_client_routes_by_provider(monkeypatch):
    async def fake_nim(model, messages, timeout=120.0, max_output_tokens=None):
        return {"content": "ok", "provider": "nim", "model": model}

    async def fake_or(model, messages, timeout=120.0, max_output_tokens=None):
        return {"content": "ok", "model": model}

    monkeypatch.setattr(llm_client.nim, "query_model", fake_nim)
    monkeypatch.setattr(llm_client.openrouter, "query_model", fake_or)

    response = await llm_client.query_model(
        "deepseek-ai/deepseek-r1", [{"role": "user", "content": "hi"}]
    )
    assert response["provider"] == "nim"


@pytest.mark.asyncio
async def test_llm_client_routes_by_prefix(monkeypatch):
    captured = {}

    async def fake_nim(model, messages, timeout=120.0, max_output_tokens=None):
        captured["model"] = model
        return {"content": "ok", "provider": "nim", "model": model}

    monkeypatch.setattr(llm_client.nim, "query_model", fake_nim)

    response = await llm_client.query_model(
        "nim:custom/model", [{"role": "user", "content": "hi"}]
    )
    assert response["provider"] == "nim"
    assert captured["model"] == "custom/model"


@pytest.mark.asyncio
async def test_llm_client_default_openrouter(monkeypatch):
    async def fake_or(model, messages, timeout=120.0, max_output_tokens=None):
        return {"content": "ok", "model": model}

    monkeypatch.setattr(llm_client.openrouter, "query_model", fake_or)

    response = await llm_client.query_model(
        "unknown/model", [{"role": "user", "content": "hi"}]
    )
    assert response["provider"] == "openrouter"
