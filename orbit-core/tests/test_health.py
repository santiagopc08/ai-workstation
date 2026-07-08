"""Tests for HealthChecker."""

from orbit_core.health.checker import HealthChecker
from orbit_core.types.models import HealthStatus


class MockCheckHealthy:
    def health(self) -> HealthStatus:
        return HealthStatus(status="healthy", version="1.0")


class MockCheckDegraded:
    def health(self) -> HealthStatus:
        return HealthStatus(status="degraded", errors=["slow"])


class MockCheckCrashing:
    def health(self) -> HealthStatus:
        raise ValueError("DB down")


def test_health_checker_healthy() -> None:
    checker = HealthChecker()
    checker.register("db", MockCheckHealthy())
    
    status = checker.check_all()
    assert status.status == "healthy"
    assert status.dependencies["db"] == "healthy"
    assert checker.check_count == 1


def test_health_checker_degraded() -> None:
    checker = HealthChecker()
    checker.register("db", MockCheckHealthy())
    checker.register("cache", MockCheckDegraded())
    
    status = checker.check_all()
    assert status.status == "degraded"
    assert "slow" in status.errors


def test_health_checker_unhealthy_crash() -> None:
    checker = HealthChecker()
    checker.register("db", MockCheckCrashing())
    
    status = checker.check_all()
    assert status.status == "unhealthy"
    assert status.dependencies["db"] == "error"
    assert any("DB down" in err for err in status.errors)


def test_health_checker_unregister() -> None:
    checker = HealthChecker()
    checker.register("db", MockCheckHealthy())
    checker.unregister("db")
    assert checker.check_count == 0
