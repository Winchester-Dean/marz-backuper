import logging
from pathlib import Path
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from config_reader import config

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("list_backup"))
async def list_backup_handler(msg: Message):
    try:
        backup_dir = Path("tmp")
        if not backup_dir.exists():
            await msg.answer("<b>📁 Папка с бэкапами пуста.</b>")
            return

        fmt = config.backup.format.lower()
        ext = "tar.gz" if fmt == "tar.gz" else "zip"

        backups = list(backup_dir.glob(f"*.{ext}"))
        if not backups:
            await msg.answer("<b>📁 Бэкапов пока нет.</b>")
            return

        text = "<b>📋 Доступные бэкапы:</b>\n\n"
        for bkp in backups:
            text += f"• <b>{bkp.name}</b>\n"
        await msg.answer(text)

    except Exception as e:
        logger.error(f"Ошибка в /list_backup: {e}", exc_info=True)
        await msg.answer("<b>❌ Ошибка при выводе списка бэкапов.</b>")

