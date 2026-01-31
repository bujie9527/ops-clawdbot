"""
任务 API：创建、拉取、回传。
"""
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.common.schemas import (
    TaskCreateRequest,
    TaskCreateResponse,
    TaskReportRequest,
    TaskReportResponse,
)

from ..db import get_db
from ..deps import require_node_token
from ..models import Node, Task, TaskEvent

router = APIRouter()


def _err(code: str, msg: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"ok": False, "error_code": code, "message": msg},
    )


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _add_task_event(db: Session, task_id: str, state: str, message: str | None = None) -> None:
    ev = TaskEvent(task_id=task_id, state=state, message=message, ts=_now_utc())
    db.add(ev)


@router.post(
    "/create",
    response_model=TaskCreateResponse,
    responses={401: {"description": "Invalid token"}, 404: {"description": "Node not found"}},
)
async def create_task(
    body: TaskCreateRequest,
    project_key: Annotated[str, Depends(require_node_token)],
    db: Annotated[Session, Depends(get_db)],
):
    """创建任务，状态 CREATED。"""
    node = db.execute(select(Node).where(Node.id == body.node_id, Node.project_key == project_key)).scalar_one_or_none()
    if node is None:
        _err("NODE_NOT_FOUND", "Node not found or access denied", status.HTTP_404_NOT_FOUND)

    task_id = f"task-{uuid.uuid4().hex[:12]}"
    now = _now_utc()

    task = Task(
        id=task_id,
        node_id=body.node_id,
        type=body.type,
        payload_json=body.payload,
        result_json=None,
        state="CREATED",
        created_at=now,
        updated_at=now,
    )
    db.add(task)
    _add_task_event(db, task_id, "CREATED", None)
    db.commit()

    return TaskCreateResponse(ok=True, task_id=task_id)


@router.post(
    "/{task_id}/report",
    response_model=TaskReportResponse,
    responses={401: {"description": "Invalid token"}, 404: {"description": "Task not found"}},
)
async def report_task(
    task_id: str,
    body: TaskReportRequest,
    project_key: Annotated[str, Depends(require_node_token)],
    db: Annotated[Session, Depends(get_db)],
):
    """任务回传：更新状态为 SUCCEEDED/FAILED，写入 task_events。"""
    if body.status not in ("SUCCEEDED", "FAILED"):
        _err("INVALID_STATUS", "status must be SUCCEEDED or FAILED", status.HTTP_400_BAD_REQUEST)

    task = db.execute(
        select(Task).join(Node, Task.node_id == Node.id).where(Task.id == task_id, Node.project_key == project_key)
    ).scalar_one_or_none()
    if task is None:
        _err("TASK_NOT_FOUND", "Task not found or access denied", status.HTTP_404_NOT_FOUND)

    task.state = body.status
    task.result_json = body.result
    task.updated_at = _now_utc()
    _add_task_event(db, task_id, body.status, None)
    db.commit()

    return TaskReportResponse(ok=True)
