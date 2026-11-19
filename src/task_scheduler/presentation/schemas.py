from datetime import datetime

from pydantic import BaseModel

from task_scheduler.domain.entities import StatusEnum, Task


class UserRegisterRequest(BaseModel):
    email: str
    login: str
    password: str


class UserLoginRequest(BaseModel):
    login: str
    password: str


class TaskCreateRequest(BaseModel):
    name: str
    description: str | None
    due_ts: datetime


class TaskResponse(BaseModel):
    task_id: str
    name: str
    description: str | None
    status: StatusEnum
    due_ts: datetime
    created_ts: datetime
    updated_ts: datetime

    @classmethod
    def from_domain_model(cls, data: Task) -> "TaskResponse":
        result = TaskResponse(
            task_id=str(data.id),
            description=data.description,
            name=data.name,
            due_ts=data.due_ts,
            created_ts=data.created_ts,
            updated_ts=data.updated_ts,
            status=data.status.value,
        )
        return result
