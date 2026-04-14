from pydantic import BaseModel
from pathlib import Path
import os


class Settings(BaseModel):
    app_name: str = "otoreis-lite"
    host: str = "0.0.0.0"
    port: int = 8000
    db_path: str = "./data/agent.db"
    workspace_dir: str = "./workspace"
    headless: bool = True
    default_timeout_sec: int = 20
    max_steps: int = 20
    max_retries: int = 1



def load_settings() -> Settings:
    return Settings(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        db_path=os.getenv("DB_PATH", "./data/agent.db"),
        workspace_dir=os.getenv("WORKSPACE_DIR", "./workspace"),
        headless=os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true",
        default_timeout_sec=int(os.getenv("DEFAULT_TIMEOUT_SEC", "20")),
        max_steps=int(os.getenv("MAX_STEPS", "20")),
        max_retries=int(os.getenv("MAX_RETRIES", "1")),
    )


def ensure_dirs(settings: Settings) -> None:
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    Path(settings.workspace_dir).mkdir(parents=True, exist_ok=True)
