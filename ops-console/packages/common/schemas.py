"""
Pydantic schemas for Node / Task / Events.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# --- Node Register ---
class NodeRegisterRequest(BaseModel):
    node_id: str
    project_key: str
    name: str
    tags: list[str] = []
    version: Optional[str] = None


class NodeRegisterResponse(BaseModel):
    ok: bool = True
    heartbeat_interval_sec: int = 10
    server_time: str  # ISO8601


# --- Node Heartbeat ---
class NodeHeartbeatRequest(BaseModel):
    status: str = "online"


class NodeHeartbeatResponse(BaseModel):
    ok: bool = True


# --- Node (generic) ---
class NodeBase(BaseModel):
    project_key: str
    name: str
    tags_json: Optional[str] = None
    version: Optional[str] = None


class NodeCreate(NodeBase):
    pass


class NodeRead(NodeBase):
    id: str
    last_seen: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True


# --- Task Create ---
class TaskCreateRequest(BaseModel):
    node_id: str
    type: str = "PING"
    payload: str = "{}"


class TaskCreateResponse(BaseModel):
    ok: bool = True
    task_id: str


# --- Task Pull ---
class TaskPullItem(BaseModel):
    task_id: str
    node_id: str
    type: str
    payload: str
    state: str
    created_at: str
    updated_at: str


class TaskPullResponse(BaseModel):
    tasks: list[TaskPullItem]


# --- Task Report ---
class TaskReportRequest(BaseModel):
    status: str  # SUCCEEDED / FAILED
    result: str = "{}"


class TaskReportResponse(BaseModel):
    ok: bool = True


# --- Task (generic) ---
class TaskBase(BaseModel):
    node_id: str
    type: str
    payload_json: Optional[str] = None


class TaskCreate(TaskBase):
    pass


class TaskRead(TaskBase):
    id: str
    result_json: Optional[str] = None
    state: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- TaskEvent ---
class TaskEventBase(BaseModel):
    task_id: str
    state: str
    message: Optional[str] = None


class TaskEventRead(TaskEventBase):
    id: int
    ts: datetime

    class Config:
        from_attributes = True


# --- 统一错误结构 ---
class ErrorResponse(BaseModel):
    ok: bool = False
    error_code: str
    message: str
