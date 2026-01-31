"""
任务结果回传。
"""
from .config import config
from .http_client import post


def report(task_id: str, status: str, result: str = "{}") -> bool:
    """回传任务结果。"""
    url = f"{config.CONSOLE_BASE_URL}/api/tasks/{task_id}/report"
    body = {"status": status, "result": result}
    r = post(url, json=body)
    if r.status_code != 200:
        return False
    data = r.json()
    return data.get("ok") is True
