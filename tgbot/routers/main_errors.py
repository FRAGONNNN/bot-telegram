# - *- coding: utf- 8 - *-
from aiogram import Router
from aiogram.filters import ExceptionMessageFilter
from aiogram.handlers import ErrorHandler

from tgbot.utils.misc.bot_logging import bot_logger

router = Router(name=__name__)


# Игнорирование повторного редактирования без падения handler-а
@router.errors(ExceptionMessageFilter(
    "Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message")
)
class MessageNotModifiedHandler(ErrorHandler):
    # Debug-запись о повторном edit
    async def handle(self):
        bot_logger.debug(
            "Телеграм отказал в повторном редактировании сообщения: %s",
            self.exception_message,
            exc_info=True,
        )


# Логирование всех ошибок, которые дошли до aiogram error router
@router.errors()
class UnknownErrorHandler(ErrorHandler):
    # Запись traceback неизвестной ошибки
    async def handle(self):
        bot_logger.error(
            "Ошибка handler-а: %s | %s",
            self.exception_name,
            self.exception_message,
            exc_info=True,
        )
