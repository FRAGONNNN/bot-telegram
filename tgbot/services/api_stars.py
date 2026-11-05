# - *- coding: utf- 8 - *-
import math
from typing import Optional, Tuple, Union

from aiogram import Bot
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery, SuccessfulPayment

from tgbot.database import Paymentsx
from tgbot.utils.const_functions import ded, gen_id, to_number
from tgbot.utils.misc.bot_logging import bot_logger
from tgbot.utils.misc.bot_models import ARS
from tgbot.utils.misc_functions import send_admins

STARS_CURRENCY = "XTR"
STARS_PAYLOAD_PREFIX = "stars_refill"


# АПИ для работы с Telegram Stars
class StarsAPI:
    # Настройка клиента Telegram Stars
    def __init__(
            self,
            bot: Bot,
            arSession: ARS,
            update: Optional[Union[Message, CallbackQuery, PreCheckoutQuery]] = None,
            stars_course: float = 1.5,
            skipping_error: bool = False,
    ):
        self.bot = bot
        self.arSession = arSession
        self.update = update
        self.stars_course = float(stars_course or 1.5)
        self.skipping_error = skipping_error

    # Инициализация данных
    @classmethod
    async def connect(
            cls,
            bot: Bot,
            arSession: ARS,
            update: Optional[Union[Message, CallbackQuery, PreCheckoutQuery]] = None,
            skipping_error: bool = False,
    ) -> "StarsAPI":
        payments = await Paymentsx().get()

        return cls(
            bot=bot,
            arSession=arSession,
            update=update,
            stars_course=payments.stars_course,
            skipping_error=skipping_error,
        )

    # Уведомление админов о проблеме со Stars
    async def error_notification(self, error_code: str = "Unknown") -> None:
        bot_logger.warning("Telegram Stars недоступны: %s", error_code)

        if self.skipping_error:
            return

        await send_admins(
            self.bot,
            f"<b>⭐️ Telegram Stars недоступны</b>\n"
            f"❗️ Ошибка: <code>{error_code}</code>"
        )

    # Проверка доступности Stars для бота
    async def check(self) -> Tuple[bool, str]:
        try:
            bot_info = await self.bot.get_me()
            balance = await self.bot.get_my_star_balance()
        except Exception as ex:
            bot_logger.warning("Не удалось проверить Telegram Stars", exc_info=True)
            await self.error_notification(str(ex))

            return False, "<b>⭐️ Не удалось проверить Telegram Stars ❌</b>"

        rub_balance = self.stars_to_rub(balance.amount)

        return True, ded(f"""
            <b>⭐️ Telegram Stars полностью функционируют ✅</b>
            ➖➖➖➖➖➖➖➖➖➖
            ▪️ Бот: <code>@{bot_info.username}</code>
            ▪️ Баланс: <code>{balance.amount} ⭐️</code> ≈ <code>{rub_balance}₽</code>
            ▪️ Курс: <code>1 ⭐️ = {self.stars_course}₽</code>
        """)

    # Получение баланса Stars у бота
    async def balance(self) -> str:
        try:
            balance = await self.bot.get_my_star_balance()
        except Exception as ex:
            bot_logger.warning("Не удалось получить баланс Telegram Stars", exc_info=True)
            await self.error_notification(str(ex))

            return "<b>⭐️ Не удалось получить баланс Telegram Stars ❌</b>"

        rub_balance = self.stars_to_rub(balance.amount)
        nanostars = balance.nanostar_amount or 0

        return ded(f"""
            <b>⭐️ Баланс Telegram Stars</b>
            ➖➖➖➖➖➖➖➖➖➖
            ▪️ Звёзды: <code>{balance.amount} ⭐️</code>
            ▪️ Нанозвёзды: <code>{nanostars}</code>
            ▪️ В рублях по курсу: <code>{rub_balance}₽</code>
            ▪️ Курс: <code>1 ⭐️ = {self.stars_course}₽</code>
        """)

    # Создание ссылки на счёт Telegram Stars
    async def bill(self, pay_amount: Union[float, int]) -> Tuple[Union[str, bool], str, int]:
        rub_amount = round(float(pay_amount), 2)
        stars_amount = self.rub_to_stars(rub_amount)
        bill_chat_id, bill_message_id = self.get_bill_message()
        receipt = gen_id(12)

        payload = self.make_payload(
            receipt,
            rub_amount,
            stars_amount,
            bill_chat_id,
            bill_message_id,
        )

        try:
            bill_link = await self.bot.create_invoice_link(
                title="Пополнение баланса",
                description=f"Пополнение баланса на {rub_amount}₽ через Telegram Stars",
                payload=payload,
                provider_token="",
                currency=STARS_CURRENCY,
                prices=[
                    LabeledPrice(
                        label=f"Пополнение на {rub_amount}₽",
                        amount=stars_amount,
                    )
                ],
            )
        except Exception as ex:
            bot_logger.warning("Не удалось создать счёт Telegram Stars", exc_info=True)
            await self.error_notification(str(ex))

            return False, "", 0

        bill_message = ded(f"""
            <b>💰 Пополнение баланса через Telegram Stars</b>
            ➖➖➖➖➖➖➖➖➖➖
            ▪️ Сумма пополнения: <code>{rub_amount}₽</code>
            ▪️ К оплате: <code>{stars_amount} ⭐️</code>
            ▪️ Курс: <code>1 ⭐️ = {self.stars_course}₽</code>
            ➖➖➖➖➖➖➖➖➖➖
            ❗️ После оплаты средства автоматически зачислятся на ваш баланс
            Если сообщение не обновилось, нажмите <code>Проверить оплату</code>
        """)

        return bill_message, bill_link, receipt

    # Проверка оплаты по истории Stars
    async def bill_check(self, bill_receipt: Optional[Union[str, int]] = None, records: int = 100) -> Tuple[int, float]:
        if bill_receipt is None:
            return 1, 0

        try:
            transactions = await self.bot.get_star_transactions(limit=records)
        except Exception as ex:
            bot_logger.warning("Не удалось проверить оплату Telegram Stars", exc_info=True)
            await self.error_notification(str(ex))

            return 1, 0

        receipt = str(bill_receipt)

        for transaction in transactions.transactions:
            source = transaction.source
            payload = getattr(source, "invoice_payload", None)

            if not payload:
                continue

            payload_data = self.parse_payload(payload)

            if payload_data is None or str(payload_data[0]) != receipt:
                continue

            _receipt, rub_amount, stars_amount, _bill_chat_id, _bill_message_id = payload_data

            if transaction.amount != stars_amount:
                bot_logger.warning(
                    "Сумма Telegram Stars не совпала с payload: receipt=%s expected=%s actual=%s",
                    receipt,
                    stars_amount,
                    transaction.amount,
                )
                return 1, 0

            return 0, rub_amount

        return 2, 0

    # Подтверждение автоматической оплаты
    async def answer_pre_checkout(self, query: PreCheckoutQuery) -> None:
        payload_data = self.parse_payload(query.invoice_payload)

        if query.currency != STARS_CURRENCY or payload_data is None or query.total_amount != payload_data[2]:
            await self.bot.answer_pre_checkout_query(
                pre_checkout_query_id=query.id,
                ok=False,
                error_message="Некорректный счёт Telegram Stars",
            )
            return

        await self.bot.answer_pre_checkout_query(
            pre_checkout_query_id=query.id,
            ok=True,
        )

    # Получение данных успешной оплаты
    def parse_successful_payment(
            self,
            payment: SuccessfulPayment,
    ) -> Tuple[int, float, str, Optional[int], Optional[int]]:
        payload_data = self.parse_payload(payment.invoice_payload)

        if payment.currency != STARS_CURRENCY or payload_data is None or payment.total_amount != payload_data[2]:
            raise ValueError("Некорректная успешная оплата Telegram Stars")

        receipt, rub_amount, _stars_amount, bill_chat_id, bill_message_id = payload_data

        return receipt, rub_amount, payment.telegram_payment_charge_id, bill_chat_id, bill_message_id

    # Возврат оплаты пользователю
    async def refund(self, user_id: int, telegram_payment_charge_id: str) -> bool:
        try:
            return await self.bot.refund_star_payment(
                user_id=user_id,
                telegram_payment_charge_id=telegram_payment_charge_id,
            )
        except Exception as ex:
            bot_logger.warning("Не удалось вернуть оплату Telegram Stars", exc_info=True)
            await self.error_notification(str(ex))

            return False

    # Конвертация рублей в звёзды
    def rub_to_stars(self, rub_amount: Union[float, int]) -> int:
        if self.stars_course <= 0:
            raise ValueError("Курс Telegram Stars должен быть больше нуля")

        return max(1, math.ceil(float(rub_amount) / self.stars_course))

    # Конвертация звёзд в рубли
    def stars_to_rub(self, stars_amount: Union[float, int]) -> float:
        return round(float(stars_amount) * self.stars_course, 2)

    # Получение данных сообщения со счётом
    def get_bill_message(self) -> Tuple[Optional[int], Optional[int]]:
        if isinstance(self.update, Message):
            return self.update.chat.id, self.update.message_id

        return None, None

    # Сбор payload для телеграм инвойса
    @staticmethod
    def make_payload(
            receipt: int,
            rub_amount: float,
            stars_amount: int,
            bill_chat_id: Optional[int] = None,
            bill_message_id: Optional[int] = None,
    ) -> str:
        payload = f"{STARS_PAYLOAD_PREFIX}:{receipt}:{rub_amount}:{stars_amount}"

        if bill_chat_id is not None and bill_message_id is not None:
            payload += f":{bill_chat_id}:{bill_message_id}"

        return payload

    # Разбор payload телеграм инвойса
    @staticmethod
    def parse_payload(
            payload: str,
    ) -> Optional[Tuple[int, float, int, Optional[int], Optional[int]]]:
        payload_parts = str(payload).split(":")

        if len(payload_parts) not in (4, 6) or payload_parts[0] != STARS_PAYLOAD_PREFIX:
            return None

        try:
            receipt = int(payload_parts[1])
            rub_amount = float(to_number(payload_parts[2]))
            stars_amount = int(payload_parts[3])
            bill_chat_id = int(payload_parts[4]) if len(payload_parts) == 6 else None
            bill_message_id = int(payload_parts[5]) if len(payload_parts) == 6 else None
        except (TypeError, ValueError):
            return None

        return receipt, rub_amount, stars_amount, bill_chat_id, bill_message_id
