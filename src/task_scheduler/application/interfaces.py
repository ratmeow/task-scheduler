from typing import Protocol

from task_scheduler.application.dto import TaskListFilter, TaskListNavigation
from task_scheduler.domain.entities import Task, TaskEvent, User


class Hasher(Protocol):
    def hash(self, text: str) -> str:
        pass

    def verify_hash(self, original_text: str, hashed_text: str) -> bool:
        pass


class DBSession(Protocol):
    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass

    async def flush(self) -> None:
        pass


class UserGateway(Protocol):
    async def get_by_id(self, user_id: str) -> User | None:
        pass

    async def get_by_login(self, login: str) -> User | None:
        pass

    async def save(self, user: User) -> None:
        pass


class TaskGateway(Protocol):
    async def get_by_id(self, task_id: str) -> Task | None:
        pass

    async def list_by(self, filters: TaskListFilter, navigation: TaskListNavigation) -> list[Task]:
        pass

    async def save(self, task: Task) -> None:
        pass

    async def delete(self, task: Task) -> None:
        pass


class TaskEventGateway(Protocol):
    async def save(self, event: TaskEvent) -> None:
        pass
