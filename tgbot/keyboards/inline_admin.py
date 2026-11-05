# - *- coding: utf- 8 - *-
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.database import Settingsx, Paymentsx
from tgbot.utils.const_functions import ikb


################################################################################
#################################### ПРОЧЕЕ ####################################
# Удаление сообщения
def close_finl() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        ikb("❌ Закрыть", data="close_this"),
    )

    return keyboard.as_markup()


# Рассылка
def mail_confirm_finl() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        ikb("✅ Отправить", data="mail_confirm:Yes"),
        ikb("❌ Отменить", data="mail_confirm:Not"),
    )

    return keyboard.as_markup()


# Поиск профиля пользователя
def profile_edit_finl(user_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        ikb("💰 Изменить баланс", data=f"admin_user_balance_set:{user_id}"),
        ikb("💰 Выдать баланс", data=f"admin_user_balance_add:{user_id}"),
    ).row(
        ikb("🎁 Покупки", data=f"admin_user_purchases:{user_id}"),
        ikb("💌 Отправить СМС", data=f"admin_user_message:{user_id}"),
    ).row(
        ikb("🔄 Обновить", data=f"admin_user_refresh:{user_id}"),
    )

    return keyboard.as_markup()


# Переход к профилю пользователя
def profile_edit_return_finl(user_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        ikb("❌ Отменить", data=f"admin_user_refresh:{user_id}"),
    )

    return keyboard.as_markup()


################################################################################
############################## ПЛАТЕЖНЫЕ СИСТЕМЫ ###############################
# Управление - CryptoBot
async def payment_cryptobot_finl() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    get_payments = await Paymentsx().get()

    if get_payments.cryptobot_token == "None":
        assets_symbol = "➖"
    else:
        assets_symbol = "➕"

    if get_payments.status_cryptobot == "True":
        status_kb = ikb(f"{assets_symbol} | Статус: Включено ✅", data="payment_cryptobot_status:False")
    else:
        status_kb = ikb(f"{assets_symbol} | Статус: Выключено ❌", data="payment_cryptobot_status:True")

    keyboard.row(
        ikb("Информация ♻️", data="payment_cryptobot_check"),
    ).row(
        ikb("Баланс 💰", data="payment_cryptobot_balance"),
    ).row(
        ikb("Изменить 🖍", data="payment_cryptobot_edit"),
    ).row(
        ikb("⁠", data="..."),
    ).row(
        status_kb,
    )

    return keyboard.as_markup()


# Управление - ЮMoney
async def payment_yoomoney_finl() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    get_payments = await Paymentsx().get()

    if get_payments.yoomoney_token == "None":
        assets_symbol = "➖"
    else:
        assets_symbol = "➕"

    if get_payments.status_yoomoney == "True":
        status_kb = ikb(f"{assets_symbol} | Статус: Включено ✅", data="payment_yoomoney_status:False")
    else:
        status_kb = ikb(f"{assets_symbol} | Статус: Выключено ❌", data="payment_yoomoney_status:True")

    keyboard.row(
        ikb("Информация ♻️", data="payment_yoomoney_check"),
    ).row(
        ikb("Баланс 💰", data="payment_yoomoney_balance"),
    ).row(
        ikb("Изменить 🖍", data="payment_yoomoney_edit"),
    ).row(
        ikb("⁠", data="..."),
    ).row(
        status_kb,
    )

    return keyboard.as_markup()


# Управление - Звёзды
async def payment_stars_finl() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    get_payments = await Paymentsx().get()

    assets_symbol = "➕"

    if get_payments.status_stars == "True":
        status_kb = ikb(f"{assets_symbol} | Статус: Включено ✅", data="payment_stars_status:False")
    else:
        status_kb = ikb(f"{assets_symbol} | Статус: Выключено ❌", data="payment_stars_status:True")

    keyboard.row(
        ikb("Информация ♻️", data="payment_stars_check"),
    ).row(
        ikb("Баланс 💰", data="payment_stars_balance"),
    ).row(
        ikb("Изменить курс 🖍", data="payment_stars_edit"),
    ).row(
        ikb("⁠", data="..."),
    ).row(
        status_kb,
    )

    return keyboard.as_markup()


