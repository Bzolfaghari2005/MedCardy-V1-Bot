import logging
from aiogram import Router, F
from aiogram.types import Message
from asgiref.sync import sync_to_async

from apps.telegram_bot.filters import LabelFilter
from apps.telegram_bot.utils import get_status_label

logger = logging.getLogger(__name__)
router = Router()


@router.message(LabelFilter('menu.my_courses'))
async def my_courses(message: Message):
    telegram_id = message.from_user.id
    purchases = await _get_user_purchases(telegram_id)

    if not purchases:
        await message.answer(
            '📚 <b>دوره‌های من</b>\n\n'
            '📭 هنوز دوره‌ای خریداری نکردی.\n\n'
            'از منوی «دوره‌ها» می‌تونی دوره‌های موجود رو ببینی.',
            parse_mode='HTML'
        )
        return

    text_lines = ['📚 <b>دوره‌های من:</b>\n']
    for idx, purchase in enumerate(purchases, 1):
        course_title = purchase.course.title
        purchase_code = purchase.purchase_code
        payment_status = get_status_label('status.payment', purchase.payment_status)
        access_status = get_status_label('status.access', purchase.access_status)

        lines = [
            f'<b>{idx}. 🎧 {course_title}</b>',
            f'🔑 کد خرید: <code>{purchase_code}</code>',
            f'💳 وضعیت پرداخت: {payment_status}',
            f'◉ وضعیت دسترسی: {access_status}',
        ]

        if purchase.personal_panel:
            if purchase.personal_panel.channel_link:
                lines.append(f'📺 پنل شخصی: {purchase.personal_panel.channel_link}')
            else:
                lines.append('📺 پنل شخصی: ⏳ در حال ساخت')

        text_lines.append('\n'.join(lines))
        text_lines.append('')

    await message.answer('\n'.join(text_lines), parse_mode='HTML')


@sync_to_async
def _get_user_purchases(telegram_id: int):
    from apps.users.models import TelegramUser
    from apps.courses.models import CoursePurchase
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        return list(
            CoursePurchase.objects.filter(user=user)
            .select_related('course', 'personal_panel')
            .order_by('-created_at')[:20]
        )
    except TelegramUser.DoesNotExist:
        return []
