"""Shared pytest configuration."""

import pytest


@pytest.fixture(autouse=True)
def _disable_rate_limit_for_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.rate_limit_enabled", False)


@pytest.fixture(autouse=True)
def _disable_legacy_api_key_for_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Step 8 default: legacy global key off unless a test explicitly re-enables it."""
    monkeypatch.setattr("app.core.config.settings.legacy_api_key_enabled", False)
