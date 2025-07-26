import logging
from aiogram.filters import BaseFilter
from aiogram.types import Message
from config_reader import config

logger = logging.getLogger(__name__)

class IsAdminFilter(BaseFilter):
    async def __call__(self, msg: Message) -> bool:
        try:
            return msg.from_user.id in config.bot.admin_id
        except Exception as e:
            logger.error(f"Ошибка при проверке админа: {e}", exc_info=True)
            return False

is_admin = IsAdminFilter()

