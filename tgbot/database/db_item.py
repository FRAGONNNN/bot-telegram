# - *- coding: utf- 8 - *-
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import BigInteger, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from tgbot.database.core import Base, session_scope
from tgbot.database.entities import Item
from tgbot.database.repository import BaseRepository
from tgbot.utils.const_functions import clear_list, gen_id, get_unix


class ItemModel(Base):
    __tablename__ = "storage_item"

    increment: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    position_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    item_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    item_unix: Mapped[int] = mapped_column(Integer, nullable=False, default=get_unix)
    item_data: Mapped[str] = mapped_column(Text, nullable=False)


ModelBase = Item
BaseModel = Item


class Itemx(BaseRepository[ItemModel, Item]):
    # Подключение модели товаров
    def __init__(self):
        super().__init__()
        self.table_model = ItemModel
        self.entity_model = Item
        self.storage_name = ItemModel.__tablename__

    # Добавление товаров пачкой
    async def add(
            self,
            user_id: int,
            category_id: int,
            position_id: int,
            item_datas: List[str],
    ) -> Optional[List[Item]]:
        item_unix = get_unix()
        item_datas = clear_list(item_datas)

        if len(item_datas) == 0:
            return None

        rows = [
            ItemModel(
                user_id=user_id,
                category_id=category_id,
                position_id=position_id,
                item_id=gen_id(17),
                item_unix=item_unix,
                item_data=item_data.strip(),
            )
            for item_data in item_datas
        ]

        async with session_scope() as session:
            session.add_all(rows)

        return [self._to_entity(row) for row in rows]

    # Обновление товара по ID или фильтру
    async def update(self, where: Optional[Union[Dict[str, Any], int]] = None, **kwargs) -> int:
        if isinstance(where, int):
            where = {"item_id": where}

        return await self._update(where=where, **kwargs)