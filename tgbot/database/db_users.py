# - *- coding: utf- 8 - *-
from typing import Any, Dict, Optional, Union

from sqlalchemy import BigInteger, Float, Integer, String, or_
from sqlalchemy import update as sqlalchemy_update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Mapped, mapped_column

from tgbot.database.core import Base, session_scope
from tgbot.database.entities import User
from tgbot.database.repository import BaseRepository
from tgbot.utils.const_functions import get_unix


class UserModel(Base):
    __tablename__ = "storage_users"

    increment: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    user_login: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    user_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    user_surname: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    user_fullname: Mapped[str] = mapped_column(String(511), nullable=False, default="")
    user_balance: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    user_refill: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    user_give: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    user_unix: Mapped[int] = mapped_column(Integer, nullable=False, default=get_unix)


ModelBase = User
BaseModel = User


class UsersRepository(BaseRepository[UserModel, User]):
    # Подключение модели пользователей
    def __init__(self):
        super().__init__()
        self.table_model = UserModel
        self.entity_model = User
        self.storage_name = UserModel.__tablename__

    # Добавление или обновление пользователя
    async def add(
            self,
            user_id: int,
            user_login: str,
            user_name: str,
            user_surname: str = "",
            user_fullname: str = "",
    ) -> User:
        return await self.upsert(
            user_id=user_id,
            user_login=user_login,
            user_name=user_name,
            user_surname=user_surname,
            user_fullname=user_fullname or " ".join(filter(None, [user_name, user_surname])),
        )

    # Выполнение upsert пользователя по телеграм ID
    async def upsert(
            self,
            user_id: int,
            user_login: str,
            user_name: str,
            user_surname: str = "",
            user_fullname: str = "",
    ) -> User:
        user_fullname = user_fullname or " ".join(filter(None, [user_name, user_surname]))
        user_table = UserModel.__table__
        statement = insert(UserModel).values(
            user_id=user_id,
            user_login=(user_login or "").lower(),
            user_name=user_name or "",
            user_surname=user_surname or "",
            user_fullname=user_fullname or "",
            user_balance=0,
            user_refill=0,
            user_give=0,
            user_unix=get_unix(),
        )
        statement = statement.on_conflict_do_update(
            index_elements=[user_table.c.user_id],
            set_={
                "user_login": statement.excluded.user_login,
                "user_name": statement.excluded.user_name,
                "user_surname": statement.excluded.user_surname,
                "user_fullname": statement.excluded.user_fullname,
            },
            where=or_(
                user_table.c.user_login != statement.excluded.user_login,
                user_table.c.user_name != statement.excluded.user_name,
                user_table.c.user_surname != statement.excluded.user_surname,
                user_table.c.user_fullname != statement.excluded.user_fullname,
            ),
        )

        async with session_scope() as session:
            await session.execute(statement)

        user = await self.get(user_id=user_id)

        if user is None:
            raise RuntimeError("Пользователь не сохранился")

        return user

    # Обновление пользователя по ID или фильтру
    async def update(self, where: Optional[Union[Dict[str, Any], int]] = None, **kwargs) -> int:
        if isinstance(where, int):
            where = {"user_id": where}

        return await self._update(where=where, **kwargs)

    # Обновление пользователя по телеграм ID
    @staticmethod
    async def update_by_user_id(user_id: int, **kwargs) -> None:
        if not kwargs:
            return

        async with session_scope() as session:
            await session.execute(
                sqlalchemy_update(UserModel)
                .where(UserModel.__table__.c.user_id == user_id)
                .values(**kwargs)
            )


Userx = UsersRepository
