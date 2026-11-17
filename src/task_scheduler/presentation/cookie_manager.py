from fastapi import Response

from task_scheduler.config import AuthConfig


class TokenCookieManager:
    def __init__(self, auth_config: AuthConfig):
        self.settings = auth_config

    def set_tokens(
        self,
        response: Response,
        access_token: str,
        refresh_token: str,
    ) -> None:
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=self.settings.cookie_secure,
            samesite="lax",
            path="/api",
            max_age=self.settings.access_token_lifetime_s,
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=self.settings.cookie_secure,
            samesite="lax",
            path="/api/auth",
            max_age=self.settings.refresh_token_lifetime_s,
        )

    def delete_tokens(self, response: Response) -> None:
        response.delete_cookie(
            key="access_token",
            path="/api",
        )
        response.delete_cookie(
            key="refresh_token",
            path="/api/auth",
        )
