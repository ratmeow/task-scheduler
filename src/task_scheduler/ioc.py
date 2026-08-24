from typing import AsyncIterable

from dishka import Provider, from_context, Scope, provide, AnyOf
from task_scheduler.config import Config
from sqlalchemy.orm import registry
from task_scheduler.infrastructure.database.orm import create_mapper_registry
from task_scheduler.infrastructure.database.session import pg_session_maker
from task_scheduler.infrastructure.database.gateway import PgUserGateway
from task_scheduler.infrastructure.hasher import BcryptHasher
from task_scheduler.application.interfaces import DBSession, UserGateway, Hasher
from task_scheduler.application.interactors import RegisterUserInteractor, LoginUserInteractor
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

class AppProvider(Provider):
    config = from_context(provides=Config, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def get_hasher(self) -> Hasher:
        return BcryptHasher()

    @provide(scope=Scope.APP)
    def get_mapper_registry(self) -> registry:
        return create_mapper_registry()

    @provide(scope=Scope.APP)
    def get_session_maker(self, config: Config, mapper_registry: registry) -> async_sessionmaker[AsyncSession]:
        return pg_session_maker(pg_config=config.postgres)

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, session_maker: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[AnyOf[AsyncSession, DBSession]]:
        async with session_maker() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def get_user_gateway(self, session: AsyncSession) -> UserGateway:
        return PgUserGateway(db_session=session)


    register_user = provide(RegisterUserInteractor, scope=Scope.REQUEST)
    login_user = provide(LoginUserInteractor, scope=Scope.REQUEST)