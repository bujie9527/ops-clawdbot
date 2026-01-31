"""
FastAPI app 入口：路由挂载、生命周期、健康检查。
"""
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# 保证可 import packages.common（ops-console 根加入 path）
_ops_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_ops_root) not in sys.path:
    sys.path.insert(0, str(_ops_root))

from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .db import ping_db

from .api import nodes, tasks
from .ui import views as ui_views


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动/关闭。"""
    yield


app = FastAPI(
    title="Clawdbot Console",
    description="云端 Web Console 控制多节点 Clawdbot - 控制面",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    """开发时返回错误详情便于排查 500。"""
    import traceback
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error_code": "INTERNAL_ERROR",
            "message": str(exc),
            "traceback": traceback.format_exc(),
        },
    )


app.include_router(nodes.router, prefix="/api/nodes", tags=["nodes"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(ui_views.router, prefix="/ui", tags=["ui"])
_static_dir = _ops_root / "apps" / "cloud_console" / "static"
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/")
def index():
    """首页重定向到 UI 节点列表。"""
    return RedirectResponse(url="/ui/nodes")


@app.get("/health")
async def health():
    """健康检查：含 DB 检测。"""
    ok, err = ping_db()
    if ok:
        return {"ok": True, "db": "ok"}
    error_msg = err[:200] if len(err) > 200 else err
    return JSONResponse(
        status_code=500,
        content={"ok": False, "db": "fail", "error": error_msg},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
