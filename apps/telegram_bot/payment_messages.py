"""
Payment-related messages and settings loaded from Django Admin.

Settings (تنظیمات): payment_card_number, payment_card_holder, ...
Bot messages (پیام‌های بات): manual_payment_instructions, receipt_received, ...

Placeholders in bot messages:
  {payment_code} {amount} {amount_copy} {card_number} {card_number_copy}
  {card_holder} {bank_name} {sheba_number} {transfer_note} {review_hours}

مقادیر داخل <code> در تلگرام با یک لمس کپی می‌شوند.
"""
from apps.telegram_bot.utils import format_toman, get_bot_message, get_setting


def render_message_template(text: str, **placeholders) -> str:
    for key, value in placeholders.items():
        text = text.replace('{' + key + '}', str(value))
    return text


def get_payment_config() -> dict:
    card_raw = get_setting('payment_card_number', '')
    return {
        'card_number': card_raw or '—',
        'card_number_copy': _digits_only(card_raw) or '—',
        'card_holder': get_setting('payment_card_holder', '') or '—',
        'bank_name': get_setting('payment_bank_name', '') or '—',
        'sheba_number': get_setting('payment_sheba_number', '') or '—',
        'transfer_note': get_setting(
            'payment_transfer_note',
            'حتماً کد پرداخت را در توضیحات واریز بنویسید.',
        ),
        'review_hours': get_setting('payment_review_hours', '24'),
    }


def _digits_only(value: str) -> str:
    return ''.join(ch for ch in str(value) if ch.isdigit())


def _amount_copy(amount_toman) -> str:
    return str(int(amount_toman))


def _render_payment_message(key: str, default: str, **extra) -> str:
    config = get_payment_config()
    merged = {**config, **extra}
    template = get_bot_message(key, default)
    return render_message_template(template, **merged)


def build_manual_payment_instructions(payment_code: str, amount_toman) -> str:
    default = (
        '💳 <b>راهنمای پرداخت کارت‌به‌کارت</b>\n\n'
        '🔑 کد پرداخت: <code>{payment_code}</code>\n'
        '💰 مبلغ: <code>{amount_copy}</code> تومان\n\n'
        '🏦 شماره کارت: <code>{card_number_copy}</code>\n'
        '👤 به نام: {card_holder}\n'
        '🏛️ بانک: {bank_name}\n'
        '🔢 شبا: {sheba_number}\n\n'
        '⚠️ <i>{transfer_note}</i>\n\n'
        '📸 سپس با دکمه زیر، عکس رسید پرداخت را ارسال کنید.\n'
        '<i>👆 روی مبلغ و شماره کارت بزن تا کپی بشه.</i>'
    )
    return _render_payment_message(
        'manual_payment_instructions',
        default,
        payment_code=payment_code,
        amount=format_toman(amount_toman),
        amount_copy=_amount_copy(amount_toman),
    )


def build_receipt_upload_prompt(payment_code: str, amount_toman) -> str:
    default = (
        '📸 <b>ارسال رسید پرداخت</b>\n\n'
        '🔑 کد پرداخت: <code>{payment_code}</code>\n'
        '💰 مبلغ: <code>{amount_copy}</code> تومان\n\n'
        'لطفاً <b>عکس یا فایل رسید</b> واریز را ارسال کن.\n'
        '<i>برای لغو: دکمه بازگشت یا /start</i>'
    )
    return _render_payment_message(
        'receipt_upload_prompt',
        default,
        payment_code=payment_code,
        amount=format_toman(amount_toman),
        amount_copy=_amount_copy(amount_toman),
    )


def build_receipt_received_message(payment_code: str) -> str:
    default = (
        '✅ <b>رسید دریافت شد!</b>\n\n'
        '🔑 کد پرداخت: <code>{payment_code}</code>\n'
        '◉ وضعیت: ⏳ در انتظار تأیید ادمین\n\n'
        '<i>بررسی و تأیید پرداخت ممکن است تا {review_hours} ساعت طول بکشد. '
        'نتیجه به شما اطلاع داده می‌شود.</i>'
    )
    return _render_payment_message(
        'receipt_received',
        default,
        payment_code=payment_code,
    )


def build_payment_request_failed_message() -> str:
    default = (
        '❌ ساخت درخواست پرداخت با مشکل مواجه شد.\n\n'
        'چند دقیقه صبر کن و دوباره تلاش کن یا با پشتیبانی در تماس باش.'
    )
    return get_bot_message('payment_request_failed', default)


def build_gateway_payment_instructions(payment_code: str, amount_toman) -> str:
    default = (
        '🔐 برای پرداخت آنلاین از طریق درگاه امن زیبال روی دکمه زیر بزن.\n\n'
        '🔑 کد پرداخت: <code>{payment_code}</code>\n'
        '💰 مبلغ: <code>{amount_copy}</code> تومان'
    )
    return _render_payment_message(
        'gateway_payment_instructions',
        default,
        payment_code=payment_code,
        amount=format_toman(amount_toman),
        amount_copy=_amount_copy(amount_toman),
    )


def build_receipt_rejected_message(payment_code: str, amount_toman, reason: str = '') -> str:
    reason_text = f'\n\n📝 دلیل: {reason}' if reason else ''
    default = (
        '❌ <b>رسید پرداخت رد شد</b>\n\n'
        '🔑 کد پرداخت: <code>{payment_code}</code>\n'
        '💰 مبلغ: <code>{amount_copy}</code> تومان{reason}\n\n'
        'می‌تونی دوباره واریز کنی و رسید جدید ارسال کنی.\n'
        '💬 برای راهنمایی با پشتیبانی تماس بگیر: @MedCardySupport'
    )
    return _render_payment_message(
        'receipt_rejected',
        default,
        payment_code=payment_code,
        amount=format_toman(amount_toman),
        amount_copy=_amount_copy(amount_toman),
        reason=reason_text,
    )
