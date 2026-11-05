# - *- coding: utf- 8 - *-
import json
from typing import Optional, Tuple

from tgbot.database import Settingsx
from tgbot.utils.const_functions import gen_id
from tgbot.utils.misc.bot_logging import bot_logger
from tgbot.utils.misc.bot_models import ARS


# API для работы с телеграфом
class TelegraphAPI:
    # Настройка клиента Telegraph
    def __init__(self, arSession: ARS, token: Optional[str] = None):
        self.arSession = arSession
        self.token = token

        self.domain = "https://api.telegra.ph"

    # Инициализация данных
    @classmethod
    async def connect(cls, arSession: ARS, token: Optional[str] = None):
        if token is None:
            settings = await Settingsx().get()
            token = settings.misc_token_telegraph

        return cls(arSession=arSession, token=token)

    # Загрузка текста в телеграф
    async def upload_text(self, text: str) -> Tuple[bool, str]:
        session = await self.arSession.get_session()

        if self.token == "None" or self.token is None:
            status, response = await self.generate_token()

            if status:
                self.token = response
            else:
                return False, "Error generate token"

        try:
            response = await session.request(
                method="POST",
                url=f"{self.domain}/createPage",
                data={
                    'access_token': self.token,
                    'title': f'shop{gen_id(18)}',
                    'content': json.dumps([{'tag': 'p', 'children': [text]}]),
                }
            )

            response_data = json.loads((await response.read()).decode())
        except Exception:
            bot_logger.warning("Не удалось загрузить текст в Telegraph", exc_info=True)
            return False, "None"
        else:
            if "ok" in response_data and response_data['ok']:
                return True, response_data['result']['url'].replace("\\\\", "")
            else:
                return False, response_data

    # Генерация нового Telegraph-токена
    async def generate_token(self) -> Tuple[bool, str]:
        session = await self.arSession.get_session()

        try:
            response = await session.request(
                method="POST",
                url=f"{self.domain}/createAccount",
                data={
                    'short_name': 'dj shop',
                }
            )

            response_data = json.loads((await response.read()).decode())
        except Exception:
            bot_logger.warning("Не удалось создать Telegraph token", exc_info=True)
            return False, "None"
        else:
            if "ok" in response_data and response_data['ok']:
                await Settingsx().update(
                    misc_token_telegraph=response_data['result']['access_token']
                )

                return True, response_data['result']['access_token']
            else:
                return False, response_data
