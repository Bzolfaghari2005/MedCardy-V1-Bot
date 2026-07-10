import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async

from apps.telegram_bot.filters import LabelFilter
from apps.telegram_bot.utils import get_status_label, aget_label

logger = logging.getLogger(__name__)
router = Router()


@router.message(LabelFilter('menu.favorites'))
async def favorites_handler(message: Message):
    telegram_id = message.from_user.id
    favorites = await _get_favorites(telegram_id)

    if not favorites:
        await message.answer(
            '❤️ <b>علاقه‌مندی‌ها</b>\n\nشما هنوز چیزی به علاقه‌مندی‌ها اضافه نکرده‌اید.',
            parse_mode='HTML'
        )
        return

    remove_prefix = await aget_label('btn.remove_favorite')
    text_lines = ['❤️ <b>علاقه‌مندی‌های من:</b>\n']
    buttons = []

    for fav in favorites:
        type_label = get_status_label('status.favorite', fav.object_type)
        title = fav.title_snapshot or f'{type_label} #{fav.object_id}'
        text_lines.append(f'• {type_label}: {title}')
        buttons.append([
            InlineKeyboardButton(
                text=f'{remove_prefix}: {title[:30]}',
                callback_data=f'rem_fav:{fav.object_type}:{fav.object_id}',
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
    await message.answer('\n'.join(text_lines), reply_markup=keyboard, parse_mode='HTML')


@sync_to_async
def _get_favorites(telegram_id: int):
    from apps.users.models import TelegramUser
    from apps.favorites.models import Favorite
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        return list(Favorite.objects.filter(user=user).order_by('-created_at')[:20])
    except TelegramUser.DoesNotExist:
        return []
