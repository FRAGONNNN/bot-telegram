# - *- coding: utf- 8 - *-
import asyncio

from aiogram import Router, Bot, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from tgbot.database import Positionx, Userx, Categoryx, Itemx, Paymentsx, Purchasesx, Settingsx
from tgbot.keyboards.inline_user import refill_method_buy_finl
from tgbot.keyboards.inline_user_page import *
from tgbot.keyboards.inline_user_products import products_buy_confirm_finl, products_return_finl
from tgbot.keyboards.reply_main import menu_frep
from tgbot.utils.const_functions import ded, del_message, convert_date, send_admins
from tgbot.utils.misc.bot_models import FSM, ARS
from tgbot.utils.products_functions import get_positions_items
from tgbot.utils.text_functions import position_open_user

router = Router(name=__name__)


# Страницы выбора категории для покупки товара
@router.callback_query(F.data.startswith("buy_category_swipe:"))
async def user_buy_category_swipe(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    remover = int(call.data.split(":")[1])

    await call.message.edit_text(
        "<b>🎁 Выберите нужный вам товар</b>",
        reply_markup=await prod_item_category_swipe_fp(remover),
    )


# Открытие категории с выбором позиции для покупки товара
@router.callback_query(F.data.startswith("buy_category_open:"))
async def user_buy_category_open(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    category_id = int(call.data.split(":")[1])
    remover = int(call.data.split(":")[2])

    get_category = await Categoryx().get_required(category_id=category_id)
    get_positions = await get_positions_items(category_id)

    if len(get_positions) >= 1:
        await del_message(call.message)

        await call.message.answer(
            f"<b>🎁 Текущая категория: <code>{get_category.category_name}</code></b>",
            reply_markup=await prod_item_position_swipe_fp(remover, category_id),
        )
    else:
        await call.answer(
            f"❕ Товары в категории {get_category.category_name} отсутствуют",
            True,
            cache_time=5,
        )


# Страницы выбора позиции для покупки товара
@router.callback_query(F.data.startswith("buy_position_swipe:"))
async def user_buy_position_swipe(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    category_id = int(call.data.split(":")[1])
    remover = int(call.data.split(":")[2])

    get_category = await Categoryx().get_required(category_id=category_id)

    await del_message(call.message)
    await call.message.answer(
        f"<b>🎁 Текущая категория: <code>{get_category.category_name}</code></b>",
        reply_markup=await prod_item_position_swipe_fp(remover, category_id),
    )


# Открытие позиции для покупки товара
@router.callback_query(F.data.startswith("buy_position_open:"))
async def user_buy_position_open(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    position_id = int(call.data.split(":")[1])
    remover = int(call.data.split(":")[2])

    await state.clear()

    await del_message(call.message)
    await position_open_user(bot, call.from_user.id, position_id, remover)


#################################### ПОКУПКА ###################################
# Покупка товара
@router.callback_query(F.data.startswith("buy_item_open:"))
async def user_buy_open(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    position_id = int(call.data.split(":")[1])
    remover = int(call.data.split(":")[2])

    get_payments = await Paymentsx().get()
    get_position = await Positionx().get_required(position_id=position_id)
    get_items = await Itemx().gets(position_id=position_id)
    get_user = await Userx().get_required(user_id=call.from_user.id)

    # Проверка, имеется ли на балансе пользователя достаточно средств
    if get_user.user_balance < get_position.position_price:
        if get_payments.status_cryptobot == "True" or get_payments.status_yoomoney == "True":
            await call.message.answer(
                "<b>❗ На вашем счёте недостаточно средств</b>\n"
                "💰 Выберите способ пополнения баланса",
                reply_markup=await refill_method_buy_finl(),
            )

            return await call.answer(cache_time=5)
        else:
            return await call.answer("❗ У вас недостаточно средств. Пополните баланс", True)

    if len(get_items) < 1:
        return await call.answer("❗ Товаров нет в наличии", True)

    # Максимальное количество товаров к покупке, подстроенные под баланс пользователя
    if get_position.position_price != 0:
        max_buy_count = int(get_user.user_balance / get_position.position_price)

        if max_buy_count > len(get_items):
            available_count = len(get_items)
        else:
            available_count = max_buy_count
    else:
        available_count = len(get_items)

    # Если в наличии всего один товар, то пропустить ввод количества товаров к покупке
    if available_count == 1:
        await state.clear()

        await del_message(call.message)

        await call.message.answer(
            ded(f"""
                <b>🎁 Вы действительно хотите купить товар(ы)?</b>
                ➖➖➖➖➖➖➖➖➖➖
                ▪️ Товар: <code>{get_position.position_name}</code>
                ▪️ Количество: <code>1шт</code>
                ▪️ Сумма к покупке: <code>{get_position.position_price}₽</code>
            """),
            reply_markup=products_buy_confirm_finl(position_id, get_position.category_id, 1),
        )
    else:
        await state.update_data(here_buy_position_id=position_id)
        await state.set_state("here_item_count")

        await del_message(call.message)
        await call.message.answer(
            ded(f"""
                <b>🎁 Введите количество товаров для покупки</b>
                ❕ От <code>1</code> до <code>{available_count}</code>
                ➖➖➖➖➖➖➖➖➖➖
                ▪️ Товар: <code>{get_position.position_name}</code> - <code>{get_position.position_price}₽</code>
                ▪️ Ваш баланс: <code>{get_user.user_balance}₽</code>
            """),
            reply_markup=products_return_finl(position_id, get_position.category_id),
        )


# Принятие количества товаров для покупки
@router.message(F.text, StateFilter("here_item_count"))
async def user_buy_count(message: Message, bot: Bot, state: FSM, arSession: ARS):
    position_id = (await state.get_data())['here_buy_position_id']

    get_position = await Positionx().get_required(position_id=position_id)
    get_user = await Userx().get_required(user_id=message.from_user.id)
    get_items = await Itemx().gets(position_id=position_id)

    # Максимальное количество товаров к покупке, подстроенные под баланс пользователя
    if get_position.position_price != 0:
        get_count = int(get_user.user_balance / get_position.position_price)

        if get_count > len(get_items):
            get_count = len(get_items)
    else:
        get_count = len(get_items)

    send_message = ded(f"""
        🎁 Введите количество товаров для покупки
        ❕ От <code>1</code> до <code>{get_count}</code>
        ➖➖➖➖➖➖➖➖➖➖
        ▪️ Товар: <code>{get_position.position_name}</code> - <code>{get_position.position_price}₽</code>
        ▪️ Ваш баланс: <code>{get_user.user_balance}₽</code>
    """)

    # Если было введено не число
    if not message.text.isdigit():
        return await message.answer(
            f"<b>❌ Данные были введены неверно</b>\n" + send_message,
            reply_markup=products_return_finl(position_id, get_position.category_id),
        )

    get_count = int(message.text)
    amount_pay = round(get_position.position_price * get_count, 2)

    # Если товаров нет в наличии
    if len(get_items) < 1:
        await state.clear()
        return await message.answer("<b>🎁 Товар который вы хотели купить, закончился</b>")

    # Если введено кол-во товаров меньше 1 или меньше кол-ва имеющегося в наличии
    if get_count < 1 or get_count > len(get_items):
        return await message.answer(
            f"<b>❌ Неверное количество товаров</b>\n" + send_message,
            reply_markup=products_return_finl(position_id, get_position.category_id),
        )

    # Если баланс пользователя меньше, чем общая цена покупки
    if get_user.user_balance < amount_pay:
        return await message.answer(
            f"<b>❌ Недостаточно средств на счете</b>\n" + send_message,
            reply_markup=products_return_finl(position_id, get_position.category_id),
        )

    await state.clear()

    await message.answer(
        ded(f"""
            <b>🎁 Вы действительно хотите купить товар(ы)?</b>
            ➖➖➖➖➖➖➖➖➖➖
            ▪️ Товар: <code>{get_position.position_name}</code>
            ▪️ Количество: <code>{get_count}шт</code>
            ▪️ Сумма к покупке: <code>{amount_pay}₽</code>
        """),
        reply_markup=products_buy_confirm_finl(position_id, get_position.category_id, get_count),
    )


# Подтверждение покупки товара
@router.callback_query(F.data.startswith("buy_item_confirm:"))
async def user_buy_confirm(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    position_id = int(call.data.split(":")[1])
    purchase_count = int(call.data.split(":")[2])

    await call.message.edit_text("⏳")

    purchase_result = await Purchasesx().buy(
        user_id=call.from_user.id,
        position_id=position_id,
        requested_count=purchase_count,
    )

    if purchase_result == "USER_NOT_FOUND":
        return await call.message.edit_text("<b>❌ Пользователь не был найден</b>")
    elif purchase_result == "POSITION_NOT_FOUND":
        return await call.message.edit_text("<b>❌ Позиция не была найдена</b>")
    elif purchase_result == "NOT_ENOUGH_ITEMS":
        return await call.message.edit_text("<b>❌ В наличии недостаточно товаров. Попробуйте другое кол-во</b>")
    elif purchase_result == "NOT_ENOUGH_BALANCE":
        return await call.message.edit_text("<b>❌ На вашем балансе недостаточно средств</b>")

    get_user = await Userx().get_required(user_id=call.from_user.id)
    get_settings = await Settingsx().get()

    for items in purchase_result.items:
        await call.message.answer("\n\n".join(items), parse_mode="None")
        await asyncio.sleep(0.3)

    await del_message(call.message)
    await call.message.answer(
        ded(f"""
            <b>✅ Вы успешно купили товар(ы)</b>
            ➖➖➖➖➖➖➖➖➖➖
            ▪️ Чек: <code>#{purchase_result.receipt}</code>
            ▪️ Товар: <code>{purchase_result.position_name} | {purchase_result.purchase_count}шт | {purchase_result.purchase_price}₽</code>
            ▪️ Дата покупки: <code>{convert_date(purchase_result.purchase_unix)}</code>
        """),
        reply_markup=menu_frep(call.from_user.id),
    )

    if get_settings.notification_buy == "True":
        await send_admins(
            bot,
            ded(f"""
                <b>🎁 Покупка товара</b>

                ▪️ Пользователь: <b>@{get_user.user_login}</b> | <a href='tg://user?id={get_user.user_id}'>{get_user.user_name}</a> | <code>{get_user.user_id}</code>
                ▪️ Товар: <code>{purchase_result.position_name} | {purchase_result.purchase_count}шт | {purchase_result.purchase_price}₽</code>
                ▪️ Чек: <code>#{purchase_result.receipt}</code>
            """)
        )
