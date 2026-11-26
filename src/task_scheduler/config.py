from os import environ

from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    access_token_alg: str = Field(default="HS256", validation_alias="ACCESS_TOKEN_ALGORITHM")
    access_token_secret: str = Field(validation_alias="ACCESS_TOKEN_SECRET")
    access_token_lifetime_s: int = Field(default=86400, validation_alias="ACCESS_TOKEN_LIFETIME_S")

    refresh_token_lifetime_s: int = Field(default=2592000, validation_alias="REFRESH_TOKEN_LIFETIME_S")
    cookie_secure: bool = Field(default=False, validation_alias="COOKIE_SECURE")


class PostgresConfig(BaseModel):
    user: str = Field(validation_alias="POSTGRES_USER")
    password: str = Field(validation_alias="POSTGRES_PASSWORD")
    db: str = Field(validation_alias="POSTGRES_DB")
    host: str = Field(validation_alias="POSTGRES_HOST")
    port: str = Field(validation_alias="POSTGRES_PORT")

    @property
    def pg_async_url(self):
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class RedisConfig(BaseModel):
    host: str = Field(validation_alias="REDIS_HOST")
    port: int = Field(validation_alias="REDIS_PORT")


class RabbitMQConfig(BaseModel):
    host: str = Field(validation_alias="RABBITMQ_HOST")
    port: int = Field(validation_alias="RABBITMQ_PORT")
    user: str = Field(validation_alias="RABBITMQ_USER")
    password: str = Field(validation_alias="RABBITMQ_PASSWORD")
    vhost: str = Field(validation_alias="RABBITMQ_VHOST")

    @property
    def amqp_url(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/{self.vhost}"


class EmailClientConfig(BaseModel):
    smtp_host: str = Field(default="smtp.resend.com", validation_alias="RESEND_SMTP_HOST")
    smtp_port: int = Field(default=465, validation_alias="RESEND_SMTP_PORT")
    api_key: str = Field(validation_alias="RESEND_API_KEY")
    sender: str = Field(validation_alias="RESEND_SENDER")


class Config(BaseModel):
    postgres: PostgresConfig = Field(default_factory=lambda: PostgresConfig(**environ))
    redis: RedisConfig = Field(default_factory=lambda: RedisConfig(**environ))
    rabbitmq: RabbitMQConfig = Field(default_factory=lambda: RabbitMQConfig(**environ))
    auth: AuthConfig = Field(default_factory=lambda: AuthConfig(**environ))
    email: EmailClientConfig = Field(default_factory=lambda: EmailClientConfig(**environ))
