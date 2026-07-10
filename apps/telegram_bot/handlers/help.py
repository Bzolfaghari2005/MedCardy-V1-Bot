import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async

from apps.telegram_bot.filters import LabelFilter
from apps.telegram_bot.utils import aget_bot_message, aget_label
from apps.telegram_bot.keyboards import main_menu_keyboard, back_to_main_keyboard

logger = logging.getLogger(__name__)
router = Router()

FAQ_TOPICS = [
    ('help_what_is', 'MedCardy چیست؟',
     'MedCardy یک استارتاپ آموزش پزشکی است که جزوه‌های دانشگاهی را به پادکست آموزشی تبدیل می‌کند.'),
    ('help_free_course', 'دوره رایگان چیست؟',
     'دوره‌های رایگان MedCardy در کانال عمومی تلگرام قرار دارند و لینک مستقیم آن‌ها برای شما ارسال می‌شود.'),
    ('help_paid_course', 'بعد از خرید دوره چطور به دستم می‌رسه؟',
     'بعد از خرید موفق، دوره در پنل شخصی MedCardy شما قرار می‌گیره:\n\n'
     '• اگر پنل ندارید → ظرف چند ساعت برایتان ساخته می‌شه\n'
     '• اگر پنل دارید → ظرف چند ساعت به پنل اضافه می‌شه\n\n'
     'لطفاً صبور باشید 🙏 وضعیت را از بخش «دوره‌های من» پیگیری کنید.'),
    ('help_personal_panel', 'پنل شخصی MedCardy چیست؟',
     'پنل شخصی یک کانال تلگرام اختصاصی برای شماست. دوره‌ها و سفارش‌های فردی شما در آن قرار می‌گیرند.'),
    ('help_individual_order', 'سفارش فردی چیست؟',
     'شما جزوه یا فایل درسی خود را می‌فرستید و MedCardy برای شما پادکست اختصاصی می‌سازد. خروجی در پنل شخصی شما قرار می‌گیرد.\n\n'
     '⏰ آماده‌سازی ممکنه ۴۸ ساعت یا بیشتر طول بکشه — هر چه زودتر سفارش دهید، زودتر تحویل می‌گیرید.'),
    ('help_group_order', 'سفارش گروهی چیست؟',
     'در سفارش گروهی چند نفر هزینه یک جزوه مشترک را تقسیم می‌کنند. خروجی در یک کانال اختصاصی همان سفارش قرار می‌گیرد.\n\n'
     '⏰ آماده‌سازی ممکنه ۴۸ ساعت یا بیشتر طول بکشه — هر چه زودتر سفارش دهید، زودتر تحویل می‌گیرید.'),
    ('help_pricing', 'قیمت‌گذاری چگونه محاسبه می‌شود؟',
     'نسخه مروری: هر صفحه ۱,۲۵۰ تومان (۱۰۰ صفحه = ۱۲۵,۰۰۰ تومان)\n'
     'آموزش کامل: هر صفحه ۲,۵۰۰ تومان (۱۰۰ صفحه = ۲۵۰,۰۰۰ تومان)\n'
     'سفارش گروهی (۵+ نفر): ۳۰٪ تخفیف روی هر دو نسخه\n'
     'پس از آپلود فایل، بات تعداد صفحات را آنالیز می‌کند.'),
    ('help_payment', 'پرداخت چگونه انجام می‌شود؟',
     'بعد از انتخاب محصول، شماره کارت و مبلغ نمایش داده می‌شود. مبلغ را کارت‌به‌کارت واریز کنید و رسید را در بات ارسال کنید. پس از تأیید ادمین، سفارش/خرید شما فعال می‌شود.'),
    ('help_after_payment', 'بعد از پرداخت موفق چه اتفاقی می‌افتد؟',
     'بات به شما پیام تأیید می‌فرستد.\n\n'
     '📚 <b>خرید دوره:</b> ظرف چند ساعت در پنل شخصی قرار می‌گیره (یا پنل ساخته می‌شه).\n'
     '🎙️ <b>سفارش فردی/گروهی:</b> وارد مرحله تولید می‌شه؛ آماده‌سازی ممکنه ۴۸ ساعت یا بیشتر طول بکشه.\n\n'
     'وضعیت را از «دوره‌های من» یا «سرویس‌های من» پیگیری کنید.'),
    ('help_failed_payment', 'اگر پرداخت ناموفق شد چه کنم؟',
     'اگر مبلغی از حساب کم شده باشد، ۷۲ ساعت دیگر برمی‌گردد. می‌توانید دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.'),
    ('help_track_order', 'چطور وضعیت سفارش را پیگیری کنم؟',
     'از بخش «سرویس‌های من» در منوی اصلی بات می‌توانید وضعیت تمام سفارش‌ها را ببینید.'),
    ('help_contact', 'چطور با پشتیبانی ارتباط بگیرم؟',
     'از طریق @MedCardySupport در تلگرام با تیم ما در ارتباط باشید.'),
]


@router.message(LabelFilter('menu.help'))
async def help_handler(message: Message):
    help_text = await aget_bot_message(
        'help_message',
        default='راهنمای MedCardy - یک موضوع را انتخاب کنید:'
    )
    buttons = [
        [InlineKeyboardButton(text=topic[1], callback_data=f'faq:{topic[0]}')]
        for topic in FAQ_TOPICS
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(help_text, reply_markup=keyboard)


@router.callback_query(F.data.startswith('faq:'))
async def faq_answer(callback: CallbackQuery):
    key = callback.data.split('faq:')[1]
    topic = next((t for t in FAQ_TOPICS if t[0] == key), None)
    if not topic:
        await callback.answer('موردی یافت نشد', show_alert=True)
        return

    text = f'❓ <b>{topic[1]}</b>\n\n{topic[2]}'
    back_label = await aget_label('btn.back_to_help')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=back_label, callback_data='back_to_help')],
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data == 'back_to_help')
async def back_to_help(callback: CallbackQuery):
    help_text = await aget_bot_message(
        'help_message',
        default='راهنمای MedCardy - یک موضوع را انتخاب کنید:'
    )
    buttons = [
        [InlineKeyboardButton(text=topic[1], callback_data=f'faq:{topic[0]}')]
        for topic in FAQ_TOPICS
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(help_text, reply_markup=keyboard)
    await callback.answer()
