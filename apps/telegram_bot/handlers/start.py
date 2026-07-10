import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from asgiref.sync import sync_to_async

from apps.telegram_bot.keyboards import main_menu_keyboard
from apps.telegram_bot.utils import aget_bot_message

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    args = message.text.split()
    deep_link_arg = args[1] if len(args) > 1 else None

    user = await _get_or_create_user(message)

    # Handle deep link for group order join
    if deep_link_arg and deep_link_arg.startswith('G'):
        from apps.telegram_bot.handlers.orders_group import handle_group_join_deep_link
        await handle_group_join_deep_link(message, user, deep_link_arg)
        return

    welcome_text = await aget_bot_message(
        'start_message',
        default=(
            '✨ سلام، خوش اومدی به MedCardy!\n\n'
            '🎙️ MedCardy جزوه‌های پزشکی رو به پادکست‌های آموزشی حرفه‌ای تبدیل می‌کنه.\n\n'
            'از منوی پایین می‌تونی:\n'
            '📚 دوره‌های آماده رو مشاهده کنی\n'
            '🎙️ جزوه‌ات رو برای ساخت پادکست اختصاصی بفرستی\n'
            '👥 با همکلاسی‌هات سفارش گروهی بدی\n'
            '💳 کیف پولت رو مدیریت کنی\n\n'
            '⬇️ یه گزینه انتخاب کن:'
        ),
    )
    await message.answer(welcome_text, reply_markup=await main_menu_keyboard())


@sync_to_async
def _get_or_create_user(message: Message):
    from apps.users.services import get_or_create_telegram_user
    tg_user = message.from_user
    return get_or_create_telegram_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name or '',
        last_name=tg_user.last_name,
    )
