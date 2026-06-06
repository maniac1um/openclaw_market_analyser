import pytest
from fastapi.testclient import TestClient

from app.core.startup_checks import validate_security_config
from app.main import app
from app.schemas.report import OpenClawReportIn


def _auth_headers(api_key: str) -> dict[str, str]:
    return {"X-Api-Key": api_key, "X-Request-Id": "req-h1"}


def _base_payload() -> dict:
    return {
        "task_id": "task-h1",
        "keyword": "羽毛球",
        "time_range": {
            "start": "2026-03-01T00:00:00+00:00",
            "end": "2026-04-01T00:00:00+00:00",
        },
        "sources": ["source-a"],
        "items": [
            {
                "title": "x",
                "source": "source-a",
                "url": "https://example.com/1",
                "published_at": "2026-03-20T10:00:00+00:00",
            }
        ],
        "analysis": "ok",
        "generated_title": "t",
        "generated_at": "2026-04-01T11:00:00+00:00",
    }


def test_production_fail_fast_weak_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.production_mode", True)
    monkeypatch.setattr("app.core.config.settings.openclaw_api_key", "dev-openclaw-key")
    with pytest.raises(RuntimeError, match="OPENCLAW_OPENCLAW_API_KEY"):
        validate_security_config()


def test_oversized_analysis_rejected_by_schema() -> None:
    data = _base_payload()
    data["analysis"] = "A" * 60_000
    with pytest.raises(Exception):
        OpenClawReportIn.model_validate(data)


def test_javascript_url_rejected_by_schema() -> None:
    data = _base_payload()
    data["items"][0]["url"] = "javascript:alert(1)"
    with pytest.raises(Exception):
        OpenClawReportIn.model_validate(data)


def test_bulk_delete_invalid_uuid_returns_422(api_headers: dict[str, str]) -> None:
    client = TestClient(app)
    client.post("/api/v1/public/auth/session", headers=api_headers)
    resp = client.post(
        "/api/v1/public/reports/bulk-delete",
        json={"ingest_ids": ["../../../etc/passwd"]},
    )
    assert resp.status_code == 422


def test_healthz_db_hides_exception_detail_by_default() -> None:
    client = TestClient(app)
    resp = client.get("/healthz/db")
    assert resp.status_code == 200
    body = resp.json()
    if not body.get("ok"):
        assert body.get("detail") == "database connection failed"


def test_rate_limit_returns_429(monkeypatch: pytest.MonkeyPatch, api_headers: dict[str, str]) -> None:
    monkeypatch.setattr("app.core.config.settings.rate_limit_enabled", True)
    monkeypatch.setattr("app.core.config.settings.rate_limit_read_per_minute", 3)
    client = TestClient(app)
    for _ in range(3):
        assert client.get("/api/v1/public/reports", headers=api_headers).status_code in {200, 503}
    assert client.get("/api/v1/public/reports", headers=api_headers).status_code == 429


def test_ssrf_guard_blocks_localhost() -> None:
    from app.utils.ssrf_guard import validate_outbound_http_url

    with pytest.raises(ValueError):
        validate_outbound_http_url("http://127.0.0.1/admin")
