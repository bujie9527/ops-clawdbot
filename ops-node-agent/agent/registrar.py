"""
注册与心跳。
"""
from .config import config
from .http_client import post


def register() -> bool:
    """向 Console 注册节点。"""
    url = f"{config.CONSOLE_BASE_URL}/api/nodes/register"
    body = {
        "node_id": config.NODE_ID,
        "project_key": config.PROJECT_KEY,
        "name": config.NODE_NAME,
        "tags": [],
        "version": "0.1.0",
    }
    r = post(url, json=body)
    if r.status_code != 200:
        return False
    data = r.json()
    return data.get("ok") is True


def heartbeat() -> bool:
    """发送心跳。"""
    url = f"{config.CONSOLE_BASE_URL}/api/nodes/{config.NODE_ID}/heartbeat"
    body = {"status": "online"}
    r = post(url, json=body)
    if r.status_code != 200:
        return False
    data = r.json()
    return data.get("ok") is True
