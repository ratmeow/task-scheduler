from os import environ

from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    access_token_alg: str = Field(default="HS256", validation_alias="ACCESS_TOKEN_ALGORITHM")
    access_token_secret: str = Field(validation_alias="ACCESS_TOKEN_SECRET")
    access_token_lifetime_s: int = Field(default=86400, validation_alias="ACCESS_TOKEN_LIFETIME_S")


class PostgresConfig(BaseModel):
    user: str = Field(validation_alias="POSTGRES_USER")
    password: str = Field(validation_alias="POSTGRES_PASSWORD")
    db: str = Field(validation_alias="POSTGRES_DB")
    host: str = Field(validation_alias="POSTGRES_HOST")
    port: str = Field(validation_alias="POSTGRES_PORT")

    @property
    def pg_async_url(self):
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class Config(BaseModel):
    postgres: PostgresConfig = Field(default_factory=lambda: PostgresConfig(**environ))
    auth: AuthConfig = Field(default_factory=lambda: AuthConfig(**environ))
