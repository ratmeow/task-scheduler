import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

from task_scheduler.application.exceptions import NotFoundError
from task_scheduler.config import AuthConfig

from .dto import TokenDTO
from .exceptions import ExpiredTokenError, WrongTokenError
from .interfaces import TokenStorage


class IdentityProvider:
    def __init__(self, auth_config: AuthConfig, token_storage: TokenStorage):
        self.settings = auth_config
        self.token_storage = token_storage

    def create_access_token(self, user_id: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(self.settings.access_token_lifetime_s),
            "jti": str(uuid4()),
        }
        token = jwt.encode(
            payload=payload, key=self.settings.access_token_secret, algorithm=self.settings.access_token_alg
        )
        return token

    def validate_access_token(self, token: str) -> str:
        try:
            payload = jwt.decode(
                jwt=token, key=self.settings.access_token_secret, algorithms=[self.settings.access_token_alg]
            )
            return payload["sub"]
        except jwt.ExpiredSignatureError:
            raise ExpiredTokenError("access")
        except jwt.InvalidTokenError:
            raise WrongTokenError

    @staticmethod
    def _generate_refresh_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def create_refresh_token(self, user_id: str) -> str:
        token = self._generate_refresh_token()
        token_hash = self.hash_token(token=token)
        await self.token_storage.set(
            token_data=TokenDTO(token_hash=token_hash, user_id=user_id, ttl=self.settings.refresh_token_lifetime_s)
        )
        return token

    async def delete_refresh_token(self, token: str):
        token_hash = self.hash_token(token=token)
        await self.token_storage.delete(token_key=token_hash)

    async def rotate_refresh_token(self, token: str) -> (str, str):
        token_hash = self.hash_token(token=token)
        try:
            user_id = await self.token_storage.get(token_key=token_hash)
        except NotFoundError:
            raise WrongTokenError(token_type="refresh")
        await self.token_storage.delete(token_key=token_hash)
        new_token = await self.create_refresh_token(user_id=user_id)
        return new_token, user_id
