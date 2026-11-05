# - *- coding: utf- 8 - *-
from typing import Any, Dict, Optional, Union

from sqlalchemy import BigInteger, Float, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from tgbot.database.core import Base, session_factory
from tgbot.database.entities import Refill
from tgbot.database.repository import BaseRepository
from tgbot.utils.const_functions import get_unix


class RefillModel(Base):
    __tablename__ = "storage_refill"

    increment: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    refill_receipt: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    refill_comment: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    refill_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    refill_method: Mapped[str] = mapped_column(String(64), nullable=False)
    refill_unix: Mapped[int] = mapped_column(Integer, nullable=False, default=get_unix)


ModelBase = Refill
BaseModel = Refill


class Refillx(BaseRepository[RefillModel, Refill]):
    # Подключение модели пополнений
    def __init__(self):
        super().__init__()
        self.table_model = RefillModel
        self.entity_model = Refill
        self.storage_name = RefillModel.__tablename__

    # Добавление записи пополнения
    async def add(
            self,
            user_id: int,
            refill_receipt: int,
            refill_comment: str,
            refill_amount: float,
            refill_method: str,
    ) -> Refill:
        return await self._insert(
            user_id=user_id,
            refill_comment=refill_comment,
            refill_amount=refill_amount,
            refill_receipt=refill_receipt,
            refill_method=refill_method,
            refill_unix=get_unix(),
        )

    # Обновление пополнения по чеку или фильтру
    async def update(self, where: Optional[Union[Dict[str, Any], int]] = None, **kwargs) -> int:
        if isinstance(where, int):
            where = {"refill_receipt": where}

        return await self._update(where=where, **kwargs)

    # Успешное зачисление пополнения
    @staticmethod
    async def success(
            user_id: int,
            pay_receipt: int,
            pay_comment: str,
            pay_amount: float,
            pay_method: str,
    ) -> str:
        async with session_factory() as session:
            try:
                await session.execute(text("BEGIN IMMEDIATE"))

                if pay_comment != "":
                    duplicate_refill = await session.execute(
                        text("SELECT increment FROM storage_refill WHERE refill_comment = :comment LIMIT 1"),
                        {"comment": pay_comment},
                    )
                else:
                    duplicate_refill = await session.execute(
                        text("SELECT increment FROM storage_refill WHERE refill_receipt = :receipt LIMIT 1"),
                        {"receipt": pay_receipt},
                    )

                if duplicate_refill.mappings().first() is not None:
                    await session.rollback()
                    return "ALREADY"

                user_result = await session.execute(
                    text(
                        """
                        SELECT user_balance, user_refill
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

                new_balance = round(float(get_user["user_balance"]) + float(pay_amount), 2)
                new_refill = round(float(get_user["user_refill"]) + float(pay_amount), 2)

                await session.execute(
                    text(
                        """
                        INSERT INTO storage_refill (user_id,
                                                    refill_receipt,
                                                    refill_comment,
                                                    refill_amount,
                                                    refill_method,
                                                    refill_unix)
                        VALUES (:user_id, :receipt, :comment, :amount, :method, :unix)
                        """
                    ),
                    {
                        "user_id": user_id,
                        "receipt": pay_receipt,
                        "comment": pay_comment,
                        "amount": pay_amount,
                        "method": pay_method,
                        "unix": get_unix(),
                    },
                )
                await session.execute(
                    text(
                        """
                        UPDATE storage_users
                        SET user_balance = :balance,
                            user_refill  = :refill
                        WHERE user_id = :user_id
                        """
                    ),
                    {"balance": new_balance, "refill": new_refill, "user_id": user_id},
                )
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return "ok"
