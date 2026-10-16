from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
import sqlite3
from typing import Callable, Iterator


class WebhookWork:
    def __init__(
        self, event_id: str, group_id: str, user_id: str, reply_token: str, command: str
    ) -> None:
        self.event_id = event_id
        self.group_id = group_id
        self.user_id = user_id
        self.reply_token = reply_token
        self.command = command


class ManagementWork:
    def __init__(
        self, event_id: str, group_id: str, user_id: str, reply_token: str, text: str
    ) -> None:
        self.event_id = event_id
        self.group_id = group_id
        self.user_id = user_id
        self.reply_token = reply_token
        self.text = text


class ManagementSession:
    def __init__(self, step: str, draft_name: str | None) -> None:
        self.step = step
        self.draft_name = draft_name


class Restaurant:
    def __init__(self, display_name: str, source_image_url: str) -> None:
        self.display_name = display_name
        self.source_image_url = source_image_url


class Database:
    def __init__(self, path: Path, clock: Callable[[], datetime] | None = None) -> None:
        self.path = path
        self.clock = clock or _default_clock

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
                    normalized_display_name TEXT NOT NULL,
                    source_image_url TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS webhook_receipts (
                    event_id TEXT PRIMARY KEY,
                    group_id TEXT NOT NULL REFERENCES groups(group_id),
                    user_id TEXT NOT NULL,
                    reply_token TEXT NOT NULL,
                    command TEXT NOT NULL CHECK (command IN ('@ginrai', '@ginrai-manage')),
                    status TEXT NOT NULL CHECK (status IN ('processing', 'retry', 'processed')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS restaurants_group_id_idx ON restaurants(group_id);

                CREATE TABLE IF NOT EXISTS management_sessions (
                    group_id TEXT NOT NULL REFERENCES groups(group_id),
                    user_id TEXT NOT NULL,
                    step TEXT NOT NULL CHECK (step IN ('action', 'name', 'image')),
                    draft_name TEXT,
                    expires_at TEXT NOT NULL,
                    PRIMARY KEY (group_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS management_receipts (
                    event_id TEXT PRIMARY KEY,
                    group_id TEXT NOT NULL REFERENCES groups(group_id),
                    user_id TEXT NOT NULL,
                    reply_token TEXT NOT NULL,
                    text TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('processing', 'retry', 'processed')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                """
            )
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(restaurants)").fetchall()
            }
            if "normalized_display_name" not in columns:
                connection.execute("ALTER TABLE restaurants ADD COLUMN normalized_display_name TEXT")
                connection.execute(
                    "UPDATE restaurants SET normalized_display_name = lower(trim(display_name)) "
                    "WHERE normalized_display_name IS NULL"
                )
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS restaurants_group_normalized_name_idx "
                "ON restaurants(group_id, normalized_display_name)"
            )
            webhook_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(webhook_receipts)").fetchall()
            }
            if "user_id" not in webhook_columns:
                connection.execute(
                    "ALTER TABLE webhook_receipts ADD COLUMN user_id TEXT NOT NULL DEFAULT ''"
                )

    def restaurant_count(self, group_id: str) -> int:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM restaurants WHERE group_id = ?", (group_id,)
            ).fetchone()
        return int(row[0])

    def begin_management(self, group_id: str, user_id: str) -> None:
        self._ensure_group(group_id)
        self._save_session(group_id, user_id, "action", None)

    def active_management_session(self, group_id: str, user_id: str) -> ManagementSession | None:
        now = self._utc_now()
        with self._connection() as connection:
            row = connection.execute(
                "SELECT step, draft_name FROM management_sessions "
                "WHERE group_id = ? AND user_id = ? AND expires_at > ?",
                (group_id, user_id, now),
            ).fetchone()
            connection.execute(
                "DELETE FROM management_sessions WHERE group_id = ? AND user_id = ? AND expires_at <= ?",
                (group_id, user_id, now),
            )
            if row:
                connection.execute(
                    "UPDATE management_sessions SET expires_at = ? WHERE group_id = ? AND user_id = ?",
                    (self._session_expiry(), group_id, user_id),
                )
        return ManagementSession(*row) if row else None

    def save_management_name(self, group_id: str, user_id: str, name: str) -> None:
        self._save_session(group_id, user_id, "image", name)

    def begin_add_restaurant(self, group_id: str, user_id: str) -> None:
        self._save_session(group_id, user_id, "name", None)

    def clear_management_session(self, group_id: str, user_id: str) -> None:
        with self._connection() as connection:
            connection.execute(
                "DELETE FROM management_sessions WHERE group_id = ? AND user_id = ?", (group_id, user_id)
            )

    def claim_management_event(
        self, event_id: str, group_id: str, user_id: str, reply_token: str, text: str
    ) -> ManagementWork | None:
        now = self._utc_now()
        with self._connection() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO groups(group_id, created_at) VALUES (?, ?)",
                (group_id, now),
            )
            inserted = connection.execute(
                """
                INSERT OR IGNORE INTO management_receipts(
                    event_id, group_id, user_id, reply_token, text, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'processing', ?, ?)
                """,
                (event_id, group_id, user_id, reply_token, text, now, now),
            ).rowcount
            if inserted:
                return ManagementWork(event_id, group_id, user_id, reply_token, text)
            claimed = connection.execute(
                "UPDATE management_receipts SET status = 'processing', updated_at = ? "
                "WHERE event_id = ? AND status = 'retry'",
                (now, event_id),
            ).rowcount
            if not claimed:
                return None
            row = connection.execute(
                "SELECT group_id, user_id, reply_token, text FROM management_receipts WHERE event_id = ?",
                (event_id,),
            ).fetchone()
        return ManagementWork(event_id, *row)

    def resume_management_work(self) -> list[ManagementWork]:
        now = self._utc_now()
        with self._connection() as connection:
            connection.execute(
                "UPDATE management_receipts SET status = 'retry', updated_at = ? "
                "WHERE status = 'processing'",
                (now,),
            )
            rows = connection.execute(
                "SELECT event_id, group_id, user_id, reply_token, text FROM management_receipts "
                "WHERE status = 'retry' ORDER BY created_at"
            ).fetchall()
            connection.execute(
                "UPDATE management_receipts SET status = 'processing', updated_at = ? "
                "WHERE status = 'retry'",
                (now,),
            )
        return [ManagementWork(*row) for row in rows]

    def mark_management_processed(self, event_id: str) -> None:
        self._set_management_status(event_id, "processed")

    def mark_management_retry(self, event_id: str) -> None:
        self._set_management_status(event_id, "retry")

    def add_restaurant(self, group_id: str, display_name: str, source_image_url: str) -> bool:
        normalized_name = _normalize_name(display_name)
        now = self._utc_now()
        with self._connection() as connection:
            inserted = connection.execute(
                """
                INSERT OR IGNORE INTO restaurants(
                    group_id, display_name, normalized_display_name, source_image_url,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (group_id, display_name, normalized_name, source_image_url, now, now),
            ).rowcount
        return bool(inserted)

    def list_restaurants(self, group_id: str) -> list[Restaurant]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT display_name, source_image_url FROM restaurants "
                "WHERE group_id = ? ORDER BY restaurant_id",
                (group_id,),
            ).fetchall()
        return [Restaurant(*row) for row in rows]

    def _ensure_group(self, group_id: str) -> None:
        with self._connection() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO groups(group_id, created_at) VALUES (?, ?)",
                (group_id, self._utc_now()),
            )

    def _save_session(self, group_id: str, user_id: str, step: str, draft_name: str | None) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO management_sessions(group_id, user_id, step, draft_name, expires_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(group_id, user_id) DO UPDATE SET
                    step = excluded.step,
                    draft_name = excluded.draft_name,
                    expires_at = excluded.expires_at
                """,
                (group_id, user_id, step, draft_name, self._session_expiry()),
            )

    def claim_webhook_event(
        self, event_id: str, group_id: str, user_id: str, reply_token: str, command: str
    ) -> WebhookWork | None:
        """Atomically persist a command and its group before any reply is sent."""
        now = self._utc_now()
        with self._connection() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO groups(group_id, created_at) VALUES (?, ?)",
                (group_id, now),
            )
            inserted = connection.execute(
                """
                INSERT OR IGNORE INTO webhook_receipts(
                    event_id, group_id, user_id, reply_token, command, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, 'processing', ?, ?)
                """,
                (event_id, group_id, user_id, reply_token, command, now, now),
            ).rowcount
            if inserted:
                return WebhookWork(event_id, group_id, user_id, reply_token, command)
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
                "SELECT group_id, user_id, reply_token, command FROM webhook_receipts WHERE event_id = ?",
                (event_id,),
            ).fetchone()
        return WebhookWork(event_id, row[0], row[1], row[2], row[3])

    def resume_webhook_work(self) -> list[WebhookWork]:
        """Return work interrupted by a prior single-worker process for replay."""
        now = self._utc_now()
        with self._connection() as connection:
            connection.execute(
                "UPDATE webhook_receipts SET status = 'retry', updated_at = ? "
                "WHERE status = 'processing'",
                (now,),
            )
            rows = connection.execute(
                """
                SELECT event_id, group_id, user_id, reply_token, command
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
                (self._utc_now(), event_id),
            )

    def mark_webhook_retry(self, event_id: str) -> None:
        with self._connection() as connection:
            connection.execute(
                "UPDATE webhook_receipts SET status = 'retry', updated_at = ? WHERE event_id = ?",
                (self._utc_now(), event_id),
            )

    def _utc_now(self) -> str:
        return self.clock().astimezone(UTC).isoformat()

    def _session_expiry(self) -> str:
        return (self.clock().astimezone(UTC) + timedelta(minutes=10)).isoformat()

    def _set_management_status(self, event_id: str, status: str) -> None:
        with self._connection() as connection:
            connection.execute(
                "UPDATE management_receipts SET status = ?, updated_at = ? WHERE event_id = ?",
                (status, self._utc_now(), event_id),
            )


def _normalize_name(name: str) -> str:
    return " ".join(name.split()).casefold()


def _default_clock() -> datetime:
    return datetime.now(UTC)
