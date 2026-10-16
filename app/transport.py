from typing import Protocol

import httpx


class ReplyTransport(Protocol):
    async def reply_text(self, reply_token: str, text: str) -> None: ...


class NonRetryableReplyError(Exception):
    """LINE rejected a reply token, so replaying this reply cannot recover it."""


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
        if 400 <= response.status_code < 500 and response.status_code != 429:
            # Reply messages have no LINE retry-key support. In the uncertain
            # timeout-after-acceptance case, retrying a one-use token is rejected
            # and must not create an endless durable retry loop.
            raise NonRetryableReplyError(f"LINE rejected the reply: HTTP {response.status_code}")
        response.raise_for_status()
