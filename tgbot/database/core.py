# - *- coding: utf- 8 - *-
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from tgbot.data.config import PATH_DATABASE

database_path = Path(PATH_DATABASE)
database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"

engine = create_async_engine(database_url, echo=False)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


# Общая база для всех SQLAlchemy-моделей
class Base(AsyncAttrs, DeclarativeBase):
    pass


# Включение SQLite-настроек на каждом соединении
@event.listens_for(engine.sync_engine, "connect")
def _configure_sqlite(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


# Открытие сессии с автокоммитом или откатом
@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Закрытие пула соединений БД
async def close_database() -> None:
    await engine.dispose()
