from app.database import Database
from app.messages import EMPTY_CATALOG, MANAGEMENT_STARTED
from app.transport import ReplyTransport


class CommandHandler:
    def __init__(self, database: Database, transport: ReplyTransport) -> None:
        self.database = database
        self.transport = transport

    async def handle_ginrai(self, group_id: str, reply_token: str) -> None:
        self.database.ensure_group(group_id)
        if self.database.restaurant_count(group_id) == 0:
            await self.transport.reply_text(reply_token, EMPTY_CATALOG)

    async def handle_manage(self, group_id: str, reply_token: str) -> None:
        self.database.ensure_group(group_id)
        await self.transport.reply_text(reply_token, MANAGEMENT_STARTED)
