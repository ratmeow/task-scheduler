from typing import AsyncIterable

from dishka import AnyOf, Provider, Scope, from_context, provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import registry

from task_scheduler.application.interactors import CreateTaskInteractor, LoginUserInteractor, RegisterUserInteractor
from task_scheduler.application.interfaces import DBSession, Hasher, TaskGateway, UserGateway
from task_scheduler.config import Config
from task_scheduler.infrastructure.database.gateway import PgTaskGateway, PgUserGateway
from task_scheduler.infrastructure.database.orm import create_mapper_registry
from task_scheduler.infrastructure.database.session import pg_session_maker
from task_scheduler.infrastructure.hasher import BcryptHasher
from task_scheduler.infrastructure.idp.interfaces import TokenStorage
from task_scheduler.infrastructure.idp.provider import IdentityProvider
from task_scheduler.infrastructure.idp.redis_storage import RedisTokenStorage
from task_scheduler.presentation.cookie_manager import TokenCookieManager


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

    @provide(scope=Scope.APP)
    async def get_redis_client(self, config: Config) -> AsyncIterable[Redis]:
        redis = Redis(host=config.redis.host, port=config.redis.port)
        try:
            yield redis
        finally:
            await redis.aclose()

    @provide(scope=Scope.APP)
    def get_redis_token_storage(self, redis_client: Redis) -> TokenStorage:
        return RedisTokenStorage(redis_client=redis_client)

    @provide(scope=Scope.APP)
    def get_idp(self, config: Config, token_storage: TokenStorage) -> IdentityProvider:
        return IdentityProvider(auth_config=config.auth, token_storage=token_storage)

    @provide(scope=Scope.APP)
    def get_cookie_manager(self, config: Config) -> TokenCookieManager:
        return TokenCookieManager(auth_config=config.auth)

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, session_maker: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[AnyOf[AsyncSession, DBSession]]:
        async with session_maker() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def get_user_gateway(self, session: AsyncSession) -> UserGateway:
        return PgUserGateway(db_session=session)

    @provide(scope=Scope.REQUEST)
    def get_task_gateway(self, session: AsyncSession) -> TaskGateway:
        return PgTaskGateway(db_session=session)

    register_user = provide(RegisterUserInteractor, scope=Scope.REQUEST)
    login_user = provide(LoginUserInteractor, scope=Scope.REQUEST)
    create_task = provide(CreateTaskInteractor, scope=Scope.REQUEST)
