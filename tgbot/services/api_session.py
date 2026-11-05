# - *- coding: utf- 8 - *-
import ssl
from typing import Optional

import aiohttp
import certifi


# Асинхронная сессия для запросов
class AsyncRequestSession:
    # Создание ленивой aiohttp-сессии
    def __init__(self) -> None:
        self._session: Optional[aiohttp.ClientSession] = None

    # Получение объекта сессии
    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            timeout = aiohttp.ClientTimeout(total=15, connect=5, sock_read=10)
            connector = aiohttp.TCPConnector(ssl=ssl_context)

            self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)

        return self._session

    # Закрытие сессии
    async def close(self) -> None:
        if self._session is None:
            return None

        await self._session.close()
