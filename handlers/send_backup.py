import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from filters.is_admin import is_admin
from config_reader import config
from services.backup import backuper

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("send_backup"), is_admin)
async def send_backup_handler(msg: Message):
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("<b>❗️ Используйте: /send_backup &lt;ip_сервера&gt;</b>")
        return
    ip = args[1]

    server = next((s for s in config.servers if s.ip == ip), None)
    if not server:
        await msg.answer(f"<b>❌ Сервер с IP {ip} не найден в конфигурации.</b>")
        return

    try:
        await msg.answer("<b>⏳ Создаю резервную копию сервера...</b>")
        archive_path = backuper.create_backup(server, save_local=False)
        doc = FSInputFile(str(archive_path))
        await msg.answer_document(doc)
        archive_path.unlink()
    except Exception as e:
        logger.error(f"Ошибка в /send_backup для {ip}: {e}", exc_info=True)
        await msg.answer("<b>❌ Ошибка при создании или отправке резервной копии сервера.</b>")

