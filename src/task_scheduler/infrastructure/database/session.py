from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from task_scheduler.config import PostgresConfig

def pg_session_maker(pg_config: PostgresConfig) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(url=pg_config.pg_async_url)
    return async_sessionmaker(engine, expire_on_commit=False)