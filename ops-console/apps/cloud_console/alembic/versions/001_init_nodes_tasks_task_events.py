"""init tables: nodes, tasks, task_events

Revision ID: 001_init
Revises:
Create Date: 2025-01-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "nodes",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("project_key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("tags_json", sa.Text(), nullable=False),
        sa.Column("version", sa.String(64), nullable=True),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'offline'")),
    )
    op.create_index(op.f("ix_nodes_project_key"), "nodes", ["project_key"], unique=False)

    op.create_table(
        "tasks",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("node_id", sa.String(64), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("state", sa.String(32), nullable=False, server_default=sa.text("'CREATED'")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(op.f("ix_tasks_node_id"), "tasks", ["node_id"], unique=False)

    op.create_table(
        "task_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("task_id", sa.String(64), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("ts", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(op.f("ix_task_events_task_id"), "task_events", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_task_events_task_id"), table_name="task_events")
    op.drop_table("task_events")
    op.drop_index(op.f("ix_tasks_node_id"), table_name="tasks")
    op.drop_table("tasks")
    op.drop_index(op.f("ix_nodes_project_key"), table_name="nodes")
    op.drop_table("nodes")
