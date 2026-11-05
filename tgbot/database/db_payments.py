# - *- coding: utf- 8 - *-
from typing import Any, Dict, Optional

from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column

from tgbot.database.core import Base
from tgbot.database.entities import Payments
from tgbot.database.repository import BaseRepository


class PaymentsModel(Base):
    __tablename__ = "storage_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    cryptobot_token: Mapped[str] = mapped_column(String, nullable=False, default="None")
    yoomoney_token: Mapped[str] = mapped_column(String, nullable=False, default="None")
    stars_course: Mapped[float] = mapped_column(Float, nullable=False, default=1.5)
    status_cryptobot: Mapped[str] = mapped_column(String(16), nullable=False, default="False")
    status_yoomoney: Mapped[str] = mapped_column(String(16), nullable=False, default="False")
    status_stars: Mapped[str] = mapped_column(String(16), nullable=False, default="False")


ModelBase = Payments
BaseModel = Payments


class Paymentsx(BaseRepository[PaymentsModel, Payments]):
    # Подключение модели платежных настроек
    def __init__(self):
        super().__init__()
        self.table_model = PaymentsModel
        self.entity_model = Payments
        self.storage_name = PaymentsModel.__tablename__

    # Создание дефолтной строки платежей
    async def ensure_default(self) -> None:
        payments = await BaseRepository.get(self, id=1)

        if payments is None:
            await self._insert(id=1)

    # Получение платежных настроек
    async def get(self, **kwargs) -> Payments:
        if not kwargs:
            kwargs = {"id": 1}

        payments = await BaseRepository.get(self, **kwargs)

        if payments is None and kwargs == {"id": 1}:
            await self.ensure_default()
            payments = await BaseRepository.get(self, id=1)

        if payments is None:
            raise RuntimeError("Настройки платежных систем по умолчанию не сохранились")

        return payments

    # Обновление платежных настроек
    async def update(self, where: Optional[Dict[str, Any]] = None, **kwargs) -> int:
        if where is None:
            where = {"id": 1}

        return await self._update(where=where, **kwargs)
