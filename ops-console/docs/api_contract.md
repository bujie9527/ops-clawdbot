# API 协议说明

统一错误结构：

```json
{
  "ok": false,
  "error_code": "INVALID_TOKEN",
  "message": "节点 Token 无效"
}
```

## 节点接口（Bearer Token 鉴权）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/nodes/register` | 节点注册 |
| POST | `/api/nodes/{node_id}/heartbeat` | 节点心跳 |
| GET | `/api/nodes` | 节点列表（需 admin 或节点 token） |
| POST | `/api/nodes/{node_id}/tasks/pull` | 节点拉取待执行任务（Pull 模式核心） |
| POST | `/api/tasks/{task_id}/result` | 节点上报任务结果 |

## 管理端接口（admin session 鉴权）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/nodes` | 节点列表页（Jinja） |
| GET | `/nodes/{node_id}` | 节点详情页 |
| GET | `/tasks` | 任务列表页 |
| GET | `/tasks/{task_id}` | 任务详情页 |
| POST | `/api/tasks` | 创建任务（含一键下发） |
| GET | `/api/tasks` | 任务列表 JSON |
| GET | `/login` | 登录页 |
| POST | `/login` | 登录提交 |

## 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 服务健康检查（可扩展 DB 检查） |

## 任务类型（MVP）

| type | 说明 |
|------|------|
| PING | 探活 |
| ECHO | 回显 payload |
| HEALTHCHECK | 健康检查 |
