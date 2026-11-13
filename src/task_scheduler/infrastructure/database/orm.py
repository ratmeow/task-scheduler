from sqlalchemy import UUID, Column, String, Table, UniqueConstraint
from sqlalchemy.orm import registry

from task_scheduler.domain.entities import User


def register_tables(mapper_registry: registry) -> None:
    users_tables = Table(
        "users",
        mapper_registry.metadata,
        Column("id", UUID, primary_key=True),
        Column("login", String),
        Column("hashed_password", String),
        Column("email", String),
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("login", name="uq_users_login"),
    )
    mapper_registry.map_imperatively(User, users_tables)


def create_mapper_registry() -> registry:
    mapper_registry = registry()
    register_tables(mapper_registry)
    return mapper_registry
