# - *- coding: utf- 8 - *-
import json
from typing import Any, Dict, Optional, Tuple, Union

from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiohttp import ClientConnectorCertificateError

from tgbot.database import Paymentsx
from tgbot.utils.const_functions import ded, to_number
from tgbot.utils.misc.bot_logging import bot_logger
from tgbot.utils.misc.bot_models import ARS
from tgbot.utils.misc_functions import send_admins

# Список поддерживаемых валют
ALLOW_CURRENCIES = ['BTC', 'ETH', 'LTC', 'USDT', 'USDC', 'TRX', 'TON', 'BNB', 'SOL', 'DOGE']


# АПИ для работы с CryptoBot
class CryptobotAPI:
    # Настройка клиента CryptoBot
    def __init__(
            self,
            bot: Bot,
            arSession: ARS,
            update: Optional[Union[Message, CallbackQuery]] = None,
            token: str = "None",
            adding: bool = False,
            skipping_error: bool = False,
    ):
        self.bot = bot
        self.arSession = arSession
        self.update = update
        self.token = token
        self.adding = adding
        self.skipping_error = skipping_error

    # Инициализация данных
    @classmethod
    async def connect(
            cls,
            bot: Bot,
            arSession: ARS,
            update: Optional[Union[Message, CallbackQuery]] = None,
            token: Optional[str] = None,
            skipping_error: bool = False,
    ) -> "CryptobotAPI":
        adding = token is not None

        if token is None:
            payments = await Paymentsx().get()
            token = payments.cryptobot_token
            adding = False

        return cls(
            bot=bot,
            arSession=arSession,
            update=update,
            token=token,
            adding=adding,
            skipping_error=skipping_error,
        )

    # Уведомления о неработоспособности кассы/кошелька
    async def error_notification(self, error_code: str = "Unknown"):
        bot_logger.warning("CryptoBot недоступен: %s", error_code)

        if not self.skipping_error:
            if self.adding and self.update is not None:
                await self.update.edit_text(
                    f"<b>🔷 Не удалось добавить CryptoBot кассу ❌</b>\n"
                    f"❗️ Ошибка: <code>{error_code}</code>"
                )
            else:
                await send_admins(
                    self.bot,
                    f"<b>🔷 CryptoBot недоступен. Как можно быстрее его замените</b>\n"
                    f"❗️ Ошибка: <code>{error_code}</code>"
                )

    # Проверка кассы/кошелька
    async def check(self) -> Tuple[bool, str]:
        status, response = await self._request("getMe")

        if status and response['ok']:
            return True, ded(f"""
                <b>🔷 CryptoBot кошелёк полностью функционирует ✅</b>
                ➖➖➖➖➖➖➖➖➖➖
                ▪️ Токен: <code>{self.token}</code>
                ▪️ Айди: <code>{response['result']['app_id']}</code>
                ▪️ Имя: <code>{response['result']['name']}</code>
            """)

        return False, "<b>🔷 Не удалось проверить CryptoBot кошелёк ❌</b>"

    # Получение баланса
    async def balance(self) -> str:
        status, response = await self._request("getBalance")

        if status and response['ok']:
            save_currencies = []

            response_balances = sorted(
                response['result'],
                reverse=True,
                key=lambda balance: to_number(balance['available']),
            )

            for currency in response_balances:
                if currency['currency_code'] in ALLOW_CURRENCIES:
                    save_currencies.append(
                        f"▪️ {currency['currency_code']}: <code>{currency['available']}</code>"
                    )

            save_currencies = "\n".join(save_currencies)

            return ded(f"""
                <b>🔷 Баланс CryptoBot кошелька составляет</b>
                ➖➖➖➖➖➖➖➖➖➖
                {save_currencies}
            """)

        return "<b>🔷 Не удалось получить баланс CryptoBot кошелька ❌</b>"

    # Создание счета на оплату
    async def bill(self, pay_amount: Union[float, int]) -> Tuple[Union[str, bool], str, str]:
        assets_currencies = ",".join(ALLOW_CURRENCIES)

        payload = {
            'currency_type': 'fiat',
            'fiat': 'RUB',
            'amount': str(pay_amount),
            'expires_in': 10800,
            'accepted_assets': assets_currencies
        }

        status, response = await self._request("createInvoice", payload)

        if status and response['ok']:
            bill_message = ded(f"""
                <b>💰 Пополнение баланса</b>
                ➖➖➖➖➖➖➖➖➖➖
                ▪️ Для пополнения баланса, нажмите на кнопку ниже 
                <code>Перейти к оплате</code> и оплатите выставленный вам счёт
                ▪️ У вас имеется 3 часа на оплату счета
                ▪️ Сумма пополнения: <code>{pay_amount}₽</code>
                ➖➖➖➖➖➖➖➖➖➖
                ❗️ После оплаты, нажмите на <code>Проверить оплату</code>
            """)

            return bill_message, response['result']['mini_app_invoice_url'], response['result']['invoice_id']

        return False, "", ""

    # Проверка счета на оплату
    async def bill_check(self, bill_receipt: Optional[Union[str, int]] = None, records: int = 1) -> Tuple[int, float]:
        payload = {
            'invoice_ids': f'{bill_receipt}',
            'fiat': 'RUB',
        }

        status, response = await self._request("getInvoices", payload)

        pay_status, pay_amount = 1, 0

        if status and response['ok']:
            get_invoice = response['result']['items'][0]

            if get_invoice['status'] == "active":
                pay_status = 2
            elif get_invoice['status'] == "expired":
                pay_status = 3
            else:
                pay_status = 0
                pay_amount = to_number(get_invoice['amount'])

        return pay_status, pay_amount

    # Генерация запроса
    async def _request(
            self,
            method: str,
            data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Any]:
        session = await self.arSession.get_session()

        base_url = 'https://pay.crypt.bot/api/'
        headers = {
            'Crypto-Pay-API-Token': self.token,
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        url = base_url + method

        try:
            response = await session.post(
                url=url,
                headers=headers,
                data=data,
            )

            response_data = json.loads((await response.read()).decode())

            if response.status == 200:
                return True, response_data
            else:
                await self.error_notification(f"{response.status} - {str(response_data)}")

                return False, response_data
        except ClientConnectorCertificateError:
            bot_logger.warning("Ошибка SSL при запросе CryptoBot", exc_info=True)
            await self.error_notification("CERTIFICATE_VERIFY_FAILED")

            return False, "CERTIFICATE_VERIFY_FAILED"
        except Exception as ex:
            bot_logger.warning("Ошибка запроса CryptoBot", exc_info=True)
            await self.error_notification(str(ex))

            return False, str(ex)
