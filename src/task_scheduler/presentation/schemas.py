from pydantic import BaseModel


class UserRegisterRequest(BaseModel):
    login: str
    password: str