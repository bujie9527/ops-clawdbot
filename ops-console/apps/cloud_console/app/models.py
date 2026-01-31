"""
SQLAlchemy ORM 模型：Node / Task / TaskEvent。
"""
from sqlalchemy import BigInteger, Column, DateTime, String, Text, func, text
from sqlalchemy.orm import foreign, relationship

from .db import Base


class Node(Base):
    __tablename__ = "nodes"

    id = Column(String(64), primary_key=True)
    project_key = Column(String(64), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    tags_json = Column(Text, nullable=False, default="[]")
    version = Column(String(64), nullable=True)
    last_seen = Column(DateTime, nullable=True)
    status = Column(String(32), nullable=False, server_default=text("'offline'"))

    tasks = relationship("Task", back_populates="node", primaryjoin="Node.id == foreign(Task.node_id)")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(64), primary_key=True)
    node_id = Column(String(64), nullable=False, index=True)
    type = Column(String(32), nullable=False)
    payload_json = Column(Text, nullable=False, default="{}")
    result_json = Column(Text, nullable=True)
    state = Column(String(32), nullable=False, server_default=text("'CREATED'"))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    node = relationship("Node", back_populates="tasks", primaryjoin="foreign(Task.node_id) == Node.id")
    events = relationship("TaskEvent", back_populates="task", primaryjoin="Task.id == foreign(TaskEvent.task_id)")


class TaskEvent(Base):
    __tablename__ = "task_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(String(64), nullable=False, index=True)
    state = Column(String(32), nullable=False)
    message = Column(Text, nullable=True)
    ts = Column(DateTime, nullable=False, server_default=func.now())

    task = relationship("Task", back_populates="events", primaryjoin="foreign(TaskEvent.task_id) == Task.id")
