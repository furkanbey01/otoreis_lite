from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.schemas import ApprovalRequest, TaskCreateRequest, TaskDetailResponse, TaskResponse
from app.services.orchestrator import Orchestrator


def get_orchestrator(request: Request) -> Orchestrator:
    return request.app.state.orchestrator


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/tasks", response_model=TaskResponse)
async def create_task(payload: TaskCreateRequest, orchestrator: Orchestrator = Depends(get_orchestrator)):
    task_id = await orchestrator.create_and_start(payload.goal, payload.steps)
    detail = orchestrator.get_task_detail(task_id)
    return TaskResponse(id=task_id, goal=payload.goal, status=detail["status"])


@router.get("/tasks")
async def list_tasks(request: Request):
    rows = request.app.state.db.list_tasks()
    return [
        {"id": r["id"], "goal": r["goal"], "status": r["status"], "summary": r["summary"], "current_step": r["current_step"], "total_steps": r["total_steps"]}
        for r in rows
    ]


@router.get("/tasks/{task_id}", response_model=TaskDetailResponse)
async def get_task(task_id: int, orchestrator: Orchestrator = Depends(get_orchestrator)):
    detail = orchestrator.get_task_detail(task_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskDetailResponse(**detail)


@router.post("/tasks/{task_id}/approval")
async def approve_task(task_id: int, payload: ApprovalRequest, orchestrator: Orchestrator = Depends(get_orchestrator)):
    try:
        return orchestrator.approve(task_id, payload.approve, payload.note)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: int, orchestrator: Orchestrator = Depends(get_orchestrator)):
    try:
        orchestrator.cancel(task_id)
        return {"ok": True}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
