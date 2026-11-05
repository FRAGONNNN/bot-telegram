# - *- coding: utf- 8 - *-
from dataclasses import fields
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy import select
from sqlalchemy import update as sqlalchemy_update
from tgbot.database.core import Base, database_path, session_scope
from tgbot.database.migration_runner import run_migrations
from tgbot.utils.misc.bot_logging import bot_logger

ModelTranslator = TypeVar("ModelTranslator", bound=Base)
EntityTranslator = TypeVar("EntityTranslator")


# Базовый репозиторий для SQLAlchemy-моделей
class BaseRepository(Generic[ModelTranslator, EntityTranslator]):
    # Настройка модели репозитория
    def __init__(self):
        self.storage_name = "storage"
        self.table_model: Optional[Type[ModelTranslator]] = None
        self.entity_model: Optional[Type[EntityTranslator]] = None

    # Получение SQLAlchemy-модели репозитория
    def _model(self) -> Type[ModelTranslator]:
        if self.table_model is None:
            raise RuntimeError("Модель базы данных не настроена")

        return self.table_model

    # Преобразование ORM-строки в безопасный DTO
    def _to_entity(self, instance: ModelTranslator) -> EntityTranslator:
        if self.entity_model is None:
            raise RuntimeError("DTO-модель базы данных не настроена")

        values = {
            field.name: getattr(instance, field.name)
            for field in fields(self.entity_model)
        }

        return self.entity_model(**values)

    # Добавление записи через текущую модель
    async def _insert(self, **kwargs) -> EntityTranslator:
        model = self._model()
        instance = model(**kwargs)

        async with session_scope() as session:
            session.add(instance)
            await session.flush()
            await session.refresh(instance)

        return self._to_entity(instance)

    # Добавление записи с возвратом DTO
    async def add(self, **kwargs) -> EntityTranslator:
        return await self._insert(**kwargs)

    # Удаление записи по явному фильтру
    async def delete(self, **kwargs) -> None:
        if not kwargs:
            raise ValueError("Для удаления нужен хотя бы один фильтр")

        model = self._model()

        async with session_scope() as session:
            await session.execute(sqlalchemy_delete(model).filter_by(**kwargs))

    # Очистка текущей таблицы
    async def clear(self) -> None:
        await self.delete_all_rows()

    # Удаление всех строк текущей таблицы
    async def delete_all_rows(self) -> None:
        model = self._model()

        async with session_scope() as session:
            await session.execute(sqlalchemy_delete(model))

    # Получение первой записи по фильтру
    async def get(self, **kwargs) -> Optional[EntityTranslator]:
        model = self._model()
        statement = select(model)

        if kwargs:
            statement = statement.filter_by(**kwargs)

        if hasattr(model, "increment"):
            statement = statement.order_by(getattr(model, "increment"))

        async with session_scope() as session:
            response = await session.execute(statement)
            instance = response.scalars().first()

            if instance is None:
                return None

            return self._to_entity(instance)

    # Получение записи или явно падает
    async def get_required(self, **kwargs) -> EntityTranslator:
        entity = await self.get(**kwargs)

        if entity is None:
            raise LookupError(f"Запись не найдена в {self.storage_name}: {kwargs}")

        return entity

    # Получение списка записей по фильтру
    async def gets(self, **kwargs) -> List[EntityTranslator]:
        model = self._model()
        statement = select(model)

        if kwargs:
            statement = statement.filter_by(**kwargs)

        if hasattr(model, "increment"):
            statement = statement.order_by(getattr(model, "increment"))

        async with session_scope() as session:
            response = await session.execute(statement)

            return [self._to_entity(instance) for instance in response.scalars().all()]

    # Получение всех записей таблицы
    async def get_all(self) -> List[EntityTranslator]:
        return await self.gets()

    # Обновление записи через текущую модель
    async def _update(self, where: Optional[Dict[str, Any]] = None, **kwargs) -> int:
        if not kwargs:
            return 0

        model = self._model()
        statement = sqlalchemy_update(model).values(**kwargs)

        if where:
            statement = statement.filter_by(**where)

        async with session_scope() as session:
            result = await session.execute(statement)
            rowcount = getattr(result, "rowcount", 0)

            return int(rowcount or 0)

    # Обновление записи по фильтру
    async def update(self, where: Optional[Dict[str, Any]] = None, **kwargs) -> int:
        return await self._update(where=where, **kwargs)


# Применение миграций и создание дефолтных строк
async def prepare_database() -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    await run_migrations()

    from tgbot.database.db_payments import Paymentsx
    from tgbot.database.db_settings import Settingsx

    await Settingsx().ensure_default()
    await Paymentsx().ensure_default()

    bot_logger.info("База данных готова")
