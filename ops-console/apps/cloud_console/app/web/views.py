"""
Jinja 页面路由：/nodes /tasks /login
MVP 阶段骨架，不实现业务逻辑。
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# from ..deps import get_admin_session

router = APIRouter()

# 模板目录（相对于 cloud_console 根）
templates = Jinja2Templates(directory="templates")


# TODO: 登录页
# @router.get("/login", response_class=HTMLResponse)
# async def login_page(request: Request): ...

# TODO: 登录提交
# @router.post("/login")
# async def login_submit(request: Request): ...


# TODO: Nodes 列表页
# @router.get("/nodes", response_class=HTMLResponse)
# async def nodes_page(request: Request, session=Depends(get_admin_session)): ...


# TODO: Node 详情页
# @router.get("/nodes/{node_id}", response_class=HTMLResponse)
# async def node_detail(request: Request, node_id: str): ...


# TODO: Tasks 列表页 + 一键下发任务按钮
# @router.get("/tasks", response_class=HTMLResponse)
# async def tasks_page(request: Request): ...


# TODO: Task 详情页
# @router.get("/tasks/{task_id}", response_class=HTMLResponse)
# async def task_detail(request: Request, task_id: str): ...
