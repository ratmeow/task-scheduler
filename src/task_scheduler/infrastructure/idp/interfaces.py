from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

from task_scheduler.application.exceptions import ApplicationError
from task_scheduler.config import AuthConfig


class ExpiredAccessTokenError(ApplicationError):
    def __init__(self):
        super().__init__(message="Access token has expired!")


class WrongAccessTokenError(ApplicationError):
    def __init__(self):
        super().__init__(message="Wrong access token!")


class IdentityProvider:
    def __init__(self, auth_config: AuthConfig):
        self.settings = auth_config

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
            raise ExpiredAccessTokenError
        except jwt.InvalidTokenError:
            raise WrongAccessTokenError

    async def create_refresh_token(self):
        pass

    async def delete_refresh_token(self, refresh_token: str):
        pass
