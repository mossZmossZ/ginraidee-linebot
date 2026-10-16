from __future__ import annotations

from contextlib import asynccontextmanager
import hashlib
import json
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response, status

from app.commands import CommandHandler
from app.config import Settings
from app.database import Database, WebhookWork
from app.security import has_valid_line_signature
from app.transport import LineReplyTransport, NonRetryableReplyError, ReplyTransport


def create_app(
    settings: Settings | None = None, transport: ReplyTransport | None = None
) -> FastAPI:
    resolved_settings = settings or Settings.from_environment()
    database = Database(resolved_settings.database_path)
    command_handler = CommandHandler(
        database, transport or LineReplyTransport(resolved_settings.channel_access_token)
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        database.initialize()
        for work in database.resume_webhook_work():
            await _process_work(work, database, command_handler)
        yield

    app = FastAPI(title="Ginraidee LINE Bot", lifespan=lifespan)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/callback", status_code=status.HTTP_200_OK)
    async def callback(request: Request) -> Response:
        raw_body = await request.body()
        if not has_valid_line_signature(
            raw_body,
            request.headers.get("x-line-signature"),
            resolved_settings.channel_secret,
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON") from error
        if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook payload")

        for event in payload["events"]:
            if isinstance(event, dict):
                await _dispatch_event(event, database, command_handler)
        return Response(status_code=status.HTTP_200_OK)

    return app


async def _dispatch_event(
    event: dict[str, Any], database: Database, command_handler: CommandHandler
) -> None:
    source = event.get("source")
    message = event.get("message")
    if (
        event.get("type") != "message"
        or not isinstance(source, dict)
        or source.get("type") != "group"
        or not isinstance(message, dict)
        or message.get("type") != "text"
    ):
        return
    group_id = source.get("groupId")
    reply_token = event.get("replyToken")
    text = message.get("text")
    if not isinstance(group_id, str) or not isinstance(reply_token, str) or text not in {
        "@ginrai",
        "@ginrai-manage",
    }:
        return

    work = database.claim_webhook_event(_event_id(event), group_id, reply_token, text)
    if work is None:
        return
    await _process_work(work, database, command_handler, raise_on_failure=True)


async def _process_work(
    work: WebhookWork,
    database: Database,
    command_handler: CommandHandler,
    *,
    raise_on_failure: bool = False,
) -> None:
    try:
        if work.command == "@ginrai":
            await command_handler.handle_ginrai(work.group_id, work.reply_token)
        else:
            await command_handler.handle_manage(work.group_id, work.reply_token)
    except NonRetryableReplyError:
        database.mark_webhook_processed(work.event_id)
        return
    except Exception:
        database.mark_webhook_retry(work.event_id)
        if raise_on_failure:
            raise
        return
    database.mark_webhook_processed(work.event_id)


def _event_id(event: dict[str, Any]) -> str:
    identifier = event.get("webhookEventId") or event.get("eventId")
    if isinstance(identifier, str) and identifier:
        return identifier
    canonical_event = json.dumps(event, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical_event).hexdigest()
