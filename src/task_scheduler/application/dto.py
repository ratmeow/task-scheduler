from dataclasses import dataclass


@dataclass(frozen=True)
class UserRegisterData:
    email: str
    login: str
    password: str


@dataclass(frozen=True)
class UserLoginData:
    login: str
    password: str
