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
