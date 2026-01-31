"""
JSON 结构化日志。
必须包含 request_id / node_id / task_id 等字段。
MVP 阶段占位，业务实现时补充完整。
"""
import logging
import json
from typing import Optional
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """输出 JSON 格式日志，便于 ELK/Loki 等采集。"""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # 可选扩展字段
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "node_id"):
            log_obj["node_id"] = record.node_id
        if hasattr(record, "task_id"):
            log_obj["task_id"] = record.task_id
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


def setup_json_logging(level: int = logging.INFO) -> None:
    """配置 JSON 日志到 stdout。"""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(level)
