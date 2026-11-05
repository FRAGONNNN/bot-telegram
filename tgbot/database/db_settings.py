# - *- coding: utf- 8 - *-
from typing import Any, Dict, Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from tgbot.database.core import Base
from tgbot.database.entities import Settings
from tgbot.database.repository import BaseRepository


class SettingsModel(Base):
    __tablename__ = "storage_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    status_work: Mapped[str] = mapped_column(String(16), nullable=False, default="True")
    status_refill: Mapped[str] = mapped_column(String(16), nullable=False, default="False")
    status_buy: Mapped[str] = mapped_column(String(16), nullable=False, default="False")
    notification_refill: Mapped[str] = mapped_column(String(16), nullable=False, default="True")
    notification_buy: Mapped[str] = mapped_column(String(16), nullable=False, default="False")
    misc_faq: Mapped[str] = mapped_column(String, nullable=False, default="None")
    misc_support: Mapped[str] = mapped_column(String, nullable=False, default="None")
    misc_bot: Mapped[str] = mapped_column(String(255), nullable=False, default="None")
    misc_hosting_text: Mapped[str] = mapped_column(String(64), nullable=False, default="telegraph")
    misc_token_telegraph: Mapped[str] = mapped_column(String, nullable=False, default="None")
    misc_discord_webhook_url: Mapped[str] = mapped_column(String, nullable=False, default="None")
    misc_discord_webhook_name: Mapped[str] = mapped_column(String(255), nullable=False, default="None")
    misc_hide_category: Mapped[str] = mapped_column(String(16), nullable=False, default="False")
    misc_hide_position: Mapped[str] = mapped_column(String(16), nullable=False, default="False")
    misc_method_prod: Mapped[str] = mapped_column(String(16), nullable=False, default="skip")
    misc_profit_day: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    misc_profit_week: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    misc_profit_month: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


ModelBase = Settings
BaseModel = Settings


class Settingsx(BaseRepository[SettingsModel, Settings]):
    # Подключение модели настроек
    def __init__(self):
        super().__init__()
        self.table_model = SettingsModel
        self.entity_model = Settings
        self.storage_name = SettingsModel.__tablename__

    # Создание дефолтной строки настроек
    async def ensure_default(self) -> None:
        settings = await BaseRepository.get(self, id=1)

        if settings is None:
            await self._insert(id=1)

    # Получение настроек бота
    async def get(self, **kwargs) -> Settings:
        if not kwargs:
            kwargs = {"id": 1}

        settings = await BaseRepository.get(self, **kwargs)

        if settings is None and kwargs == {"id": 1}:
            await self.ensure_default()
            settings = await BaseRepository.get(self, id=1)

        if settings is None:
            raise RuntimeError("Настройки бота по умолчанию не сохранились")

        return settings

    # Обновление настроек бота
    async def update(self, where: Optional[Dict[str, Any]] = None, **kwargs) -> int:
        if where is None:
            where = {"id": 1}

        return await self._update(where=where, **kwargs)
