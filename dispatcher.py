import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update
from config_reader import config

logger = logging.getLogger(__name__)

bot = Bot(token=config.bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def global_error_handler(update: Update, exception: Exception):
    logger.error(f"Глобальная ошибка: {exception}", exc_info=True)
    if update and update.message:
        try:
            await update.message.answer("<b>❌ Произошла внутренняя ошибка, попробуйте позже.</b>")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения об ошибке: {e}", exc_info=True)

dp.errors.register(global_error_handler)

