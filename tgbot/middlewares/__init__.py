# - *- coding: utf- 8 - *-
from aiogram import Dispatcher

from tgbot.middlewares.middleware_throttling import ThrottlingMiddleware
from tgbot.middlewares.middleware_user import ExistsUserMiddleware


# Регистрация пользовательских middleware
def register_all_middlewares(dp: Dispatcher):
    dp.callback_query.outer_middleware(ExistsUserMiddleware())
    dp.message.outer_middleware(ExistsUserMiddleware())

    throttling = ThrottlingMiddleware()
    dp.message.middleware(throttling)
    dp.callback_query.middleware(throttling)


# Совместимое имя для старых импортов
def register_all_middlwares(dp: Dispatcher):
    register_all_middlewares(dp)
