# - *- coding: utf- 8 - *-
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import colorlog

from tgbot.data.config import PATH_LOGS

LOG_FILE_MAX_BYTES = 5 * 1024 * 1024
LOG_FILE_BACKUP_COUNT = 5

log_path = Path(PATH_LOGS)
log_path.parent.mkdir(parents=True, exist_ok=True)

bot_logger = logging.getLogger("tgbot")
bot_logger.setLevel(logging.INFO)
bot_logger.propagate = False

if not bot_logger.handlers:
    file_formatter = logging.Formatter(
        "%(levelname)s | %(asctime)s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)s%(reset)s | %(blue)s%(asctime)s%(reset)s | "
        "%(purple)s%(filename)s:%(lineno)d%(reset)s | %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=LOG_FILE_MAX_BYTES,
        backupCount=LOG_FILE_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    bot_logger.addHandler(file_handler)
    bot_logger.addHandler(console_handler)
