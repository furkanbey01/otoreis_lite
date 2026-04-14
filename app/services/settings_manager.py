from __future__ import annotations

from app.core.db import DB
from app.models.schemas import RuntimeSettings, RuntimeSettingsUpdate


class SettingsManager:
    def __init__(self, db: DB, defaults: RuntimeSettings):
        self.db = db
        self.defaults = defaults

    def get(self) -> RuntimeSettings:
        return RuntimeSettings(
            default_timeout_sec=int(self.db.get_setting("default_timeout_sec", self.defaults.default_timeout_sec)),
            max_steps=int(self.db.get_setting("max_steps", self.defaults.max_steps)),
            max_retries=int(self.db.get_setting("max_retries", self.defaults.max_retries)),
            require_approval=bool(self.db.get_setting("require_approval", self.defaults.require_approval)),
        )

    def update(self, patch: RuntimeSettingsUpdate) -> RuntimeSettings:
        current = self.get()
        next_settings = current.model_copy(update=patch.model_dump(exclude_none=True))

        if next_settings.default_timeout_sec < 3:
            next_settings.default_timeout_sec = 3
        if next_settings.max_steps < 1:
            next_settings.max_steps = 1
        if next_settings.max_retries < 0:
            next_settings.max_retries = 0

        self.db.set_setting("default_timeout_sec", next_settings.default_timeout_sec)
        self.db.set_setting("max_steps", next_settings.max_steps)
        self.db.set_setting("max_retries", next_settings.max_retries)
        self.db.set_setting("require_approval", next_settings.require_approval)
        return next_settings
