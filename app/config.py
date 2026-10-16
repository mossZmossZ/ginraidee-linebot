from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    channel_secret: str
    channel_access_token: str
    database_path: Path
    image_directory: Path | None = None
    public_base_url: str = "http://localhost:8000"

    @classmethod
    def from_environment(cls) -> "Settings":
        secret = os.environ.get("LINE_CHANNEL_SECRET", "")
        access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
        if not secret or not access_token:
            raise RuntimeError(
                "LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN must be set before starting the bot."
            )
        database_path = Path(os.environ.get("APP_DATABASE_PATH", "/data/ginraidee.db"))
        public_base_url = os.environ.get("APP_PUBLIC_BASE_URL", "http://localhost:8000")
        return cls(
            channel_secret=secret,
            channel_access_token=access_token,
            database_path=database_path,
            image_directory=Path(os.environ.get("APP_IMAGE_DIRECTORY", str(database_path.parent / "images"))),
            public_base_url=public_base_url,
        )
