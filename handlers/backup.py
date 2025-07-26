import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from filters.is_admin import is_admin
from config_reader import config
from services.backup import backuper
from scheduler import scheduler_service
from datetime import datetime
import zoneinfo
from pathlib import Path

logger = logging.getLogger(__name__)
router = Router()

AUTHOR = "t.me/stix_r"

def get_file_creation_datetime_str(filepath: Path) -> str:
    try:
        moscow_tz = zoneinfo.ZoneInfo("Europe/Moscow")
        timestamp = filepath.stat().st_mtime
        dt_obj = datetime.fromtimestamp(timestamp, tz=moscow_tz)
        return dt_obj.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return "неизвестно"

@router.message(Command("backup"), is_admin)
async def backup_now_handler(msg: Message):
    args = msg.text.split()
    if len(args) > 1:
        time_arg = args[1]
        try:
            hh, mm = map(int, time_arg.split(":"))
            if not (0 <= hh < 24 and 0 <= mm < 60):
                raise ValueError
            await msg.answer(f"<b>⏰ Запускаю интервальные бэкапы начиная с {time_arg} (МСК) с интервалами из конфигурации.</b>")
            scheduler_service.schedule_interval_backup_starting(time_arg)
        except Exception:
            await msg.answer("<b>❌ Неверный формат времени. Используйте HH:MM.</b>")
    else:
        waiting_msg = await msg.answer("<b>⏳ Создаю резервную копию и отправляю...</b>")

        for server in config.servers:
            try:
                archive_path = backuper.create_backup(server, save_local=False)
                filename = archive_path.name
                dt_str = get_file_creation_datetime_str(archive_path)
                caption = (
                    f"<b>📦 Файл:</b> <code>{filename}</code>\n"
                    f"<b>🌐 IP сервера:</b> <code>{server.ip}</code>\n"
                    f"<b>📅 Дата и время:</b> <code>{dt_str}</code>\n"
                    f"<b>👤 Автор:</b> <a href='https://{AUTHOR}'>{AUTHOR}</a>"
                )
                await msg.answer_document(FSInputFile(str(archive_path)), caption=caption)
                archive_path.unlink()
            except Exception as e:
                logger.error(f"Ошибка при создании и отправке бэкапа сервера {server.name}: {e}", exc_info=True)
                await msg.answer(f"<b>❌ Не удалось создать и отправить бэкап для сервера {server.name}.</b>")

        try:
            await msg.bot.delete_message(chat_id=waiting_msg.chat.id, message_id=waiting_msg.message_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение ожидания: {e}")

