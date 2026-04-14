from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.config import ensure_dirs, load_settings
from app.core.db import DB
from app.mcp.routes import router as mcp_router
from app.models.schemas import RuntimeSettings
from app.services.executor import Executor
from app.services.orchestrator import Orchestrator
from app.services.planner import Planner
from app.services.policy import PolicyEngine
from app.services.settings_manager import SettingsManager
from app.services.state_manager import StateManager
from app.tools.browser_tool import BrowserTool
from app.tools.filesystem_tool import FilesystemTool

settings = load_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dirs(settings)
    db = DB(settings.db_path)
    db.init()

    browser = BrowserTool(headless=settings.headless)
    fs_tool = FilesystemTool(settings.workspace_dir)

    planner = Planner()
    policy = PolicyEngine()
    state = StateManager(db)
    runtime_defaults = RuntimeSettings(
        default_timeout_sec=settings.default_timeout_sec,
        max_steps=settings.max_steps,
        max_retries=settings.max_retries,
        require_approval=True,
    )
    settings_manager = SettingsManager(db, runtime_defaults)
    executor = Executor(browser, fs_tool, settings.default_timeout_sec)
    orchestrator = Orchestrator(planner, executor, policy, state, settings_manager.get)

    app.state.db = db
    app.state.orchestrator = orchestrator
    app.state.settings_manager = settings_manager
    app.state.browser = browser
    yield
    await browser.stop()


app = FastAPI(title="otoreis-lite", lifespan=lifespan)
app.include_router(api_router, prefix="/api", tags=["api"])
app.include_router(mcp_router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/health")
async def health():
    return {"ok": True}
