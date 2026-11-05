# - *- coding: utf- 8 - *-
from typing import Union

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.database import Paymentsx
from tgbot.utils.const_functions import ikb


################################################################################
#################################### ПРОЧЕЕ ####################################
# Открытие своего профиля
def user_profile_finl() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        ikb("💰 Пополнить", data="user_refill"),
        ikb("🎁 Мои покупки", data="user_purchases"),
    )

    return keyboard.as_markup()


# Ссылка на поддержку
def user_support_finl(support_login: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        ikb("💌 Написать в поддержку", url=f"https://t.me/{support_login}"),
    )

    return keyboard.as_markup()


################################################################################
################################### ПЛАТЕЖИ ####################################
# Выбор способа пополнения
async def refill_method_finl() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    get_payments = await Paymentsx().get()

    if get_payments.status_cryptobot == "True":
        keyboard.row(ikb("🔷 CryptoBot", data="user_refill_method:Cryptobot"))
    if get_payments.status_yoomoney == "True":
        keyboard.row(ikb("🔮 ЮMoney", data="user_refill_method:Yoomoney"))
    if get_payments.status_stars == "True":
        keyboard.row(ikb("⭐️ Звёзды", data="user_refill_method:Stars"))

    keyboard.row(ikb("🔙 Вернуться", data="user_profile"))

    return keyboard.as_markup()


# Проверка платежа
def refill_bill_finl(pay_link: str, pay_receipt: Union[str, int], pay_method: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        ikb("🌀 Перейти к оплате", url=pay_link),
    ).row(
        ikb("🔄 Проверить оплату", data=f"Pay:{pay_method}:{pay_receipt}"),
    )

    return keyboard.as_markup()


# Выбор способа пополнения при нехватке баланса во время покупки товара
async def refill_method_buy_finl() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    get_payments = await Paymentsx().get()

    if get_payments.status_cryptobot == "True":
        keyboard.row(ikb("🔷 CryptoBot", data="user_refill_method:Cryptobot"))
    if get_payments.status_yoomoney == "True":
        keyboard.row(ikb("🔮 ЮMoney", data="user_refill_method:Yoomoney"))
    if get_payments.status_stars == "True":
        keyboard.row(ikb("⭐️ Звёзды", data="user_refill_method:Stars"))

    keyboard.row(ikb("❌ Закрыть", data="close_this"))

    return keyboard.as_markup()
