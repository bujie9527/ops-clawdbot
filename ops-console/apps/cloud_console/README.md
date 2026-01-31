# Clawdbot Console

云端 Web Console 控制多节点 Clawdbot 的最小可用系统（MVP）控制面。

## 技术栈

- Python 3.11
- FastAPI + Jinja2
- MySQL 8
- SQLAlchemy 2.0 + PyMySQL
- Alembic 迁移

## 本地启动（Windows PowerShell）

### 第一次使用：创建虚拟环境并安装依赖

在 **PowerShell** 中进入本目录后执行（请把 `d:\AI_Hub\ops-console\apps\cloud_console` 换成你的实际路径）：

```powershell
cd d:\AI_Hub\ops-console\apps\cloud_console

# 创建虚拟环境（若还没有 .venv）
python -m venv .venv

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 若提示“无法加载，因为在此系统上禁止运行脚本”，先执行：
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

```powershell
copy .env.example .env
# 用记事本等编辑 .env，确认 DB_HOST / DB_PORT / DB_USER / DB_PASSWORD 与本地 MySQL 一致
```

### 启动 MySQL（Docker，可选）

若用项目自带的 MySQL：

```powershell
cd d:\AI_Hub\ops-console\infra\docker
docker compose -f docker-compose.dev.yml up -d
```

然后回到 `apps\cloud_console`，在 `.env` 里设置例如：`DB_HOST=localhost`，`DB_PORT=3306`，`DB_NAME=ops_console`，`DB_USER=root`，`DB_PASSWORD=rootpass`。

### 启动服务

在 **已激活虚拟环境** 的情况下（提示符前有 `(.venv)`）：

```powershell
cd d:\AI_Hub\ops-console\apps\cloud_console
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

或使用脚本（自动用本目录的 .venv，无需先 activate）：

```powershell
.\run.ps1
```

浏览器访问：**http://localhost:8000/health**

- 若返回 `{"ok":true,"db":"ok"}` 说明服务与数据库均正常。
- 若出现 **ERR_CONNECTION_REFUSED**：说明服务没起来，请确认上面 `uvicorn` 已运行且无报错。
- 若返回 500 且 `"db":"fail"`：说明数据库未启动或 `.env` 中 DB_* 配置错误。

### 数据库迁移

```powershell
cd d:\AI_Hub\ops-console\apps\cloud_console
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

## 目录说明

- `app/`：FastAPI 应用、配置、DB、API、Web
- `templates/`：Jinja 模板
- `alembic/`：数据库迁移
- `.env`：本地环境变量（由 `.env.example` 复制后修改）
