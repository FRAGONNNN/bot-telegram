# - *- coding: utf- 8 - *-
from functools import lru_cache
from pathlib import Path
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pytz import UnknownTimeZoneError, timezone

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"


# Все настройки из окружения и локального .env
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
        enable_decoding=False,
    )

    bot_token: str = Field(default="", validation_alias="BOT_TOKEN")
    admin_ids: List[int] = Field(default_factory=list, validation_alias="BOT_ADMIN_IDS")
    database_export: bool = Field(
        default=True,
        validation_alias="BOT_DATABASE_EXPORT",
    )
    status_notification: bool = Field(default=True, validation_alias="BOT_STATUS_NOTIFICATION")
    timezone: str = Field(default="Europe/Moscow", validation_alias="BOT_TIMEZONE")
    database_path: str = Field(default="tgbot/data/database.db", validation_alias="PATH_DATABASE")
    logs_path: str = Field(default="tgbot/data/logs.log", validation_alias="PATH_LOGS")
    user_cache_ttl: int = Field(default=300, ge=0, validation_alias="BOT_USER_CACHE_TTL")
    throttle_rate: float = Field(default=0.5, ge=0, validation_alias="BOT_THROTTLE_RATE")
    yoomoney_client_id: str = Field(default="", validation_alias="YOOMONEY_CLIENT_ID")

    # Очистка строковых значений из окружения
    @field_validator("bot_token", "timezone", "database_path", "logs_path", "yoomoney_client_id", mode="before")
    @classmethod
    def _strip_string(cls, value: object) -> str:
        return str(value or "").strip()

    # Разбор списка телеграм ID админов
    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: object) -> List[int]:
        if value is None or value == "":
            return []

        if isinstance(value, int):
            values = [value]
        elif isinstance(value, str):
            values = [admin_id for admin_id in value.replace(" ", "").split(",") if admin_id]
        elif isinstance(value, (list, tuple, set)):
            values = list(value)
        else:
            raise ValueError("BOT_ADMIN_IDS должен быть числом или списком чисел через запятую")

        admin_ids = []

        for admin_id in values:
            try:
                parsed_id = int(admin_id)
            except (TypeError, ValueError) as error:
                raise ValueError("BOT_ADMIN_IDS должен содержать только Телеграм ID через запятую") from error

            if parsed_id <= 0:
                raise ValueError("BOT_ADMIN_IDS должен содержать Телеграм ID больше нуля")

            admin_ids.append(parsed_id)

        return admin_ids

    # Проверка корректности timezone
    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, value: str) -> str:
        try:
            timezone(value)
        except UnknownTimeZoneError as error:
            raise ValueError("BOT_TIMEZONE должен быть корректной временной зоной, например Europe/Moscow") from error

        return value

    # Проверка непустых путей файлов
    @field_validator("database_path", "logs_path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        if not value:
            raise ValueError("Путь к файлу не должен быть пустым")

        return value

    # Получение копии списка админов
    @property
    def admins(self) -> List[int]:
        return list(self.admin_ids)

    # Преобразование относительного пути в абсолютный
    @staticmethod
    def resolve_path(path_value: str) -> Path:
        path = Path(path_value)

        if path.is_absolute():
            return path

        return BASE_DIR / path


# Кэширование настроек
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# Константы для старых импортов
BOT_TOKEN = settings.bot_token.replace(" ", "")
PATH_DATABASE = str(Settings.resolve_path(settings.database_path))
PATH_LOGS = str(Settings.resolve_path(settings.logs_path))
BOT_STATUS_NOTIFICATION = settings.status_notification
BOT_DATABASE_EXPORT = settings.database_export
BOT_TIMEZONE = settings.timezone
BOT_USER_CACHE_TTL = settings.user_cache_ttl
BOT_THROTTLE_RATE = settings.throttle_rate
YOOMONEY_CLIENT_ID = settings.yoomoney_client_id
BOT_SCHEDULER = AsyncIOScheduler(timezone=BOT_TIMEZONE)
BOT_VERSION = 4.2


# Получение администраторов бота
def get_admins() -> List[int]:
    return settings.admins


# Проверка настроек, которые нужны именно для запуска бота
def validate_bot_config() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("В .env не заполнен BOT_TOKEN")


# Получение описания
def get_text_desc() -> str:
    from tgbot.utils.const_functions import ded

    return ded(f"""
        <b>♻️ Версия бота: <code>{BOT_VERSION}</code>
        👑 Разработчик бота - @djimbox
        🍩 Донат разработчику: <a href='https://t.me/send?start=IV8bjPKhYkYJ'>Click me</a>
        🤖 Новости и обновления: <a href='https://t.me/DJIMBO_SHOP'>Click me</a>
        🔗 Тема с ботом [LOLZ]: <a href='https://lolz.guru/threads/1888814'>Click me</a></b>
    """).strip()


# Получение варнинг-текста
def get_text_warning() -> str:
    from tgbot.utils.const_functions import ded

    return ded(f"""
        ❗️ Если вы видите данное сообщение, значит <u>Администратор</u> бота не изменил текст установленный
        по умолчанию. Скорее всего данный бот занимается <u>скамом, обманом</u> или другими схожими действиями.

        ❗️ Если вас обманули, не надо писать <b><u>РАЗРАБОТЧИКУ</u></b> бота, он ничем не сможет помочь. Бот является
        открытым и распространяется публично. Абсолютно любой желающий мог его запустить.
    """)
