# - *- coding: utf- 8 - *-
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from tgbot.data.config import get_admins
from tgbot.utils.const_functions import rkb


# Главное меню
def menu_frep(user_id: int) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(
        rkb("🎁 Купить"), rkb("👤 Профиль"), rkb("🧮 Наличие товаров"),
    ).row(
        rkb("☎️ Поддержка"), rkb("❔ FAQ"),
    )

    if user_id in get_admins():
        keyboard.row(
            rkb("🎁 Управление товарами"), rkb("📊 Статистика"),
        ).row(
            rkb("⚙️ Настройки"), rkb("🔆 Общие функции"), rkb("🔑 Платежные системы"),
        )

    return keyboard.as_markup(resize_keyboard=True)


# Платежные системы
def payments_frep() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(
        rkb("🔷 CryptoBot"), rkb("🔮 ЮMoney"), rkb("⭐️ Звёзды"),
    ).row(
        rkb("🔙 Главное меню"),
    )

    return keyboard.as_markup(resize_keyboard=True)


# Общие функции
def functions_frep() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(
        rkb("🔍 Поиск"), rkb("📢 Рассылка"),
    ).row(
        rkb("🔙 Главное меню"),
    )

    return keyboard.as_markup(resize_keyboard=True)


# Настройки бота
def settings_frep() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(
        rkb("🖍 Изменить данные"), rkb("🕹 Выключатели"),
    ).row(
        rkb("🔙 Главное меню"),
    )

    return keyboard.as_markup(resize_keyboard=True)


# Управление товарами
def items_frep() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(
        rkb("📁 Создать позицию ➕"), rkb("🗃 Создать категорию ➕"),
    ).row(
        rkb("📁 Изменить позицию 🖍"), rkb("🗃 Изменить категорию 🖍"),
    ).row(
        rkb("🔙 Главное меню"), rkb("🎁 Добавить товары ➕"), rkb("❌ Удаление"),
    )

    return keyboard.as_markup(resize_keyboard=True)
