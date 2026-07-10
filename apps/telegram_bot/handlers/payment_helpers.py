"""Shared helpers for payment UI in Telegram bot handlers."""
from asgiref.sync import sync_to_async
from aiogram.types import Message

from apps.telegram_bot.keyboards import manual_payment_keyboard, payment_link_keyboard, main_menu_keyboard
from apps.telegram_bot.payment_messages import (
    build_gateway_payment_instructions,
    build_manual_payment_instructions,
    build_payment_request_failed_message,
)
from apps.telegram_bot.utils import ais_payment_gateway_enabled


async def send_payment_instructions(
    message: Message,
    payment,
    success: bool,
    url_or_code: str,
    header_text: str = '',
    footer_text: str = '',
):
    """Send gateway link or manual payment instructions based on settings."""
    if not success:
        failed_text = await sync_to_async(build_payment_request_failed_message)()
        await message.answer(failed_text, reply_markup=await main_menu_keyboard())
        return

    gateway_enabled = await ais_payment_gateway_enabled()
    parts = []
    if header_text:
        parts.append(header_text)
    if gateway_enabled:
        gateway_text = await sync_to_async(build_gateway_payment_instructions)(
            payment.payment_code, payment.amount_toman,
        )
        parts.append(gateway_text)
        if footer_text:
            parts.append(footer_text)
        await message.answer(
            '\n\n'.join(parts),
            parse_mode='HTML',
            reply_markup=await payment_link_keyboard(url_or_code),
        )
    else:
        if header_text:
            parts.append('')
        manual_text = await sync_to_async(build_manual_payment_instructions)(
            payment.payment_code, payment.amount_toman,
        )
        parts.append(manual_text)
        if footer_text:
            parts.append(footer_text)
        await message.answer(
            '\n\n'.join(parts),
            parse_mode='HTML',
            reply_markup=await manual_payment_keyboard(payment.id),
        )
