import pytest

from backend import llm_client
from backend import nim


@pytest.mark.asyncio
async def test_e2e_nim_provider_rate_limited(monkeypatch):
    # Patch the nim module instance that llm_client is actually using
    monkeypatch.setattr(llm_client.nim, "NIM_API_KEYS", [])
    monkeypatch.setattr(llm_client.nim, "_key_manager", nim.NIMKeyManager([], rpm_per_key=1))

    response = await llm_client.query_model(
        "nim:dummy/model", [{"role": "user", "content": "hi"}]
    )
    assert response["provider"] == "nim"
    assert response.get("error_code") == "provider_rate_limited"
