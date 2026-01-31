# ops-console

云端 Web Console 控制多节点 Clawdbot 的最小可用系统（MVP），用于跨云管理与任务下发。

## 项目结构

```
ops-console/
  apps/
    cloud_console/     # Web 面板 + JSON API（控制面）
    node_adapter/      # 节点适配器（本阶段仅骨架）
  packages/
    common/            # 公共 schemas、安全、日志
  infra/
    docker/            # MySQL 本地开发
  docs/
    architecture.md    # 架构说明
    api_contract.md    # API 协议
```

## 技术栈

- Python 3.11
- FastAPI + Jinja2（非前后端分离）
- MySQL 8
- SQLAlchemy 2.0 + PyMySQL
- Alembic 迁移

## 快速开始

1. 启动 MySQL：`docker compose -f infra/docker/docker-compose.dev.yml up -d`
2. 进入 Console：`cd apps/cloud_console`
3. 创建 venv、安装依赖、配置 `.env`
4. 执行迁移：`alembic upgrade head`
5. 启动：`uvicorn app.main:app --reload --port 8000`

详见 [apps/cloud_console/README.md](apps/cloud_console/README.md)。

## 文档

- [架构说明](docs/architecture.md)：跨云 Pull 模式与节点不开放入站端口的理由
- [API 协议](docs/api_contract.md)：接口列表与错误结构
