"""
拉取任务。
"""
from .config import config
from .http_client import get


def pull_created_tasks() -> list[dict]:
    """拉取 state=CREATED 的任务。"""
    url = f"{config.CONSOLE_BASE_URL}/api/nodes/{config.NODE_ID}/tasks?state=CREATED"
    r = get(url)
    if r.status_code != 200:
        return []
    data = r.json()
    tasks = data.get("tasks") or []
    return tasks
