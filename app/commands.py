from pathlib import Path
from urllib.parse import urlsplit

from app.database import Database
from app.images import ImageFetcher, ImageValidationError, delete_image, save_normalized_image
from app.messages import (
    ADD_IMAGE_PROMPT,
    ADD_NAME_PROMPT,
    CANCELED,
    EMPTY_CATALOG,
    INVALID_IMAGE,
    LIST_EMPTY,
    MANAGEMENT_STARTED,
    RESTAURANT_ADDED,
    UNKNOWN_MANAGEMENT_ACTION,
)
from app.transport import ReplyTransport


class CommandHandler:
    def __init__(
        self,
        database: Database,
        transport: ReplyTransport,
        image_fetcher: ImageFetcher | None = None,
        image_directory: Path | None = None,
        public_base_url: str = "http://localhost:8000",
    ) -> None:
        self.database = database
        self.transport = transport
        self.image_fetcher = image_fetcher or ImageFetcher()
        self.image_directory = image_directory
        self.public_base_url = public_base_url.rstrip("/")

    async def handle_ginrai(self, group_id: str, reply_token: str) -> None:
        if self.database.restaurant_count(group_id) == 0:
            await self.transport.reply_text(reply_token, EMPTY_CATALOG)

    async def handle_manage(self, group_id: str, user_id: str, reply_token: str) -> None:
        self.database.begin_management(group_id, user_id)
        await self.transport.reply_text(reply_token, MANAGEMENT_STARTED)

    async def handle_management_input(
        self, group_id: str, user_id: str, reply_token: str, text: str
    ) -> None:
        session = self.database.active_management_session(group_id, user_id)
        if session is None:
            return
        normalized_text = text.strip()
        if normalized_text == "ยกเลิก":
            self.database.clear_management_session(group_id, user_id)
            await self.transport.reply_text(reply_token, CANCELED)
            return
        if session.step == "action":
            await self._handle_management_action(group_id, user_id, reply_token, normalized_text)
            return
        if session.step == "name":
            if not normalized_text:
                await self.transport.reply_text(reply_token, ADD_NAME_PROMPT)
                return
            self.database.save_management_name(group_id, user_id, normalized_text)
            await self.transport.reply_text(reply_token, ADD_IMAGE_PROMPT)
            return
        await self._handle_image(group_id, user_id, reply_token, normalized_text, session.draft_name)

    async def _handle_management_action(
        self, group_id: str, user_id: str, reply_token: str, action: str
    ) -> None:
        if action == "เพิ่ม":
            self.database.begin_add_restaurant(group_id, user_id)
            await self.transport.reply_text(reply_token, ADD_NAME_PROMPT)
            return
        if action == "รายการ":
            restaurants = self.database.list_restaurants(group_id)
            if not restaurants:
                await self.transport.reply_text(reply_token, LIST_EMPTY)
                return
            messages: list[dict[str, str]] = []
            for restaurant in restaurants[:5]:
                image_url = self._image_url(restaurant.stored_image_id)
                messages.extend(
                    [
                        {"type": "text", "text": restaurant.display_name},
                        {
                            "type": "image",
                            "originalContentUrl": image_url,
                            "previewImageUrl": image_url,
                        },
                    ]
                )
            await self.transport.reply_messages(reply_token, messages)
            return
        await self.transport.reply_text(reply_token, UNKNOWN_MANAGEMENT_ACTION)

    async def _handle_image(
        self,
        group_id: str,
        user_id: str,
        reply_token: str,
        url: str,
        draft_name: str | None,
    ) -> None:
        if not draft_name or self.image_directory is None:
            raise RuntimeError("Management image storage is not configured")
        try:
            downloaded = await self.image_fetcher.fetch(url)
        except (ImageValidationError, ValueError):
            await self.transport.reply_text(reply_token, INVALID_IMAGE)
            return
        if not _is_https_url(self.public_base_url):
            await self.transport.reply_text(reply_token, "ตั้งค่า APP_PUBLIC_BASE_URL เป็น HTTPS ก่อนเพิ่มรูปภาพ")
            return
        try:
            image_id = save_normalized_image(self.image_directory, downloaded.content)
        except (ImageValidationError, ValueError):
            await self.transport.reply_text(reply_token, INVALID_IMAGE)
            return
        if not self.database.add_restaurant(group_id, draft_name, downloaded.source_url, image_id):
            delete_image(self.image_directory, image_id)
            self.database.clear_management_session(group_id, user_id)
            await self.transport.reply_text(reply_token, "มีร้านชื่อนี้อยู่แล้ว กรุณาเริ่มใหม่")
            return
        self.database.clear_management_session(group_id, user_id)
        image_url = self._image_url(image_id)
        await self.transport.reply_messages(
            reply_token,
            [
                {"type": "text", "text": RESTAURANT_ADDED.format(name=draft_name)},
                {
                    "type": "image",
                    "originalContentUrl": image_url,
                    "previewImageUrl": image_url,
                },
            ],
        )

    def _image_url(self, image_id: str) -> str:
        return f"{self.public_base_url}/images/{image_id}"


def _is_https_url(url: str) -> bool:
    parsed = urlsplit(url)
    return parsed.scheme == "https" and parsed.hostname is not None
