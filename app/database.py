from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
import sqlite3
from typing import Iterator


class WebhookWork:
    def __init__(self, event_id: str, group_id: str, reply_token: str, command: str) -> None:
        self.event_id = event_id
        self.group_id = group_id
        self.reply_token = reply_token
        self.command = command


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS groups (
                    group_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS restaurants (
                    restaurant_id INTEGER PRIMARY KEY,
                    group_id TEXT NOT NULL REFERENCES groups(group_id),
                    display_name TEXT NOT NULL,
                    source_image_url TEXT NOT NULL,
                    stored_image_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS webhook_receipts (
                    event_id TEXT PRIMARY KEY,
                    group_id TEXT NOT NULL REFERENCES groups(group_id),
                    reply_token TEXT NOT NULL,
                    command TEXT NOT NULL CHECK (command IN ('@ginrai', '@ginrai-manage')),
                    status TEXT NOT NULL CHECK (status IN ('processing', 'retry', 'processed')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS restaurants_group_id_idx ON restaurants(group_id);
                """
            )
    def restaurant_count(self, group_id: str) -> int:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM restaurants WHERE group_id = ?", (group_id,)
            ).fetchone()
        return int(row[0])

    def claim_webhook_event(
        self, event_id: str, group_id: str, reply_token: str, command: str
    ) -> WebhookWork | None:
        """Atomically persist a command and its group before any reply is sent."""
        now = _utc_now()
        with self._connection() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO groups(group_id, created_at) VALUES (?, ?)",
                (group_id, now),
            )
            inserted = connection.execute(
                """
                INSERT OR IGNORE INTO webhook_receipts(
                    event_id, group_id, reply_token, command, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, 'processing', ?, ?)
                """,
                (event_id, group_id, reply_token, command, now, now),
            ).rowcount
            if inserted:
                return WebhookWork(event_id, group_id, reply_token, command)
            claimed = connection.execute(
                """
                UPDATE webhook_receipts
                SET status = 'processing', updated_at = ?
                WHERE event_id = ? AND status = 'retry'
                """,
                (now, event_id),
            ).rowcount
            if not claimed:
                return None
            row = connection.execute(
                "SELECT group_id, reply_token, command FROM webhook_receipts WHERE event_id = ?",
                (event_id,),
            ).fetchone()
        return WebhookWork(event_id, row[0], row[1], row[2])

    def resume_webhook_work(self) -> list[WebhookWork]:
        """Return work interrupted by a prior single-worker process for replay."""
        now = _utc_now()
        with self._connection() as connection:
            connection.execute(
                "UPDATE webhook_receipts SET status = 'retry', updated_at = ? "
                "WHERE status = 'processing'",
                (now,),
            )
            rows = connection.execute(
                """
                SELECT event_id, group_id, reply_token, command
                FROM webhook_receipts
                WHERE status = 'retry'
                ORDER BY created_at
                """
            ).fetchall()
            connection.execute(
                "UPDATE webhook_receipts SET status = 'processing', updated_at = ? "
                "WHERE status = 'retry'",
                (now,),
            )
        return [WebhookWork(*row) for row in rows]

    def mark_webhook_processed(self, event_id: str) -> None:
        with self._connection() as connection:
            connection.execute(
                "UPDATE webhook_receipts SET status = 'processed', updated_at = ? WHERE event_id = ?",
                (_utc_now(), event_id),
            )

    def mark_webhook_retry(self, event_id: str) -> None:
        with self._connection() as connection:
            connection.execute(
                "UPDATE webhook_receipts SET status = 'retry', updated_at = ? WHERE event_id = ?",
                (_utc_now(), event_id),
            )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
