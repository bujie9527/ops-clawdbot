"""
Web Operator Console：节点与任务管理页面。
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..deps import require_admin_basic_auth
from ..models import Node, Task, TaskEvent

router = APIRouter()
_templates_dir = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))

OFFLINE_THRESHOLD_SEC = 30


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_offline(last_seen: datetime | None) -> bool:
    if last_seen is None:
        return True
    return (_now_utc() - last_seen).total_seconds() > OFFLINE_THRESHOLD_SEC


TOKEN_DEFAULT = "changeme_node_token_project_a"


def _build_connection_info(request: Request, node: Node) -> dict:
    """构建节点代理连接信息及完整性校验。"""
    base_url = settings.CONSOLE_PUBLIC_URL.strip()
    if not base_url:
        base_url = str(request.base_url).rstrip("/")
    token = settings.NODE_TOKEN_PROJECT_A
    token_ok = token != TOKEN_DEFAULT and len(token) > 0
    url_ok = bool(base_url)
    node_ok = bool(node.id and node.name and node.project_key)
    return {
        "console_base_url": base_url,
        "node_id": node.id,
        "project_key": node.project_key,
        "node_token": token,
        "node_token_masked": f"{token[:4]}***{token[-4:]}" if len(token) >= 8 else "***",
        "node_name": node.name,
        "token_ok": token_ok,
        "url_ok": url_ok,
        "node_ok": node_ok,
        "all_ok": token_ok and url_ok and node_ok,
    }


@router.get("/nodes", response_class=HTMLResponse)
async def ui_nodes(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin_basic_auth)],
):
    """节点列表：id / name / project_key / status / last_seen。last_seen 超 30 秒显示 offline。"""
    rows = db.execute(
        select(Node).order_by(Node.last_seen.isnot(None).desc(), Node.last_seen.desc())
    ).scalars().all()
    nodes = []
    for n in rows:
        display_status = "offline" if _is_offline(n.last_seen) else (n.status or "online")
        nodes.append({
            "id": n.id,
            "name": n.name,
            "project_key": n.project_key,
            "status": display_status,
            "last_seen": n.last_seen.isoformat() if n.last_seen else None,
        })
    return templates.TemplateResponse(
        "ui_nodes.html",
        {"request": request, "nodes": nodes},
    )


@router.get("/nodes/new", response_class=HTMLResponse)
async def ui_nodes_new_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin_basic_auth)],
):
    """创建节点表单。"""
    return templates.TemplateResponse(
        "ui_nodes_new.html",
        {"request": request, "project_key_default": settings.PROJECT_KEY_DEFAULT},
    )


@router.post("/nodes/new")
async def ui_nodes_new_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin_basic_auth)],
):
    """提交创建节点。"""
    form = await request.form()
    node_id = (form.get("node_id") or "").strip()
    name = (form.get("name") or "").strip()
    project_key = (form.get("project_key") or settings.PROJECT_KEY_DEFAULT).strip()

    error = None
    if not node_id:
        error = "node_id 必填"
    elif db.get(Node, node_id) is not None:
        error = f"节点 ID 已存在: {node_id}"

    if error:
        return templates.TemplateResponse(
            "ui_nodes_new.html",
            {
                "request": request,
                "project_key_default": settings.PROJECT_KEY_DEFAULT,
                "error": error,
                "node_id": node_id,
                "name": name,
                "project_key": project_key,
            },
        )

    node = Node(
        id=node_id,
        project_key=project_key or settings.PROJECT_KEY_DEFAULT,
        name=name or node_id,
        tags_json="[]",
        version=None,
        last_seen=None,
        status="offline",
    )
    db.add(node)
    db.commit()
    return RedirectResponse(url="/ui/nodes", status_code=303)


@router.get("/nodes/{node_id}", response_class=HTMLResponse)
async def ui_node_detail(
    request: Request,
    node_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin_basic_auth)],
):
    """节点详情：基本信息 + 最近 20 条 tasks。"""
    node = db.get(Node, node_id)
    if node is None:
        return templates.TemplateResponse("ui_error.html", {"request": request, "message": "Node not found"}, status_code=404)
    tasks = (
        db.execute(select(Task).where(Task.node_id == node_id).order_by(Task.updated_at.desc()).limit(20))
        .scalars()
        .all()
    )
    connection_info = _build_connection_info(request, node)
    return templates.TemplateResponse(
        "ui_node_detail.html",
        {
            "request": request,
            "node": node,
            "tasks": tasks,
            "connection_info": connection_info,
        },
    )


@router.get("/nodes/{node_id}/edit", response_class=HTMLResponse)
async def ui_nodes_edit_get(
    request: Request,
    node_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin_basic_auth)],
):
    """编辑节点表单。"""
    node = db.get(Node, node_id)
    if node is None:
        return templates.TemplateResponse("ui_error.html", {"request": request, "message": "Node not found"}, status_code=404)
    return templates.TemplateResponse(
        "ui_nodes_edit.html",
        {"request": request, "node": node},
    )


@router.post("/nodes/{node_id}/edit")
async def ui_nodes_edit_post(
    request: Request,
    node_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin_basic_auth)],
):
    """提交修改节点。"""
    node = db.get(Node, node_id)
    if node is None:
        return templates.TemplateResponse("ui_error.html", {"request": request, "message": "Node not found"}, status_code=404)
    form = await request.form()
    name = (form.get("name") or "").strip()
    project_key = (form.get("project_key") or "").strip()
    node.name = name or node.name
    node.project_key = project_key or node.project_key
    db.commit()
    return RedirectResponse(url=f"/ui/nodes/{node_id}", status_code=303)


@router.post("/nodes/{node_id}/delete")
async def ui_nodes_delete_post(
    request: Request,
    node_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin_basic_auth)],
):
    """删除节点（级联删除任务及事件）。"""
    node = db.get(Node, node_id)
    if node is None:
        return templates.TemplateResponse("ui_error.html", {"request": request, "message": "Node not found"}, status_code=404)
    task_ids = [r.id for r in db.execute(select(Task.id).where(Task.node_id == node_id)).scalars().all()]
    if task_ids:
        db.execute(delete(TaskEvent).where(TaskEvent.task_id.in_(task_ids)))
    db.execute(delete(Task).where(Task.node_id == node_id))
    db.delete(node)
    db.commit()
    return RedirectResponse(url="/ui/nodes", status_code=303)


@router.get("/tasks/new", response_class=HTMLResponse)
async def ui_tasks_new_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin_basic_auth)],
):
    """创建任务表单：node_id 下拉、task_type 固定 PING。"""
    rows = db.execute(select(Node).order_by(Node.id)).scalars().all()
    return templates.TemplateResponse(
        "ui_tasks_new.html",
        {"request": request, "nodes": rows},
    )


@router.post("/tasks/new")
async def ui_tasks_new_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin_basic_auth)],
):
    """提交创建任务：内部调用逻辑，不走 HTTP API。"""
    form = await request.form()
    node_id = form.get("node_id", "").strip()
    task_type = form.get("task_type", "PING").strip() or "PING"
    all_nodes = db.execute(select(Node).order_by(Node.id)).scalars().all()
    if not node_id:
        return templates.TemplateResponse(
            "ui_tasks_new.html",
            {"request": request, "nodes": all_nodes, "error": "node_id required"},
        )
    node = db.get(Node, node_id)
    if node is None:
        return templates.TemplateResponse(
            "ui_tasks_new.html",
            {"request": request, "nodes": all_nodes, "error": "Node not found"},
        )
    task_id = f"task-{uuid.uuid4().hex[:12]}"
    now = _now_utc()
    task = Task(
        id=task_id,
        node_id=node_id,
        type=task_type,
        payload_json="{}",
        result_json=None,
        state="CREATED",
        created_at=now,
        updated_at=now,
    )
    db.add(task)
    ev = TaskEvent(task_id=task_id, state="CREATED", message=None, ts=now)
    db.add(ev)
    db.commit()
    return RedirectResponse(url=f"/ui/tasks", status_code=303)


@router.get("/tasks", response_class=HTMLResponse)
async def ui_tasks(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin_basic_auth)],
):
    """任务列表：最近 50 条，展示 state / node_id / type / created_at。"""
    rows = (
        db.execute(select(Task).order_by(Task.created_at.desc()).limit(50))
        .scalars()
        .all()
    )
    return templates.TemplateResponse(
        "ui_tasks.html",
        {"request": request, "tasks": rows},
    )
