"""
Phase 4: Paid course purchase flow.
Triggered from courses.py when user clicks 'خرید دوره'.
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from asgiref.sync import sync_to_async

from apps.telegram_bot.handlers.order_flow_helpers import COURSE_DELIVERY_TIME_NOTE
from apps.telegram_bot.handlers.payment_helpers import send_payment_instructions

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith('buy_course:'))
async def buy_course(callback: CallbackQuery):
    course_id = int(callback.data.split(':')[1])
    telegram_id = callback.from_user.id

    await callback.answer('⏳ در حال پردازش...')

    result = await _create_course_purchase(telegram_id, course_id)
    if result is None:
        await callback.message.answer('❌ دوره یافت نشد یا برای خرید در دسترس نیست.')
        return

    purchase, payment, success, url_or_error, course_title, amount = result

    header = (
        f'✅ درخواست خرید شما ثبت شد\n\n'
        f'کد خرید: <code>{purchase.purchase_code}</code>\n'
        f'دوره: {course_title}\n'
        f'مبلغ قابل پرداخت: {int(amount):,} تومان'
    )
    footer = (
        f'{COURSE_DELIVERY_TIME_NOTE}\n\n'
        f'وضعیت را می‌توانید از بخش «دوره‌های من» پیگیری کنید.'
    )
    await send_payment_instructions(
        callback.message, payment, success, url_or_error,
        header_text=header, footer_text=footer,
    )


@sync_to_async
def _create_course_purchase(telegram_id: int, course_id: int):
    from apps.users.services import get_or_create_telegram_user
    from apps.courses.models import Course
    from apps.courses.services import create_course_purchase
    from aiogram.types import User as TgUser

    try:
        from apps.users.models import TelegramUser
        user = TelegramUser.objects.get(telegram_id=telegram_id)
    except Exception:
        return None

    try:
        course = Course.objects.get(id=course_id, status='active', course_type='paid')
    except Course.DoesNotExist:
        return None

    purchase, payment, success, url_or_error = create_course_purchase(user, course)
    return purchase, payment, success, url_or_error, course.title, course.price_toman
