import asyncio
import logging
from handlers import (
    start_router,
    help_router,
    backup_router,
    send_backup_router,
    clear_backups_router,
    list_backup_router,
)
from dispatcher import dp, bot
from scheduler import scheduler_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

dp.include_routers(
    start_router,
    help_router,
    backup_router,
    send_backup_router,
    clear_backups_router,
    list_backup_router
)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    scheduler_service.start()
    logging.info("[INFO] Scheduler started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

