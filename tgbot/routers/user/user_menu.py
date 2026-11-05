# - *- coding: utf- 8 - *-
import asyncio

from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from tgbot.data.config import BOT_VERSION, get_text_desc, get_text_warning
from tgbot.database import Purchasesx, Settingsx
from tgbot.keyboards.inline_user import user_support_finl
from tgbot.keyboards.inline_user_page import *
from tgbot.services.api_hosting_text import HostingAPI
from tgbot.utils.const_functions import ded, del_message, convert_date
from tgbot.utils.misc.bot_models import FSM, ARS
from tgbot.utils.misc_functions import insert_tags
from tgbot.utils.products_functions import get_items_available
from tgbot.utils.text_functions import open_profile_user

router = Router(name=__name__)


# Открытие товаров
@router.message(F.text == "🎁 Купить")
async def user_shop(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    get_categories = await get_categories_items()

    if len(get_categories) >= 1:
        await message.answer(
            "<b>🎁 Выберите нужный вам товар</b>",
            reply_markup=await prod_item_category_swipe_fp(0),
        )
    else:
        await message.answer("<b>🎁 Увы, товары в данное время отсутствуют</b>")


# Открытие профиля
@router.message(F.text == "👤 Профиль")
async def user_profile(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    await open_profile_user(bot, message.from_user.id)


# Проверка товаров в наличии
@router.message(F.text == "🧮 Наличие товаров")
async def user_available(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    items_available, remover_max, remover_now = await get_items_available(0)

    if len(items_available) >= 1:
        await message.answer(
            items_available,
            reply_markup=prod_available_swipe_fp(remover_now, remover_max),
        )
    else:
        await message.answer("<b>🎁 Увы, товары в данное время отсутствуют</b>")


# Открытие FAQ
@router.message(F.text.in_(('❔ FAQ', '/faq')))
async def user_faq(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    get_settings = await Settingsx().get()

    if get_settings.misc_faq == "None":
        return await message.answer(
            ded(f"""
                ❔ Текст FAQ не указан. Измените его в настройках бота.

                ➖➖➖➖➖➖➖➖➖➖
                {get_text_desc()}

                ➖➖➖➖➖➖➖➖➖➖
                {get_text_warning()}
            """),
            disable_web_page_preview=True,
        )

    await message.answer(
        await insert_tags(message.from_user.id, get_settings.misc_faq),
        disable_web_page_preview=True,
    )


# Открытие сообщения с ссылкой на поддержку
@router.message(F.text.in_(('☎️ Поддержка', '/support')))
async def user_support(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    get_settings = await Settingsx().get()

    if get_settings.misc_support == "None":
        return await message.answer(
            ded(f"""
                ☎️ Контакты поддержки не указаны. Измените их в настройках бота.

                ➖➖➖➖➖➖➖➖➖➖
                {get_text_desc()}

                ➖➖➖➖➖➖➖➖➖➖
                {get_text_warning()}
            """),
            disable_web_page_preview=True,
        )

    await message.answer(
        "<b>☎️ Нажмите кнопку ниже для связи с Администратором</b>",
        reply_markup=user_support_finl(get_settings.misc_support),
    )


# Получение версии бота
@router.message(Command(commands=['version']))
async def admin_version(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    await message.answer(f"<b>❇️ Текущая версия бота: <code>{BOT_VERSION}</code></b>")


# Получение информации о боте
@router.message(Command(commands=['dj_desc']))
async def admin_desc(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    await message.answer(get_text_desc(), disable_web_page_preview=True)


################################################################################
# Переход к профилю
@router.callback_query(F.data == "user_profile")
async def user_profile_return(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    await del_message(call.message)
    await open_profile_user(bot, call.from_user.id)


# Просмотр истории покупок
@router.callback_query(F.data == "user_purchases")
async def user_purchases(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    get_purchases = await Purchasesx().gets(user_id=call.from_user.id)
    get_purchases = get_purchases[-5:]

    if len(get_purchases) >= 1:
        await call.answer("🎁 Последние 5 покупок")
        await del_message(call.message)

        for purchase in get_purchases:
            link_items = await (
                await HostingAPI.connect(
                    bot=bot,
                    arSession=arSession,
                )
            ).upload_text(purchase.purchase_data)

            await call.message.answer(
                ded(f"""
                    <b>🧾 Чек: <code>#{purchase.purchase_receipt}</code></b>
                    ▪️ Товар: <code>{purchase.purchase_position_name} | {purchase.purchase_count}шт | {purchase.purchase_price}₽</code>
                    ▪️ Дата покупки: <code>{convert_date(purchase.purchase_unix)}</code>
                    ▪️ Товары: <a href='{link_items}'>кликабельно</a>
                """),
                disable_web_page_preview=True,
            )

            await asyncio.sleep(0.2)

        await open_profile_user(bot, call.from_user.id)
    else:
        await call.answer("❗ У вас отсутствуют покупки", True)


# Страницы наличия товаров
@router.callback_query(F.data.startswith("user_available_swipe:"))
async def user_available_swipe(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    remover = int(call.data.split(":")[1])

    items_available, remover_max, remover_now = await get_items_available(remover)

    await call.message.edit_text(
        items_available,
        reply_markup=prod_available_swipe_fp(remover_now, remover_max),
    )
