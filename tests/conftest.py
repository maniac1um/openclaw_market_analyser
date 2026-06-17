"""Shared pytest configuration."""

import pytest


@pytest.fixture(autouse=True)
def _disable_rate_limit_for_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.rate_limit_enabled", False)


@pytest.fixture(autouse=True)
def _disable_legacy_api_key_for_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Step 8 default: legacy global key off unless a test explicitly re-enables it."""
    monkeypatch.setattr("app.core.config.settings.legacy_api_key_enabled", False)


@pytest.fixture(autouse=True)
def _allow_insecure_dev_deployment_for_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.allow_insecure_dev_deployment", True)


@pytest.fixture(autouse=True)
def _disable_signature_for_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.openclaw_enable_signature", False)


@pytest.fixture(autouse=True)
def _demo_public_bind_for_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.demo_allow_public_bind", True)


@pytest.fixture(autouse=True)
def _allow_simulated_subscription_upgrade_for_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.subscriptions_simulated_upgrade_enabled", True)
