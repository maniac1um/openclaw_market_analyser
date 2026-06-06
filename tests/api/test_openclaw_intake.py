from fastapi.testclient import TestClient

from app.main import app
from tests.api.conftest import AuthTestUser, api_key_headers, minimal_report_payload
import uuid


def test_post_and_get_status(user_a: AuthTestUser, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.publish_service.PublishService.trigger_publish",
        lambda self, rendered_path: None,
    )
    client = TestClient(app)
    request_id = f"req-{uuid.uuid4().hex[:12]}"
    headers = {**api_key_headers(user_a), "X-Request-Id": request_id}

    post_resp = client.post(
        "/api/v1/openclaw/reports",
        headers=headers,
        json=minimal_report_payload(task_id=request_id),
    )
    assert post_resp.status_code == 202
    ingest_id = post_resp.json()["ingest_id"]

    get_resp = client.get(
        f"/api/v1/openclaw/reports/{ingest_id}",
        headers=api_key_headers(user_a),
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] in {"processing", "published", "queued"}


def test_idempotent_request(user_a: AuthTestUser, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.publish_service.PublishService.trigger_publish",
        lambda self, rendered_path: None,
    )
    client = TestClient(app)
    request_id = f"req-{uuid.uuid4().hex[:12]}"
    headers = {**api_key_headers(user_a), "X-Request-Id": request_id}
    payload = minimal_report_payload(task_id=request_id)

    first = client.post("/api/v1/openclaw/reports", headers=headers, json=payload).json()
    second = client.post("/api/v1/openclaw/reports", headers=headers, json=payload).json()
    assert first["ingest_id"] == second["ingest_id"]
