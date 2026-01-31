"""
鉴权依赖：admin session / node bearer token。
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials, HTTPBearer

from .config import settings

node_security = HTTPBearer(auto_error=False)
basic_auth = HTTPBasic(auto_error=False)


async def require_admin_basic_auth(
    credentials: Annotated[HTTPBasicCredentials | None, Depends(basic_auth)],
) -> None:
    """Web UI 页面：Basic Auth 校验（ADMIN_USER / ADMIN_PASSWORD）。"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )
    if credentials.username != settings.ADMIN_USER or credentials.password != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


def verify_node_token(token: str) -> str | None:
    """
    校验节点 Token，返回 project_key；不匹配返回 None。
    MVP：仅 project_a 可用 NODE_TOKEN_PROJECT_A。
    """
    if token == settings.NODE_TOKEN_PROJECT_A:
        return settings.PROJECT_KEY_DEFAULT
    return None


async def require_node_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(node_security)],
) -> str:
    """
    FastAPI 依赖：要求有效 Bearer Token，返回 project_key。
    否则抛出 401，返回统一错误结构。
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"ok": False, "error_code": "MISSING_TOKEN", "message": "Authorization header required"},
        )
    token = credentials.credentials
    project_key = verify_node_token(token)
    if project_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"ok": False, "error_code": "INVALID_TOKEN", "message": "Invalid or expired token"},
        )
    return project_key


# Admin 管理端（MVP 未实现）
async def get_admin_session():
    return None
