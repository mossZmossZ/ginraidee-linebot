import base64
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient

from app.config import Settings
from app.database import Database
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
        "เริ่มจัดการร้านอาหารแล้ว พิมพ์ เพิ่ม, รายการ, แก้ไข, ลบ หรือ ยกเลิก",
        "กรุณาส่งชื่อร้านอาหาร",
    ]


def test_member_can_edit_a_restaurant_and_duplicate_names_can_be_corrected(
    tmp_path: Path,
) -> None:
    transport = RecordingTransport()
    settings = Settings("secret", "token", tmp_path / "state.db")
    client = TestClient(create_app(settings, transport))

    with client:
        add_restaurant(client, name="ร้านแรก")
        add_restaurant(client, user_id="member-2", name="ร้านสอง")
        post(client, event("@ginrai-manage", "edit-manage", user_id="editor"))
        post(client, event("แก้ไข", "edit-start", user_id="editor"))
        selection_text = transport.replies[-1][1][1]["text"]
        restaurant_id = int(selection_text.split()[0].removeprefix("#"))
        post(client, event(str(restaurant_id), "edit-select", user_id="editor"))
        post(client, event("ร้านสอง", "edit-duplicate-name", user_id="editor"))
        post(
            client,
            event("https://images.example/duplicate.jpg", "edit-duplicate-url", user_id="editor"),
        )
        assert "มีร้านชื่อนี้อยู่แล้ว" in transport.replies[-1][1][0]["text"]
        post(client, event("ร้านใหม่", "edit-new-name", user_id="editor"))
        post(
            client,
            event("https://images.example/new.jpg", "edit-new-url", user_id="editor"),
        )

    assert transport.replies[-1][1] == [
        {"type": "text", "text": "แก้ไขร้าน ร้านใหม่ แล้ว"},
        {
            "type": "image",
            "originalContentUrl": "https://images.example/new.jpg",
            "previewImageUrl": "https://images.example/new.jpg",
        },
    ]
    with sqlite3.connect(settings.database_path) as connection:
        row = connection.execute(
            "SELECT display_name, source_image_url, version FROM restaurants WHERE restaurant_id = ?",
            (restaurant_id,),
        ).fetchone()
    assert row == ("ร้านใหม่", "https://images.example/new.jpg", 2)


def test_delete_requires_confirmation_and_cancel_preserves_restaurant(tmp_path: Path) -> None:
    transport = RecordingTransport()
    settings = Settings("secret", "token", tmp_path / "state.db")
    client = TestClient(create_app(settings, transport))

    with client:
        add_restaurant(client, name="ร้านเก็บไว้")
        post(client, event("@ginrai-manage", "delete-manage", user_id="deleter"))
        post(client, event("ลบ", "delete-start", user_id="deleter"))
        selection_text = transport.replies[-1][1][1]["text"]
        restaurant_id = int(selection_text.split()[0].removeprefix("#"))
        post(client, event(str(restaurant_id), "delete-select", user_id="deleter"))
        post(client, event("ไม่ใช่", "delete-no-confirm", user_id="deleter"))
        assert "กรุณาพิมพ์ ยืนยัน" in transport.replies[-1][1][0]["text"]
        post(client, event("ยกเลิก", "delete-cancel", user_id="deleter"))
        post(client, event("@ginrai-manage", "delete-manage-again", user_id="deleter"))
        post(client, event("ลบ", "delete-start-again", user_id="deleter"))
        post(client, event(str(restaurant_id), "delete-select-again", user_id="deleter"))
        post(client, event("ยืนยัน", "delete-confirm", user_id="deleter"))

    with sqlite3.connect(settings.database_path) as connection:
        remaining = connection.execute(
            "SELECT COUNT(*) FROM restaurants WHERE restaurant_id = ?", (restaurant_id,)
        ).fetchone()[0]
    assert remaining == 0
    assert transport.replies[-1][1] == [{"type": "text", "text": "ลบร้าน ร้านเก็บไว้ แล้ว"}]


