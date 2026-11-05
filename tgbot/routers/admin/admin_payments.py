# - *- coding: utf- 8 - *-
from aiogram import Router, Bot, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from tgbot.database import Paymentsx
from tgbot.keyboards.inline_admin import payment_yoomoney_finl, close_finl, payment_cryptobot_finl, payment_stars_finl
from tgbot.services.api_cryptobot import CryptobotAPI
from tgbot.services.api_stars import StarsAPI
from tgbot.services.api_yoomoney import YoomoneyAPI
from tgbot.utils.const_functions import ded, is_number, to_number
from tgbot.utils.misc.bot_logging import bot_logger
from tgbot.utils.misc.bot_models import FSM, ARS

router = Router(name=__name__)


# Управление - CryptoBot
@router.message(F.text == "🔷 CryptoBot")
async def payments_cryptobot_open(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    await message.answer(
        "<b>🔷 Управление - CryptoBot</b>",
        reply_markup=await payment_cryptobot_finl(),
    )


# Управление - ЮMoney
@router.message(F.text == "🔮 ЮMoney")
async def payments_yoomoney_open(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    await message.answer(
        "<b>🔮 Управление - ЮMoney</b>",
        reply_markup=await payment_yoomoney_finl(),
    )


# Управление - Звёзды
@router.message(F.text == "⭐️ Звёзды")
async def payments_stars_open(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    await message.answer(
        "<b>⭐️ Управление - Звёзды</b>",
        reply_markup=await payment_stars_finl(),
    )


################################################################################
################################### CRYPTOBOT ##################################
# Баланс - CryptoBot
@router.callback_query(F.data == "payment_cryptobot_balance")
async def payments_cryptobot_balance(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    response = await (
        await CryptobotAPI.connect(
            bot=bot,
            arSession=arSession,
            update=call,
            skipping_error=True,
        )
    ).balance()

    await call.message.answer(
        response,
        reply_markup=close_finl(),
    )


# Информация - CryptoBot
@router.callback_query(F.data == "payment_cryptobot_check")
async def payments_cryptobot_check(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    status, response = await (
        await CryptobotAPI.connect(
            bot=bot,
            arSession=arSession,
            update=call,
            skipping_error=True,
        )
    ).check()

    await call.message.answer(
        response,
        reply_markup=close_finl(),
    )


# Изменение - CryptoBot
@router.callback_query(F.data == "payment_cryptobot_edit")
async def payments_cryptobot_edit(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    await state.set_state("here_cryptobot_token")
    await call.message.edit_text(
        ded(f"""
            <b>🔷 Изменение @CryptoBot кошелька - <a href='https://teletype.in/@djimbox/djimboshop-cryptobot'>Инструкция</a></b>
            ➖➖➖➖➖➖➖➖➖➖
            ▪️ Создайте Приложение в "Crypto Pay" и отправьте токен
        """),
        disable_web_page_preview=True,
    )


# Выключатель - CryptoBot
@router.callback_query(F.data.startswith("payment_cryptobot_status:"))
async def payments_cryptobot_status(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    get_status = call.data.split(":")[1]

    get_payments = await Paymentsx().get()

    if get_status == "True" and get_payments.cryptobot_token == "None":
        return await call.answer("❌ Токен данной платежной системы не был добавлен", True)

    await Paymentsx().update(status_cryptobot=get_status)

    await call.message.edit_text(
        "<b>🔷 Управление - CryptoBot</b>",
        reply_markup=await payment_cryptobot_finl(),
    )


############################## ПРИНЯТИЕ CRYPTOBOT ##############################
# Принятие токена Cryptobot
@router.message(StateFilter("here_cryptobot_token"))
async def payments_cryptobot_get(message: Message, bot: Bot, state: FSM, arSession: ARS):
    get_token = message.text

    await state.clear()

    cache_message = await message.answer("<b>🔷 Проверка введённых CryptoBot данных... 🔄</b>")

    status, response = await (
        await CryptobotAPI.connect(
            bot=bot,
            arSession=arSession,
            update=message,
            skipping_error=True,
            token=get_token,
        )
    ).check()

    if status:
        await Paymentsx().update(cryptobot_token=get_token)
        await cache_message.edit_text("<b>🔷 CryptoBot кошелёк был успешно изменён ✅</b>")
    else:
        await cache_message.edit_text("<b>🔷 Не удалось изменить CryptoBot кошелёк ❌</b>")

    await message.answer(
        "<b>🔷 Управление - CryptoBot</b>",
        reply_markup=await payment_cryptobot_finl(),
    )


################################################################################
#################################### ЮMoney ####################################
# Баланс - ЮMoney
@router.callback_query(F.data == "payment_yoomoney_balance")
async def payments_yoomoney_balance(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    response = await (
        await YoomoneyAPI.connect(
            bot=bot,
            arSession=arSession,
            update=call,
            skipping_error=True,
        )
    ).balance()

    await call.message.answer(
        response,
        reply_markup=close_finl(),
    )


# Информация - ЮMoney
@router.callback_query(F.data == "payment_yoomoney_check")
async def payments_yoomoney_check(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    response = await (
        await YoomoneyAPI.connect(
            bot=bot,
            arSession=arSession,
            update=call,
            skipping_error=True,
        )
    ).check()

    await call.message.answer(
        response,
        reply_markup=close_finl(),
    )


# Изменение - ЮMoney
@router.callback_query(F.data == "payment_yoomoney_edit")
async def payments_yoomoney_edit(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    response = await (
        await YoomoneyAPI.connect(
            bot=bot,
            arSession=arSession,
        )
    ).authorization_get()

    await state.set_state("here_yoomoney_token")
    await call.message.edit_text(
        ded(f"""
            <b>🔮 Изменение ЮMoney кошелька - <a href='https://teletype.in/@djimbox/djimboshop-yoomoney'>Инструкция</a></b>
            ➖➖➖➖➖➖➖➖➖➖
            ▪️ Отправьте ссылку/код из адресной строки
            ▪️ {response}
        """),
        disable_web_page_preview=True,
    )


# Выключатель - ЮMoney
@router.callback_query(F.data.startswith("payment_yoomoney_status:"))
async def payments_yoomoney_status(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    get_status = call.data.split(":")[1]

    get_payments = await Paymentsx().get()

    if get_status == "True" and get_payments.yoomoney_token == "None":
        return await call.answer("❌ Токен данной платежной системы не был добавлен", True)

    await Paymentsx().update(status_yoomoney=get_status)

    await call.message.edit_text(
        "<b>🔮 Управление - ЮMoney</b>",
        reply_markup=await payment_yoomoney_finl(),
    )


################################ ПРИНЯТИЕ ЮMONEY ###############################
# Принятие токена ЮMoney
@router.message(StateFilter("here_yoomoney_token"))
async def payments_yoomoney_get(message: Message, bot: Bot, state: FSM, arSession: ARS):
    get_code = message.text

    try:
        get_code = get_code[get_code.index("code=") + 5:].replace(" ", "")
    except Exception:
        bot_logger.debug("ЮMoney code= не найден в сообщении, пробую использовать текст как код", exc_info=True)

    cache_message = await message.answer("<b>🔮 Проверка введённых ЮMoney данных... 🔄</b>")

    status, token, response = await (
        await YoomoneyAPI.connect(
            bot=bot,
            arSession=arSession,
        )
    ).authorization_enter(str(get_code))

    if status:
        await Paymentsx().update(yoomoney_token=token)

    await cache_message.edit_text(response)

    await state.clear()
    await message.answer(
        "<b>🔮 Управление - ЮMoney</b>",
        reply_markup=await payment_yoomoney_finl(),
    )


################################################################################
#################################### ЗВЁЗДЫ ####################################
# Баланс - Звёзды
@router.callback_query(F.data == "payment_stars_balance")
async def payments_stars_balance(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    response = await (
        await StarsAPI.connect(
            bot=bot,
            arSession=arSession,
            update=call,
            skipping_error=True,
        )
    ).balance()

    await call.message.answer(
        response,
        reply_markup=close_finl(),
    )


# Информация - Звёзды
@router.callback_query(F.data == "payment_stars_check")
async def payments_stars_check(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    status, response = await (
        await StarsAPI.connect(
            bot=bot,
            arSession=arSession,
            update=call,
            skipping_error=True,
        )
    ).check()

    await call.message.answer(
        response,
        reply_markup=close_finl(),
    )


# Изменение - Звёзды
@router.callback_query(F.data == "payment_stars_edit")
async def payments_stars_edit(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    get_payments = await Paymentsx().get()

    await state.set_state("here_stars_course")
    await call.message.edit_text(
        ded(f"""
            <b>⭐️ Изменение курса Telegram Stars</b>
            ➖➖➖➖➖➖➖➖➖➖
            ▪️ Текущий курс: <code>1 ⭐️ = {get_payments.stars_course}₽</code>
            ▪️ Отправьте новый курс в рублях за одну звезду
        """),
        disable_web_page_preview=True,
    )


# Выключатель - Звёзды
@router.callback_query(F.data.startswith("payment_stars_status:"))
async def payments_stars_status(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    get_status = call.data.split(":")[1]

    await Paymentsx().update(status_stars=get_status)

    await call.message.edit_text(
        "<b>⭐️ Управление - Звёзды</b>",
        reply_markup=await payment_stars_finl(),
    )


############################# ПРИНЯТИЕ КУРСА ЗВЁЗД #############################
# Принятие курса Telegram Stars
@router.message(StateFilter("here_stars_course"))
async def payments_stars_course_get(message: Message, bot: Bot, state: FSM, arSession: ARS):
    if not is_number(message.text):
        return await message.answer(
            "<b>❌ Введите число. Например: <code>1.5</code></b>"
        )

    stars_course = float(to_number(message.text))

    if stars_course <= 0:
        return await message.answer("<b>❌ Курс должен быть больше нуля</b>")

    await Paymentsx().update(stars_course=stars_course)
    await state.clear()

    await message.answer(
        f"<b>⭐️ Курс Telegram Stars изменён: <code>1 ⭐️ = {stars_course}₽</code></b>",
    )

    await message.answer(
        "<b>⭐️ Управление - Звёзды</b>",
        reply_markup=await payment_stars_finl(),
    )
