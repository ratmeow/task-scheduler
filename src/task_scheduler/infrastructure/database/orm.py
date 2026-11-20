from sqlalchemy import UUID, Boolean, Column, DateTime, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.orm import registry

from task_scheduler.domain.entities import Task, User


def register_tables(mapper_registry: registry) -> None:
    users_table = Table(
        "users",
        mapper_registry.metadata,
        Column("id", UUID, primary_key=True),
        Column("login", String, nullable=False),
        Column("hashed_password", String, nullable=False),
        Column("email", String, nullable=False),
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("login", name="uq_users_login"),
    )
    tasks_table = Table(
        "tasks",
        mapper_registry.metadata,
        Column("id", UUID, primary_key=True),
        Column("user_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        Column("name", String, nullable=False),
        Column("description", String, nullable=True),
        Column("is_complete", Boolean, nullable=False),
        Column("created_ts", DateTime(timezone=True), nullable=False),
        Column("updated_ts", DateTime(timezone=True), nullable=False),
        Column("due_ts", DateTime(timezone=True), nullable=False),
    )

    mapper_registry.map_imperatively(User, users_table)
    mapper_registry.map_imperatively(Task, tasks_table)


def create_mapper_registry() -> registry:
    mapper_registry = registry()
    register_tables(mapper_registry)
    return mapper_registry
