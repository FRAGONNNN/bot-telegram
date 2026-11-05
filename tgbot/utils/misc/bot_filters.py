# - *- coding: utf- 8 - *-
from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from tgbot.data.config import get_admins
from tgbot.database import Settingsx


class IsAdmin(BaseFilter):
    # Проверка, что пользователь админ
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        user = getattr(event, "from_user", None)

        return bool(user and user.id in get_admins())


class IsPrivate(BaseFilter):
    # Проверка приватного чата
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        chat = getattr(event, "chat", None)
        message = getattr(event, "message", None)

        if chat is None and message is not None:
            chat = message.chat

        if chat is None:
            return True

        return chat.type == "private"


class IsWork(BaseFilter):
    # Проверка режима тех. работ
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        user = getattr(event, "from_user", None)
        settings = await Settingsx().get()

        if settings.status_work == "False" or (user and user.id in get_admins()):
            return False

        return True


class IsRefill(BaseFilter):
    # Проверка доступности пополнений
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        user = getattr(event, "from_user", None)
        settings = await Settingsx().get()

        if settings.status_refill == "True" or (user and user.id in get_admins()):
            return False

        return True


class IsBuy(BaseFilter):
    # Проверка доступности покупок
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        user = getattr(event, "from_user", None)
        settings = await Settingsx().get()

        if settings.status_buy == "True" or (user and user.id in get_admins()):
            return False

        return True
