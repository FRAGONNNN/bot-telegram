# - *- coding: utf- 8 - *-
from typing import Any, Dict, Optional, Union

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from tgbot.database.core import Base
from tgbot.database.entities import Category
from tgbot.database.repository import BaseRepository
from tgbot.utils.const_functions import get_unix


class CategoryModel(Base):
    __tablename__ = "storage_category"

    increment: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    category_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_unix: Mapped[int] = mapped_column(Integer, nullable=False, default=get_unix)


ModelBase = Category
BaseModel = Category


class Categoryx(BaseRepository[CategoryModel, Category]):
    # Подключение модели категорий
    def __init__(self):
        super().__init__()
        self.table_model = CategoryModel
        self.entity_model = Category
        self.storage_name = CategoryModel.__tablename__

    # Добавление категории товара
    async def add(self, category_id: int, category_name: str) -> Category:
        return await self._insert(
            category_id=category_id,
            category_name=category_name,
            category_unix=get_unix(),
        )

    # Обновление категории по ID или фильтру
    async def update(self, where: Optional[Union[Dict[str, Any], int]] = None, **kwargs) -> int:
        if isinstance(where, int):
            where = {"category_id": where}

        return await self._update(where=where, **kwargs)
