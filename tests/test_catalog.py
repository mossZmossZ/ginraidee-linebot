import base64
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


class RecordingTransport:
    def __init__(self) -> None:
        self.replies: list[tuple[str, list[dict[str, str]]]] = []

    async def reply_messages(self, reply_token: str, messages: list[dict[str, str]]) -> None:
        self.replies.append((reply_token, messages))

    async def reply_text(self, reply_token: str, text: str) -> None:
        await self.reply_messages(reply_token, [{"type": "text", "text": text}])


def signed_headers(secret: str, body: bytes) -> dict[str, str]:
    signature = base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()
    return {"x-line-signature": signature, "content-type": "application/json"}


def event(
    text: str, event_id: str, *, group_id: str = "group-1", user_id: str = "user-1"
) -> dict:
    return {
        "webhookEventId": event_id,
        "type": "message",
        "replyToken": f"reply-{event_id}",
        "source": {"type": "group", "groupId": group_id, "userId": user_id},
        "message": {"type": "text", "id": f"message-{event_id}", "text": text},
    }


def post(client: TestClient, payload: dict) -> None:
    body = json.dumps({"events": [payload]}, separators=(",", ":")).encode()
    response = client.post("/callback", content=body, headers=signed_headers("secret", body))
    assert response.status_code == 200


def add_restaurant(
    client: TestClient,
    *,
    group_id: str = "group-1",
    user_id: str = "user-1",
    name: str = "ร้านอร่อย",
    image_url: str = "https://images.example/restaurant.jpg",
) -> None:
    post(client, event("@ginrai-manage", f"manage-{group_id}-{user_id}", group_id=group_id, user_id=user_id))
    post(client, event("เพิ่ม", f"add-{group_id}-{user_id}", group_id=group_id, user_id=user_id))
    post(client, event(name, f"name-{group_id}-{user_id}", group_id=group_id, user_id=user_id))
    post(client, event(image_url, f"image-{group_id}-{user_id}", group_id=group_id, user_id=user_id))


def test_member_can_add_a_restaurant_and_line_receives_the_original_image_url(tmp_path: Path) -> None:
    transport = RecordingTransport()
    settings = Settings("secret", "token", tmp_path / "data" / "ginraidee.db")
    client = TestClient(create_app(settings, transport))

    with client:
        add_restaurant(client)

    assert transport.replies[-1] == (
        "reply-image-group-1-user-1",
        [
            {"type": "text", "text": "เพิ่มร้าน ร้านอร่อย แล้ว"},
            {
                "type": "image",
                "originalContentUrl": "https://images.example/restaurant.jpg",
                "previewImageUrl": "https://images.example/restaurant.jpg",
            },
        ],
    )
    assert not (tmp_path / "data" / "images").exists()
    with sqlite3.connect(settings.database_path) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(restaurants)")}
    assert "stored_image_id" not in columns


def test_members_share_only_their_group_catalog_after_restart(tmp_path: Path) -> None:
    settings = Settings("secret", "token", tmp_path / "data" / "ginraidee.db")
    first_transport = RecordingTransport()
    first_client = TestClient(create_app(settings, first_transport))
    with first_client:
        add_restaurant(first_client)

    restarted_transport = RecordingTransport()
    restarted_client = TestClient(create_app(settings, restarted_transport))
    with restarted_client:
        post(restarted_client, event("@ginrai-manage", "member-manage", user_id="user-2"))
        post(restarted_client, event("รายการ", "member-list", user_id="user-2"))
        post(restarted_client, event("@ginrai-manage", "other-manage", group_id="group-2"))
        post(restarted_client, event("รายการ", "other-list", group_id="group-2"))

    assert restarted_transport.replies[1][1][1] == {
        "type": "image",
        "originalContentUrl": "https://images.example/restaurant.jpg",
        "previewImageUrl": "https://images.example/restaurant.jpg",
    }
    assert restarted_transport.replies[-1][1] == [{"type": "text", "text": "ยังไม่มีร้านอาหารในกลุ่มนี้"}]


def test_invalid_or_cancelled_url_does_not_create_a_restaurant(tmp_path: Path) -> None:
    transport = RecordingTransport()
    settings = Settings("secret", "token", tmp_path / "state.db")
    client = TestClient(create_app(settings, transport))

    with client:
        add_restaurant(client, image_url="http://images.example/restaurant.jpg")
        post(client, event("https://[invalid/restaurant.jpg", "malformed-url"))
        post(client, event("ยกเลิก", "cancel"))
        post(client, event("@ginrai-manage", "list-manage"))
        post(client, event("รายการ", "list"))

    assert transport.replies[-1][1] == [{"type": "text", "text": "ยังไม่มีร้านอาหารในกลุ่มนี้"}]


def test_catalog_paginates_without_exceeding_lines_reply_message_limit(tmp_path: Path) -> None:
    transport = RecordingTransport()
    settings = Settings("secret", "token", tmp_path / "state.db")
    client = TestClient(create_app(settings, transport))

    with client:
        for number in range(1, 7):
            add_restaurant(
                client,
                user_id=f"member-{number}",
                name=f"ร้าน {number}",
                image_url=f"https://images.example/{number}.jpg",
            )
        post(client, event("@ginrai-manage", "list-manage", user_id="viewer"))
        post(client, event("รายการ", "list-page-one", user_id="viewer"))
        post(client, event("รายการ 3", "list-page-three", user_id="viewer"))

    first_page = transport.replies[-2][1]
    third_page = transport.replies[-1][1]
    assert len(first_page) == 5
    assert first_page[-1] == {"type": "text", "text": "ยังมีร้านอาหารอีก 4 ร้าน พิมพ์ รายการ 2 เพื่อดูต่อ"}
    assert [message["text"] for message in third_page[::2]] == ["ร้าน 5", "ร้าน 6"]


def test_sessions_are_isolated_and_expire_after_ten_minutes_of_inactivity(tmp_path: Path) -> None:
    clock = [datetime(2026, 10, 16, 9, 0, tzinfo=UTC)]
    transport = RecordingTransport()
    settings = Settings("secret", "token", tmp_path / "state.db")
    client = TestClient(create_app(settings, transport, clock=lambda: clock[0]))

    with client:
        add_restaurant(client, user_id="first", name="ร้านแรก")
        add_restaurant(client, user_id="second", name="ร้านสอง")
        post(client, event("@ginrai-manage", "expired-manage", user_id="expired"))
        post(client, event("เพิ่ม", "expired-add", user_id="expired"))
        clock[0] += timedelta(minutes=10)
        post(client, event("ร้านหมดอายุ", "expired-name", user_id="expired"))

    added_names = [reply[1][0]["text"] for reply in transport.replies if len(reply[1]) == 2]
    assert added_names == ["เพิ่มร้าน ร้านแรก แล้ว", "เพิ่มร้าน ร้านสอง แล้ว"]


def test_duplicate_management_event_is_processed_once(tmp_path: Path) -> None:
    transport = RecordingTransport()
    settings = Settings("secret", "token", tmp_path / "state.db")
    client = TestClient(create_app(settings, transport))
    repeated_add = event("เพิ่ม", "same-add")

    with client:
        post(client, event("@ginrai-manage", "manage"))
        post(client, repeated_add)
        post(client, repeated_add)

    assert [reply[1][0]["text"] for reply in transport.replies] == [
        "เริ่มจัดการร้านอาหารแล้ว พิมพ์ เพิ่ม, รายการ หรือ ยกเลิก",
        "กรุณาส่งชื่อร้านอาหาร",
    ]
