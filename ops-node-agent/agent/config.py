"""
配置管理：从 .env 读取，校验必需变量。
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

_REQUIRED = (
    "CONSOLE_BASE_URL",
    "NODE_ID",
    "PROJECT_KEY",
    "NODE_TOKEN",
    "HEARTBEAT_INTERVAL_SEC",
)


def _validate():
    missing = [k for k in _REQUIRED if not os.getenv(k)]
    if missing:
        print(f"[config] missing required env: {', '.join(missing)}")
        sys.exit(1)
    try:
        int(os.getenv("HEARTBEAT_INTERVAL_SEC"))
    except (TypeError, ValueError):
        print("[config] HEARTBEAT_INTERVAL_SEC must be integer")
        sys.exit(1)


class Config:
    """运行配置。"""

    CONSOLE_BASE_URL: str = os.getenv("CONSOLE_BASE_URL", "").rstrip("/")
    NODE_ID: str = os.getenv("NODE_ID", "")
    PROJECT_KEY: str = os.getenv("PROJECT_KEY", "")
    NODE_TOKEN: str = os.getenv("NODE_TOKEN", "")
    HEARTBEAT_INTERVAL_SEC: int = int(os.getenv("HEARTBEAT_INTERVAL_SEC", "10") or "10")

    NODE_NAME: str = os.getenv("NODE_NAME", "Node")
    TASK_POLL_INTERVAL_SEC: int = int(os.getenv("TASK_POLL_INTERVAL_SEC", "5") or "5")


_validate()
config = Config()
