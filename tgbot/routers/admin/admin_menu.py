# - *- coding: utf- 8 - *-
import os

import aiofiles
from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder

from tgbot.data.config import PATH_LOGS, PATH_DATABASE
from tgbot.keyboards.reply_main import payments_frep, settings_frep, functions_frep, items_frep
from tgbot.utils.const_functions import get_date
from tgbot.utils.misc.bot_models import FSM, ARS
from tgbot.utils.misc_functions import get_statistics

router = Router(name=__name__)


# Платежные системы
@router.message(F.text == "🔑 Платежные системы")
async def admin_payments(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    await message.answer(
        "<b>🔑 Настройка платежных системы</b>",
        reply_markup=payments_frep(),
    )


# Настройки бота
@router.message(F.text == "⚙️ Настройки")
async def admin_settings(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    await message.answer(
        "<b>⚙️ Основные настройки бота</b>",
        reply_markup=settings_frep(),
    )


# Общие функции
@router.message(F.text == "🔆 Общие функции")
async def admin_functions(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    await message.answer(
        "<b>🔆 Общие функции бота</b>",
        reply_markup=functions_frep(),
    )


# Управление товарами
@router.message(F.text == "🎁 Управление товарами")
async def admin_products(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    await message.answer(
        "<b>🎁 Редактирование товаров</b>",
        reply_markup=items_frep(),
    )


# Статистика бота
@router.message(F.text == "📊 Статистика")
async def admin_statistics(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    await message.answer(await get_statistics())


# Получение базы данных
@router.message(Command(commands=['db', 'database']))
async def admin_database(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    await message.answer_document(
        FSInputFile(PATH_DATABASE),
        caption=f"<b>📦 #BACKUP | <code>{get_date()}</code></b>",
    )


# Получение логов
@router.message(Command(commands=['log', 'logs']))
async def admin_log(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    media_group = MediaGroupBuilder(
        caption=f"<b>🖨 #LOGS | <code>{get_date()}</code></b>",
    )

    if os.path.isfile(PATH_LOGS):
        media_group.add_document(media=FSInputFile(PATH_LOGS))

    if os.path.isfile("tgbot/data/sv_log_err.log"):
        media_group.add_document(media=FSInputFile("tgbot/data/sv_log_err.log"))

    if os.path.isfile("tgbot/data/sv_log_out.log"):
        media_group.add_document(media=FSInputFile("tgbot/data/sv_log_out.log"))

    await message.answer_media_group(media=media_group.build())


# Очистка логов
@router.message(Command(commands=['clear_log', 'clear_logs', 'log_clear', 'logs_clear']))
async def admin_log_clear(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    if os.path.isfile(PATH_LOGS):
        async with aiofiles.open(PATH_LOGS, "w") as file:
            await file.write(f"{get_date()} | LOGS WAS CLEAR")

    if os.path.isfile("tgbot/data/sv_log_err.log"):
        async with aiofiles.open("tgbot/data/sv_log_err.log", "w") as file:
            await file.write(f"{get_date()} | LOGS ERR WAS CLEAR")

    if os.path.isfile("tgbot/data/sv_log_out.log"):
        async with aiofiles.open("tgbot/data/sv_log_out.log", "w") as file:
            await file.write(f"{get_date()} | LOGS OUT WAS CLEAR")

    await message.answer("<b>🖨 Логи были успешно очищены</b>")
