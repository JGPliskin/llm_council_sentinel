import pytest

from backend.nim import NIMKeyManager, ProviderRateLimitError


@pytest.mark.asyncio
async def test_nim_key_manager_exhausts_tokens():
    manager = NIMKeyManager(["k1"], rpm_per_key=1, cooldown_seconds=10)
    key = await manager.acquire_key()
    assert key == "k1"
    with pytest.raises(ProviderRateLimitError):
        await manager.acquire_key()


@pytest.mark.asyncio
async def test_nim_key_manager_cooldown_blocks_key():
    manager = NIMKeyManager(["k1"], rpm_per_key=10, cooldown_seconds=10)
    await manager.mark_cooldown("k1")
    with pytest.raises(ProviderRateLimitError):
        await manager.acquire_key()
