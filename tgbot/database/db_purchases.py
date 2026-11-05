# - *- coding: utf- 8 - *-
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import BigInteger, Float, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from tgbot.database.core import Base, session_factory
from tgbot.database.entities import Purchase
from tgbot.database.repository import BaseRepository
from tgbot.utils.const_functions import gen_id, get_unix

TELEGRAM_LIMIT = 4000


@dataclass
class PurchaseResult:
    receipt: int
    items: List[List[str]]
    purchase_count: int
    purchase_unix: int
    purchase_price: float
    new_balance: float
    position_name: str


class PurchaseModel(Base):
    __tablename__ = "storage_purchases"

    increment: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_balance_before: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    user_balance_after: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    purchase_receipt: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    purchase_data: Mapped[str] = mapped_column(Text, nullable=False)
    purchase_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    purchase_price_one: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    purchase_position_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    purchase_position_name: Mapped[str] = mapped_column(String(255), nullable=False)
    purchase_category_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    purchase_category_name: Mapped[str] = mapped_column(String(255), nullable=False)
    purchase_unix: Mapped[int] = mapped_column(Integer, nullable=False, default=get_unix)


ModelBase = Purchase
BaseModel = Purchase


class Purchasesx(BaseRepository[PurchaseModel, Purchase]):
    # Подключение модели покупок
    def __init__(self):
        super().__init__()
        self.table_model = PurchaseModel
        self.entity_model = Purchase
        self.storage_name = PurchaseModel.__tablename__

    # Добавление записи покупки
    async def add(
            self,
            user_id: int,
            user_balance_before: float,
            user_balance_after: float,
            purchase_receipt: int,
            purchase_data: str,
            purchase_count: int,
            purchase_price: float,
            purchase_price_one: float,
            purchase_position_id: int,
            purchase_position_name: str,
            purchase_category_id: int,
            purchase_category_name: str,
    ) -> Purchase:
        return await self._insert(
            user_id=user_id,
            user_balance_before=user_balance_before,
            user_balance_after=user_balance_after,
            purchase_receipt=purchase_receipt,
            purchase_data=purchase_data,
            purchase_count=purchase_count,
            purchase_price=purchase_price,
            purchase_price_one=purchase_price_one,
            purchase_position_id=purchase_position_id,
            purchase_position_name=purchase_position_name,
            purchase_category_id=purchase_category_id,
            purchase_category_name=purchase_category_name,
            purchase_unix=get_unix(),
        )

    # Обновление покупки по чеку или фильтру
    async def update(self, where: Optional[Union[Dict[str, Any], int]] = None, **kwargs) -> int:
        if isinstance(where, int):
            where = {"purchase_receipt": where}

        return await self._update(where=where, **kwargs)

    # Атомарная покупка товаров
    @staticmethod
    async def buy(*, user_id: int, position_id: int, requested_count: int) -> Union[PurchaseResult, str]:
        async with session_factory() as session:
            try:
                await session.execute(text("BEGIN IMMEDIATE"))

                user_result = await session.execute(
                    text(
                        """
                        SELECT user_balance
                        FROM storage_users
                        WHERE user_id = :user_id
                        """
                    ),
                    {"user_id": user_id},
                )
                get_user = user_result.mappings().first()

                if get_user is None:
                    await session.rollback()
                    return "USER_NOT_FOUND"

                position_result = await session.execute(
                    text(
                        """
                        SELECT position_price, position_name, category_id
                        FROM storage_position
                        WHERE position_id = :position_id
                        """
                    ),
                    {"position_id": position_id},
                )
                get_position = position_result.mappings().first()

                if get_position is None:
                    await session.rollback()
                    return "POSITION_NOT_FOUND"

                items_result = await session.execute(
                    text(
                        """
                        SELECT increment, item_id, item_data
                        FROM storage_item
                        WHERE position_id = :position_id
                        ORDER BY increment
                        LIMIT :requested_count
                        """
                    ),
                    {"position_id": position_id, "requested_count": requested_count},
                )
                items = items_result.mappings().all()

                if len(items) < requested_count:
                    await session.rollback()
                    return "NOT_ENOUGH_ITEMS"

                purchase_price = round(float(get_position["position_price"]) * requested_count, 2)

                if float(get_user["user_balance"]) < purchase_price:
                    await session.rollback()
                    return "NOT_ENOUGH_BALANCE"

                item_ids = [row["item_id"] for row in items]
                delete_params = {f"item_id_{index}": item_id for index, item_id in enumerate(item_ids)}
                delete_marks = ", ".join(f":item_id_{index}" for index in range(len(item_ids)))
                await session.execute(
                    text(f"DELETE FROM storage_item WHERE item_id IN ({delete_marks})"),
                    delete_params,
                )

                new_balance = round(float(get_user["user_balance"]) - purchase_price, 2)

                await session.execute(
                    text(
                        """
                        UPDATE storage_users
                        SET user_balance = :new_balance
                        WHERE user_id = :user_id
                        """
                    ),
                    {"new_balance": new_balance, "user_id": user_id},
                )

                receipt = gen_id()
                purchase_data = "\n".join([row["item_data"] for row in items])
                purchase_unix = get_unix()

                category_result = await session.execute(
                    text("SELECT category_name FROM storage_category WHERE category_id = :category_id"),
                    {"category_id": get_position["category_id"]},
                )
                category = category_result.mappings().first()
                category_name = category["category_name"] if category else "Unknown"

                await session.execute(
                    text(
                        """
                        INSERT INTO storage_purchases (user_id,
                                                       user_balance_before,
                                                       user_balance_after,
                                                       purchase_receipt,
                                                       purchase_data,
                                                       purchase_count,
                                                       purchase_price,
                                                       purchase_price_one,
                                                       purchase_position_id,
                                                       purchase_position_name,
                                                       purchase_category_id,
                                                       purchase_category_name,
                                                       purchase_unix)
                        VALUES (:user_id,
                                :balance_before,
                                :balance_after,
                                :receipt,
                                :purchase_data,
                                :purchase_count,
                                :purchase_price,
                                :purchase_price_one,
                                :position_id,
                                :position_name,
                                :category_id,
                                :category_name,
                                :purchase_unix)
                        """
                    ),
                    {
                        "user_id": user_id,
                        "balance_before": float(get_user["user_balance"]),
                        "balance_after": new_balance,
                        "receipt": receipt,
                        "purchase_data": purchase_data,
                        "purchase_count": requested_count,
                        "purchase_price": purchase_price,
                        "purchase_price_one": float(get_position["position_price"]),
                        "position_id": position_id,
                        "position_name": get_position["position_name"],
                        "category_id": get_position["category_id"],
                        "category_name": category_name,
                        "purchase_unix": purchase_unix,
                    },
                )
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        purchase_items = [row["item_data"] for row in items]
        purchase_items_parts = chunk_items_by_len(purchase_items)

        return PurchaseResult(
            receipt=receipt,
            items=purchase_items_parts,
            purchase_count=requested_count,
            purchase_unix=purchase_unix,
            purchase_price=purchase_price,
            position_name=get_position["position_name"],
            new_balance=new_balance,
        )


