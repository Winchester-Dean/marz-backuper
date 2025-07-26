import logging
from pathlib import Path
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from config_reader import config
from datetime import datetime, time, timedelta
import zoneinfo

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("help"))
async def help_handler(msg: Message):
    try:
        backups = list(Path("tmp").glob(f"*.{config.backup.format}")) if Path("tmp").exists() else []

        # Читаем время ежедневного бэкапа
        hh, mm = map(int, config.backup.auto.split(":"))

        # МСК часовой пояс
        moscow_tz = zoneinfo.ZoneInfo("Europe/Moscow")
        now = datetime.now(moscow_tz)

        # Время запуска сегодня (сегодня в backup.auto)
        today_backup_time = datetime.combine(now.date(), time(hour=hh, minute=mm), tzinfo=moscow_tz)

        # Если время сегодня уже прошло, следующий бэкап завтра
        if now >= today_backup_time:
            next_backup_dt = today_backup_time + timedelta(days=1)
        else:
            next_backup_dt = today_backup_time

        next_backup_str = next_backup_dt.strftime("%d.%m.%Y %H:%M")

        servers_count = len(config.servers)
        backup_format = config.backup.format
        author = "t.me/stix_r"

        text = (
            f"<b>📚 Информация по командам и логике бота:</b>\n\n"
            f"• Следующий автоматический бэкап запланирован на <b>{next_backup_str}</b> (МСК)\n"
            f"• Количество бэкапов в tmp: <b>{len(backups)}</b>\n"
            f"• Количество серверов: <b>{servers_count}</b>\n"
            f"• Формат архивов: <b>{backup_format}</b>\n"
            f"• Автор: <b>{author}</b>\n\n"
            "<b>Команды:</b>\n"
            "/backup — сделать резервную копию прямо сейчас\n"
            "/backup HH:MM — запустить интервальные бэкапы начиная с времени HH:MM\n"
            "/send_backup &lt;ip&gt; — получить бэкап сервера по IP\n"
            "/list_backup — показать список бэкапов\n"
            "/clear_backups — удалить все локальные бэкапы\n"
            "/help — эта справка"
        )
        await msg.answer(text)
    except Exception as e:
        logger.error(f"Ошибка в /help: {e}", exc_info=True)
        await msg.answer("<b>❌ Произошла ошибка при отображении справки.</b>")

