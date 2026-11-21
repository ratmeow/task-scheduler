import re
import uuid
from datetime import datetime, timezone

from task_scheduler.domain.entities import Task, User

from .dto import TaskCreateData, TaskListFilter, TaskListNavigation, TaskUpdateData, UserLoginData, UserRegisterData
from .exceptions import NotFoundError, PasswordRequirementError, UserNotFoundError, WrongPasswordError
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
            is_complete=False,
            created_ts=datetime.now(timezone.utc),
            updated_ts=datetime.now(timezone.utc),
            due_ts=task_data.due_ts,
            user_id=uuid.UUID(task_data.user_id),
        )
        await self.task_gateway.save(task=task)
        await self.db_session.commit()
        return task


class UpdateTaskInteractor:
    def __init__(self, task_gateway: TaskGateway, db_session: DBSession):
        self.task_gateway = task_gateway
        self.db_session = db_session

    async def __call__(self, task_data: TaskUpdateData) -> Task:
        task = await self.task_gateway.get_by_id(task_id=task_data.task_id)
        if task is None:
            raise NotFoundError(spec="Task")
        if task_data.is_data_to_update:
            task.name = task_data.name or task.name
            task.description = task_data.description or task.description
            task.due_ts = task_data.due_ts or task.due_ts
            if task_data.is_complete is not None:
                task.is_complete = task_data.is_complete
            task.updated_ts = datetime.now(timezone.utc)
        await self.task_gateway.save(task=task)
        await self.db_session.commit()
        return task


class DeleteTaskInteractor:
    def __init__(self, task_gateway: TaskGateway, db_session: DBSession):
        self.task_gateway = task_gateway
        self.db_session = db_session

    async def __call__(self, task_id) -> None:
        task = await self.task_gateway.get_by_id(task_id=task_id)
        if task is None:
            raise NotFoundError(spec="Task")
        await self.task_gateway.delete(task=task)
        await self.db_session.commit()


class ListTaskInteractor:
    def __init__(self, task_gateway: TaskGateway, db_session: DBSession):
        self.task_gateway = task_gateway
        self.db_session = db_session

    async def __call__(self, filters: TaskListFilter, navigation: TaskListNavigation) -> list[Task]:
        return await self.task_gateway.list_by(filters=filters, navigation=navigation)
