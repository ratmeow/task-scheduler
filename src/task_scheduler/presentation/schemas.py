from pydantic import BaseModel


class UserRegisterRequest(BaseModel):
    email: str
    login: str
    password: str


class UserLoginRequest(BaseModel):
    login: str
    password: str
