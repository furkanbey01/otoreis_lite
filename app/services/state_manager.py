from __future__ import annotations

import json
from typing import Any
from app.core.db import DB
from app.models.schemas import TaskStatus, Action


class StateManager:
    def __init__(self, db: DB):
        self.db = db

    def create_task(self, goal: str, plan: list[Action]) -> int:
        return self.db.create_task(goal, TaskStatus.queued.value, [a.model_dump() for a in plan])

    def set_status(self, task_id: int, status: TaskStatus, summary: str | None = None) -> None:
        payload: dict[str, Any] = {"status": status.value}
        if summary is not None:
            payload["summary"] = summary
        self.db.update_task(task_id, **payload)

    def set_current_step(self, task_id: int, step: int, summary: str | None = None) -> None:
        payload: dict[str, Any] = {"current_step": step}
        if summary is not None:
            payload["summary"] = summary
        self.db.update_task(task_id, **payload)

    def set_pending_approval(self, task_id: int, action: Action | None) -> None:
        self.db.update_task(task_id, pending_approval_json=json.dumps(action.model_dump()) if action else None)

    def append_log(self, task_id: int, level: str, event: str, data: dict[str, Any]) -> None:
        self.db.add_log(task_id, level, event, data)
