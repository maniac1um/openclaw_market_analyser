from pathlib import Path

from fastapi.testclient import TestClient

from app.db import public_queries as pq
from app.main import app
from app.services.report_management_service import ReportManagementService


def test_public_write_requires_credentials() -> None:
    client = TestClient(app)
    resp = client.post(
        "/api/v1/public/reports/bulk-delete",
        json={"ingest_ids": ["00000000-0000-0000-0000-000000000001"]},
    )
    assert resp.status_code == 401


def test_public_write_rejects_invalid_api_key() -> None:
    client = TestClient(app)
    resp = client.post(
        "/api/v1/public/reports/bulk-delete",
        json={"ingest_ids": ["00000000-0000-0000-0000-000000000001"]},
        headers={"X-Api-Key": "wrong-key"},
    )
    assert resp.status_code == 401


def test_portal_session_cookie_authorizes_write(api_headers: dict[str, str]) -> None:
    client = TestClient(app)
    session = client.post("/api/v1/public/auth/session", headers=api_headers)
    assert session.status_code == 200
    resp = client.post(
        "/api/v1/public/reports/bulk-delete",
        json={"ingest_ids": ["00000000-0000-0000-0000-000000000001"]},
    )
    assert resp.status_code in {200, 503}


def test_public_read_requires_auth_or_api_key(api_headers: dict[str, str]) -> None:
    client = TestClient(app)
    unauth = client.get("/api/v1/public/reports")
    assert unauth.status_code == 401
    with_key = client.get("/api/v1/public/reports", headers=api_headers)
    assert with_key.status_code in {200, 503}


def test_spa_index_does_not_embed_api_key() -> None:
    client = TestClient(app)
    resp = client.get("/")
    if resp.status_code == 200 and "html" in resp.headers.get("content-type", ""):
        assert "apiKey" not in resp.text
        assert "__OPENCLAW_RUNTIME__" not in resp.text


def test_delete_reports_from_db_skips_invalid_uuid(monkeypatch) -> None:
    executed: list[tuple] = []

    class FakeCursor:
        def execute(self, sql, params=None):
            executed.append((sql, params))

        def fetchone(self):
            return None

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class FakeConn:
        def cursor(self):
            return FakeCursor()

        def commit(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(pq.settings, "database_url", "postgresql://test")
    monkeypatch.setattr("psycopg.connect", lambda _url: FakeConn())

    from app.db.query_context import LEGACY_ADMIN_USER_ID, QueryContext

    result = pq.delete_reports_from_db(["../../../etc/passwd"], QueryContext(user_id=LEGACY_ADMIN_USER_ID, role="ADMIN"))
    assert result["not_found"] == ["../../../etc/passwd"]
    assert executed == []


def test_bulk_delete_invalid_uuid_rejected_at_schema(api_headers: dict[str, str]) -> None:
    client = TestClient(app)
    client.post("/api/v1/public/auth/session", headers=api_headers)
    resp = client.post(
        "/api/v1/public/reports/bulk-delete",
        json={"ingest_ids": ["../../../etc/passwd"]},
    )
    assert resp.status_code == 422


def test_report_file_delete_blocks_path_traversal(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    rendered_root = tmp_path / "rendered"
    raw_root.mkdir()
    rendered_root.mkdir()

    outside = tmp_path / "outside.json"
    outside.write_text("secret", encoding="utf-8")

    svc = ReportManagementService(raw_root=raw_root, rendered_root=rendered_root)
    result = svc.delete_reports(["../../../outside"])

    assert outside.exists()
    assert result["deleted"] == []
    assert "../../../outside" in result["not_found"]


def test_report_file_delete_only_removes_valid_uuid_files(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    rendered_root = tmp_path / "rendered"
    raw_root.mkdir()
    rendered_root.mkdir()

    ingest_id = "11111111-1111-1111-1111-111111111111"
    target = raw_root / f"{ingest_id}.json"
    target.write_text("{}", encoding="utf-8")

    svc = ReportManagementService(raw_root=raw_root, rendered_root=rendered_root)
    result = svc.delete_reports([ingest_id])

    assert not target.exists()
    assert ingest_id in result["deleted"]


def test_chat_websocket_requires_auth() -> None:
    client = TestClient(app)
    try:
        with client.websocket_connect("/api/v1/chat/ws") as _ws:
            raised = False
    except Exception:
        raised = True
    assert raised


def test_chat_websocket_rejects_query_api_key() -> None:
    client = TestClient(app)
    try:
        with client.websocket_connect("/api/v1/chat/ws?api_key=dev-openclaw-key") as _ws:
            raised = False
    except Exception:
        raised = True
    assert raised


def test_chat_websocket_accepts_header_api_key(api_headers: dict[str, str]) -> None:
    client = TestClient(app)
    with client.websocket_connect("/api/v1/chat/ws", headers={"x-api-key": api_headers["X-Api-Key"]}) as ws:
        ws.send_json({"type": "ping"})
        assert ws is not None


def test_chat_websocket_accepts_portal_session_cookie(api_headers: dict[str, str]) -> None:
    client = TestClient(app)
    client.post("/api/v1/public/auth/session", headers=api_headers)
    with client.websocket_connect("/api/v1/chat/ws") as ws:
        ws.send_json({"type": "ping"})
        assert ws is not None
