# - *- coding: utf- 8 - *-
import asyncio
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from tgbot.database.core import database_url

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"


# Сбор Alembic-конфига от корня проекта
def get_alembic_config(url: str = database_url) -> Config:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", url)

    return config


# Применение миграций до последней версии
async def run_migrations(engine: Optional[AsyncEngine] = None) -> None:
    if engine is None:
        config = get_alembic_config()
        await asyncio.to_thread(command.upgrade, config, "head")
        return

    config = get_alembic_config(str(engine.url))

    connection = engine.connect()
    await connection.start()
    transaction = connection.begin()
    await transaction.start()

    try:
        await connection.run_sync(_upgrade_with_connection, config)
    except Exception:
        await transaction.rollback()
        raise
    else:
        await transaction.commit()
    finally:
        await connection.close()


# Запуск Alembic на готовом соединении
def _upgrade_with_connection(connection: Connection, config: Config) -> None:
    config.attributes["connection"] = connection
    command.upgrade(config, "head")
