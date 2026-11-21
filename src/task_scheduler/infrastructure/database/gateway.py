from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from task_scheduler.application.dto import TaskListFilter, TaskListNavigation
from task_scheduler.application.exceptions import AlreadyExistsError, ApplicationError
from task_scheduler.domain.entities import Task, User


class PgUserGateway:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_login(self, login: str) -> User | None:
        query = select(User).filter_by(login=login)
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        user = await self.db_session.get(User, user_id)
        return user

    async def save(self, user: User) -> None:
        self.db_session.add(user)
        try:
            await self.db_session.flush()
        except IntegrityError as exc:
            constraint = getattr(
                getattr(exc.orig, "__cause__", None),
                "constraint_name",
                None,
            )
            match constraint:
                case "uq_users_login":
                    raise AlreadyExistsError(user.login)
                case "uq_users_email":
                    raise AlreadyExistsError(user.email)


class PgTaskGateway:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_id(self, task_id: str) -> Task | None:
        task = await self.db_session.get(Task, task_id)
        return task

    async def list_by(self, filters: TaskListFilter, navigation: TaskListNavigation) -> list[Task]:
        query = select(Task)
        if filters.user_id:
            query = query.where(Task.user_id == filters.user_id)
        if filters.name:
            query = query.where(Task.name.ilike(f"%{filters.name}%"))
        if filters.is_complete:
            query = query.where(Task.is_complete == filters.is_complete)
        query = (
            query.limit(navigation.limit)
            .offset(navigation.offset)
            .order_by(navigation.sort_column.desc() if navigation.sort_desc else navigation.sort_column.asc())
        )
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def save(self, task: Task) -> None:
        self.db_session.add(task)
        try:
            await self.db_session.flush()
        except IntegrityError as exc:
            print(exc)
            raise ApplicationError()

    async def delete(self, task: Task) -> None:
        try:
            await self.db_session.delete(task)
        except IntegrityError as exc:
            print(exc)
            raise ApplicationError()
