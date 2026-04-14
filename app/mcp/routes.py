from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.schemas import MCPToolCall, RuntimeSettingsUpdate, TaskCreateRequest
from app.services.orchestrator import Orchestrator
from app.services.settings_manager import SettingsManager


router = APIRouter(prefix="/mcp", tags=["mcp"])


def get_orchestrator(request: Request) -> Orchestrator:
    return request.app.state.orchestrator


def get_settings_manager(request: Request) -> SettingsManager:
    return request.app.state.settings_manager


@router.get("/tools")
async def list_tools():
    return {
        "tools": [
            {
                "name": "create_task",
                "description": "Create and run an agent task",
                "input_schema": {"goal": "string", "steps": "optional action list"},
            },
            {"name": "task_status", "description": "Get task detail by id", "input_schema": {"task_id": "int"}},
            {
                "name": "approve_task",
                "description": "Approve/deny pending action",
                "input_schema": {"task_id": "int", "approve": "bool", "note": "optional"},
            },
            {"name": "cancel_task", "description": "Cancel task", "input_schema": {"task_id": "int"}},
            {"name": "settings_get", "description": "Get runtime settings", "input_schema": {}},
            {
                "name": "settings_set",
                "description": "Update runtime settings",
                "input_schema": {"default_timeout_sec": "optional int", "max_steps": "optional int", "max_retries": "optional int", "require_approval": "optional bool"},
            },
        ]
    }


@router.post("/call")
async def call_tool(
    payload: MCPToolCall,
    orchestrator: Orchestrator = Depends(get_orchestrator),
    settings_manager: SettingsManager = Depends(get_settings_manager),
):
    tool = payload.tool
    args = payload.arguments

    if tool == "create_task":
        req = TaskCreateRequest(
            goal=args["goal"],
            steps=args.get("steps"),
            require_approval=args.get("require_approval", True),
            timeout_sec=args.get("timeout_sec"),
            max_steps=args.get("max_steps"),
            max_retries=args.get("max_retries"),
        )
        task_id = await orchestrator.create_and_start(
            req.goal,
            req.steps,
            req.require_approval,
            req.timeout_sec,
            req.max_steps,
            req.max_retries,
        )
        return {"task_id": task_id}

    if tool == "task_status":
        detail = orchestrator.get_task_detail(int(args["task_id"]))
        if not detail:
            raise HTTPException(status_code=404, detail="Task not found")
        return detail

    if tool == "approve_task":
        return orchestrator.approve(int(args["task_id"]), bool(args["approve"]), args.get("note"))

    if tool == "cancel_task":
        orchestrator.cancel(int(args["task_id"]))
        return {"ok": True}

    if tool == "settings_get":
        return settings_manager.get().model_dump()

    if tool == "settings_set":
        return settings_manager.update(RuntimeSettingsUpdate(**args)).model_dump()

    raise HTTPException(status_code=400, detail="Unknown tool")
