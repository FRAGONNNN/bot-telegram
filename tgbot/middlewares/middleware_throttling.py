# - *- coding: utf- 8 - *-
import time
from typing import Any, Awaitable, Callable, Dict, Optional, Union

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import CallbackQuery, Message, TelegramObject, User
from cachetools import TTLCache

from tgbot.data.config import BOT_THROTTLE_RATE


class ThrottlingMiddleware(BaseMiddleware):
    # Создание хранилищ лимитов
    def __init__(self, default_rate: Union[int, float] = BOT_THROTTLE_RATE) -> None:
        self.default_rate = default_rate
        self.message_users = TTLCache(maxsize=10_000, ttl=600)
        self.callback_users = TTLCache(maxsize=10_000, ttl=600)

    # Ограничение частых сообщений и колбэков
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject, data):
        this_user: Optional[User] = data.get("event_from_user")

        if this_user is None:
            return await handler(event, data)

        flag_rate = get_flag(data, "rate")
        rate = float(self.default_rate if flag_rate is None else flag_rate)

        if rate == 0:
            return await handler(event, data)

        now_time = time.monotonic()
        bucket = self._get_bucket(event)
        user_key = this_user.id

        if user_key not in bucket:
            bucket[user_key] = {
                "last_throttled": now_time,
                "count_throttled": 0,
                "now_rate": rate,
            }

            return await handler(event, data)

        if now_time - bucket[user_key]["last_throttled"] >= bucket[user_key]["now_rate"]:
            bucket.pop(user_key)

            return await handler(event, data)

        bucket[user_key]["last_throttled"] = now_time
        bucket[user_key]["count_throttled"] += 1

        if bucket[user_key]["count_throttled"] == 1:
            bucket[user_key]["now_rate"] = rate + 2
            await self._warn_user(event)
        elif bucket[user_key]["count_throttled"] == 2:
            bucket[user_key]["now_rate"] = rate + 3
        else:
            bucket[user_key]["now_rate"] = rate + 5

        return None

    # Выбор bucket под тип апдейта
    def _get_bucket(self, event: TelegramObject) -> TTLCache:
        if isinstance(event, CallbackQuery):
            return self.callback_users

        return self.message_users

    # Предупреждение пользователя о спаме
    @staticmethod
    async def _warn_user(event: TelegramObject) -> None:
        if isinstance(event, Message):
            await event.reply("<b>❗ Пожалуйста, не спамьте</b>")
        elif isinstance(event, CallbackQuery) or hasattr(event, "answer"):
            await event.answer("❗ Пожалуйста, не спамьте", cache_time=1)
