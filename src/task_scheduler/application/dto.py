from dataclasses import dataclass
from datetime import datetime


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
    name: str | None
    description: str | None
    due_ts: datetime | None
    is_complete: bool | None = None

    @property
    def is_data_to_update(self) -> bool:
        return any(value is not None for value in (self.name, self.description, self.due_ts, self.is_complete))
