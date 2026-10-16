from urllib.parse import urlsplit

from app.database import Database
from app.messages import (
    ADD_IMAGE_PROMPT,
    ADD_NAME_PROMPT,
    CANCELED,
    EMPTY_CATALOG,
    INVALID_IMAGE,
    LIST_EMPTY,
    LIST_MORE,
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
    ) -> None:
        self.database = database
        self.transport = transport

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
        page = _catalog_page(action)
        if page is not None:
            restaurants = self.database.list_restaurants(group_id)
            if not restaurants:
                await self.transport.reply_text(reply_token, LIST_EMPTY)
                return
            messages: list[dict[str, str]] = []
            first_index = (page - 1) * 2
            page_restaurants = restaurants[first_index : first_index + 2]
            if not page_restaurants:
                await self.transport.reply_text(reply_token, UNKNOWN_MANAGEMENT_ACTION)
                return
            for restaurant in page_restaurants:
                image_url = restaurant.source_image_url
                messages.extend(
                    [
                        {"type": "text", "text": restaurant.display_name},
                        _image_message(image_url),
                    ]
                )
            remaining_count = len(restaurants) - (first_index + len(page_restaurants))
            if remaining_count:
                messages.append(
                    {
                        "type": "text",
                        "text": LIST_MORE.format(count=remaining_count, page=page + 1),
                    }
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
        if not draft_name:
            raise RuntimeError("Management session is missing the restaurant name")
        if not _is_https_url(url):
            await self.transport.reply_text(reply_token, INVALID_IMAGE)
            return
        if not self.database.add_restaurant(group_id, draft_name, url):
            self.database.clear_management_session(group_id, user_id)
            await self.transport.reply_text(reply_token, "มีร้านชื่อนี้อยู่แล้ว กรุณาเริ่มใหม่")
            return
        self.database.clear_management_session(group_id, user_id)
        await self.transport.reply_messages(
            reply_token,
            [
                {"type": "text", "text": RESTAURANT_ADDED.format(name=draft_name)},
                _image_message(url),
            ],
        )


def _is_https_url(url: str) -> bool:
    if not url or any(character.isspace() for character in url):
        return False
    try:
        parsed = urlsplit(url)
        parsed.port
    except ValueError:
        return False
    return parsed.scheme.lower() == "https" and parsed.hostname is not None


def _catalog_page(action: str) -> int | None:
    parts = action.split()
    if parts == ["รายการ"]:
        return 1
    if len(parts) == 2 and parts[0] == "รายการ" and parts[1].isdecimal():
        page = int(parts[1])
        return page if page > 0 else None
    return None


def _image_message(url: str) -> dict[str, str]:
    return {"type": "image", "originalContentUrl": url, "previewImageUrl": url}