################################################################################
################################## НАСТРОЙКИ ###################################
# Основные настройки
async def settings_finl() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    get_settings = await Settingsx().get()

    # Текст для FAQ
    if get_settings.misc_faq == "None":
        faq_kb = ikb("Не установлено ❌", data="settings_edit_faq")
    else:
        faq_kb = ikb(f"{get_settings.misc_faq[:15]}... ✅", data="settings_edit_faq")

    # Контакты поддержки
    if get_settings.misc_support == "None":
        support_kb = ikb("Не установлена ❌", data="settings_edit_support")
    else:
        support_kb = ikb(f"@{get_settings.misc_support} ✅", data="settings_edit_support")

    # Вебхук дискорда
    if get_settings.misc_discord_webhook_url == "None":
        discord_webhook_kb = ikb("Отсутствует ❌", data="settings_edit_discord_webhook")
    else:
        discord_webhook_kb = ikb(f"{get_settings.misc_discord_webhook_name} ✅", data="settings_edit_discord_webhook")

    # Текстовый хостинг по умолчанию
    hosting_text_default_kb = ikb(get_settings.misc_hosting_text.title(), data="settings_edit_hosting_text")

    # Скрытие категорий без товаров
    if get_settings.misc_hide_category == "True":
        hide_category_kb = ikb("Скрыты", data="settings_edit_hide_category:False")
    else:
        hide_category_kb = ikb("Отображены", data="settings_edit_hide_category:True")

    # Скрытие позиций без товаров
    if get_settings.misc_hide_position == "True":
        hide_position_kb = ikb("Скрыты", data="settings_edit_hide_position:False")
    else:
        hide_position_kb = ikb("Отображены", data="settings_edit_hide_position:True")

    # Метод добавления товаров
    if get_settings.misc_method_prod == "skip":
        method_prod_kb = ikb("Через строку", data="settings_edit_method_prod:every")
    else:
        method_prod_kb = ikb("На каждой строке", data="settings_edit_method_prod:skip")

    keyboard.row(
        ikb("❔ FAQ", data="..."), faq_kb,
    ).row(
        ikb("☎️ Поддержка", data="..."), support_kb,
    ).row(
        ikb("🧿 Дискорд Webhook", url="https://teletype.in/@djimbox/djimboshop-discord"), discord_webhook_kb,
    ).row(
        ikb("🗯 Текстовый хостинг", data="..."), hosting_text_default_kb,
    ).row(
        ikb("🎁 Категории без товаров", data="..."), hide_category_kb,
    ).row(
        ikb("🎁 Позиции без товаров", data="..."), hide_position_kb,
    ).row(
        ikb("🎁 Метод добавления", data="..."), method_prod_kb,
    )

    return keyboard.as_markup()


# Выключатели
async def settings_status_finl() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    get_settings = await Settingsx().get()

    status_work_kb = ikb("Включены ✅", data="settings_status_work:False")
    status_buy_kb = ikb("Включены ✅", data="settings_status_buy:False")
    status_refill_kb = ikb("Включены ✅", data="settings_status_refill:False")
    notification_buy_kb = ikb("Включены 🔔", data="settings_notification_buy:False")
    notification_refill_kb = ikb("Включены 🔔", data="settings_notification_refill:False")

    if get_settings.status_buy == "False":
        status_buy_kb = ikb("Выключены ❌", data="settings_status_buy:True")
    if get_settings.status_work == "False":
        status_work_kb = ikb("Выключены ❌", data="settings_status_work:True")
    if get_settings.status_refill == "False":
        status_refill_kb = ikb("Выключены ❌", data="settings_status_refill:True")
    if get_settings.notification_buy == "False":
        notification_buy_kb = ikb("Выключены 🔕", data="settings_notification_buy:True")
    if get_settings.notification_refill == "False":
        notification_refill_kb = ikb("Выключены 🔕", data="settings_notification_refill:True")

    keyboard.row(
        ikb("⛔ Тех. работы", data="..."), status_work_kb,
    ).row(
        ikb("💰 Пополнения", data="..."), status_refill_kb,
    ).row(
        ikb("🎁 Покупки", data="..."), status_buy_kb,
    ).row(
        ikb("📢 Увед. о покупках", data="..."), notification_buy_kb,
    ).row(
        ikb("📢 Увед. о пополнениях", data="..."), notification_refill_kb,
    )

    return keyboard.as_markup()