def test_canceling_an_edit_and_rejecting_http_url_leave_catalog_unchanged(tmp_path: Path) -> None:
    transport = RecordingTransport()
    settings = Settings("secret", "token", tmp_path / "state.db")
    client = TestClient(create_app(settings, transport))

    with client:
        add_restaurant(client, name="ร้านเดิม")
        post(client, event("@ginrai-manage", "cancel-edit-manage", user_id="editor"))
        post(client, event("แก้ไข", "cancel-edit-start", user_id="editor"))
        selection_text = transport.replies[-1][1][1]["text"]
        restaurant_id = int(selection_text.split()[0].removeprefix("#"))
        post(client, event(str(restaurant_id), "cancel-edit-select", user_id="editor"))
        post(client, event("ร้านที่เปลี่ยน", "cancel-edit-name", user_id="editor"))
        post(
            client,
            event("http://images.example/new.jpg", "cancel-edit-http", user_id="editor"),
        )
        assert "HTTPS" in transport.replies[-1][1][0]["text"]
        post(client, event("ยกเลิก", "cancel-edit-cancel", user_id="editor"))

    with sqlite3.connect(settings.database_path) as connection:
        row = connection.execute(
            "SELECT display_name, source_image_url, version FROM restaurants WHERE restaurant_id = ?",
            (restaurant_id,),
        ).fetchone()
    assert row == ("ร้านเดิม", "https://images.example/restaurant.jpg", 1)


def test_foreign_group_id_and_stale_delete_cannot_mutate_restaurant(tmp_path: Path) -> None:
    transport = RecordingTransport()
    settings = Settings("secret", "token", tmp_path / "state.db")
    client = TestClient(create_app(settings, transport))

    with client:
        add_restaurant(client, name="ร้านกลุ่มหนึ่ง")
        with sqlite3.connect(settings.database_path) as connection:
            restaurant_id = connection.execute(
                "SELECT restaurant_id FROM restaurants WHERE group_id = ?", ("group-1",)
            ).fetchone()[0]

        post(
            client,
            event("@ginrai-manage", "foreign-manage", group_id="group-2", user_id="member"),
        )
        post(client, event("ลบ", "foreign-delete", group_id="group-2", user_id="member"))
        post(
            client,
            event(str(restaurant_id), "foreign-select", group_id="group-2", user_id="member"),
        )
        assert "ไม่พบหมายเลขร้านนี้" in transport.replies[-1][1][0]["text"]
        post(
            client,
            event("9" * 20, "foreign-huge-id", group_id="group-2", user_id="member"),
        )
        assert "ไม่พบหมายเลขร้านนี้" in transport.replies[-1][1][0]["text"]

        post(client, event("@ginrai-manage", "stale-manage", user_id="deleter"))
        post(client, event("ลบ", "stale-delete", user_id="deleter"))
        post(client, event(str(restaurant_id), "stale-select", user_id="deleter"))
        with sqlite3.connect(settings.database_path) as connection:
            connection.execute(
                "UPDATE restaurants SET version = version + 1 WHERE restaurant_id = ?",
                (restaurant_id,),
            )
        post(client, event("ยืนยัน", "stale-confirm", user_id="deleter"))

    with sqlite3.connect(settings.database_path) as connection:
        row = connection.execute(
            "SELECT display_name FROM restaurants WHERE restaurant_id = ?", (restaurant_id,)
        ).fetchone()
    assert row == ("ร้านกลุ่มหนึ่ง",)
    assert "ถูกเปลี่ยนแปลง" in transport.replies[-1][1][0]["text"]


def test_reused_sqlite_id_cannot_make_stale_confirmation_delete_new_restaurant(
    tmp_path: Path,
) -> None:
    transport = RecordingTransport()
    settings = Settings("secret", "token", tmp_path / "state.db")
    client = TestClient(create_app(settings, transport))

    with client:
        add_restaurant(client, name="ร้านเก่า")
        with sqlite3.connect(settings.database_path) as connection:
            original_id, original_key = connection.execute(
                "SELECT restaurant_id, selection_key FROM restaurants"
            ).fetchone()

        post(client, event("@ginrai-manage", "stale-owner-manage", user_id="stale-owner"))
        post(client, event("ลบ", "stale-owner-delete", user_id="stale-owner"))
        post(client, event(str(original_id), "stale-owner-select", user_id="stale-owner"))

        post(client, event("@ginrai-manage", "new-owner-manage", user_id="new-owner"))
        post(client, event("ลบ", "new-owner-delete", user_id="new-owner"))
        post(client, event(str(original_id), "new-owner-select", user_id="new-owner"))
        post(client, event("ยืนยัน", "new-owner-confirm", user_id="new-owner"))
        add_restaurant(client, user_id="new-owner", name="ร้านใหม่")

        post(client, event("ยืนยัน", "stale-owner-confirm", user_id="stale-owner"))

    with sqlite3.connect(settings.database_path) as connection:
        new_row = connection.execute(
            "SELECT restaurant_id, selection_key, display_name FROM restaurants"
        ).fetchone()
    assert new_row[0] == original_id
    assert new_row[2] == "ร้านใหม่"
    assert new_row[1] != original_key
    assert "ถูกเปลี่ยนแปลง" in transport.replies[-1][1][0]["text"]


