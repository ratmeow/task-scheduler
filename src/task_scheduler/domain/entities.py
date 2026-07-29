from dataclasses import dataclass, field
import uuid
import re
from .exceptions import DomainError

@dataclass
class User:
    login: str
    hashed_password: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not self._is_valid_login(self.login):
            raise DomainError(
                "Login must be at least 3 characters long, "
                "with only Latin letters, digits and special character(!@#$%^&*_)."
            )

    @staticmethod
    def _is_valid_login(login: str) -> bool:
        pattern = r"^[A-Za-z\d!@#$%^&*_]{3,}$"
        return bool(re.fullmatch(pattern, login))
