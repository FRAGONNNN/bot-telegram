# - *- coding: utf- 8 - *-
import json
from typing import Any, Dict, Optional, Tuple, Union
from urllib.parse import urlencode

from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiohttp import ClientConnectorCertificateError

from tgbot.data.config import YOOMONEY_CLIENT_ID
from tgbot.database import Paymentsx
from tgbot.utils.const_functions import ded, gen_id
from tgbot.utils.misc.bot_logging import bot_logger
from tgbot.utils.misc.bot_models import ARS
from tgbot.utils.misc_functions import send_admins


# АПИ для работы с ЮMoney
class YoomoneyAPI:
    # Настройка клиента ЮMoney
    def __init__(
            self,
            bot: Bot,
            arSession: ARS,
            update: Optional[Union[Message, CallbackQuery]] = None,
            token: str = "None",
            adding: bool = False,
            skipping_error: bool = False,
    ):
        self.token = token
        self.adding = adding

        self.base_url = 'https://yoomoney.ru/api/'
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        self.bot = bot
        self.arSession = arSession
        self.update = update
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
    ) -> "YoomoneyAPI":
        adding = token is not None

        if token is None:
            payments = await Paymentsx().get()
            token = payments.yoomoney_token
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
        bot_logger.warning("ЮMoney недоступен: %s", error_code)

        if not self.skipping_error:
            if self.adding and self.update is not None:
                await self.update.edit_text(
                    f"<b>🔮 Не удалось добавить ЮMoney кассу ❌</b>\n"
                    f"❗️ Ошибка: <code>{error_code}</code>"
                )
            else:
                await send_admins(
                    self.bot,
                    f"<b>🔮 ЮMoney недоступен. Как можно быстрее его замените</b>\n"
                    f"❗️ Ошибка: <code>{error_code}</code>"
                )

    # Проверка кассы/кошелька
    async def check(self) -> str:
        status, response = await self._request("account-info")

        if status:
            if len(response) >= 1:
                if response['identified']:
                    text_identified = "Присутствует"
                else:
                    text_identified = "Отсутствует"

                if response['account_status'] == "identified":
                    text_status = "Идентифицированный счет"
                elif response['account_status'] == "anonymous":
                    text_status = "Анонимный счет"
                elif response['account_status'] == "named":
                    text_status = "Именной счет"
                else:
                    text_status = response['account_status']

                if response['account_type'] == "personal":
                    text_type = "Пользовательский счет"
                elif response['account_type'] == "professional":
                    text_type = "Профессиональный счет"
                else:
                    text_type = response['account_type']

                return ded(f"""
                    <b>🔮 ЮMoney кошелёк полностью функционирует ✅</b>
                    ➖➖➖➖➖➖➖➖➖➖
                    ▪️ Кошелёк: <code>{response['account']}</code>
                    ▪️ Идентификация: <code>{text_identified}</code>
                    ▪️ Статус аккаунта: <code>{text_status}</code>
                    ▪️ Тип счета: <code>{text_type}</code>
                """)

        return "<b>🔮 Не удалось проверить ЮMoney кошелёк ❌</b>"

    # Получение баланса
    async def balance(self) -> str:
        status, response = await self._request("account-info")

        if status:
            wallet_balance = response['balance']

            wallet_status, wallet_number = await self.account_info()

            if wallet_status:
                return ded(f"""
                    <b>🔮 Баланс ЮMoney кошелька составляет</b>
                    ➖➖➖➖➖➖➖➖➖➖
                    ▪️ Кошелёк: <code>{wallet_number}</code>
                    ▪️ Баланс: <code>{wallet_balance}₽</code>
                """)

        return "<b>🔮 Не удалось получить баланс ЮMoney кошелька ❌</b>"

    # Информация об аккаунте
    async def account_info(self) -> Tuple[bool, str]:
        status, response = await self._request("account-info")

        try:
            return True, response['account']
        except Exception:
            bot_logger.warning("Не удалось получить номер ЮMoney", exc_info=True)
            return False, ""

    # Получение ссылки на авторизацию
    async def authorization_get(self) -> str:
        if not YOOMONEY_CLIENT_ID:
            return "В .env не заполнен YOOMONEY_CLIENT_ID"

        session = await self.arSession.get_session()

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        url = "https://yoomoney.ru/oauth/authorize?" + urlencode({
            "client_id": YOOMONEY_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": "https://yoomoney.ru",
            "scope": "account-info operation-history operation-details",
        })

        response = await session.post(
            url=url,
            headers=headers,
        )

        return str(response.url)

    # Принятие кода авторизации и получение токена
    async def authorization_enter(self, get_code: str) -> Tuple[bool, str, str]:
        if not YOOMONEY_CLIENT_ID:
            return False, "", "<b>❌ В .env не заполнен YOOMONEY_CLIENT_ID</b>"

        session = await self.arSession.get_session()

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        url = "https://yoomoney.ru/oauth/token?" + urlencode({
            "code": get_code,
            "client_id": YOOMONEY_CLIENT_ID,
            "grant_type": "authorization_code",
            "redirect_uri": "https://yoomoney.ru",
        })

        response = await session.post(
            url=url,
            headers=headers,
        )
        response_data = json.loads((await response.read()).decode())

        if "error" in response_data:
            error = response_data['error']

            if error == "invalid_request":
                return_message = ded(f"""
                    <b>❌ Требуемые параметры запроса отсутствуют или имеют неправильные или недопустимые значения</b>
                """)
            elif error == "unauthorized_client":
                return_message = ded(f"""
                    <b>❌ Недопустимое значение параметра 'client_id' или 'client_secret', или приложение
                    не имеет права запрашивать авторизацию (например, ЮMoney заблокировал его 'client_id')</b>
                """)
            elif error == "invalid_grant":
                return_message = ded(f"""
                    <b>❌ В выпуске 'access_token' отказано. ЮMoney не выпускал временный токен,
                    срок действия токена истек или этот временный токен уже выдан
                    'access_token' (повторный запрос токена авторизации с тем же временным токеном)</b>
                """)
            else:
                return_message = f"Unknown error: {error}"

            return False, "", return_message
        elif response_data['access_token'] == "":
            return False, "", "<b>❌ Не удалось получить токен. Попробуйте всё снова</b>"

        return True, response_data['access_token'], "<b>🔮 ЮMoney кошелёк был успешно изменён ✅</b>"

    # Создание счета на оплату
    async def bill(self, pay_amount: Union[float, int]) -> Tuple[Union[str, bool], str, str]:
        session = await self.arSession.get_session()

        bill_receipt = str(gen_id(12))
        url = "https://yoomoney.ru/quickpay/confirm.xml?"

        wallet_status, wallet_number = await self.account_info()

        if wallet_status:
            pay_amount_bill = pay_amount + (pay_amount * 0.031)

            if float(pay_amount_bill) < 2:
                pay_amount_bill = 2.04

            payload = {
                'receiver': wallet_number,
                'quickpay_form': 'button',
                'targets': 'Добровольное пожертвование',
                'paymentType': 'SB',
                'sum': pay_amount_bill,
                'label': bill_receipt,
            }

            for value in payload:
                url += str(value).replace("_", "-") + "=" + str(payload[value])
                url += "&"

            bill_link = str((await session.post(url[:-1].replace(" ", "%20"))).url)

            bill_message = ded(f"""
                <b>💰 Пополнение баланса</b>
                ➖➖➖➖➖➖➖➖➖➖
                ▪️ Для пополнения баланса, нажмите на кнопку ниже 
                <code>Перейти к оплате</code> и оплатите выставленный вам счёт
                ▪️ У вас имеется 60 минут на оплату счета
                ▪️ Сумма пополнения: <code>{pay_amount}₽</code>
                ➖➖➖➖➖➖➖➖➖➖
                ❗️ После оплаты, нажмите на <code>Проверить оплату</code>
            """)

            return bill_message, bill_link, bill_receipt

        return False, "", ""

    # Проверка счета на оплату
    async def bill_check(self, bill_receipt: Optional[Union[str, int]] = None, records: int = 1) -> Tuple[int, float]:
        data = {
            'type': 'deposition',
            'details': 'true',
        }

        if bill_receipt is not None:
            data['label'] = bill_receipt
        if records is not None:
            data['records'] = str(records)

        status, response = await self._request("operation-history", data)

        pay_status, pay_amount, pay_currency = 1, 0, 0

        if status:
            pay_status = 2

            if len(response['operations']) >= 1:
                pay_currency = response['operations'][0]['amount_currency']
                pay_amount = response['operations'][0]['amount']

                pay_status = 3

                if pay_currency == "RUB":
                    pay_status = 0

        return pay_status, pay_amount

    # Генерация запроса
    async def _request(
            self,
            method: str,
            data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Any]:
        session = await self.arSession.get_session()

        url = self.base_url + method

        try:
            response = await session.post(
                url=url,
                headers=self.headers,
                data=data,
            )

            response_data = json.loads((await response.read()).decode())

            if response.status == 200:
                return True, response_data
            else:
                await self.error_notification(f"{response.status} - {str(response_data)}")

                return False, response_data
        except ClientConnectorCertificateError:
            bot_logger.warning("Ошибка SSL при запросе ЮMoney", exc_info=True)
            await self.error_notification("CERTIFICATE_VERIFY_FAILED")

            return False, "CERTIFICATE_VERIFY_FAILED"
        except Exception as ex:
            bot_logger.warning("Ошибка запроса ЮMoney", exc_info=True)
            await self.error_notification(str(ex))

            return False, str(ex)
