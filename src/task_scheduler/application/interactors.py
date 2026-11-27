import re
import uuid
from datetime import datetime, timezone

from task_scheduler.domain.entities import (
    Task,
    TaskCreatedDetails,
    TaskDeletedDetails,
    TaskEvent,
    TaskUpdatedDetails,
    User,
)

from .dto import TaskCreateData, TaskListFilter, TaskListNavigation, TaskUpdateData, UserLoginData, UserRegisterData
from .exceptions import NotFoundError, PasswordRequirementError, UserNotFoundError, WrongPasswordError
from .interfaces import DBSession, Hasher, TaskEventGateway, TaskGateway, UserGateway


class RegisterUserInteractor:
    def __init__(self, user_gateway: UserGateway, hasher: Hasher, db_session: DBSession):
        self.user_gateway = user_gateway
        self.hasher = hasher
        self.db_session = db_session

    async def __call__(self, register_data: UserRegisterData) -> User:
        if not self._is_strong_password(password=register_data.password):
            raise PasswordRequirementError()

        user = User(
            email=register_data.email,
            login=register_data.login,
            hashed_password=self.hasher.hash(text=register_data.password),
        )

        await self.user_gateway.save(user=user)
        await self.db_session.commit()
        return user

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
    def __init__(self, task_gateway: TaskGateway, task_event_gateway: TaskEventGateway, db_session: DBSession):
        self.task_gateway = task_gateway
        self.task_event_gateway = task_event_gateway
        self.db_session = db_session

    async def __call__(self, task_data: TaskCreateData) -> Task:
        event_ts = datetime.now(timezone.utc)
        task = Task(
            name=task_data.name,
            description=task_data.description,
            is_complete=False,
            created_ts=event_ts,
            updated_ts=event_ts,
            due_ts=task_data.due_ts,
            user_id=uuid.UUID(task_data.user_id),
        )
        event = TaskEvent(
            task_id=task.id,
            user_id=task.user_id,
            action="created",
            details=TaskCreatedDetails(name=task.name, description=task.description),
            event_ts=event_ts,
        )
        await self.task_gateway.save(task=task)
        await self.task_event_gateway.save(event=event)
        await self.db_session.commit()
        return task


class UpdateTaskInteractor:
    def __init__(self, task_gateway: TaskGateway, task_event_gateway: TaskEventGateway, db_session: DBSession):
        self.task_gateway = task_gateway
        self.task_event_gateway = task_event_gateway
        self.db_session = db_session

    async def __call__(self, task_data: TaskUpdateData) -> Task:
        task = await self.task_gateway.get_by_id(task_id=task_data.task_id)
        if task is None:
            raise NotFoundError(spec="Task")

        changes = self._apply_changes(task=task, task_data=task_data)
        if changes:
            user_id = uuid.UUID(task_data.user_id)
            task.updated_ts = datetime.now(timezone.utc)
            await self.task_gateway.save(task=task)
            for details in changes:
                await self.task_event_gateway.save(
                    event=TaskEvent(
                        task_id=task.id,
                        user_id=user_id,
                        action="updated",
                        details=details,
                        event_ts=task.updated_ts,
                    )
                )
        await self.db_session.commit()
        return task

    @staticmethod
    def _apply_changes(task: Task, task_data: TaskUpdateData) -> list[TaskUpdatedDetails]:
        changes = []
        if task_data.name and task_data.name != task.name:
            task.name = task_data.name
            changes.append(TaskUpdatedDetails(name=task.name, field="name", value=task.name))

        description = task_data.description or None
        if task_data.description is not None and description != task.description:
            task.description = description
            changes.append(TaskUpdatedDetails(name=task.name, field="description", value=description))

        due_ts = task_data.due_ts
        if due_ts is not None and due_ts.astimezone(timezone.utc) != task.due_ts.astimezone(timezone.utc):
            task.due_ts = due_ts
            changes.append(TaskUpdatedDetails(name=task.name, field="due_ts", value=due_ts.isoformat()))

        if task_data.is_complete is not None and task_data.is_complete != task.is_complete:
            task.is_complete = task_data.is_complete
            changes.append(TaskUpdatedDetails(name=task.name, field="is_complete", value=task.is_complete))
        return changes


class DeleteTaskInteractor:
    def __init__(self, task_gateway: TaskGateway, task_event_gateway: TaskEventGateway, db_session: DBSession):
        self.task_gateway = task_gateway
        self.task_event_gateway = task_event_gateway
        self.db_session = db_session

    async def __call__(self, task_id: str, user_id: str) -> None:
        task = await self.task_gateway.get_by_id(task_id=task_id)
        if task is None:
            raise NotFoundError(spec="Task")
        event = TaskEvent(
            task_id=task.id,
            user_id=uuid.UUID(user_id),
            action="deleted",
            details=TaskDeletedDetails(name=task.name),
            event_ts=datetime.now(timezone.utc),
        )
        await self.task_gateway.delete(task=task)
        await self.task_event_gateway.save(event=event)
        await self.db_session.commit()


class ListTaskInteractor:
    def __init__(self, task_gateway: TaskGateway, db_session: DBSession):
        self.task_gateway = task_gateway
        self.db_session = db_session

    async def __call__(self, filters: TaskListFilter, navigation: TaskListNavigation) -> list[Task]:
        return await self.task_gateway.list_by(filters=filters, navigation=navigation)
