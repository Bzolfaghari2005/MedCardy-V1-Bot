"""
Aiogram bot setup.
Creates Bot, Dispatcher, and registers all routers.
"""
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message, TelegramObject
from django.conf import settings

logger = logging.getLogger(__name__)


class MaintenanceMiddleware(BaseMiddleware):
    """Block non-admin users when maintenance_mode is enabled."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        from apps.telegram_bot.utils import aget_setting

        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if user and user.id in settings.ADMIN_TELEGRAM_IDS:
            return await handler(event, data)

        maintenance_mode = await aget_setting('maintenance_mode', 'false')
        is_maintenance = maintenance_mode.lower() in ('true', '1', 'yes')
        if not is_maintenance:
            return await handler(event, data)

        msg = await aget_setting(
            'maintenance_message',
            'بات در حال به‌روزرسانی است. لطفاً کمی صبر کنید.',
        )
        if isinstance(event, Message):
            await event.answer(msg)
        elif isinstance(event, CallbackQuery):
            await event.answer('بات در حالت تعمیر است.', show_alert=True)
        return None


def create_bot() -> Bot:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise ValueError('TELEGRAM_BOT_TOKEN is not set in .env')
    return Bot(token=token)


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(MaintenanceMiddleware())
    dp.callback_query.middleware(MaintenanceMiddleware())
    _register_routers(dp)
    return dp


def _register_routers(dp: Dispatcher):
    from apps.telegram_bot.handlers import (
        admin_panel, start, support, help, courses, buy_course,
        my_courses, my_services, favorites,
        orders_individual, orders_group, wallet, payment_receipt,
    )

    # Order matters: more specific handlers first
    dp.include_router(admin_panel.router)
    dp.include_router(start.router)
    dp.include_router(payment_receipt.router)
    dp.include_router(wallet.router)
    dp.include_router(orders_individual.router)
    dp.include_router(orders_group.router)
    dp.include_router(buy_course.router)
    dp.include_router(courses.router)
    dp.include_router(my_courses.router)
    dp.include_router(my_services.router)
    dp.include_router(favorites.router)
    dp.include_router(help.router)
    dp.include_router(support.router)

    logger.info('All bot routers registered.')
