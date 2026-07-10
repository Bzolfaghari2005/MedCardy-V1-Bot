import logging
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from apps.telegram_bot.filters import LabelFilter
from apps.telegram_bot.utils import aget_bot_message, aget_label
from apps.telegram_bot.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(LabelFilter('menu.support'))
async def support_handler(message: Message):
    support_text = await aget_bot_message(
        'support_message',
        default=(
            'برای پشتیبانی، ارسال نظر، گزارش مشکل یا پیگیری سفارش:\n\n'
            '@MedCardySupport\n\n'
            'لطفاً کد سفارش یا کد پرداخت را هم ارسال کنید.'
        )
    )
    btn_label = await aget_label('btn.view_my_orders')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_label, callback_data='my_order_codes')],
    ])
    await message.answer(support_text, reply_markup=keyboard)


@router.message(LabelFilter('btn.back_to_main'))
async def back_to_main(message: Message):
    text = await aget_bot_message(
        'start_message',
        default='از منوی زیر انتخاب کن:'
    )
    await message.answer(text, reply_markup=await main_menu_keyboard())
