import os
from dataclasses import dataclass
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    database_url: str
    admin_id: int

    # Parsed DB fields
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    @classmethod
    def from_env(cls) -> "Config":
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN is required")

        admin_id_raw = os.getenv("ADMIN_ID")
        if not admin_id_raw:
            raise ValueError("ADMIN_ID is required")

        database_url = os.getenv(
            "DATABASE_URL", "postgresql://localhost/botseller"
        )

        parsed = urlparse(database_url)

        return cls(
            bot_token=bot_token,
            database_url=database_url,
            admin_id=int(admin_id_raw),
            db_host=parsed.hostname or "localhost",
            db_port=parsed.port or 5432,
            db_name=(parsed.path or "/botseller").lstrip("/"),
            db_user=parsed.username or "postgres",
            db_password=parsed.password or "",
        )
