import logging
from datetime import timedelta

from redis.asyncio import Redis, RedisError

from task_scheduler.application.exceptions import ApplicationError

from .dto import TokenDTO

logger = logging.getLogger(__name__)


class RedisNotFoundError(ApplicationError):
    def __init__(self):
        super().__init__(message="Token not found")


class RedisTokenGateway:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

    async def set(self, token_data: TokenDTO):
        try:
            await self.redis_client.setex(
                name=token_data.token_hash, time=timedelta(seconds=token_data.ttl), value=token_data.user_id
            )
        except RedisError as e:
            logger.error("Redis Internal Error:", e)
            raise ApplicationError()

    async def get(self, token_hash: str) -> str:
        try:
            user_id = await self.redis_client.get(token_hash)
            if user_id is None:
                logger.error("Not found user_id for token", token_hash)
                raise RedisNotFoundError()
            return user_id.decode()
        except RedisError as e:
            logger.error("Redis Internal Error:", e)
            raise ApplicationError()

    async def delete(self, token_hash: str) -> None:
        try:
            await self.redis_client.delete(token_hash)
        except RedisError as e:
            logger.error("Redis Internal Error:", e)
            raise ApplicationError()
