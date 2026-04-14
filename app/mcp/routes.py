from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.schemas import MCPToolCall, TaskCreateRequest
from app.services.orchestrator import Orchestrator


router = APIRouter(prefix="/mcp", tags=["mcp"])


def get_orchestrator(request: Request) -> Orchestrator:
    return request.app.state.orchestrator


@router.get("/tools")
async def list_tools():
    return {
        "tools": [
            {"name": "create_task", "description": "Create and run an agent task", "input_schema": {"goal": "string", "steps": "optional action list"}},
            {"name": "task_status", "description": "Get task detail by id", "input_schema": {"task_id": "int"}},
            {"name": "approve_task", "description": "Approve/deny pending action", "input_schema": {"task_id": "int", "approve": "bool", "note": "optional"}},
            {"name": "cancel_task", "description": "Cancel task", "input_schema": {"task_id": "int"}},
        ]
    }


@router.post("/call")
async def call_tool(payload: MCPToolCall, orchestrator: Orchestrator = Depends(get_orchestrator)):
    tool = payload.tool
    args = payload.arguments

    if tool == "create_task":
        req = TaskCreateRequest(goal=args["goal"], steps=args.get("steps"), require_approval=args.get("require_approval", True))
        task_id = await orchestrator.create_and_start(req.goal, req.steps)
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

    raise HTTPException(status_code=400, detail="Unknown tool")
