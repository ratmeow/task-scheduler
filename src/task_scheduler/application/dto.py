from dataclasses import dataclass


@dataclass(frozen=True)
class UserRegisterData:
    login: str
    password: str
