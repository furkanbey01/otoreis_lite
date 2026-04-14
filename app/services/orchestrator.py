from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field

from app.config import Settings
from app.models.schemas import Action, TaskStatus
from app.services.executor import Executor
from app.services.planner import Planner
from app.services.policy import PolicyEngine
from app.services.state_manager import StateManager


@dataclass
class RuntimeTask:
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    approval_event: asyncio.Event = field(default_factory=asyncio.Event)


class Orchestrator:
    def __init__(self, settings: Settings, planner: Planner, executor: Executor, policy: PolicyEngine, state: StateManager):
        self.settings = settings
        self.planner = planner
        self.executor = executor
        self.policy = policy
        self.state = state
        self.runtime: dict[int, RuntimeTask] = {}

    async def create_and_start(self, goal: str, explicit_steps: list[Action] | None = None) -> int:
        plan = self.planner.make_plan(goal, explicit_steps)
        task_id = self.state.create_task(goal, plan)
        self.runtime[task_id] = RuntimeTask()
        self.state.append_log(task_id, "info", "task_created", {"steps": len(plan)})
        asyncio.create_task(self._run(task_id, plan))
        return task_id

    async def _run(self, task_id: int, plan: list[Action]) -> None:
        rt = self.runtime[task_id]
        ctx: dict = {"task_id": task_id}
        self.state.set_status(task_id, TaskStatus.running, "started")

        for idx, action in enumerate(plan, start=1):
            if rt.cancel_event.is_set():
                self.state.set_status(task_id, TaskStatus.cancelled, "cancelled by user")
                self.state.append_log(task_id, "warning", "task_cancelled", {})
                return

            self.state.set_current_step(task_id, idx - 1, f"step {idx}/{len(plan)}")
            self.state.append_log(task_id, "info", "step_start", {"step": idx, "action": action.model_dump()})

            if self.policy.needs_approval(action):
                self.state.set_status(task_id, TaskStatus.waiting_approval, f"approval needed for {action.type}")
                self.state.set_pending_approval(task_id, action)
                self.state.append_log(task_id, "info", "approval_requested", {"step": idx, "action": action.model_dump()})
                rt.approval_event.clear()
                try:
                    await asyncio.wait_for(rt.approval_event.wait(), timeout=3600)
                except TimeoutError:
                    self.state.set_status(task_id, TaskStatus.failed, "approval timeout")
                    self.state.append_log(task_id, "error", "approval_timeout", {"step": idx})
                    return
                task_row = self.state.db.get_task(task_id)
                if task_row and task_row["status"] == TaskStatus.cancelled.value:
                    return
                self.state.set_pending_approval(task_id, None)
                self.state.set_status(task_id, TaskStatus.running, "approval granted")

            try:
                result = await self.executor.run_action_with_retry(
                    action,
                    ctx,
                    retries=self.settings.max_retries,
                    timeout_sec=self.settings.default_timeout_sec,
                )
                self.state.append_log(task_id, "info", "step_ok", {"step": idx, "result": result})
            except Exception as exc:  # noqa: BLE001
                self.state.set_status(task_id, TaskStatus.failed, f"failed at step {idx}: {exc}")
                self.state.append_log(task_id, "error", "step_failed", {"step": idx, "error": str(exc)})
                return

            if idx >= self.settings.max_steps:
                self.state.set_status(task_id, TaskStatus.failed, "max steps reached")
                self.state.append_log(task_id, "error", "max_steps", {"max_steps": self.settings.max_steps})
                return

            self.state.set_current_step(task_id, idx, f"step {idx}/{len(plan)} done")

        self.state.set_status(task_id, TaskStatus.completed, "done")
        self.state.append_log(task_id, "info", "task_done", {"steps": len(plan)})

    def get_task_detail(self, task_id: int) -> dict | None:
        row = self.state.db.get_task(task_id)
        if not row:
            return None
        pending = json.loads(row["pending_approval_json"]) if row["pending_approval_json"] else None
        return {
            "id": row["id"],
            "goal": row["goal"],
            "status": row["status"],
            "summary": row["summary"],
            "current_step": row["current_step"],
            "total_steps": row["total_steps"],
            "pending_approval": pending,
            "logs": self.state.db.get_logs(task_id),
        }

    def approve(self, task_id: int, approve: bool, note: str | None = None) -> dict:
        row = self.state.db.get_task(task_id)
        if not row:
            raise ValueError("task not found")
        rt = self.runtime.get(task_id)
        if not rt:
            raise ValueError("task runtime not found")

        if approve:
            self.state.append_log(task_id, "info", "approval_granted", {"note": note})
            rt.approval_event.set()
            return {"ok": True, "message": "approved"}

        self.state.set_status(task_id, TaskStatus.cancelled, "approval denied")
        self.state.set_pending_approval(task_id, None)
        self.state.append_log(task_id, "warning", "approval_denied", {"note": note})
        rt.cancel_event.set()
        rt.approval_event.set()
        return {"ok": True, "message": "denied and cancelled"}

    def cancel(self, task_id: int) -> None:
        row = self.state.db.get_task(task_id)
        if not row:
            raise ValueError("task not found")
        rt = self.runtime.get(task_id)
        if rt:
            rt.cancel_event.set()
            rt.approval_event.set()
        self.state.set_status(task_id, TaskStatus.cancelled, "cancel requested")
        self.state.append_log(task_id, "warning", "cancel_requested", {})
