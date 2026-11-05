# - *- coding: utf- 8 - *-
import html
import secrets
import string
import time
from datetime import datetime
from typing import List, Optional, Union

from aiogram import Bot
from aiogram.types import (
    CopyTextButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from pytz import timezone

from tgbot.data.config import BOT_TIMEZONE, get_admins
from tgbot.utils.misc.bot_logging import bot_logger


# Быстрая сборка reply-кнопки
def rkb(text: str) -> KeyboardButton:
    return KeyboardButton(text=text)


# Быстрая сборка inline-кнопки
def ikb(
        text: str,
        data: Optional[str] = None,
        url: Optional[str] = None,
        switch: Optional[str] = None,
        web: Optional[str] = None,
        copy: Optional[str] = None,
        login: Optional[str] = None,
) -> InlineKeyboardButton:
    if data is not None:
        return InlineKeyboardButton(text=text, callback_data=data)
    if url is not None:
        return InlineKeyboardButton(text=text, url=url)
    if switch is not None:
        return InlineKeyboardButton(text=text, switch_inline_query=switch)
    if web is not None:
        return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=web))
    if copy is not None:
        return InlineKeyboardButton(text=text, copy_text=CopyTextButton(text=copy))
    if login is not None:
        return InlineKeyboardButton(text=text, url=f"https://t.me/{login}")

    raise ValueError("Не указано действие для inline-кнопки")


# Удаление сообщения с логированием ошибок
async def del_message(message: Message) -> None:
    try:
        await message.delete()
    except Exception:
        bot_logger.debug("Не удалось удалить сообщение", exc_info=True)


# Отправка фото или обычного сообщения
async def smart_message(
        bot: Bot,
        user_id: int,
        text: str,
        keyboard: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
        photo: Optional[str] = None,
) -> None:
    if photo is not None and photo.title() != "None":
        await bot.send_photo(
            chat_id=user_id,
            photo=photo,
            caption=text,
            reply_markup=keyboard,
        )
    else:
        await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=keyboard,
        )


# Отправка сообщения всем админам
async def send_admins(
        bot: Bot,
        text: str,
        keyboard: Optional[InlineKeyboardMarkup] = None,
        markup: Optional[InlineKeyboardMarkup] = None,
        not_me: int = 0,
) -> None:
    reply_markup = markup or keyboard

    for admin in get_admins():
        try:
            if str(admin) != str(not_me):
                await bot.send_message(
                    admin,
                    text,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True,
                )
        except Exception:
            bot_logger.warning("Не удалось отправить сообщение админу %s", admin, exc_info=True)


# Логирование ошибки и отправка админам
async def send_errors(bot: Bot, error_code: int, error_text: str = "") -> None:
    text_error = f"myError {error_code}: {error_text}"

    bot_logger.warning(text_error)
    await send_admins(bot, text_error)


# Очистка лишних отступов в многострочном тексте
def ded(get_text: str) -> str:
    if get_text is not None:
        split_text = get_text.split("\n")

        if split_text[0] == "": split_text.pop(0)
        if split_text[-1] == "": split_text.pop()
        save_text = []

        for text in split_text:
            while text.startswith(" "):
                text = text[1:]

            save_text.append(text)
        get_text = "\n".join(save_text)
    else:
        get_text = ""

    return get_text


# Экранирование HTML-символов для телеграм разметки
def clear_html(get_text: Optional[str]) -> str:
    return html.escape(get_text or "", quote=False)


# Очистка пустых и мусорных элементов из списка
def clear_list(get_list: list) -> list:
    trash = {"", " ", ".", ",", "\r", "\n"}

    return [value for value in get_list if value not in trash]


# Склейка нескольких списков в один
def convert_list(get_lists: List[list]) -> list:
    save_lists = []

    for select_list in get_lists:
        cache_list = clear_list(select_list)

        if len(cache_list) > 0:
            save_lists += cache_list

    return save_lists


# Разделение списка на части нужного размера
def split_list(get_list: list, count: int) -> List[list]:
    return [get_list[i:i + count] for i in range(0, len(get_list), count)]


# Старое имя для разделения сообщений
def split_messages(get_list: list, count: int) -> List[list]:
    return split_list(get_list, count)


# Получение текущей даты
def get_date(full: bool = True) -> str:
    bot_timezone = timezone(BOT_TIMEZONE)

    if full:
        return datetime.now(bot_timezone).strftime("%d.%m.%Y %H:%M:%S")

    return datetime.now(bot_timezone).strftime("%d.%m.%Y")


# Получение Unix-времени в секундах или наносекундах
def get_unix(full: bool = False, nano: bool = False) -> int:
    if full or nano:
        return time.time_ns()

    return int(time.time())


