# - *- coding: utf- 8 - *-
import asyncio
import json
from dataclasses import dataclass

from aiogram import Bot

from tgbot.database import Settingsx
from tgbot.services.api_telegraph import TelegraphAPI
from tgbot.utils.const_functions import send_errors
from tgbot.utils.misc.bot_logging import bot_logger
from tgbot.utils.misc.bot_models import ARS


# Model Hosting Text
@dataclass
class ModelHostingText:
    telegraph: str = "telegraph"
    pastie: str = "pastie"
    friendpaste: str = "friendpaste"
    snippet: str = "snippet"


# API для работы с текстовыми хостингами
class HostingAPI:
    # Настройка клиента текстового хостинга
    def __init__(
            self,
            arSession: ARS,
            bot: Bot,
            text_hosting: str,
    ):
        self.arSession = arSession
        self.bot = bot
        self.text_hosting = text_hosting

    # Инициализация данных
    @classmethod
    async def connect(cls, arSession: ARS, bot: Bot):
        settings = await Settingsx().get()

        return cls(
            arSession=arSession,
            bot=bot,
            text_hosting=settings.misc_hosting_text,  # telegraph, pastie, friendpaste, snippet
        )

    # Загрузка текста на хостинг
    async def upload_text(self, text: str) -> str:
        session = await self.arSession.get_session()

        max_attempts = 10

        for attempt in range(max_attempts):
            status_success = True
            return_link = "None"

            ############################################################
            ######################## TELEGRAPH #########################
            if self.text_hosting == ModelHostingText.telegraph:
                telegraph_api = await TelegraphAPI.connect(arSession=self.arSession)
                status, response = await telegraph_api.upload_text(text)

                if status:
                    return_link = response
                else:
                    await send_errors(self.bot, 4044321, str(response))
                    status_success = False

            ############################################################
            ########################## PASTIE ##########################
            elif self.text_hosting == ModelHostingText.pastie:
                try:
                    response = await session.request(
                        method="post",
                        url="http://pastie.org/pastes/create/",
                        data={
                            'language': 'plaintext',
                            'content': text,
                        },
                    )
                except Exception as ex:
                    bot_logger.warning("Ошибка загрузки текста в Pastie", exc_info=True)
                    await send_errors(self.bot, 4719012, str(ex))
                    status_success = False
                else:
                    cache_link = response.url

                    if "create" in str(cache_link) or str(cache_link) == "http://pastie.org/":
                        status_success = False
                    else:
                        return_link = cache_link

            ############################################################
            ######################## FRIENDPASTE #######################
            elif self.text_hosting == ModelHostingText.friendpaste:
                try:
                    response = await session.request(
                        method="post",
                        url="https://www.friendpaste.com/",
                        json={
                            'language': 'text',
                            'title': '',
                            'snippet': text,
                        },
                    )
                    cache_link = json.loads((await response.read()).decode())['url']
                except Exception as ex:
                    bot_logger.warning("Ошибка загрузки текста в FriendPaste", exc_info=True)
                    await send_errors(self.bot, 8434711, str(ex))
                    status_success = False
                else:
                    return_link = cache_link

            ############################################################
            ######################### SNIPPET ##########################
            elif self.text_hosting == ModelHostingText.snippet:
                try:
                    response = await session.request(
                        method="post",
                        url="https://snippet.host/",
                        data={
                            'title': '',
                            'content': text,
                            'visibility': '1',
                            'expires': 'never',
                            'language': 'plain text'
                        },
                    )
                    cache_link = response.url
                except Exception as ex:
                    bot_logger.warning("Ошибка загрузки текста в Snippet", exc_info=True)
                    await send_errors(self.bot, 8900012, str(ex))
                    status_success = False
                else:
                    return_link = cache_link

            if status_success:
                return str(return_link)

            # pastie -> friendpaste
            if self.text_hosting == ModelHostingText.pastie:
                self.text_hosting = ModelHostingText.friendpaste
            # friendpaste -> snippet
            elif self.text_hosting == ModelHostingText.friendpaste:
                self.text_hosting = ModelHostingText.snippet
            # snippet -> telegraph
            elif self.text_hosting == ModelHostingText.snippet:
                self.text_hosting = ModelHostingText.telegraph
            # telegraph -> pastie
            elif self.text_hosting == ModelHostingText.telegraph:
                self.text_hosting = ModelHostingText.pastie

            if attempt < max_attempts - 1:
                await asyncio.sleep(3)

        return "None"
