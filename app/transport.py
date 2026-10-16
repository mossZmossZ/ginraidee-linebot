from typing import Protocol

import httpx


class ReplyTransport(Protocol):
    async def reply_text(self, reply_token: str, text: str) -> None: ...


class LineReplyTransport:
    def __init__(self, channel_access_token: str) -> None:
        self.channel_access_token = channel_access_token

    async def reply_text(self, reply_token: str, text: str) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.line.me/v2/bot/message/reply",
                headers={"Authorization": f"Bearer {self.channel_access_token}"},
                json={
                    "replyToken": reply_token,
                    "messages": [{"type": "text", "text": text}],
                },
            )
        response.raise_for_status()
