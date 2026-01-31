"""
ops-node-agent 入口：注册 → 心跳 → 拉取 → 执行 → 回传。
"""
import signal
import sys
import threading
import time

from .config import config
from .registrar import heartbeat, register
from .reporter import report
from .task_executor import execute
from .task_puller import pull_created_tasks


def _heartbeat_loop():
    """心跳循环。"""
    while True:
        time.sleep(config.HEARTBEAT_INTERVAL_SEC)
        try:
            if heartbeat():
                print("[heartbeat] ok")
            else:
                print("[heartbeat] fail")
        except Exception as e:
            print(f"[heartbeat] error: {e}")


def _main_loop():
    """主循环：拉取 → 执行 → 回传。"""
    print(f"[agent] node_id={config.NODE_ID} console={config.CONSOLE_BASE_URL}")

    if not register():
        print("[agent] register failed")
        sys.exit(1)
    print("[agent] register ok")

    t = threading.Thread(target=_heartbeat_loop, daemon=True)
    t.start()

    while True:
        time.sleep(config.TASK_POLL_INTERVAL_SEC)
        try:
            tasks = pull_created_tasks()
            for task in tasks:
                task_id = task.get("task_id", "")
                if not task_id:
                    continue
                status, result = execute(task)
                if report(task_id, status, result):
                    print(f"[task] {task_id} {status}")
                else:
                    print(f"[task] {task_id} report fail")
        except Exception as e:
            print(f"[pull] error: {e}")


def main():
    def _sig(signum, frame):
        print("\n[agent] shutdown")
        sys.exit(0)

    signal.signal(signal.SIGINT, _sig)
    signal.signal(signal.SIGTERM, _sig)
    _main_loop()


if __name__ == "__main__":
    main()
