"""
Payment receipt upload handlers.
Users upload proof of card-to-card payment for admin approval.
"""
import logging
from pathlib import Path

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.core.files import File

from apps.telegram_bot.states.payment_states import PaymentReceiptStates
from apps.telegram_bot.keyboards import main_menu_keyboard
from apps.telegram_bot.services.telegram_files import download_telegram_file
from apps.telegram_bot.payment_messages import (
    build_receipt_received_message,
    build_receipt_upload_prompt,
)
from apps.telegram_bot.utils import is_cancel_nav, is_label_text

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith('pay:submit_receipt:'))
async def cb_submit_receipt(callback: CallbackQuery, state: FSMContext):
    payment_id = int(callback.data.split(':')[-1])
    payment = await _get_user_payment(callback.from_user.id, payment_id)
    if not payment:
        await callback.answer('پرداخت یافت نشد یا متعلق به شما نیست.', show_alert=True)
        return

    if payment.status == 'receipt_submitted':
        await callback.answer('رسید قبلاً ارسال شده و در انتظار تأیید ادمین است.', show_alert=True)
        return

    if payment.status == 'verified':
        await callback.answer('این پرداخت قبلاً تأیید شده است.', show_alert=True)
        return

    await state.set_state(PaymentReceiptStates.waiting_receipt)
    await state.update_data(payment_id=payment_id)
    prompt_text = await sync_to_async(build_receipt_upload_prompt)(
        payment.payment_code, payment.amount_toman,
    )
    await callback.message.answer(prompt_text, parse_mode='HTML')
    await callback.answer()


@router.message(PaymentReceiptStates.waiting_receipt, F.photo | F.document)
async def receive_receipt(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    payment_id = data.get('payment_id')
    if not payment_id:
        await state.clear()
        await message.answer('❌ خطا در پردازش. لطفاً دوباره تلاش کن.')
        return

    if message.photo:
        file_id = message.photo[-1].file_id
        file_name = f'receipt_{payment_id}.jpg'
    else:
        file_id = message.document.file_id
        file_name = message.document.file_name or f'receipt_{payment_id}'

    local_path = await download_telegram_file(bot, file_id, file_name)
    result = await _submit_receipt(message.from_user.id, payment_id, local_path, file_name)
    await state.clear()

    try:
        local_path.unlink(missing_ok=True)
    except OSError:
        pass

    if not result:
        await message.answer(
            '❌ ارسال رسید با مشکل مواجه شد. لطفاً دوباره تلاش کن.',
            reply_markup=await main_menu_keyboard(),
        )
        return

    payment, success, msg = result
    if not success:
        await message.answer(f'⚠️ {msg}')
        return

    received_text = await sync_to_async(build_receipt_received_message)(payment.payment_code)
    await message.answer(
        received_text,
        parse_mode='HTML',
        reply_markup=await main_menu_keyboard(),
    )


@router.message(PaymentReceiptStates.waiting_receipt)
async def receipt_invalid_input(message: Message, state: FSMContext):
    if await is_cancel_nav(message.text) or await is_label_text(message.text, 'btn.cancel'):
        await state.clear()
        await message.answer('❌ ارسال رسید لغو شد.', reply_markup=await main_menu_keyboard())
        return
    await message.answer('⚠️ لطفاً عکس یا فایل رسید پرداخت را ارسال کن.')


@sync_to_async
def _get_user_payment(telegram_id: int, payment_id: int):
    from apps.users.models import TelegramUser
    from apps.payments.models import Payment
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        return Payment.objects.get(id=payment_id, user=user)
    except (TelegramUser.DoesNotExist, Payment.DoesNotExist):
        return None


@sync_to_async
def _submit_receipt(telegram_id: int, payment_id: int, local_path: Path, file_name: str):
    from apps.users.models import TelegramUser
    from apps.payments.models import Payment
    from apps.payments.services.payment_service import submit_payment_receipt

    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        payment = Payment.objects.get(id=payment_id, user=user)
    except (TelegramUser.DoesNotExist, Payment.DoesNotExist):
        return None

    with open(local_path, 'rb') as f:
        django_file = File(f, name=file_name)
        return submit_payment_receipt(payment, django_file)
