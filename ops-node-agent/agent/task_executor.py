"""
任务执行：当前仅支持 PING，模拟成功。
"""
# task: {"task_id", "node_id", "type", "payload", "state", "created_at", "updated_at"}


def execute(task: dict) -> tuple[str, str]:
    """
    执行任务，返回 (status, result)。
    status: SUCCEEDED | FAILED
    result: JSON 字符串
    """
    t = task.get("type", "")
    if t == "PING":
        return "SUCCEEDED", "{}"
    return "FAILED", '{"error": "unsupported type"}'
