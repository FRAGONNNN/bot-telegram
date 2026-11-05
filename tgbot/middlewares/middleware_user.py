# - *- coding: utf- 8 - *-
from aiogram import BaseMiddleware
from cachetools import TTLCache

from tgbot.data.config import BOT_USER_CACHE_TTL
from tgbot.database import Userx
from tgbot.utils.const_functions import clear_html


class ExistsUserMiddleware(BaseMiddleware):
    # Создание кеша пользователей
    def __init__(self, cache_ttl: int = BOT_USER_CACHE_TTL) -> None:
        self.users = Userx()
        self.cache = TTLCache(maxsize=10_000, ttl=cache_ttl)

    # Добавление или обновление пользователя перед handler-ом
    async def __call__(self, handler, event, data):
        this_user = data.get("event_from_user")

        if this_user is not None and not this_user.is_bot:
            user_id = this_user.id
            user_login = (this_user.username or "").lower()
            user_name = clear_html(this_user.first_name) or ""
            user_surname = clear_html(this_user.last_name) or ""
            user_fullname = clear_html(this_user.full_name) or " ".join(filter(None, [user_name, user_surname]))

            user_data = (
                user_login,
                user_name,
                user_surname,
                user_fullname,
            )

            cached_user = self.cache.get(user_id)

            if cached_user is None or cached_user["data"] != user_data:
                user = await self.users.upsert(
                    user_id=user_id,
                    user_login=user_data[0],
                    user_name=user_data[1],
                    user_surname=user_data[2],
                    user_fullname=user_data[3],
                )
                self.cache[user_id] = {"data": user_data, "user": user}
            else:
                user = cached_user["user"]

            data["User"] = user

        return await handler(event, data)
