import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def start_handler(msg: Message):
    try:
        await msg.answer(
            "<b>👋 Привет!</b>\n"
            "Я бот для резервного копирования серверов на базе Marzban.\n\n"
            "<b>Доступные команды:</b>\n"
            "/backup — сделать резервную копию прямо сейчас и получить архив\n"
            "/help — подробная справка по командам"
        )
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}", exc_info=True)

