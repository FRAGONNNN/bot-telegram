# - *- coding: utf- 8 - *-
from typing import Any, Dict, Optional, Union

from sqlalchemy import BigInteger, Float, Integer, String, Text, func, select
from sqlalchemy.orm import Mapped, mapped_column

from tgbot.database.core import Base, session_scope
from tgbot.database.entities import Position
from tgbot.database.repository import BaseRepository
from tgbot.utils.const_functions import get_unix


class PositionModel(Base):
    __tablename__ = "storage_position"

    increment: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    position_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    position_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position_price: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    position_desc: Mapped[str] = mapped_column(Text, nullable=False, default="None")
    position_photo: Mapped[str] = mapped_column(Text, nullable=False, default="None")
    position_unix: Mapped[int] = mapped_column(Integer, nullable=False, default=get_unix)


ModelBase = Position
BaseModel = Position


class Positionx(BaseRepository[PositionModel, Position]):
    # Подключение модели позиций
    def __init__(self):
        super().__init__()
        self.table_model = PositionModel
        self.entity_model = Position
        self.storage_name = PositionModel.__tablename__

    # Добавление позиции товара
    async def add(
            self,
            category_id: int,
            position_id: int,
            position_name: str,
            position_price: float,
            position_desc: str,
            position_photo: str,
    ) -> Position:
        return await self._insert(
            category_id=category_id,
            position_id=position_id,
            position_name=position_name,
            position_price=position_price,
            position_desc=position_desc,
            position_photo=position_photo,
            position_unix=get_unix(),
        )

    # Обновление позиции по ID или фильтру
    async def update(self, where: Optional[Union[Dict[str, Any], int]] = None, **kwargs) -> int:
        if isinstance(where, int):
            where = {"position_id": where}

        return await self._update(where=where, **kwargs)

    # Получение остатков товаров по позициям
    @staticmethod
    async def item_counts() -> Dict[int, int]:
        from tgbot.database.db_item import ItemModel

        item_table = ItemModel.__table__
        statement = (
            select(item_table.c.position_id, func.count(item_table.c.increment).label("item_count"))
            .group_by(item_table.c.position_id)
        )

        async with session_scope() as session:
            rows = await session.execute(statement)

            return {int(position_id): int(item_count) for position_id, item_count in rows.all()}
