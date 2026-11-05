# - *- coding: utf- 8 - *-
from typing import Optional, Tuple

from aiogram import Router, Bot, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery

from tgbot.database import Paymentsx, Refillx, Userx, Settingsx
from tgbot.keyboards.inline_user import refill_bill_finl, refill_method_finl
from tgbot.services.api_cryptobot import CryptobotAPI
from tgbot.services.api_stars import StarsAPI
from tgbot.services.api_yoomoney import YoomoneyAPI
from tgbot.utils.const_functions import is_number, to_number, gen_id, ded
from tgbot.utils.misc.bot_logging import bot_logger
from tgbot.utils.misc.bot_models import FSM, ARS
from tgbot.utils.misc_functions import send_admins

min_refill_rub = 5  # Минимальная сумма пополнения в рублях

router = Router(name=__name__)


# Выбор способа пополнения
@router.callback_query(F.data == "user_refill")
async def refill_method_list(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    get_payments = await Paymentsx().get()

    if (
            get_payments.status_cryptobot == "False" and
            get_payments.status_yoomoney == "False" and
            get_payments.status_stars == "False"
    ):
        return await call.answer("❗️ Пополнения временно недоступны", True)

    await call.message.edit_text(
        "<b>💰 Выберите способ пополнения баланса</b>",
        reply_markup=await refill_method_finl(),
    )


# Выбор способа пополнения
@router.callback_query(F.data.startswith("user_refill_method:"))
async def refill_method_select(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    refill_method = call.data.split(":")[1]

    get_payments = await Paymentsx().get()

    if refill_method == "Cryptobot" and get_payments.status_cryptobot == "False":
        return await call.answer("❌ Пополнение данным способом временно недоступно", True)
    elif refill_method == "Yoomoney" and get_payments.status_yoomoney == "False":
        return await call.answer("❌ Пополнение данным способом временно недоступно", True)
    elif refill_method == "Stars" and get_payments.status_stars == "False":
        return await call.answer("❌ Пополнение данным способом временно недоступно", True)

    await state.update_data(here_refill_method=refill_method)

    await state.set_state("here_refill_amount")
    await call.message.edit_text("<b>💰 Введите сумму пополнения</b>")


################################################################################
################################### ВВОД СУММЫ #################################
# Принятие суммы для пополнения средств
@router.message(F.text, StateFilter("here_refill_amount"))
async def refill_amount_get(message: Message, bot: Bot, state: FSM, arSession: ARS):
    if not is_number(message.text):
        return await message.answer(
            ded(f"""
                <b>❌ Данные были введены неверно</b>
                💰 Введите сумму для пополнения средств
            """),
        )

    if to_number(message.text) < min_refill_rub or to_number(message.text) > 150_000:
        return await message.answer(
            ded(f"""
                <b>❌ Неверная сумма пополнения</b>
                ❗️ Cумма не должна быть меньше <code>{min_refill_rub}₽</code> и больше <code>150 000₽</code>
                💰 Введите сумму для пополнения средств
            """),
        )

    cache_message = await message.answer("<b>♻️ Подождите, платёж генерируется..</b>")

    refill_amount = to_number(message.text)
    refill_method = (await state.get_data())['here_refill_method']
    await state.clear()

    # Генерация платежа
    if refill_method == "Cryptobot":
        bill_message, bill_link, bill_receipt = await (
            await CryptobotAPI.connect(
                bot=bot,
                arSession=arSession,
                update=cache_message,
            )
        ).bill(refill_amount)
    elif refill_method == "Yoomoney":
        bill_message, bill_link, bill_receipt = await (
            await YoomoneyAPI.connect(
                bot=bot,
                arSession=arSession,
                update=cache_message,
            )
        ).bill(refill_amount)
    elif refill_method == "Stars":
        bill_message, bill_link, bill_receipt = await (
            await StarsAPI.connect(
                bot=bot,
                arSession=arSession,
                update=cache_message,
            )
        ).bill(refill_amount)
    else:
        return await cache_message.edit_text(
            f"<b>❌ Данный способ пополнения не найден. Попробуйте позже: {refill_method}</b>"
        )

    # Обработка статуса генерации платежа
    if bill_message:
        await cache_message.edit_text(
            bill_message,
            reply_markup=refill_bill_finl(bill_link, bill_receipt, refill_method),
        )
    else:
        await cache_message.edit_text(
            f"<b>❌ Не удалось сгенерировать платёж. Попробуйте позже</b>"
        )


################################################################################
############################### ПРОВЕРКА ПЛАТЕЖЕЙ ##############################
# Проверка оплаты - ЮMoney
@router.callback_query(F.data.startswith('Pay:Yoomoney'))
async def refill_check_yoomoney(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    pay_method = call.data.split(":")[1]
    pay_receipt = call.data.split(":")[2]

    pay_status, pay_amount = await (
        await YoomoneyAPI.connect(
            bot=bot,
            arSession=arSession,
            update=call,
        )
    ).bill_check(pay_receipt)

    if pay_status == 0:
        refill_status = await refill_success(
            bot=bot,
            call=call,
            pay_method=pay_method,
            pay_amount=pay_amount,
            pay_receipt=int(pay_receipt),
            pay_comment=pay_receipt,
        )

        if refill_status == "ALREADY":
            await call.answer("❗ Ваше пополнение уже зачислено.", True, cache_time=60)
            await delete_refill_message(bot, call.message.chat.id, call.message.message_id)
        elif refill_status == "USER_NOT_FOUND":
            await call.answer("❗ Пользователь не найден. Напишите в поддержку.", True, cache_time=30)
    elif pay_status == 1:
        await call.answer("❗️ Не удалось проверить платёж. Попробуйте позже", True, cache_time=30)
    elif pay_status == 2:
        await call.answer("❗️ Оплата не была найдена. Попробуйте позже", True, cache_time=5)
    elif pay_status == 3:
        await call.answer("❗️ Оплата была произведена не в рублях", True, cache_time=5)
    else:
        await call.answer(f"❗ Неизвестная ошибка {pay_status}. Обратитесь в поддержку.", True, cache_time=5)


# Проверка оплаты - Cryptobot
@router.callback_query(F.data.startswith('Pay:Cryptobot'))
async def refill_check_cryptobot(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    pay_method = call.data.split(":")[1]
    pay_comment = call.data.split(":")[2]

    pay_status, pay_amount = await (
        await CryptobotAPI.connect(
            bot=bot,
            arSession=arSession,
            update=call,
        )
    ).bill_check(pay_comment)

    if pay_status == 0:
        refill_status = await refill_success(
            bot=bot,
            call=call,
            pay_method=pay_method,
            pay_amount=pay_amount,
            pay_comment=pay_comment,
        )

        if refill_status == "ALREADY":
            await call.answer("❗ Ваше пополнение уже зачислено.", True, cache_time=60)
            await delete_refill_message(bot, call.message.chat.id, call.message.message_id)
        elif refill_status == "USER_NOT_FOUND":
            await call.answer("❗ Пользователь не найден. Напишите в поддержку.", True, cache_time=30)
    elif pay_status == 1:
        await call.answer("❗️ Не удалось проверить платёж. Попробуйте позже", True, cache_time=30)
    elif pay_status == 2:
        await call.answer("❗️ Оплата не была найдена. Попробуйте позже", True, cache_time=5)
    elif pay_status == 3:
        await call.answer("❗️ Вы не успели оплатить счёт", True, cache_time=5)
        await call.message.edit_reply_markup()
    else:
        await call.answer(f"❗ Неизвестная ошибка {pay_status}. Обратитесь в поддержку.", True, cache_time=5)


# Проверка оплаты - Звёзды
@router.callback_query(F.data.startswith('Pay:Stars'))
async def refill_check_stars(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    pay_method = call.data.split(":")[1]
    pay_receipt = int(call.data.split(":")[2])

    pay_status, pay_amount = await (
        await StarsAPI.connect(
            bot=bot,
            arSession=arSession,
            update=call,
        )
    ).bill_check(pay_receipt)

    if pay_status == 0:
        refill_status = await refill_success(
            bot=bot,
            call=call,
            pay_method=pay_method,
            pay_amount=pay_amount,
            pay_receipt=pay_receipt,
        )

        if refill_status == "ALREADY":
            await call.answer("❗ Ваше пополнение уже зачислено.", True, cache_time=60)
            await delete_refill_message(bot, call.message.chat.id, call.message.message_id)
        elif refill_status == "USER_NOT_FOUND":
            await call.answer("❗ Пользователь не найден. Напишите в поддержку.", True, cache_time=30)
    elif pay_status == 1:
        await call.answer("❗️ Не удалось проверить платёж. Попробуйте позже", True, cache_time=30)
    elif pay_status == 2:
        await call.answer("❗️ Оплата не была найдена. Попробуйте позже", True, cache_time=5)
    else:
        await call.answer(f"❗ Неизвестная ошибка {pay_status}. Обратитесь в поддержку.", True, cache_time=5)


################################################################################
#################################### ЗВЁЗДЫ ####################################
# Подтверждение платежа Telegram Stars
@router.pre_checkout_query()
async def refill_stars_pre_checkout(query: PreCheckoutQuery, bot: Bot, state: FSM, arSession: ARS):
    await (
        await StarsAPI.connect(
            bot=bot,
            arSession=arSession,
            update=query,
        )
    ).answer_pre_checkout(query)


# Автоматическое зачисление Telegram Stars
@router.message(F.successful_payment)
async def refill_stars_success(message: Message, bot: Bot, state: FSM, arSession: ARS):
    payment = message.successful_payment

    if payment is None:
        return

    stars_api = await StarsAPI.connect(
        bot=bot,
        arSession=arSession,
        update=message,
    )

    try:
        pay_receipt, pay_amount, pay_comment, bill_chat_id, bill_message_id = (
            stars_api.parse_successful_payment(payment)
        )
    except ValueError:
        bot_logger.warning("Некорректная successful_payment для Telegram Stars", exc_info=True)
        return

    refill_status, receipt = await save_refill_success(
        bot=bot,
        user_id=message.from_user.id,
        pay_method="Stars",
        pay_amount=pay_amount,
        pay_receipt=pay_receipt,
        pay_comment=pay_comment,
    )

    if refill_status == "ok":
        if bill_chat_id == message.chat.id:
            await delete_refill_message(bot, bill_chat_id, bill_message_id)

        await message.answer(
            ded(f"""
                <b>💰 Вы пополнили баланс на сумму <code>{pay_amount}₽</code>. Удачи ❤️
                🧾 Чек: <code>#{receipt}</code></b>
            """)
        )
    elif refill_status == "ALREADY":
        if bill_chat_id == message.chat.id:
            await delete_refill_message(bot, bill_chat_id, bill_message_id)

        await message.answer("<b>❗ Ваше пополнение уже было зачислено.</b>")
    elif refill_status == "USER_NOT_FOUND":
        await message.answer("<b>❗ Пользователь не найден. Напишите в поддержку.</b>")


################################################################################
#################################### ПРОЧЕЕ ####################################
# Зачисление средств
async def refill_success(
        bot: Bot,
        call: CallbackQuery,
        pay_method: str,
        pay_amount: float,
        pay_receipt: Optional[int] = None,
        pay_comment: Optional[str] = None,
):
    user_id = call.from_user.id

    if pay_receipt is None:
        pay_receipt = gen_id(12)
    if pay_comment is None:
        pay_comment = ""

    response_success, receipt = await save_refill_success(
        bot=bot,
        user_id=user_id,
        pay_method=pay_method,
        pay_amount=pay_amount,
        pay_receipt=pay_receipt,
        pay_comment=pay_comment,
    )

    if response_success != "ok":
        return response_success

    await call.message.answer(
        ded(f"""
            <b>💰 Вы пополнили баланс на сумму <code>{pay_amount}₽</code>. Удачи ❤️
            🧾 Чек: <code>#{receipt}</code></b>
        """)
    )
    await delete_refill_message(bot, call.message.chat.id, call.message.message_id)

    return response_success


# Удаление сообщения со счётом
async def delete_refill_message(bot: Bot, chat_id: Optional[int], message_id: Optional[int]) -> None:
    if chat_id is None or message_id is None:
        return

    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        bot_logger.warning("Не удалось удалить сообщение со счётом", exc_info=True)


# Сохранение пополнения и уведомление админов
async def save_refill_success(
        bot: Bot,
        user_id: int,
        pay_method: str,
        pay_amount: float,
        pay_receipt: int,
        pay_comment: str,
) -> Tuple[str, int]:
    if pay_method == "Yoomoney":
        text_method = "ЮMoney"
    elif pay_method == "Cryptobot":
        text_method = "CryptoBot"
    elif pay_method == "Stars":
        text_method = "Telegram Stars"
    else:
        text_method = f"Unknown - {pay_method}"

    response_success = await Refillx().success(
        user_id=user_id,
        pay_receipt=pay_receipt,
        pay_comment=pay_comment,
        pay_amount=pay_amount,
        pay_method=pay_method,
    )

    if response_success != "ok":
        return response_success, pay_receipt

    get_user = await Userx().get_required(user_id=user_id)
    get_settings = await Settingsx().get()

    if get_settings.notification_refill == "True":
        await send_admins(
            bot,
            ded(f"""
                <b>💰 Пополнение баланса</b>

                ▪️ Пользователь: <b>@{get_user.user_login}</b> | <a href='tg://user?id={user_id}'>{get_user.user_name}</a> | <code>{user_id}</code>
                ▪️ Сумма пополнения: <code>{pay_amount}₽</code> <code>({text_method})</code>
                ▪️ Чек: <code>#{pay_receipt}</code>
            """)
        )

    return response_success, pay_receipt
