"""
Telegram notification service for payment-related events.
Called after Zibal callback verification to send bot messages.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram_message(telegram_id: int, text: str, parse_mode: str = 'HTML', reply_markup=None) -> bool:
    """
    Send a message to a Telegram user via Bot API.
    Returns True on success, False on failure.
    Does NOT raise exceptions — failures are logged only.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning('TELEGRAM_BOT_TOKEN not set; cannot send notification.')
        return False

    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {
        'chat_id': telegram_id,
        'text': text,
        'parse_mode': parse_mode,
    }
    if reply_markup is not None:
        payload['reply_markup'] = reply_markup
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            return True
        else:
            logger.warning(f'Telegram sendMessage failed: {resp.status_code} {resp.text}')
            return False
    except Exception as exc:
        logger.error(f'Telegram sendMessage exception for chat_id={telegram_id}: {exc}')
        return False


def send_telegram_photo(telegram_id: int, photo_path: str, caption: str = '', reply_markup=None) -> bool:
    """Send a photo to a Telegram user via Bot API."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning('TELEGRAM_BOT_TOKEN not set; cannot send photo.')
        return False

    url = f'https://api.telegram.org/bot{token}/sendPhoto'
    try:
        with open(photo_path, 'rb') as photo_file:
            files = {'photo': photo_file}
            data = {'chat_id': str(telegram_id), 'parse_mode': 'HTML'}
            if caption:
                data['caption'] = caption
            if reply_markup is not None:
                import json
                data['reply_markup'] = json.dumps(reply_markup)
            resp = requests.post(url, data=data, files=files, timeout=15)
        if resp.status_code == 200:
            return True
        logger.warning(f'Telegram sendPhoto failed: {resp.status_code} {resp.text}')
        return False
    except Exception as exc:
        logger.error(f'Telegram sendPhoto exception for chat_id={telegram_id}: {exc}')
        return False


def _payment_for_type_label(payment) -> str:
    labels = {
        'course_purchase': 'خرید دوره',
        'individual_service_order': 'سفارش فردی',
        'group_order_member': 'عضویت گروهی',
        'wallet_charge': 'شارژ کیف پول',
    }
    return labels.get(payment.payment_for_type, payment.payment_for_type)


def notify_admins_pending_receipt(payment) -> None:
    """Notify admins that a payment receipt needs review."""
    if not settings.ADMIN_TELEGRAM_IDS:
        return

    username = f'@{payment.user.username}' if payment.user.username else '—'
    text = (
        f'💳 <b>رسید پرداخت جدید</b>\n\n'
        f'🔑 کد: <code>{payment.payment_code}</code>\n'
        f'📂 نوع: {_payment_for_type_label(payment)}\n'
        f'💰 مبلغ: <b>{int(payment.amount_toman):,} تومان</b>\n'
        f'👤 کاربر: {payment.user.user_code} ({username})'
    )
    reply_markup = {
        'inline_keyboard': [
            [
                {'text': '✅ تأیید', 'callback_data': f'admin:approve_payment:{payment.id}'},
                {'text': '❌ رد', 'callback_data': f'admin:reject_payment:{payment.id}'},
            ],
            [{'text': '👁️ جزئیات', 'callback_data': f'admin:payment:{payment.id}'}],
        ],
    }
    for admin_id in settings.ADMIN_TELEGRAM_IDS:
        if payment.receipt_file:
            try:
                send_telegram_photo(
                    admin_id,
                    payment.receipt_file.path,
                    caption=text,
                    reply_markup=reply_markup,
                )
            except Exception as exc:
                logger.warning(f'Failed to send receipt photo to admin {admin_id}: {exc}')
                send_telegram_message(admin_id, text, reply_markup=reply_markup)
        else:
            send_telegram_message(admin_id, text, reply_markup=reply_markup)


def notify_receipt_rejected(payment) -> bool:
    from apps.telegram_bot.payment_messages import build_receipt_rejected_message
    text = build_receipt_rejected_message(
        payment.payment_code,
        payment.amount_toman,
        payment.receipt_rejected_reason,
    )
    reply_markup = {
        'inline_keyboard': [[
            {'text': '📸 ارسال رسید پرداخت', 'callback_data': f'pay:submit_receipt:{payment.id}'},
        ]],
    }
    return send_telegram_message(payment.user.telegram_id, text, reply_markup=reply_markup)


def notify_admins_new_order_waiting_review(order) -> None:
    """Notify all admins that a service order needs review."""
    if not settings.ADMIN_TELEGRAM_IDS:
        return

    type_label = 'فردی' if order.order_type == 'individual' else 'گروهی'
    username = f'@{order.creator_user.username}' if order.creator_user.username else '—'
    text = (
        f'📬 <b>سفارش جدید در انتظار بررسی</b>\n\n'
        f'🔖 کد: <code>{order.order_code}</code>\n'
        f'📂 نوع: {type_label}\n'
        f'📌 عنوان: {order.title}\n'
        f'👤 کاربر: {order.creator_user.user_code} ({username})'
    )
    reply_markup = {
        'inline_keyboard': [[
            {'text': '👁️ مشاهده سفارش', 'callback_data': f'admin:order:{order.id}'},
        ]],
    }
    for admin_id in settings.ADMIN_TELEGRAM_IDS:
        send_telegram_message(admin_id, text, reply_markup=reply_markup)


def notify_payment_success_course(payment, purchase) -> bool:
    from apps.users.models import PersonalPanel
    panel = purchase.personal_panel
    panel_status_text = ''
    if panel:
        if panel.status == PersonalPanel.STATUS_ACTIVE and panel.channel_link:
            panel_status_text = f'\n\n🔗 لینک پنل شخصی: {panel.channel_link}'
        elif panel.status == PersonalPanel.STATUS_NEEDS_CREATION:
            panel_status_text = '\n\n⏳ وضعیت پنل: در حال آماده‌سازی'
    else:
        panel_status_text = '\n\n⏳ وضعیت پنل: در حال آماده‌سازی'

    text = (
        f'🎉 <b>پرداخت موفق!</b>\n\n'
        f'🎧 دوره «{purchase.course.title}» به بخش «دوره‌های من» اضافه شد.\n\n'
        f'📱 این دوره داخل پنل شخصی MedCardy شما قرار می‌گیره.\n'
        f'<i>⏳ اگر پنل ندارید، ظرف چند ساعت براتون ساخته می‌شه؛ '
        f'اگر پنل دارید، دوره ظرف چند ساعت اضافه می‌شه. لطفاً کمی صبر کنید 🙏</i>'
        f'{panel_status_text}'
    )
    return send_telegram_message(payment.user.telegram_id, text)


def notify_payment_success_individual_order(payment, order) -> bool:
    text = (
        f'🎉 <b>پرداخت موفق!</b>\n\n'
        f'🔖 کد سفارش: <code>{order.order_code}</code>\n'
        f'◉ وضعیت: ⏳ در انتظار بررسی و تولید\n\n'
        f'📱 خروجی این سفارش داخل پنل شخصی MedCardy شما قرار می‌گیره.\n'
        f'<i>اگر پنل شخصی هنوز ساخته نشده باشه، توسط تیم ما ساخته می‌شه.</i>\n\n'
        f'<i>⏰ آماده‌سازی ممکنه ۴۸ ساعت یا بیشتر طول بکشه — هر چه زودتر سفارش دادید، زودتر تحویل می‌گیرید.</i>\n\n'
        f'💡 از بخش «سرویس‌های من» می‌تونی وضعیت سفارش رو پیگیری کنی.'
    )
    return send_telegram_message(payment.user.telegram_id, text)


def notify_payment_success_group_member(payment, member, order) -> bool:
    text = (
        f'🎉 <b>پرداخت موفق!</b>\n\n'
        f'✅ شما به سفارش گروهی اضافه شدید!\n\n'
        f'🔖 کد سفارش: <code>{order.order_code}</code>\n'
        f'📌 عنوان: {order.title}\n'
        f'👥 اعضای پرداخت موفق: {order.paid_members_count} از {order.min_group_members} نفر\n\n'
        f'💡 از بخش «سرویس‌های من» می‌تونی وضعیت سفارش رو پیگیری کنی.'
    )
    return send_telegram_message(payment.user.telegram_id, text)


def notify_group_minimum_reached(order) -> None:
    """Notify all paid members that minimum group count is reached."""
    text = (
        f'🚀 <b>سفارش گروهی تکمیل شد!</b>\n\n'
        f'🎊 حداقل تعداد لازم برای سفارش شما تکمیل شد.\n\n'
        f'🔖 کد سفارش: <code>{order.order_code}</code>\n'
        f'📌 عنوان: {order.title}\n\n'
        f'🎙️ سفارش وارد مرحله بررسی و تولید شد.\n'
        f'<i>⏰ آماده‌سازی ممکنه ۴۸ ساعت یا بیشتر طول بکشه — لطفاً صبور باشید.</i>\n\n'
        f'💡 از بخش «سرویس‌های من» می‌تونی وضعیت رو پیگیری کنی.'
    )
    from apps.orders.models import ServiceOrderMember
    paid_members = ServiceOrderMember.objects.filter(
        order=order, status=ServiceOrderMember.STATUS_PAID
    ).select_related('user')
    for member in paid_members:
        send_telegram_message(member.user.telegram_id, text)


def notify_wallet_charge_success(payment) -> bool:
    from apps.users.models import TelegramUser
    user = TelegramUser.objects.get(id=payment.user_id)
    text = (
        f'🎉 <b>کیف پول شارژ شد!</b>\n\n'
        f'💰 مبلغ شارژ: <b>{int(payment.amount_toman):,} تومان</b>\n'
        f'💳 موجودی جدید: <b>{int(user.wallet_balance):,} تومان</b>'
    )
    return send_telegram_message(payment.user.telegram_id, text)


def notify_payment_failed(payment) -> bool:
    text = (
        f'⚠️ <b>پرداخت ناموفق</b>\n\n'
        f'🔑 کد پرداخت: <code>{payment.payment_code}</code>\n\n'
        f'<i>اگر مبلغی از حساب شما کم شده باشه، طبق قوانین بانکی ظرف ۷۲ ساعت به حسابت برمی‌گرده.</i>\n\n'
        f'💬 برای راهنمایی با پشتیبانی MedCardy تماس بگیر: @MedCardySupport'
    )
    return send_telegram_message(payment.user.telegram_id, text)


def notify_payment_cancelled_individual_order(payment, order) -> bool:
    text = (
        f'❌ <b>پرداخت انجام نشد</b>\n\n'
        f'پرداخت سفارش زیر لغو شد:\n\n'
        f'🔖 کد سفارش: <code>{order.order_code}</code>\n'
        f'📌 عنوان: {order.title}\n'
        f'💰 مبلغ: <b>{int(order.final_price_per_user_toman):,} تومان</b>\n\n'
        f'این سفارش لغو شده. برای ثبت مجدد، از منوی «ثبت سفارش» اقدام کن.\n\n'
        f'<i>اگر مبلغی از حساب شما کم شده باشه، طبق قوانین بانکی ظرف ۷۲ ساعت برمی‌گرده.</i>\n\n'
        f'💬 برای راهنمایی با پشتیبانی تماس بگیر: @MedCardySupport'
    )
    return send_telegram_message(payment.user.telegram_id, text)


def notify_payment_cancelled_group_member(payment, member, order) -> bool:
    text = (
        f'❌ <b>پرداخت انجام نشد</b>\n\n'
        f'پرداخت عضویت در سفارش گروهی زیر لغو شد:\n\n'
        f'🔖 کد سفارش: <code>{order.order_code}</code>\n'
        f'📌 عنوان: {order.title}\n'
        f'💰 مبلغ: <b>{int(order.final_price_per_user_toman):,} تومان</b>\n\n'
        f'اگه می‌خوای مجدداً به این سفارش گروهی بپیوندی، از لینک ورود گروه استفاده کن:\n'
        f'{order.group_join_link}\n\n'
        f'<i>اگر مبلغی از حساب شما کم شده باشه، طبق قوانین بانکی ظرف ۷۲ ساعت برمی‌گرده.</i>\n\n'
        f'💬 برای راهنمایی با پشتیبانی تماس بگیر: @MedCardySupport'
    )
    return send_telegram_message(payment.user.telegram_id, text)


def notify_order_cancelled_with_refund(user, order, amount_toman: int) -> bool:
    from apps.users.models import TelegramUser
    user = TelegramUser.objects.get(id=user.id)
    text = (
        f'❌ <b>سفارش لغو شد</b>\n\n'
        f'🔖 کد سفارش: <code>{order.order_code}</code>\n'
        f'📌 عنوان: {order.title}\n\n'
        f'متأسفانه امکان ساخت یا تکمیل این سفارش وجود نداشت و سفارش توسط تیم MedCardy لغو شد.\n\n'
        f'💰 مبلغ <b>{amount_toman:,} تومان</b> به کیف پول شما برگشت داده شد.\n'
        f'💳 موجودی جدید: <b>{int(user.wallet_balance):,} تومان</b>\n\n'
        f'برای ثبت سفارش جدید، از منوی «ثبت سفارش» اقدام کن.'
    )
    return send_telegram_message(user.telegram_id, text)


def notify_payment_cancelled_course(payment, purchase) -> bool:
    text = (
        f'❌ <b>پرداخت انجام نشد</b>\n\n'
        f'پرداخت خرید دوره زیر لغو شد:\n\n'
        f'🔖 کد خرید: <code>{purchase.purchase_code}</code>\n'
        f'🎧 دوره: {purchase.course.title}\n'
        f'💰 مبلغ: <b>{int(purchase.course.price_toman):,} تومان</b>\n\n'
        f'برای خرید مجدد این دوره، از بخش «دوره‌ها» اقدام کن.\n\n'
        f'<i>اگر مبلغی از حساب شما کم شده باشه، طبق قوانین بانکی ظرف ۷۲ ساعت برمی‌گرده.</i>\n\n'
        f'💬 برای راهنمایی با پشتیبانی تماس بگیر: @MedCardySupport'
    )
    return send_telegram_message(payment.user.telegram_id, text)
