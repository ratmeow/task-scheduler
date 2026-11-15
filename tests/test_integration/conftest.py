from typing import AsyncIterable

import pytest
import pytest_asyncio
from redis.asyncio import Redis

from task_scheduler.config import Config
from task_scheduler.infrastructure.idp.provider import IdentityProvider
from task_scheduler.infrastructure.idp.redis_storage import RedisTokenStorage


@pytest.fixture(scope="session")
def config() -> Config:
    return Config()


@pytest_asyncio.fixture
async def redis_client(config: Config) -> AsyncIterable[Redis]:
    redis = Redis(host=config.redis.host, port=config.redis.port, db=15)
    try:
        await redis.flushdb()
        yield redis
    finally:
        await redis.aclose()


@pytest.fixture
def token_storage(redis_client: Redis) -> RedisTokenStorage:
    return RedisTokenStorage(redis_client=redis_client)


@pytest.fixture
def idp(config: Config, token_storage: RedisTokenStorage) -> IdentityProvider:
    return IdentityProvider(auth_config=config.auth, token_storage=token_storage)