# Конвертация даты в Unix и обратно
def convert_date(from_time, full=True, second=True) -> Union[str, int]:
    bot_timezone = timezone(BOT_TIMEZONE)
    from_time = str(from_time).strip().replace("-", ".")

    if from_time.isdigit():
        from_timestamp = int(from_time)

        if full:
            return datetime.fromtimestamp(from_timestamp, bot_timezone).strftime("%d.%m.%Y %H:%M:%S")
        if second:
            return datetime.fromtimestamp(from_timestamp, bot_timezone).strftime("%d.%m.%Y %H:%M")

        return datetime.fromtimestamp(from_timestamp, bot_timezone).strftime("%d.%m.%Y")

    parts = from_time.split()

    if len(parts) == 2 and ":" in parts[0]:
        time_part, date_part = parts
    elif len(parts) == 2:
        date_part, time_part = parts
    else:
        date_part, time_part = from_time, "00:00:00"

    date_values = date_part.split(".")
    time_values = time_part.split(":")

    if len(time_values) == 2:
        time_values.append("0")

    if len(date_values[0]) == 4:
        x_year, x_month, x_day = date_values[0], date_values[1], date_values[2]
    else:
        x_day, x_month, x_year = date_values[0], date_values[1], date_values[2]

    date_time = datetime(
        int(x_year),
        int(x_month),
        int(x_day),
        int(time_values[0]),
        int(time_values[1]),
        int(time_values[2]),
    )
    date_time = bot_timezone.localize(date_time)

    return int(date_time.timestamp())


# Генерация числового ID
def gen_id(len_id: int = 16) -> int:
    if len_id <= 0:
        raise ValueError("Длина ID должна быть больше нуля")

    first_digit = secrets.choice("123456789")
    other_digits = "".join(secrets.choice(string.digits) for _ in range(len_id - 1))

    return int(f"{first_digit}{other_digits}")


# Генерация пароля под разные сценарии
def gen_password(len_password: int = 16, type_password: str = "default") -> str:
    if len_password <= 0:
        raise ValueError("Длина пароля должна быть больше нуля")

    if type_password == "default":
        alphabet = string.ascii_letters + string.digits
    elif type_password == "letter":
        alphabet = string.ascii_letters
    elif type_password == "number":
        alphabet = string.digits
    elif type_password == "onechar":
        alphabet = string.digits
    else:
        raise ValueError("Неизвестный тип пароля")

    random_chars = "".join(secrets.choice(alphabet) for _ in range(len_password))

    if type_password == "onechar":
        random_chars = f"{secrets.choice(string.ascii_letters)}{random_chars[1:]}"

    return random_chars


# Склонение единицы времени под число
def convert_times(get_time: int, get_type: str = "day") -> str:
    get_time = int(get_time)

    if get_time < 0:
        get_time = 0

    if get_type == "second":
        values = ["секунда", "секунды", "секунд"]
    elif get_type == "minute":
        values = ["минута", "минуты", "минут"]
    elif get_type == "hour":
        values = ["час", "часа", "часов"]
    elif get_type == "day":
        values = ["день", "дня", "дней"]
    elif get_type == "month":
        values = ["месяц", "месяца", "месяцев"]
    else:
        values = ["год", "года", "лет"]

    if get_time % 10 == 1 and get_time % 100 != 11:
        count = 0
    elif 2 <= get_time % 10 <= 4 and (get_time % 100 < 10 or get_time % 100 >= 20):
        count = 1
    else:
        count = 2

    return f"{get_time} {values[count]}"


# Старое имя для склонения дней
def convert_day(day: int) -> str:
    return convert_times(day)


# Приведение строки или числа к bool
def is_bool(value: Union[bool, str, int]) -> bool:
    value = str(value).strip().lower()

    if value in ("y", "yes", "t", "true", "on", "1"):
        return True
    if value in ("n", "no", "f", "false", "off", "0"):
        return False

    raise ValueError(f"Некорректное bool-значение: {value}")


# Форматирование числа без лишних нулей
def snum(amount: Union[int, float], remains: int = 2) -> str:
    format_str = "{:." + str(remains) + "f}"
    str_amount = format_str.format(float(amount))

    if remains != 0 and "." in str_amount:
        remains_find = str_amount.find(".")
        remains_save = remains_find + 8 - (8 - remains) + 1
        str_amount = str_amount[:remains_save]

    if "." in str(str_amount):
        while str(str_amount).endswith("0"):
            str_amount = str(str_amount)[:-1]

    if str(str_amount).endswith("."):
        str_amount = str(str_amount)[:-1]

    return str(str_amount)


# Приведение значения к int или float
def to_float(get_number, remains: int = 2) -> Union[int, float]:
    value = str(get_number).strip().replace(" ", "").replace(",", ".")
    number = round(float(value), remains)

    if number.is_integer():
        return int(number)

    return number


# Старое имя для приведения числа
def to_number(get_number, remains: int = 2) -> Union[int, float]:
    return to_float(get_number, remains)


# Округление числа до int
def to_int(get_number: float) -> int:
    value = str(get_number).replace(",", ".")

    return int(round(float(value)))


# Проверка, является ли значение числом
def is_number(get_number: Union[str, int, float]) -> bool:
    if str(get_number).isdigit():
        return True

    value = str(get_number).replace(",", ".")

    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


# Форматирование числа с разделением тысяч
def format_rate(amount: Union[float, int], around: int = 2) -> str:
    value = str(amount).strip().replace(" ", "").replace(",", ".")
    number = round(float(value), around)
    response = f"{number:,.{around}f}".replace(",", " ")

    if "." in response:
        response = response.rstrip("0").rstrip(".")

    return response
