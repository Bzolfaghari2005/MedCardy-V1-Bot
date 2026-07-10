"""
Utility helpers for the Telegram bot.
All DB calls are synchronous but wrapped with sync_to_async when called from async handlers.
"""
import logging
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

_label_cache: dict[str, str] | None = None


# ─── Default labels (fallback when DB entry missing) ─────────────────────────

LABEL_DEFAULTS: dict[str, str] = {
    # Main menu
    'menu.courses': '📚 دوره‌ها / مجموعه پادکست‌ها',
    'menu.order': '🎙️ سفارش ساخت پادکست',
    'menu.my_courses': '📖 دوره‌های من',
    'menu.my_services': '🗂️ سرویس‌های من',
    'menu.favorites': '❤️ علاقه‌مندی‌ها',
    'menu.wallet': '💳 کیف پول',
    'menu.support': '💬 نظرات و پشتیبانی',
    'menu.help': '❓ راهنما',
    # Navigation buttons
    'btn.back': '🔙 بازگشت',
    'btn.main': '🏠 منوی اصلی',
    'btn.back_to_main': '🏠 بازگشت به منوی اصلی',
    'btn.view_other_courses': '📚 مشاهده دوره‌های دیگر',
    'btn.back_to_help': '🔙 بازگشت به راهنما',
    # Action buttons
    'btn.free_get': '✅ دریافت رایگان',
    'btn.buy': '💳 خرید دوره',
    'btn.add_favorite': '❤️ افزودن به علاقه‌مندی‌ها',
    'btn.remove_favorite': '💔 حذف از علاقه‌مندی‌ها',
    'btn.individual_order': '👤 سفارش فردی',
    'btn.group_order': '👥 سفارش گروهی',
    'btn.pricing_guide': '💰 راهنمای قیمت‌گذاری',
    'btn.charge_wallet': '💳 شارژ کیف پول',
    'btn.transactions': '📋 مشاهده تراکنش‌ها',
    'btn.pay_online': '💳 پرداخت آنلاین',
    'btn.submit_receipt': '📸 ارسال رسید پرداخت',
    'btn.pay_my_share': '💳 پرداخت سهم من',
    'btn.join_and_pay': '💳 پرداخت و عضویت در سفارش',
    'btn.skip': '⏭️ رد کردن',
    'btn.confirm_pay': '✅ تأیید و ثبت سفارش',
    'btn.cancel': '❌ انصراف',
    'btn.custom_amount': '💰 مبلغ دلخواه',
    'btn.view_my_orders': '📋 مشاهده کد سفارش‌های من',
    'btn.confirm_pages': '✅ تأیید',
    'btn.edit_pages': '✏️ ویرایش',
    # Wallet amounts
    'wallet.amount.100000': '۱۰۰,۰۰۰ تومان',
    'wallet.amount.250000': '۲۵۰,۰۰۰ تومان',
    'wallet.amount.500000': '۵۰۰,۰۰۰ تومان',
    'wallet.amount.1000000': '۱,۰۰۰,۰۰۰ تومان',
    # Service tiers
    'tier.review': 'نسخه مروری',
    'tier.full': 'آموزش کامل',
    'tier.review_inline': '📘 نسخه مروری',
    'tier.full_inline': '📗 آموزش کامل',
    # Course status
    'status.course.active': '✅ فعال',
    'status.course.inactive': '❌ غیرفعال',
    'status.course.coming_soon': '⏳ به‌زودی',
    'status.course_type.free': '🆓 رایگان',
    'status.course_type.paid': '✨',
    # Course purchase status
    'status.access.waiting_payment': '⏳ در انتظار پرداخت',
    'status.access.payment_failed': '❌ پرداخت ناموفق',
    'status.access.payment_verified': '✅ پرداخت تأیید شده',
    'status.access.waiting_personal_panel': '⏳ در انتظار ساخت پنل شخصی',
    'status.access.waiting_content_addition': '⏳ در انتظار افزودن محتوا به پنل شخصی',
    'status.access.delivered': '✅ آماده / تحویل داده شده',
    'status.access.problem': '⚠️ دارای مشکل',
    'status.access.cancelled': '❌ لغو شده',
    'status.payment.payment_created': 'ساخته شده',
    'status.payment.waiting_payment': '⏳ در انتظار پرداخت',
    'status.payment.paid': '✅ پرداخت موفق',
    'status.payment.failed': '❌ پرداخت ناموفق',
    'status.payment.cancelled': '❌ لغو شده',
    'status.payment.refunded': '↩️ مسترد شده',
    # Order status
    'status.order.pending_payment': '⏳ در انتظار پرداخت',
    'status.order.waiting_group_members': '⏳ در انتظار تکمیل اعضا',
    'status.order.waiting_admin_review': '⏳ در انتظار بررسی ادمین',
    'status.order.in_production': '🎙️ در حال تولید',
    'status.order.delivered': '✅ تحویل داده شده',
    'status.order.cancelled': '❌ لغو شده',
    'status.order.problem': '⚠️ دارای مشکل',
    'status.production.not_started': 'شروع نشده',
    'status.production.waiting_admin_review': '⏳ در انتظار بررسی ادمین',
    'status.production.in_progress': '🎙️ در حال تولید',
    'status.production.done': '✅ تولید شده',
    'status.member.payment_created': 'ساخته شده',
    'status.member.waiting_payment': '⏳ در انتظار پرداخت',
    'status.member.paid': '✅ پرداخت موفق',
    'status.member.failed': '❌ پرداخت ناموفق',
    'status.member.cancelled': '❌ لغو شده',
    # Wallet transaction types
    'status.wallet.charge': '⬆️ شارژ',
    'status.wallet.purchase': '⬇️ خرید',
    'status.wallet.refund': '↩️ استرداد',
    'status.wallet.admin_adjustment': '🔧 تعدیل ادمین',
    # Favorites
    'status.favorite.course': 'دوره',
    'status.favorite.service_order': 'سفارش',
}

