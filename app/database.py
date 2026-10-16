from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
import sqlite3
from typing import Iterator


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
                    status TEXT NOT NULL CHECK (status IN ('processing', 'retry', 'processed')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS restaurants_group_id_idx ON restaurants(group_id);
                """
            )
            # This deployment uses one worker. Anything marked processing before a
            # process restart can safely be retried when LINE redelivers it.
            connection.execute(
                "UPDATE webhook_receipts SET status = 'retry', updated_at = ? "
                "WHERE status = 'processing'",
                (_utc_now(),),
            )

    def ensure_group(self, group_id: str) -> None:
        now = _utc_now()
        with self._connection() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO groups(group_id, created_at) VALUES (?, ?)",
                (group_id, now),
            )

    def restaurant_count(self, group_id: str) -> int:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM restaurants WHERE group_id = ?", (group_id,)
            ).fetchone()
        return int(row[0])

    def claim_webhook_event(self, event_id: str) -> bool:
        """Claim a webhook receipt once; failed delivery can be retried by LINE."""
        now = _utc_now()
        with self._connection() as connection:
            inserted = connection.execute(
                """
                INSERT OR IGNORE INTO webhook_receipts(event_id, status, created_at, updated_at)
                VALUES (?, 'processing', ?, ?)
                """,
                (event_id, now, now),
            ).rowcount
            if inserted:
                return True
            claimed = connection.execute(
                """
                UPDATE webhook_receipts
                SET status = 'processing', updated_at = ?
                WHERE event_id = ? AND status = 'retry'
                """,
                (now, event_id),
            ).rowcount
        return bool(claimed)

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
