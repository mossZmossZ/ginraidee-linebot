from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    channel_secret: str
    channel_access_token: str
    database_path: Path

    @classmethod
    def from_environment(cls) -> "Settings":
        secret = os.environ.get("LINE_CHANNEL_SECRET", "")
        access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
        if not secret or not access_token:
            raise RuntimeError(
                "LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN must be set before starting the bot."
            )
        database_path = Path(os.environ.get("APP_DATABASE_PATH", "/data/ginraidee.db"))
        return cls(
            channel_secret=secret,
            channel_access_token=access_token,
            database_path=database_path,
        )
