import base64
import hashlib
import hmac
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


class RecordingTransport:
    def __init__(self) -> None:
        self.replies: list[tuple[str, str]] = []

    async def reply_text(self, reply_token: str, text: str) -> None:
        self.replies.append((reply_token, text))


class FailingTransport:
    async def reply_text(self, reply_token: str, text: str) -> None:
        raise RuntimeError("simulated LINE outage")


def signed_headers(secret: str, body: bytes) -> dict[str, str]:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    signature = base64.b64encode(digest).decode()
    return {"x-line-signature": signature, "content-type": "application/json"}


def text_event(text: str, *, event_id: str = "event-1", source_type: str = "group") -> dict:
    source = {"type": source_type, "groupId": "group-1", "userId": "user-1"}
    if source_type != "group":
        source.pop("groupId")
    return {
        "webhookEventId": event_id,
        "type": "message",
        "replyToken": "reply-token",
        "source": source,
        "message": {"type": "text", "id": "message-1", "text": text},
    }


def make_client(tmp_path: Path) -> tuple[TestClient, RecordingTransport]:
    transport = RecordingTransport()
    settings = Settings(
        channel_secret="test-channel-secret",
        channel_access_token="test-access-token",
        database_path=tmp_path / "state" / "ginraidee.db",
    )
    return TestClient(create_app(settings, transport)), transport


def post_event(client: TestClient, event: dict, secret: str = "test-channel-secret"):
    import json

    body = json.dumps({"events": [event]}, separators=(",", ":")).encode()
    return client.post("/callback", content=body, headers=signed_headers(secret, body))


def test_health_initializes_a_persistent_sqlite_database(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)

    with client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert (tmp_path / "state" / "ginraidee.db").is_file()


def test_signed_ginrai_from_empty_group_prompts_setup_in_thai(tmp_path: Path) -> None:
    client, transport = make_client(tmp_path)

    with client:
        response = post_event(client, text_event("@ginrai"))

    assert response.status_code == 200
    assert transport.replies == [
        ("reply-token", "ยังไม่มีร้านอาหารในกลุ่มนี้ พิมพ์ @ginrai-manage เพื่อเพิ่มร้านอาหาร")
    ]


def test_manage_command_reaches_its_own_entry_point(tmp_path: Path) -> None:
    client, transport = make_client(tmp_path)

    with client:
        response = post_event(client, text_event("@ginrai-manage"))

    assert response.status_code == 200
    assert transport.replies == [
        ("reply-token", "เริ่มจัดการร้านอาหารแล้ว พิมพ์ เพิ่ม, รายการ หรือ ยกเลิก")
    ]


def test_invalid_signature_has_no_effect(tmp_path: Path) -> None:
    client, transport = make_client(tmp_path)

    with client:
        response = post_event(client, text_event("@ginrai"), secret="not-the-channel-secret")

    assert response.status_code == 401
    assert transport.replies == []


def test_ordinary_or_unsupported_messages_have_no_effect(tmp_path: Path) -> None:
    client, transport = make_client(tmp_path)

    with client:
        ordinary = post_event(client, text_event("กินอะไรดี", event_id="event-ordinary"))
        direct = post_event(
            client,
            text_event("@ginrai", event_id="event-direct", source_type="user"),
        )

    assert ordinary.status_code == 200
    assert direct.status_code == 200
    assert transport.replies == []


def test_duplicate_signed_event_does_not_repeat_its_effect(tmp_path: Path) -> None:
    client, transport = make_client(tmp_path)
    event = text_event("@ginrai", event_id="event-once")

    with client:
        first = post_event(client, event)
        second = post_event(client, event)

    assert first.status_code == 200
    assert second.status_code == 200
    assert len(transport.replies) == 1


def test_restart_preserves_webhook_receipts(tmp_path: Path) -> None:
    first_client, first_transport = make_client(tmp_path)
    event = text_event("@ginrai", event_id="event-before-restart")
    with first_client:
        first = post_event(first_client, event)

    restarted_client, restarted_transport = make_client(tmp_path)
    with restarted_client:
        after_restart = post_event(restarted_client, event)

    assert first.status_code == 200
    assert after_restart.status_code == 200
    assert len(first_transport.replies) == 1
    assert restarted_transport.replies == []


def test_startup_retries_durable_webhook_work_after_failed_delivery(tmp_path: Path) -> None:
    settings = Settings(
        channel_secret="test-channel-secret",
        channel_access_token="test-access-token",
        database_path=tmp_path / "state" / "ginraidee.db",
    )
    failed_client = TestClient(create_app(settings, FailingTransport()), raise_server_exceptions=False)

    with failed_client:
        failed_delivery = post_event(failed_client, text_event("@ginrai", event_id="event-retry"))

    recovered_transport = RecordingTransport()
    recovered_client = TestClient(create_app(settings, recovered_transport))
    with recovered_client:
        pass

    assert failed_delivery.status_code == 500
    assert recovered_transport.replies == [
        ("reply-token", "ยังไม่มีร้านอาหารในกลุ่มนี้ พิมพ์ @ginrai-manage เพื่อเพิ่มร้านอาหาร")
    ]


def test_retrying_a_management_command_retains_its_member_scope(tmp_path: Path) -> None:
    settings = Settings(
        channel_secret="test-channel-secret",
        channel_access_token="test-access-token",
        database_path=tmp_path / "state" / "ginraidee.db",
    )
    failed_client = TestClient(create_app(settings, FailingTransport()), raise_server_exceptions=False)

    with failed_client:
        failed_delivery = post_event(
            failed_client, text_event("@ginrai-manage", event_id="event-manage-retry")
        )

    recovered_transport = RecordingTransport()
    recovered_client = TestClient(create_app(settings, recovered_transport))
    with recovered_client:
        pass

    assert failed_delivery.status_code == 500
    assert recovered_transport.replies == [
        ("reply-token", "เริ่มจัดการร้านอาหารแล้ว พิมพ์ เพิ่ม, รายการ หรือ ยกเลิก")
    ]
