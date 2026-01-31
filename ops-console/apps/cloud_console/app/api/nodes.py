"""
节点 API：注册、心跳。
"""
import json
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.common.schemas import (
    NodeHeartbeatRequest,
    NodeHeartbeatResponse,
    NodeRegisterRequest,
    NodeRegisterResponse,
    TaskPullItem,
    TaskPullResponse,
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


@router.post(
    "/register",
    response_model=NodeRegisterResponse,
    responses={
        401: {"description": "Invalid or missing token"},
        400: {"description": "project_key mismatch"},
    },
)
async def register_node(
    body: NodeRegisterRequest,
    project_key: Annotated[str, Depends(require_node_token)],
    db: Annotated[Session, Depends(get_db)],
):
    """节点注册：校验 token 与 project_key，创建或更新节点。"""
    if body.project_key != project_key:
        _err("PROJECT_KEY_MISMATCH", "project_key does not match token", status.HTTP_403_FORBIDDEN)

    now = _now_utc()
    tags_json = json.dumps(body.tags)

    node = db.get(Node, body.node_id)
    if node is None:
        node = Node(
            id=body.node_id,
            project_key=body.project_key,
            name=body.name,
            tags_json=tags_json,
            version=body.version,
            last_seen=now,
            status="online",
        )
        db.add(node)
    else:
        if node.project_key != project_key:
            _err("FORBIDDEN", "Node belongs to another project", status.HTTP_403_FORBIDDEN)
        node.name = body.name
        node.tags_json = tags_json
        node.version = body.version
        node.status = "online"
        node.last_seen = now

    db.commit()
    db.refresh(node)

    return NodeRegisterResponse(
        ok=True,
        heartbeat_interval_sec=10,
        server_time=now.isoformat(),
    )


@router.post(
    "/{node_id}/heartbeat",
    response_model=NodeHeartbeatResponse,
    responses={401: {"description": "Invalid or missing token"}, 404: {"description": "Node not found"}},
)
async def heartbeat(
    node_id: str,
    body: NodeHeartbeatRequest,
    project_key: Annotated[str, Depends(require_node_token)],
    db: Annotated[Session, Depends(get_db)],
):
    """节点心跳：更新 last_seen 与 status。"""
    node = db.execute(select(Node).where(Node.id == node_id, Node.project_key == project_key)).scalar_one_or_none()
    if node is None:
        _err("NODE_NOT_FOUND", "Node not found or access denied", status.HTTP_404_NOT_FOUND)

    now = _now_utc()
    node.last_seen = now
    node.status = body.status

    db.commit()

    return NodeHeartbeatResponse(ok=True)


@router.get(
    "/{node_id}/tasks",
    response_model=TaskPullResponse,
    responses={401: {"description": "Invalid token"}, 404: {"description": "Node not found"}},
)
async def pull_tasks(
    node_id: str,
    project_key: Annotated[str, Depends(require_node_token)],
    db: Annotated[Session, Depends(get_db)],
    state: str = "CREATED",
):
    """拉取节点任务：返回指定 state 的任务，并更新为 RUNNING。"""
    node = db.execute(select(Node).where(Node.id == node_id, Node.project_key == project_key)).scalar_one_or_none()
    if node is None:
        _err("NODE_NOT_FOUND", "Node not found or access denied", status.HTTP_404_NOT_FOUND)

    tasks = (
        db.execute(select(Task).where(Task.node_id == node_id, Task.state == state))
        .scalars()
        .all()
    )
    now = _now_utc()
    result = []
    for t in tasks:
        t.state = "RUNNING"
        t.updated_at = now
        ev = TaskEvent(task_id=t.id, state="RUNNING", message=None, ts=now)
        db.add(ev)
        result.append(
            TaskPullItem(
                task_id=t.id,
                node_id=t.node_id,
                type=t.type,
                payload=t.payload_json or "{}",
                state="RUNNING",
                created_at=t.created_at.isoformat(),
                updated_at=t.updated_at.isoformat(),
            )
        )
    db.commit()

    return TaskPullResponse(tasks=result)
