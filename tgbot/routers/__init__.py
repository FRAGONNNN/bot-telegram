# - *- coding: utf- 8 - *-
from aiogram import Dispatcher

from tgbot.routers import main_errors, main_start, main_missed
from tgbot.routers.admin import admin_menu, admin_functions, admin_payments, admin_products, admin_settings
from tgbot.routers.user import user_menu, user_transactions, user_products
from tgbot.utils.misc.bot_filters import IsAdmin, IsPrivate


# Регистрация всех роутеров
def register_all_routers(dp: Dispatcher):
    # Подключение фильтров
    main_errors.router.message.filter(IsPrivate())
    main_errors.router.callback_query.filter(IsPrivate())
    main_start.router.message.filter(IsPrivate())
    main_start.router.callback_query.filter(IsPrivate())
    main_missed.router.message.filter(IsPrivate())
    main_missed.router.callback_query.filter(IsPrivate())

    user_menu.router.message.filter(IsPrivate())
    user_menu.router.callback_query.filter(IsPrivate())
    user_products.router.message.filter(IsPrivate())
    user_products.router.callback_query.filter(IsPrivate())
    user_transactions.router.message.filter(IsPrivate())
    user_transactions.router.callback_query.filter(IsPrivate())

    admin_menu.router.message.filter(IsPrivate(), IsAdmin())  # Работа message роутера только для админов
    admin_menu.router.callback_query.filter(IsPrivate(), IsAdmin())  # Работа callback роутера только для админов
    admin_functions.router.message.filter(IsPrivate(), IsAdmin())  # Работа message роутера только для админов
    admin_functions.router.callback_query.filter(IsPrivate(), IsAdmin())  # Работа callback роутера только для админов
    admin_payments.router.message.filter(IsPrivate(), IsAdmin())  # Работа message роутера только для админов
    admin_payments.router.callback_query.filter(IsPrivate(), IsAdmin())  # Работа callback роутера только для админов
    admin_settings.router.message.filter(IsPrivate(), IsAdmin())  # Работа message роутера только для админов
    admin_settings.router.callback_query.filter(IsPrivate(), IsAdmin())  # Работа callback роутера только для админов
    admin_products.router.message.filter(IsPrivate(), IsAdmin())  # Работа message роутера только для админов
    admin_products.router.callback_query.filter(IsPrivate(), IsAdmin())  # Работа callback роутера только для админов

    # Подключение обязательных роутеров
    dp.include_router(main_errors.router)  # Роутер ошибки
    dp.include_router(main_start.router)  # Роутер основных команд

    # Подключение пользовательских роутеров (юзеров и админов)
    dp.include_router(user_menu.router)  # Юзер роутер
    dp.include_router(admin_menu.router)  # Админ роутер
    dp.include_router(user_products.router)  # Юзер роутер
    dp.include_router(user_transactions.router)  # Юзер роутер
    dp.include_router(admin_functions.router)  # Админ роутер
    dp.include_router(admin_payments.router)  # Админ роутер
    dp.include_router(admin_settings.router)  # Админ роутер
    dp.include_router(admin_products.router)  # Админ роутер

    # Подключение обязательных роутеров
    dp.include_router(main_missed.router)  # Роутер пропущенных апдейтов
