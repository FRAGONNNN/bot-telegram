# - *- coding: utf- 8 - *-
import asyncio
import os
import sys

import colorama
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

from tgbot.data.config import BOT_DATABASE_EXPORT, BOT_SCHEDULER, BOT_TOKEN, get_admins, validate_bot_config
from tgbot.database.core import close_database
from tgbot.database.repository import prepare_database
from tgbot.middlewares import register_all_middlewares
from tgbot.routers import register_all_routers
from tgbot.services.api_session import AsyncRequestSession
from tgbot.utils.misc.bot_commands import set_commands
from tgbot.utils.misc.bot_logging import bot_logger
from tgbot.utils.misc.bot_models import ARS
from tgbot.utils.misc_functions import (
    autobackup_admin,
    autosettings_unix,
    check_bot_username,
    check_mail,
    check_update,
    startup_notify,
    update_profit_day,
    update_profit_month,
    update_profit_week,
)


# Включение мгновенного вывода консоли
def configure_console_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(line_buffering=True, write_through=True)


configure_console_output()
colorama.init()


# Подключение шедулеров
async def scheduler_start(bot: Bot, arSession: ARS):
    # Автоматический сброс ежемесячной статистики
    BOT_SCHEDULER.add_job(
        update_profit_month,
        trigger="cron",
        day=1,
        hour=0,
        minute=0,
        second=5,
        id="update_profit_month",
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=60,
    )

    # Автоматический сброс еженедельной статистики
    BOT_SCHEDULER.add_job(
        update_profit_week,
        trigger="cron",
        day_of_week="mon",
        hour=0,
        minute=0,
        second=10,
        id="update_profit_week",
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=60,
    )

    # Автоматический сброс ежедневной статистики
    BOT_SCHEDULER.add_job(
        update_profit_day,
        trigger="cron",
        hour=0,
        minute=0,
        second=15,
        args=(bot,),
        id="update_profit_day",
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=60,
    )

    # Автоматический бэкап БД (если включено)
    if BOT_DATABASE_EXPORT:
        BOT_SCHEDULER.add_job(
            autobackup_admin,
            trigger="cron",
            hour=0,
            args=(bot,),
            id="autobackup_admin",
            replace_existing=True,
            coalesce=True,
            misfire_grace_time=60,
        )

    # Ежедневная проверка обновлений
    BOT_SCHEDULER.add_job(
        check_update,
        trigger="cron",
        hour=0,
        args=(bot, arSession),
        id="check_update",
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=60,
    )

    # Ежедневная проверка важных пушей
    BOT_SCHEDULER.add_job(
        check_mail,
        trigger="cron",
        hour=12,
        args=(bot, arSession),
        id="check_mail",
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=60,
    )

    if not BOT_SCHEDULER.running:
        BOT_SCHEDULER.start()


# Запуск миграций, роутеров и polling
async def main():
    validate_bot_config()
    await prepare_database()

    dp = Dispatcher()
    arSession = AsyncRequestSession()

    proxy = ""
    session = AiohttpSession(proxy=proxy) if len(proxy) > 1 else AiohttpSession()

    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        ),
    )

    register_all_middlewares(dp)
    register_all_routers(dp)

    try:
        await autosettings_unix()
        await set_commands(bot)
        await check_bot_username(bot)
        await check_update(bot, arSession)
        await check_mail(bot, arSession)
        await startup_notify(bot, arSession)
        await scheduler_start(bot, arSession)

        bot_info = await bot.get_me()
        bot_logger.info("Бот запущен: @%s", bot_info.username)
        print(colorama.Fore.LIGHTYELLOW_EX + f"~~~~~ Бот запущен - @{bot_info.username} ~~~~~")
        print(colorama.Fore.LIGHTBLUE_EX + "~~~~~ TG developer - @djimbox ~~~~~")
        print(colorama.Fore.RESET)

        if len(get_admins()) == 0:
            print("***** УКАЖИТЕ BOT_ADMIN_IDS В .env *****")

        await bot.delete_webhook()
        await bot.get_updates(offset=-1)

        await dp.start_polling(
            bot,
            arSession=arSession,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        if BOT_SCHEDULER.running:
            BOT_SCHEDULER.shutdown(wait=False)

        await arSession.close()
        await bot.session.close()
        await close_database()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        bot_logger.warning("Бот остановлен")
    finally:
        if sys.platform.startswith("win"):
            os.system("cls")
        else:
            os.system("clear")
