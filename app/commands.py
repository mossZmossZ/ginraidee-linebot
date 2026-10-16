from urllib.parse import urlsplit

from app.database import Database, ManagementSession
from app.messages import (
    ADD_IMAGE_PROMPT,
    ADD_NAME_PROMPT,
    CANCELED,
    DELETE_CONFIRM_PROMPT,
    DELETE_CONFIRM_REQUIRED,
    EDIT_RESTAURANT_DUPLICATE,
    EDIT_IMAGE_PROMPT,
    EDIT_NAME_PROMPT,
    EMPTY_CATALOG,
    INVALID_EDIT_IMAGE,
    INVALID_IMAGE,
    INVALID_NAME,
    LIST_EMPTY,
    LIST_MORE,
    MANAGEMENT_STARTED,
    RESTAURANT_DELETED,
    RESTAURANT_DUPLICATE,
    RESTAURANT_NOT_FOUND,
    RESTAURANT_ADDED,
    RESTAURANT_UPDATED,
    SELECTION_ROW,
    SELECT_RESTAURANT_PROMPT,
    STALE_RESTAURANT,
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
            await self._handle_management_action(
                group_id, user_id, reply_token, normalized_text, session
            )
            return
        if session.step == "name":
            if not normalized_text:
                await self.transport.reply_text(reply_token, INVALID_NAME)
                return
            if session.draft_action == "edit-name":
                self.database.save_edit_name(group_id, user_id, normalized_text)
                await self.transport.reply_text(reply_token, EDIT_IMAGE_PROMPT)
            else:
                self.database.save_management_name(group_id, user_id, normalized_text)
                await self.transport.reply_text(reply_token, ADD_IMAGE_PROMPT)
            return
        await self._handle_image(group_id, user_id, reply_token, normalized_text, session)

    async def _handle_management_action(
        self,
        group_id: str,
        user_id: str,
        reply_token: str,
        action: str,
        session: ManagementSession,
    ) -> None:
        if session.draft_action in {"edit-select", "delete-select"}:
            page = _catalog_page(action)
            if page is not None:
                await self._send_selection_page(group_id, user_id, reply_token, page)
                return
            if action.isdecimal():
                restaurant_id = _restaurant_id(action)
                if restaurant_id is None:
                    await self.transport.reply_text(reply_token, RESTAURANT_NOT_FOUND)
                    return
                restaurant = self.database.select_restaurant(group_id, user_id, restaurant_id)
                if restaurant is None:
                    await self.transport.reply_text(reply_token, RESTAURANT_NOT_FOUND)
                    return
                if session.draft_action == "edit-select":
                    await self.transport.reply_text(reply_token, EDIT_NAME_PROMPT)
                else:
                    await self.transport.reply_text(
                        reply_token,
                        DELETE_CONFIRM_PROMPT.format(name=restaurant.display_name),
                    )
                return
            await self.transport.reply_text(reply_token, SELECT_RESTAURANT_PROMPT)
            return

        if session.draft_action == "delete-confirm":
            if action != "ยืนยัน":
                await self.transport.reply_text(reply_token, DELETE_CONFIRM_REQUIRED)
                return
            restaurant_id = session.selected_restaurant_id
            selection_key = session.selected_restaurant_key
            version = session.selected_version
            if restaurant_id is None or selection_key is None or version is None:
                raise RuntimeError("Delete session is missing its restaurant selection")
            deleted = self.database.delete_restaurant(
                group_id, restaurant_id, selection_key, version
            )
            if not deleted:
                self.database.clear_management_session(group_id, user_id)
                await self.transport.reply_text(reply_token, STALE_RESTAURANT)
                return
            self.database.clear_management_session(group_id, user_id)
            await self.transport.reply_text(
                reply_token, RESTAURANT_DELETED.format(name=session.draft_name or "")
            )
            return

        if action == "เพิ่ม":
            self.database.begin_add_restaurant(group_id, user_id)
            await self.transport.reply_text(reply_token, ADD_NAME_PROMPT)
            return
        if action in {"แก้ไข", "ลบ"}:
            selection_action = "edit" if action == "แก้ไข" else "delete"
            self.database.begin_restaurant_selection(group_id, user_id, selection_action)
            await self._send_selection_page(group_id, user_id, reply_token, 1)
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

    async def _send_selection_page(
        self, group_id: str, user_id: str, reply_token: str, page: int
    ) -> None:
        restaurants = self.database.list_selection_restaurants(group_id, user_id)
        if not restaurants:
            await self.transport.reply_text(reply_token, LIST_EMPTY)
            return
        first_index = (page - 1) * 2
        page_restaurants = restaurants[first_index : first_index + 2]
        if not page_restaurants:
            await self.transport.reply_text(reply_token, UNKNOWN_MANAGEMENT_ACTION)
            return
        messages: list[dict[str, str]] = [
            {"type": "text", "text": SELECT_RESTAURANT_PROMPT}
        ]
        messages.extend(
            {
                "type": "text",
                "text": SELECTION_ROW.format(
                    id=restaurant.restaurant_id, name=restaurant.display_name
                ),
            }
            for restaurant in page_restaurants
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

    async def _handle_image(
        self,
        group_id: str,
        user_id: str,
        reply_token: str,
        url: str,
        session: ManagementSession,
    ) -> None:
        draft_name = session.draft_name
        if not draft_name:
            raise RuntimeError("Management session is missing the restaurant name")
        if not _is_https_url(url):
            message = INVALID_EDIT_IMAGE if session.draft_action == "edit-image" else INVALID_IMAGE
            await self.transport.reply_text(reply_token, message)
            return
        if session.draft_action == "edit-image":
            restaurant_id = session.selected_restaurant_id
            selection_key = session.selected_restaurant_key
            version = session.selected_version
            if restaurant_id is None or selection_key is None or version is None:
                raise RuntimeError("Edit session is missing its restaurant selection")
            result = self.database.update_restaurant(
                group_id,
                restaurant_id,
                selection_key,
                version,
                draft_name,
                url,
            )
            if result == "duplicate":
                self.database.retry_edit_name(group_id, user_id)
                await self.transport.reply_text(
                    reply_token, f"{EDIT_RESTAURANT_DUPLICATE} {EDIT_NAME_PROMPT}"
                )
                return
            if result == "stale":
                self.database.clear_management_session(group_id, user_id)
                await self.transport.reply_text(reply_token, STALE_RESTAURANT)
                return
            self.database.clear_management_session(group_id, user_id)
            await self.transport.reply_messages(
                reply_token,
                [
                    {"type": "text", "text": RESTAURANT_UPDATED.format(name=draft_name)},
                    _image_message(url),
                ],
            )
            return
        if not self.database.add_restaurant(group_id, draft_name, url):
            self.database.clear_management_session(group_id, user_id)
            await self.transport.reply_text(reply_token, RESTAURANT_DUPLICATE)
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
    if (
        len(parts) == 2
        and parts[0] == "รายการ"
        and parts[1].isdecimal()
        and len(parts[1]) <= 9
    ):
        page = int(parts[1])
        return page if page > 0 else None
    return None


def _restaurant_id(value: str) -> int | None:
    if len(value) > 19:
        return None
    restaurant_id = int(value)
    return restaurant_id if 0 <= restaurant_id <= 9_223_372_036_854_775_807 else None


def _image_message(url: str) -> dict[str, str]:
    return {"type": "image", "originalContentUrl": url, "previewImageUrl": url}
