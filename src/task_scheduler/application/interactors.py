import re
import uuid
from datetime import datetime, timezone

from task_scheduler.domain.entities import StatusEnum, Task, User

from .dto import TaskCreateData, UserLoginData, UserRegisterData
from .exceptions import PasswordRequirementError, UserNotFoundError, WrongPasswordError
from .interfaces import DBSession, Hasher, TaskGateway, UserGateway


class RegisterUserInteractor:
    def __init__(self, user_gateway: UserGateway, hasher: Hasher, db_session: DBSession):
        self.user_gateway = user_gateway
        self.hasher = hasher
        self.db_session = db_session

    async def __call__(self, register_data: UserRegisterData) -> str:
        if not self._is_strong_password(password=register_data.password):
            raise PasswordRequirementError()

        user = User(
            email=register_data.email,
            login=register_data.login,
            hashed_password=self.hasher.hash(text=register_data.password),
        )

        await self.user_gateway.save(user=user)
        await self.db_session.commit()
        return str(user.id)

    @staticmethod
    def _is_strong_password(password: str) -> bool:
        pattern = r"^[A-Za-z\d!@#$%^&*_]{8,}$"
        has_required_char = bool(re.search(r"[\d!@#$%^&*_]", password))
        return bool(re.fullmatch(pattern, password)) and has_required_char


class LoginUserInteractor:
    def __init__(self, user_gateway: UserGateway, hasher: Hasher):
        self.user_gateway = user_gateway
        self.hasher = hasher

    async def __call__(self, login_data: UserLoginData) -> str:
        exist_user = await self.user_gateway.get_by_login(login=login_data.login)
        if not exist_user:
            raise UserNotFoundError(info=login_data.login)

        if not self.hasher.verify_hash(original_text=login_data.password, hashed_text=exist_user.hashed_password):
            raise WrongPasswordError()
        return str(exist_user.id)


class CreateTaskInteractor:
    def __init__(self, task_gateway: TaskGateway, db_session: DBSession):
        self.task_gateway = task_gateway
        self.db_session = db_session

    async def __call__(self, task_data: TaskCreateData) -> Task:
        task = Task(
            name=task_data.name,
            description=task_data.description,
            status=StatusEnum.TO_DO,
            created_ts=datetime.now(timezone.utc),
            updated_ts=datetime.now(timezone.utc),
            due_ts=task_data.due_ts,
            user_id=uuid.UUID(task_data.user_id),
        )
        await self.task_gateway.save(task=task)
        await self.db_session.commit()
        return task
