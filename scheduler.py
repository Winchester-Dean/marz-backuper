import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import zoneinfo
from config_reader import config
from services.backup import backuper
from dispatcher import bot
from aiogram.types import FSInputFile

logger = logging.getLogger(__name__)
AUTHOR = "t.me/stix_r"

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=zoneinfo.ZoneInfo("Europe/Moscow"))
        self.daily_job = None
        self.interval_jobs = {}

    def start(self):
        try:
            hh, mm = map(int, config.backup.auto.split(":"))
            self.daily_job = self.scheduler.add_job(
                self._create_and_send_daily_backup,
                CronTrigger(hour=hh, minute=mm, timezone=self.scheduler.timezone)
            )
            self.scheduler.start()
            logger.info("Scheduler started with daily backup at %02d:%02d", hh, mm)
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}", exc_info=True)

    def schedule_interval_backup_starting(self, start_time_str: str):
        try:
            # Удаляем старые интервальные задачи
            for job in self.interval_jobs.values():
                job.remove()
            self.interval_jobs.clear()

            hh, mm = map(int, start_time_str.split(":"))
            tz = self.scheduler.timezone

            now = datetime.now(tz)
            first_run = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
            if first_run < now:
                first_run += timedelta(days=1)

            # Для каждого сервера создаём отдельную задачу с интервалом из конфиге
            for server in config.servers:
                interval_min = server.backup_interval
                job = self.scheduler.add_job(
                    self._create_and_send_interval_backup,
                    IntervalTrigger(minutes=interval_min, start_date=first_run),
                    id=f"interval_backup_{server.name}",
                    args=[server]
                )
                self.interval_jobs[server.name] = job

            logger.info(f"Started interval backups from {start_time_str} for each server with their intervals")
        except Exception as e:
            logger.error(f"Error scheduling interval backups: {e}", exc_info=True)

    async def _create_and_send_daily_backup(self):
        local = config.backup.local
        moscow_tz = zoneinfo.ZoneInfo("Europe/Moscow")
        for admin_id in config.bot.admin_id:
            for server in config.servers:
                try:
                    archive_path = backuper.create_backup(server, save_local=local)
                    if local:
                        # Когда сохраняем локально — отправляем с подробным комментарием
                        timestamp = archive_path.stat().st_mtime
                        dt_obj = datetime.fromtimestamp(timestamp, tz=moscow_tz)
                        dt_str = dt_obj.strftime("%d.%m.%Y %H:%M")

                        caption = (
                            f"<b>📦 Файл:</b> <code>{archive_path.name}</code>\n"
                            f"<b>🌐 IP сервера:</b> <code>{server.ip}</code>\n"
                            f"<b>📅 Дата и время:</b> <code>{dt_str}</code>\n"
                            f"<b>👤 Автор:</b> {AUTHOR}"
                        )
                        await bot.send_document(admin_id, FSInputFile(str(archive_path)), caption=caption)
                    else:
                        # Если не сохраняем локально — отправляем архив без комментария и отдельное сообщение
                        await bot.send_document(admin_id, FSInputFile(str(archive_path)))
                        await bot.send_message(admin_id, f"<b>✅ Создан ежедневный бэкап для сервера <code>{server.ip}</code></b>")
                        archive_path.unlink()
                except Exception as e:
                    logger.error(f"Error sending daily backup for server {server.name} to admin {admin_id}: {e}", exc_info=True)

    async def _create_and_send_interval_backup(self, server):
        local = False  # Для интервальных бэкапов не сохраняем локально
        moscow_tz = zoneinfo.ZoneInfo("Europe/Moscow")

        for admin_id in config.bot.admin_id:
            try:
                archive_path = backuper.create_backup(server, save_local=local)

                timestamp = archive_path.stat().st_mtime
                dt_obj = datetime.fromtimestamp(timestamp, tz=moscow_tz)
                dt_str = dt_obj.strftime("%d.%m.%Y %H:%M")

                caption = (
                    f"<b>📦 Файл:</b> <code>{archive_path.name}</code>\n"
                    f"<b>🌐 IP сервера:</b> <code>{server.ip}</code>\n"
                    f"<b>📅 Дата и время:</b> <code>{dt_str}</code>\n"
                    f"<b>👤 Автор:</b> {AUTHOR}"
                )

                await bot.send_document(admin_id, FSInputFile(str(archive_path)), caption=caption)
                archive_path.unlink()
            except Exception as e:
                logger.error(f"Error sending interval backup for server {server.name} to admin {admin_id}: {e}", exc_info=True)

scheduler_service = SchedulerService()

