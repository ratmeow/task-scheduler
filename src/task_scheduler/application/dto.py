from dataclasses import dataclass
from datetime import datetime

from task_scheduler.domain.entities import Task


@dataclass(frozen=True)
class UserRegisterData:
    email: str
    login: str
    password: str


@dataclass(frozen=True)
class UserLoginData:
    login: str
    password: str


@dataclass(frozen=True)
class TaskCreateData:
    user_id: str
    name: str
    description: str | None
    due_ts: datetime


@dataclass(frozen=True)
class TaskUpdateData:
    task_id: str
    user_id: str
    name: str | None
    description: str | None
    due_ts: datetime | None
    is_complete: bool | None = None


@dataclass(frozen=True)
class TaskListNavigation:
    sort_by: str | None = "updated_ts"
    sort_desc: bool | None = False
    limit: int | None = 10
    offset: int | None = 0

    @property
    def sort_column(self):
        return {
            "name": Task.name,
            "is_complete": Task.is_complete,
            "created_ts": Task.created_ts,
            "updated_ts": Task.updated_ts,
            "due_ts": Task.due_ts,
        }[self.sort_by]


@dataclass(frozen=True)
class TaskListFilter:
    user_id: str | None
    name: str | None
    # created_ts: datetime | None
    # due_ts: datetime | None
    is_complete: bool | None