WALLET_AMOUNT_KEYS = {
    'wallet.amount.100000': 100_000,
    'wallet.amount.250000': 250_000,
    'wallet.amount.500000': 500_000,
    'wallet.amount.1000000': 1_000_000,
}


def invalidate_label_cache() -> None:
    global _label_cache
    _label_cache = None


def _load_label_cache() -> dict[str, str]:
    from apps.bot_messages.models import BotLabel
    return {
        lbl.key: lbl.text
        for lbl in BotLabel.objects.filter(is_active=True)
    }


def get_label(key: str, default: str = '') -> str:
    global _label_cache
    if _label_cache is None:
        _label_cache = _load_label_cache()
    fallback = default or LABEL_DEFAULTS.get(key, '')
    return _label_cache.get(key, fallback)


async def aget_label(key: str, default: str = '') -> str:
    return await sync_to_async(get_label)(key, default)


async def message_matches_labels(text: str | None, *keys: str) -> bool:
    if not text:
        return False
    for key in keys:
        if text == await aget_label(key):
            return True
    return False


async def is_label_text(text: str | None, key: str) -> bool:
    if not text:
        return False
    return text == await aget_label(key)


async def is_cancel_nav(text: str | None) -> bool:
    return await message_matches_labels(text, 'btn.back', 'btn.back_to_main')


async def aget_wallet_amounts() -> dict[str, int]:
    result = {}
    for key, amount in WALLET_AMOUNT_KEYS.items():
        result[await aget_label(key)] = amount
    return result


def get_status_label(prefix: str, code: str) -> str:
    return get_label(f'{prefix}.{code}', code)


async def aget_status_label(prefix: str, code: str) -> str:
    return await aget_label(f'{prefix}.{code}', code)


# ─── Bot message helpers ─────────────────────────────────────────────────────

def get_bot_message(key: str, default: str = '') -> str:
    from apps.bot_messages.models import BotMessage
    try:
        msg = BotMessage.objects.get(key=key, is_active=True)
        return msg.text
    except BotMessage.DoesNotExist:
        return default


def get_setting(key: str, default: str = '') -> str:
    from apps.settings_app.models import Setting
    try:
        return Setting.objects.get(key=key).value
    except Setting.DoesNotExist:
        return default


def is_payment_gateway_enabled() -> bool:
    return get_setting('enable_payment_gateway', 'false').lower() in ('true', '1', 'yes')


def format_manual_payment_instructions(payment_code: str, amount_toman) -> str:
    from apps.telegram_bot.payment_messages import build_manual_payment_instructions
    return build_manual_payment_instructions(payment_code, amount_toman)


async def ais_payment_gateway_enabled() -> bool:
    return await sync_to_async(is_payment_gateway_enabled)()


async def aformat_manual_payment_instructions(payment_code: str, amount_toman) -> str:
    return await sync_to_async(format_manual_payment_instructions)(payment_code, amount_toman)


async def aget_bot_message(key: str, default: str = '') -> str:
    return await sync_to_async(get_bot_message)(key, default)


async def aget_setting(key: str, default: str = '') -> str:
    return await sync_to_async(get_setting)(key, default)


async def notify_admins(bot, text: str, reply_markup=None) -> None:
    """Send a message to all configured admin Telegram IDs."""
    from django.conf import settings

    for admin_id in settings.ADMIN_TELEGRAM_IDS:
        try:
            await bot.send_message(admin_id, text, reply_markup=reply_markup, parse_mode='HTML')
        except Exception as exc:
            logger.warning(f'Failed to notify admin {admin_id}: {exc}')


# ─── Format helpers ───────────────────────────────────────────────────────────

def format_toman(amount) -> str:
    """Format amount as Persian-style toman string."""
    return f'{int(amount):,} تومان'


def persian_number(n: int) -> str:
    """Convert integer to Persian digit string."""
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    return ''.join(persian_digits[int(d)] for d in str(n))


def tier_label(tier: str) -> str:
    from apps.orders.models import ServiceOrder
    if tier == ServiceOrder.TIER_REVIEW:
        return get_label('tier.review')
    if tier == ServiceOrder.TIER_FULL:
        return get_label('tier.full')
    return tier