def test_reused_sqlite_id_cannot_change_target_after_selection_list_was_shown(
    tmp_path: Path,
) -> None:
    transport = RecordingTransport()
    settings = Settings("secret", "token", tmp_path / "state.db")
    client = TestClient(create_app(settings, transport))

    with client:
        add_restaurant(client, name="ร้านที่แสดง")
        post(client, event("@ginrai-manage", "snapshot-owner-manage", user_id="snapshot-owner"))
        post(client, event("ลบ", "snapshot-owner-delete", user_id="snapshot-owner"))
        selection_text = transport.replies[-1][1][1]["text"]
        original_id = int(selection_text.split()[0].removeprefix("#"))

        post(client, event("@ginrai-manage", "replacement-manage", user_id="replacement-owner"))
        post(client, event("ลบ", "replacement-delete", user_id="replacement-owner"))
        post(
            client,
            event(str(original_id), "replacement-select", user_id="replacement-owner"),
        )
        post(client, event("ยืนยัน", "replacement-confirm", user_id="replacement-owner"))
        add_restaurant(client, user_id="replacement-owner", name="ร้านทดแทน")

        post(
            client,
            event(str(original_id), "snapshot-stale-select", user_id="snapshot-owner"),
        )
        stale_selection_reply = transport.replies[-1][1][0]["text"]
        assert "ไม่พบหมายเลขร้านนี้" in stale_selection_reply
        assert "ยกเลิก" in stale_selection_reply
        post(client, event("ยืนยัน", "snapshot-stale-confirm", user_id="snapshot-owner"))
        assert "ส่งหมายเลขร้านที่แสดง" in transport.replies[-1][1][0]["text"]

    with sqlite3.connect(settings.database_path) as connection:
        remaining = connection.execute(
            "SELECT restaurant_id, display_name FROM restaurants"
        ).fetchone()
    assert remaining == (original_id, "ร้านทดแทน")


def test_existing_database_migration_preserves_restaurants_and_adds_selection_identity(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "legacy.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE groups (group_id TEXT PRIMARY KEY, created_at TEXT NOT NULL);
            CREATE TABLE restaurants (
                restaurant_id INTEGER PRIMARY KEY,
                group_id TEXT NOT NULL,
                display_name TEXT NOT NULL,
                source_image_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE management_sessions (
                group_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                step TEXT NOT NULL,
                draft_name TEXT,
                expires_at TEXT NOT NULL,
                PRIMARY KEY (group_id, user_id)
            );
            INSERT INTO groups VALUES ('legacy-group', '2026-10-16T00:00:00+00:00');
            INSERT INTO restaurants VALUES (
                47,
                'legacy-group',
                'ร้านเดิม',
                'https://images.example/legacy.jpg',
                '2026-10-16T00:00:00+00:00',
                '2026-10-16T00:00:00+00:00'
            );
            """
        )

    database = Database(database_path)
    database.initialize()
    restaurant = database.list_restaurants("legacy-group")[0]

    assert restaurant.restaurant_id == 47
    assert restaurant.display_name == "ร้านเดิม"
    assert restaurant.source_image_url == "https://images.example/legacy.jpg"
    assert restaurant.version == 1
    assert restaurant.selection_key
    with sqlite3.connect(database_path) as connection:
        session_columns = {row[1] for row in connection.execute("PRAGMA table_info(management_sessions)")}
    assert "selected_restaurant_key" in session_columns
    assert "selection_snapshot" in session_columns
