from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    queued = "queued"
    running = "running"
    waiting_approval = "waiting_approval"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ActionType(str, Enum):
    navigate = "navigate"
    click = "click"
    type = "type"
    scroll = "scroll"
    extract_text = "extract_text"
    save_json = "save_json"
    read_file = "read_file"
    write_file = "write_file"
    form_submit = "form_submit"
    login = "login"
    send_mail = "send_mail"
    delete_file = "delete_file"
    purchase = "purchase"
    system_change = "system_change"


class Action(BaseModel):
    type: ActionType
    args: dict[str, Any] = Field(default_factory=dict)


class TaskCreateRequest(BaseModel):
    goal: str
    plan_hint: str | None = None
    steps: list[Action] | None = None
    require_approval: bool = True
    timeout_sec: int | None = None
    max_steps: int | None = None
    max_retries: int | None = None


class TaskResponse(BaseModel):
    id: int
    goal: str
    status: TaskStatus


class TaskDetailResponse(BaseModel):
    id: int
    goal: str
    status: TaskStatus
    summary: str
    current_step: int
    total_steps: int
    pending_approval: Action | None = None
    options: dict[str, Any] = Field(default_factory=dict)
    logs: list[dict[str, Any]]


class ApprovalRequest(BaseModel):
    approve: bool
    note: str | None = None


class MCPToolCall(BaseModel):
    tool: Literal["create_task", "task_status", "approve_task", "cancel_task", "settings_get", "settings_set"]
    arguments: dict[str, Any]


class RuntimeSettings(BaseModel):
    default_timeout_sec: int = 20
    max_steps: int = 20
    max_retries: int = 1
    require_approval: bool = True


class RuntimeSettingsUpdate(BaseModel):
    default_timeout_sec: int | None = None
    max_steps: int | None = None
    max_retries: int | None = None
    require_approval: bool | None = None
