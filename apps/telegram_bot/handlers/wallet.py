"""
Phase 7: Wallet handler.
Show balance, charge via receipt or gateway, view transactions.
"""
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from asgiref.sync import sync_to_async

from apps.telegram_bot.states.wallet_states import WalletStates
from apps.telegram_bot.handlers.payment_helpers import send_payment_instructions
from apps.telegram_bot.keyboards import (
    wallet_keyboard, wallet_amounts_keyboard, main_menu_keyboard,
)
from apps.telegram_bot.filters import LabelFilter, WalletAmountFilter
from apps.telegram_bot.utils import (
    format_toman, is_cancel_nav, aget_wallet_amounts, get_status_label,
)

logger = logging.getLogger(__name__)
router = Router()


@router.message(LabelFilter('menu.wallet'))
async def wallet_home(message: Message, state: FSMContext):
    await state.clear()
    balance = await _get_wallet_balance(message.from_user.id)
    text = (
        f'💳 <b>کیف پول من</b>\n\n'
        f'💰 موجودی فعلی: <b>{format_toman(balance)}</b>'
    )
    await message.answer(text, parse_mode='HTML', reply_markup=await wallet_keyboard())


@router.message(LabelFilter('btn.charge_wallet'))
async def charge_wallet_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        '💳 مبلغ شارژ رو انتخاب کن:',
        reply_markup=await wallet_amounts_keyboard()
    )


@router.message(WalletAmountFilter())
async def charge_predefined(message: Message, state: FSMContext):
    amounts = await aget_wallet_amounts()
    amount = amounts[message.text]
    await _process_wallet_charge(message, amount)


@router.message(LabelFilter('btn.custom_amount'))
async def charge_custom_prompt(message: Message, state: FSMContext):
    await state.set_state(WalletStates.waiting_custom_amount)
    await message.answer(
        '💰 مبلغ مورد نظرت رو به تومان وارد کن:\n'
        '<i>مثال: 300000</i>\n'
        '<i>حداقل: ۱۰,۰۰۰ تومان</i>',
        parse_mode='HTML',
        reply_markup=await wallet_amounts_keyboard(),
    )


@router.message(WalletStates.waiting_custom_amount)
async def charge_custom_amount(message: Message, state: FSMContext):
    if await is_cancel_nav(message.text):
        await state.clear()
        await wallet_home(message, state)
        return

    cleaned = message.text.replace(',', '').replace('،', '').strip()
    if not cleaned.isdigit():
        await message.answer('⚠️ لطفاً فقط عدد وارد کن.')
        return

    amount = int(cleaned)
    if amount < 10_000:
        await message.answer('⚠️ حداقل مبلغ شارژ ۱۰,۰۰۰ تومان است.')
        return
    if amount > 50_000_000:
        await message.answer('⚠️ حداکثر مبلغ شارژ ۵۰,۰۰۰,۰۰۰ تومان است.')
        return

    await state.clear()
    await _process_wallet_charge(message, amount)


async def _process_wallet_charge(message: Message, amount: int):
    result = await _create_wallet_charge(message.from_user.id, amount)
    if not result:
        await message.answer(
            '❌ ساخت درخواست شارژ با مشکل مواجه شد. لطفاً دوباره تلاش کن.',
            reply_markup=await main_menu_keyboard()
        )
        return

    payment, success, url_or_error = result
    header = (
        f'✅ <b>درخواست شارژ ثبت شد!</b>\n\n'
        f'💰 <b>مبلغ: {format_toman(amount)}</b>'
    )
    footer = (
        '<i>✔️ بعد از تأیید پرداخت توسط ادمین، موجودی کیف پولت به‌صورت خودکار افزایش پیدا می‌کنه.</i>'
    )
    await send_payment_instructions(
        message, payment, success, url_or_error,
        header_text=header, footer_text=footer,
    )


@router.message(LabelFilter('btn.transactions'))
async def view_transactions(message: Message):
    transactions = await _get_transactions(message.from_user.id)
    if not transactions:
        await message.answer(
            '📋 <b>تراکنش‌های کیف پول</b>\n\n'
            '📭 هنوز هیچ تراکنشی ثبت نشده.',
            parse_mode='HTML'
        )
        return

    lines = ['📋 <b>تراکنش‌های اخیر:</b>\n']
    for t in transactions:
        type_label = get_status_label('status.wallet', t.transaction_type)
        sign = '+' if t.transaction_type in ('charge', 'refund', 'admin_adjustment') else '-'
        date_str = t.created_at.strftime('%y/%m/%d')
        lines.append(f'{date_str} | {type_label} | {sign}{format_toman(t.amount_toman)}')
        if t.description:
            lines.append(f'  {t.description}')

    await message.answer('\n'.join(lines), parse_mode='HTML', reply_markup=await wallet_keyboard())


# ─── DB helpers ──────────────────────────────────────────────────────────────

@sync_to_async
def _get_wallet_balance(telegram_id: int) -> int:
    from apps.users.models import TelegramUser
    try:
        return int(TelegramUser.objects.get(telegram_id=telegram_id).wallet_balance)
    except TelegramUser.DoesNotExist:
        return 0


@sync_to_async
def _create_wallet_charge(telegram_id: int, amount: int):
    from apps.users.models import TelegramUser
    from apps.wallet.services import create_wallet_charge_payment
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
    except TelegramUser.DoesNotExist:
        return None
    return create_wallet_charge_payment(user, amount)


@sync_to_async
def _get_transactions(telegram_id: int):
    from apps.users.models import TelegramUser
    from apps.wallet.models import WalletTransaction
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        return list(WalletTransaction.objects.filter(user=user).order_by('-created_at')[:20])
    except TelegramUser.DoesNotExist:
        return []
