import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from .exceptions import DomainError


@dataclass
class User:
    login: str
    hashed_password: str
    email: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not self._is_valid_login(self.login):
            raise DomainError(
                "Login must be at least 3 characters long, "
                "with only Latin letters, digits and special character(!@#$%^&*_)."
            )
        if not self._is_valid_email(self.email):
            raise DomainError("Incorrect email")

    @staticmethod
    def _is_valid_login(login: str) -> bool:
        pattern = r"^[A-Za-z\d!@#$%^&*_]{3,}$"
        return bool(re.fullmatch(pattern, login))

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$"
        return bool(re.fullmatch(pattern, email))


@dataclass
class Task:
    name: str
    description: str | None
    is_complete: bool
    created_ts: datetime
    updated_ts: datetime
    due_ts: datetime
    user_id: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        self.validate()

    def validate(self):
        if len(self.name) < 3:
            raise DomainError("Task name must be at least 3 characters long")
