import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from services.backup import backuper

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("clear_backups"))
async def clear_backups_handler(msg: Message):
    try:
        removed = backuper.cleanup_all_backups()
        if removed:
            text = "<b>🗑 Удалены бэкапы:</b>\n" + "\n".join(f"• <b>{n}</b>" for n in removed)
        else:
            text = "<b>ℹ️ Нет бэкапов для удаления.</b>"
        await msg.answer(text)
    except Exception as e:
        logger.error(f"Ошибка в /clear_backups: {e}", exc_info=True)
        await msg.answer("<b>❌ Ошибка при удалении бэкапов.</b>")