# Разделение товаров на сообщения под лимит телеграма
def chunk_items_by_len(items: List[str], limit: int = TELEGRAM_LIMIT, separator: str = "\n\n") -> List[List[str]]:
    chunks: List[List[str]] = []
    current_chunk: List[str] = []
    current_len = 0
    sep_len = len(separator)

    for raw_item in items:
        item = str(raw_item)

        if len(item) > limit:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_len = 0

            for part in split_long_item(item, limit):
                chunks.append([part])

            continue

        add_len = len(item) if not current_chunk else sep_len + len(item)

        if current_len + add_len <= limit:
            current_chunk.append(item)
            current_len += add_len
        else:
            chunks.append(current_chunk)
            current_chunk = [item]
            current_len = len(item)

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# Разделение длинного товара без разрыва строк
def split_long_item(item: str, limit: int = TELEGRAM_LIMIT) -> List[str]:
    chunks: List[str] = []
    current_lines: List[str] = []
    current_len = 0

    for line in item.splitlines():
        line_len = len(line)
        add_len = line_len if not current_lines else 1 + line_len

        if current_lines and current_len + add_len > limit:
            chunks.append("\n".join(current_lines))
            current_lines = []
            current_len = 0
            add_len = line_len

        if line_len > limit:
            if current_lines:
                chunks.append("\n".join(current_lines))
                current_lines = []
                current_len = 0

            start = 0

            while start < line_len:
                chunks.append(line[start:start + limit])
                start += limit

            continue

        current_lines.append(line)
        current_len += add_len

    if current_lines:
        chunks.append("\n".join(current_lines))

    return chunks
