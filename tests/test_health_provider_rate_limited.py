from backend.health import HealthManager


def test_health_update_skips_provider_rate_limited():
    manager = HealthManager()
    manager.update_status("nim:test-model", False, "provider_rate_limited", 429, source="probe")
    status = manager.get_status("nim:test-model")
    assert status["health_status"] == "unknown"
    assert status["health_checked_at"] is None
