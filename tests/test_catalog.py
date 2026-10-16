import base64
import asyncio
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import ipaddress
import json
from pathlib import Path
import sqlite3

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.images import DownloadedImage, ImageFetcher, ImageValidationError
from app.main import create_app


SAMPLE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLv"
    "AAAAAElFTkSuQmCC"
)


class RecordingTransport:
    def __init__(self) -> None:
        self.replies: list[tuple[str, list[dict[str, str]]]] = []

    async def reply_messages(self, reply_token: str, messages: list[dict[str, str]]) -> None:
        self.replies.append((reply_token, messages))

    async def reply_text(self, reply_token: str, text: str) -> None:
        await self.reply_messages(reply_token, [{"type": "text", "text": text}])


class FakeImageFetcher:
    def __init__(self) -> None:
        self.urls: list[str] = []

    async def fetch(self, url: str) -> DownloadedImage:
        self.urls.append(url)
        return DownloadedImage(source_url=url, content=SAMPLE_PNG)


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
    client: TestClient, *, group_id: str = "group-1", user_id: str = "user-1"
) -> None:
    post(client, event("@ginrai-manage", f"manage-{group_id}-{user_id}", group_id=group_id, user_id=user_id))
    post(client, event("เพิ่ม", f"add-{group_id}-{user_id}", group_id=group_id, user_id=user_id))
    post(client, event("ร้านอร่อย", f"name-{group_id}-{user_id}", group_id=group_id, user_id=user_id))
    post(
        client,
        event(
            "https://images.example/restaurant.jpg",
            f"image-{group_id}-{user_id}",
            group_id=group_id,
            user_id=user_id,
        ),
    )


def test_member_can_add_a_restaurant_and_receive_a_backend_hosted_image(tmp_path: Path) -> None:
    transport = RecordingTransport()
    fetcher = FakeImageFetcher()
    settings = Settings(
        channel_secret="secret",
        channel_access_token="token",
        database_path=tmp_path / "data" / "ginraidee.db",
        image_directory=tmp_path / "data" / "images",
        public_base_url="https://bot.example",
    )
    client = TestClient(create_app(settings, transport, image_fetcher=fetcher))

    with client:
        add_restaurant(client)

        image_url = transport.replies[-1][1][1]["originalContentUrl"]
        image_response = client.get(image_url)

    assert fetcher.urls == ["https://images.example/restaurant.jpg"]
    assert transport.replies[-1][0] == "reply-image-group-1-user-1"
    assert transport.replies[-1][1][0] == {"type": "text", "text": "เพิ่มร้าน ร้านอร่อย แล้ว"}
    assert image_url.startswith("https://bot.example/images/")
    assert transport.replies[-1][1][1]["previewImageUrl"] == image_url
    assert image_response.status_code == 200
    assert image_response.headers["content-type"] == "image/png"


def test_members_share_only_their_group_catalog_and_images_survive_restart(tmp_path: Path) -> None:
    settings = Settings(
        channel_secret="secret",
        channel_access_token="token",
        database_path=tmp_path / "data" / "ginraidee.db",
        image_directory=tmp_path / "data" / "images",
        public_base_url="https://bot.example",
    )
    first_transport = RecordingTransport()
    first_client = TestClient(create_app(settings, first_transport, image_fetcher=FakeImageFetcher()))
    with first_client:
        add_restaurant(first_client)
        image_url = first_transport.replies[-1][1][1]["originalContentUrl"]

    restarted_transport = RecordingTransport()
    restarted_client = TestClient(
        create_app(settings, restarted_transport, image_fetcher=FakeImageFetcher())
    )
    with restarted_client:
        post(restarted_client, event("@ginrai-manage", "member-manage", user_id="user-2"))
        post(restarted_client, event("รายการ", "member-list", user_id="user-2"))
        post(restarted_client, event("@ginrai-manage", "other-manage", group_id="group-2"))
        post(restarted_client, event("รายการ", "other-list", group_id="group-2"))
        image_response = restarted_client.get(image_url)
        database_response = restarted_client.get("/images/ginraidee.db")

    assert restarted_transport.replies[1][1][0] == {"type": "text", "text": "ร้านอร่อย"}
    assert restarted_transport.replies[-1][1] == [
        {"type": "text", "text": "ยังไม่มีร้านอาหารในกลุ่มนี้"}
    ]
    assert image_response.status_code == 200
    assert database_response.status_code == 404


def test_cancel_discards_a_draft_before_an_image_is_downloaded(tmp_path: Path) -> None:
    transport = RecordingTransport()
    fetcher = FakeImageFetcher()
    settings = Settings(
        "secret", "token", tmp_path / "state.db", tmp_path / "images", "https://bot.example"
    )
    client = TestClient(create_app(settings, transport, image_fetcher=fetcher))

    with client:
        post(client, event("@ginrai-manage", "manage"))
        post(client, event("เพิ่ม", "add"))
        post(client, event("ร้านที่ยกเลิก", "name"))
        post(client, event("ยกเลิก", "cancel"))
        post(client, event("https://images.example/after-cancel.jpg", "after-cancel"))

    assert fetcher.urls == []
    assert transport.replies[-1][1] == [{"type": "text", "text": "ยกเลิกการจัดการร้านอาหารแล้ว"}]


def test_image_downloader_rejects_private_hosts_and_unsafe_redirects() -> None:
    async def private_host(_: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
        return [ipaddress.ip_address("127.0.0.1")]

    with pytest.raises(ImageValidationError, match="Private or local"):
        asyncio.run(ImageFetcher(resolve_host=private_host).fetch("https://images.example/photo.png"))

    async def public_host(host: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
        if host == "127.0.0.1":
            return [ipaddress.ip_address(host)]
        return [ipaddress.ip_address("8.8.8.8")]

    def redirect_to_private(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://images.example/photo.png"
        return httpx.Response(302, headers={"location": "https://127.0.0.1/private.png"})

    fetcher = ImageFetcher(
        client_factory=lambda **kwargs: httpx.AsyncClient(
            transport=httpx.MockTransport(redirect_to_private), **kwargs
        ),
        resolve_host=public_host,
    )
    with pytest.raises(ImageValidationError, match="Private or local"):
        asyncio.run(fetcher.fetch("https://images.example/photo.png"))


def test_invalid_image_does_not_create_a_file_or_restaurant(tmp_path: Path) -> None:
    class InvalidImageFetcher:
        async def fetch(self, url: str) -> DownloadedImage:
            return DownloadedImage(source_url=url, content=b"not an image")

    image_directory = tmp_path / "images"
    transport = RecordingTransport()
    settings = Settings(
        "secret", "token", tmp_path / "state.db", image_directory, "https://bot.example"
    )
    client = TestClient(create_app(settings, transport, image_fetcher=InvalidImageFetcher()))

    with client:
        add_restaurant(client)
        post(client, event("@ginrai-manage", "list-manage"))
        post(client, event("รายการ", "list"))

    assert not image_directory.exists() or list(image_directory.iterdir()) == []
    assert transport.replies[-1][1] == [{"type": "text", "text": "ยังไม่มีร้านอาหารในกลุ่มนี้"}]


def test_sessions_are_isolated_per_member_and_expire_after_ten_minutes(tmp_path: Path) -> None:
    clock = [datetime(2026, 10, 16, 9, 0, tzinfo=UTC)]
    transport = RecordingTransport()
    fetcher = FakeImageFetcher()
    settings = Settings(
        "secret", "token", tmp_path / "state.db", tmp_path / "images", "https://bot.example"
    )
    client = TestClient(create_app(settings, transport, image_fetcher=fetcher, clock=lambda: clock[0]))

    with client:
        post(client, event("@ginrai-manage", "first-manage", user_id="first"))
        post(client, event("เพิ่ม", "first-add", user_id="first"))
        post(client, event("ร้านแรก", "first-name", user_id="first"))
        post(client, event("@ginrai-manage", "second-manage", user_id="second"))
        post(client, event("เพิ่ม", "second-add", user_id="second"))
        post(client, event("ร้านสอง", "second-name", user_id="second"))
        post(client, event("https://images.example/first.jpg", "first-image", user_id="first"))
        post(client, event("https://images.example/second.jpg", "second-image", user_id="second"))

        post(client, event("@ginrai-manage", "expired-manage", user_id="expired"))
        post(client, event("เพิ่ม", "expired-add", user_id="expired"))
        clock[0] += timedelta(minutes=10)
        post(client, event("ร้านหมดอายุ", "expired-name", user_id="expired"))

    assert [reply[1][0]["text"] for reply in transport.replies if len(reply[1]) == 2] == [
        "เพิ่มร้าน ร้านแรก แล้ว",
        "เพิ่มร้าน ร้านสอง แล้ว",
    ]
    assert fetcher.urls == ["https://images.example/first.jpg", "https://images.example/second.jpg"]


def test_oversized_images_and_duplicate_names_leave_no_orphaned_entry(tmp_path: Path) -> None:
    async def public_host(_: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
        return [ipaddress.ip_address("8.8.8.8")]

    fetcher = ImageFetcher(
        client_factory=lambda **kwargs: httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, headers={"content-length": str(5 * 1024 * 1024 + 1)})
            ),
            **kwargs,
        ),
        resolve_host=public_host,
    )
    with pytest.raises(ImageValidationError, match="larger than 5 MB"):
        asyncio.run(fetcher.fetch("https://images.example/large.png"))

    image_directory = tmp_path / "images"
    transport = RecordingTransport()
    settings = Settings(
        "secret", "token", tmp_path / "state.db", image_directory, "https://bot.example"
    )
    client = TestClient(create_app(settings, transport, image_fetcher=FakeImageFetcher()))
    with client:
        add_restaurant(client, user_id="first")
        add_restaurant(client, user_id="second")

    assert [path for path in image_directory.iterdir() if path.suffix == ".png"]
    assert len(list(image_directory.iterdir())) == 1
    assert transport.replies[-1][1] == [{"type": "text", "text": "มีร้านชื่อนี้อยู่แล้ว กรุณาเริ่มใหม่"}]


def test_existing_card_one_database_migrates_before_catalog_use(tmp_path: Path) -> None:
    database_path = tmp_path / "ginraidee.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE groups (group_id TEXT PRIMARY KEY, created_at TEXT NOT NULL);
            CREATE TABLE restaurants (
                restaurant_id INTEGER PRIMARY KEY,
                group_id TEXT NOT NULL,
                display_name TEXT NOT NULL,
                source_image_url TEXT NOT NULL,
                stored_image_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE webhook_receipts (
                event_id TEXT PRIMARY KEY,
                group_id TEXT NOT NULL,
                reply_token TEXT NOT NULL,
                command TEXT NOT NULL CHECK (command IN ('@ginrai', '@ginrai-manage')),
                status TEXT NOT NULL CHECK (status IN ('processing', 'retry', 'processed')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
    settings = Settings("secret", "token", database_path, tmp_path / "images")
    client = TestClient(create_app(settings, RecordingTransport(), image_fetcher=FakeImageFetcher()))

    with client:
        assert client.get("/healthz").status_code == 200

    with sqlite3.connect(database_path) as connection:
        restaurant_columns = {row[1] for row in connection.execute("PRAGMA table_info(restaurants)")}
        webhook_columns = {row[1] for row in connection.execute("PRAGMA table_info(webhook_receipts)")}
    assert "normalized_display_name" in restaurant_columns
    assert "user_id" in webhook_columns


def test_duplicate_management_reply_is_processed_once_and_activity_refreshes_expiry(tmp_path: Path) -> None:
    clock = [datetime(2026, 10, 16, 9, 0, tzinfo=UTC)]
    transport = RecordingTransport()
    settings = Settings("secret", "token", tmp_path / "state.db", tmp_path / "images")
    client = TestClient(create_app(settings, transport, image_fetcher=FakeImageFetcher(), clock=lambda: clock[0]))
    repeated_add = event("เพิ่ม", "same-add")

    with client:
        post(client, event("@ginrai-manage", "manage"))
        post(client, repeated_add)
        post(client, repeated_add)
        clock[0] += timedelta(minutes=9)
        post(client, event("   ", "blank-name"))
        clock[0] += timedelta(minutes=9)
        post(client, event("ร้านที่ยังไม่หมดอายุ", "name-after-activity"))

    assert [reply[1][0]["text"] for reply in transport.replies] == [
        "เริ่มจัดการร้านอาหารแล้ว พิมพ์ เพิ่ม, รายการ หรือ ยกเลิก",
        "กรุณาส่งชื่อร้านอาหาร",
        "กรุณาส่งชื่อร้านอาหาร",
        "กรุณาส่งลิงก์รูปภาพ HTTPS ของร้านอาหาร",
    ]


def test_startup_moves_interrupted_unreferenced_images_to_recoverable_storage(tmp_path: Path) -> None:
    image_directory = tmp_path / "images"
    image_directory.mkdir()
    orphan_id = "a" * 32
    (image_directory / f"{orphan_id}.png").write_bytes(SAMPLE_PNG)
    settings = Settings("secret", "token", tmp_path / "state.db", image_directory)
    client = TestClient(create_app(settings, RecordingTransport(), image_fetcher=FakeImageFetcher()))

    with client:
        assert client.get("/healthz").status_code == 200

    assert not (image_directory / f"{orphan_id}.png").exists()
    assert (image_directory / "orphaned" / f"{orphan_id}.png").is_file()
