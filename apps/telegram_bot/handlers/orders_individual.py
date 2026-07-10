"""
Phase 5: Individual order FSM flow.
Collects: title → category → lesson → university → file → pages → tier → notes → confirm → pay
"""
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from asgiref.sync import sync_to_async

from apps.telegram_bot.states.order_states import IndividualOrderStates
from apps.telegram_bot.handlers.order_flow_helpers import (
    handle_order_file_upload,
    proceed_with_pages,
    apply_tier_selection,
    format_tier_price_confirmation,
    save_uploaded_file_to_order,
    ORDER_REFUND_POLICY_NOTE,
    ORDER_DELIVERY_TIME_NOTE,
)
from apps.telegram_bot.filters import LabelFilter
from apps.telegram_bot.handlers.payment_helpers import send_payment_instructions
from apps.telegram_bot.keyboards import (
    order_type_keyboard, back_keyboard, skip_keyboard, confirm_keyboard,
    main_menu_keyboard, select_category_inline, select_lesson_inline,
)
from apps.telegram_bot.utils import (
    format_toman, is_cancel_nav, is_label_text, tier_label, aget_label,
)
from apps.orders.models import ServiceOrder
from apps.orders.services import (
    get_full_price_per_page,
    get_review_price_per_page,
    get_group_discount_percent,
)

logger = logging.getLogger(__name__)
router = Router()


# ─── Order menu entry point ───────────────────────────────────────────────────

@router.message(LabelFilter('menu.order'))
async def order_menu(message: Message):
    from apps.telegram_bot.utils import aget_bot_message
    intro = await aget_bot_message(
        'individual_order_intro',
        default=(
            '🎙️ <b>ساخت پادکست اختصاصی</b>\n\n'
            'جزوه‌ات رو آپلود کن، ما یه پادکست آموزشی حرفه‌ای ازش می‌سازیم.\n\n'
            '👤 فردی — خروجی فقط برای شما\n'
            '👥 گروهی — با همکلاسی‌ها هزینه رو تقسیم کنید\n\n'
            'کدوم نوع رو می‌خوای؟'
        )
    )
    await message.answer(intro, reply_markup=await order_type_keyboard())


@router.message(LabelFilter('btn.individual_order'))
async def start_individual_order(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(IndividualOrderStates.waiting_title)
    await message.answer(
        '👤 <b>سفارش فردی</b>\n\n'
        'یه عنوان برای سفارشت انتخاب کن:\n'
        '<i>مثال: فیزیولوژی گردش خون — دکتر کریمی</i>',
        parse_mode='HTML',
        reply_markup=await back_keyboard(),
    )


@router.message(IndividualOrderStates.waiting_title)
async def individual_title(message: Message, state: FSMContext):
    if await is_cancel_nav(message.text):
        await state.clear()
        await message.answer('❌ سفارش لغو شد.', reply_markup=await main_menu_keyboard())
        return
    await state.update_data(title=message.text.strip())
    categories = await _get_categories()
    await state.set_state(IndividualOrderStates.waiting_category)
    await message.answer(
        '📂 دسته‌بندی تحصیلی سفارشت رو انتخاب کن:',
        reply_markup=await select_category_inline(categories)
    )


@router.callback_query(IndividualOrderStates.waiting_category, F.data.startswith('ord_cat:'))
async def individual_category(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split(':')[1])
    await state.update_data(category_id=cat_id)
    lessons = await _get_lessons(cat_id)
    await state.set_state(IndividualOrderStates.waiting_lesson)
    await callback.message.edit_text(
        '📖 درس مربوطه رو انتخاب کن:',
        reply_markup=await select_lesson_inline(lessons),
    )
    await callback.answer()


@router.callback_query(IndividualOrderStates.waiting_lesson, F.data.startswith('ord_les:'))
async def individual_lesson(callback: CallbackQuery, state: FSMContext):
    lesson_id = int(callback.data.split(':')[1])
    await state.update_data(lesson_id=lesson_id)
    await state.set_state(IndividualOrderStates.waiting_university)
    await callback.message.delete()
    await callback.message.answer(
        '🏫 نام دانشگاه یا منبع جزوه رو وارد کن (اختیاری):',
        reply_markup=await skip_keyboard()
    )
    await callback.answer()


@router.message(IndividualOrderStates.waiting_university)
async def individual_university(message: Message, state: FSMContext):
    if await is_label_text(message.text, 'btn.back'):
        await state.set_state(IndividualOrderStates.waiting_category)
        categories = await _get_categories()
        await message.answer(
            '📂 دسته‌بندی تحصیلی سفارشت رو انتخاب کن:',
            reply_markup=await select_category_inline(categories),
        )
        return
    if await is_label_text(message.text, 'btn.back_to_main'):
        await state.clear()
        await message.answer('❌ سفارش لغو شد.', reply_markup=await main_menu_keyboard())
        return
    university = '' if await is_label_text(message.text, 'btn.skip') else message.text.strip()
    await state.update_data(university=university)
    await state.set_state(IndividualOrderStates.waiting_file)
    await message.answer(
        '📎 فایل جزوه یا کتابت رو اینجا آپلود کن:\n'
        '<i>فرمت‌های پشتیبانی‌شده: PDF، Word، تصویر</i>',
        parse_mode='HTML',
        reply_markup=await back_keyboard(),
    )


@router.message(IndividualOrderStates.waiting_file)
async def individual_file(message: Message, state: FSMContext):
    if await is_cancel_nav(message.text):
        await state.clear()
        await message.answer('❌ سفارش لغو شد.', reply_markup=await main_menu_keyboard())
        return

    file_id = None
    file_name = None

    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_name = 'image.jpg'
    else:
        await message.answer('⚠️ لطفاً یه فایل ارسال کن (PDF، Word یا تصویر).')
        return

    await handle_order_file_upload(
        message, state, file_id, file_name,
        IndividualOrderStates.waiting_pages_confirm,
        IndividualOrderStates.waiting_pages,
        IndividualOrderStates.waiting_service_tier,
        is_group=False,
    )


@router.callback_query(IndividualOrderStates.waiting_pages_confirm, F.data == 'ord_pages:confirm')
async def individual_pages_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    pages = data.get('suggested_pages', 0)
    if pages < 1:
        await callback.answer('خطا در تشخیص صفحات.', show_alert=True)
        return
    await callback.message.edit_reply_markup(reply_markup=None)
    await proceed_with_pages(
        callback.message, state, pages,
        IndividualOrderStates.waiting_service_tier,
        is_group=False,
    )
    await callback.answer()


@router.callback_query(IndividualOrderStates.waiting_pages_confirm, F.data == 'ord_pages:edit')
async def individual_pages_edit(callback: CallbackQuery, state: FSMContext):
    await state.set_state(IndividualOrderStates.waiting_pages)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        '✏️ تعداد صفحات واقعی جزوه رو وارد کن:',
        reply_markup=await back_keyboard(),
    )
    await callback.answer()


@router.message(IndividualOrderStates.waiting_pages_confirm)
async def individual_pages_confirm_message(message: Message, state: FSMContext):
    if await is_cancel_nav(message.text):
        await state.clear()
        await message.answer('❌ سفارش لغو شد.', reply_markup=await main_menu_keyboard())
        return
    if message.text and message.text.isdigit() and int(message.text) >= 1:
        await proceed_with_pages(
            message, state, int(message.text),
            IndividualOrderStates.waiting_service_tier,
            is_group=False,
        )
        return
    await message.answer(
        '⚠️ از دکمه تأیید استفاده کن یا تعداد صفحات رو به عدد وارد کن.',
        reply_markup=await back_keyboard(),
    )


@router.message(IndividualOrderStates.waiting_pages)
async def individual_pages(message: Message, state: FSMContext):
    if await is_cancel_nav(message.text):
        await state.clear()
        await message.answer('❌ سفارش لغو شد.', reply_markup=await main_menu_keyboard())
        return

    if not message.text.isdigit() or int(message.text) < 1:
        await message.answer('⚠️ لطفاً یه عدد مثبت وارد کن.')
        return

    pages = int(message.text)
    await proceed_with_pages(
        message, state, pages,
        IndividualOrderStates.waiting_service_tier,
        is_group=False,
    )


@router.callback_query(IndividualOrderStates.waiting_service_tier, F.data.startswith('ord_tier:'))
async def individual_service_tier(callback: CallbackQuery, state: FSMContext):
    result = await apply_tier_selection(callback.data, state, is_group=False)
    if not result:
        await callback.answer('گزینه نامعتبر.', show_alert=True)
        return
    tier, data = result
    await state.set_state(IndividualOrderStates.waiting_notes)
    await callback.message.edit_text(
        format_tier_price_confirmation(tier, data, is_group=False),
        parse_mode='HTML',
    )
    await callback.message.answer(
        '📝 اگه توضیح خاصی داری بنویس (اختیاری):\n'
        '<i>مثال: صفحات ۱ تا ۵۰ بخش اصلیه</i>',
        parse_mode='HTML',
        reply_markup=await skip_keyboard(),
    )
    await callback.answer()


@router.message(IndividualOrderStates.waiting_notes)
async def individual_notes(message: Message, state: FSMContext):
    if await is_cancel_nav(message.text):
        await state.clear()
        await message.answer('❌ سفارش لغو شد.', reply_markup=await main_menu_keyboard())
        return
    notes = '' if await is_label_text(message.text, 'btn.skip') else message.text.strip()
    await state.update_data(notes=notes)
    data = await state.get_data()
    await state.set_state(IndividualOrderStates.waiting_confirm)
    await _show_individual_order_summary(message, data)


async def _show_individual_order_summary(message: Message, data: dict):
    pages = data['pages']
    price = data['base_price']
    category_title = await _get_category_title(data.get('category_id'))
    lesson_title = await _get_lesson_title(data.get('lesson_id'))

    text = (
        f'📋 <b>خلاصه سفارش فردی</b>\n\n'
        f'📌 عنوان: {data["title"]}\n'
        f'📂 دسته‌بندی: {category_title}\n'
        f'📖 درس: {lesson_title}\n'
        f'🏫 دانشگاه: {data.get("university") or "—"}\n'
        f'📦 نوع نسخه: {tier_label(data.get("service_tier", ServiceOrder.TIER_FULL))}\n'
        f'📄 تعداد صفحات: {pages}\n'
    )
    text += (
        f'📝 یادداشت: {data.get("notes") or "—"}\n\n'
        f'💰 <b>مبلغ قابل پرداخت: {format_toman(price)}</b>\n\n'
        f'<i>⚠️ قیمت بر اساس تعداد صفحات اعلام‌شده محاسبه شده. '
        f'در صورت کیفیت پایین فایل، ممکنه ادمین قیمت رو اصلاح کنه.</i>\n\n'
        f'{ORDER_DELIVERY_TIME_NOTE}\n\n'
        f'{ORDER_REFUND_POLICY_NOTE}'
    )
    await message.answer(text, parse_mode='HTML', reply_markup=await confirm_keyboard())


@router.message(IndividualOrderStates.waiting_confirm)
async def individual_confirm(message: Message, state: FSMContext):
    if await is_label_text(message.text, 'btn.cancel') or await is_cancel_nav(message.text):
        await state.clear()
        await message.answer('❌ سفارش لغو شد.', reply_markup=await main_menu_keyboard())
        return

    if not await is_label_text(message.text, 'btn.confirm_pay'):
        await message.answer('⚠️ لطفاً یکی از دکمه‌های موجود رو انتخاب کن.')
        return

    data = await state.get_data()
    await state.clear()
    await message.answer('⏳ در حال ثبت سفارش...')

    result = await _create_individual_order(message.from_user.id, data)
    if not result:
        await message.answer(
            '❌ در ثبت سفارش مشکلی پیش اومد. لطفاً دوباره تلاش کن یا با پشتیبانی تماس بگیر.',
            reply_markup=await main_menu_keyboard()
        )
        return

    order, payment, success, url_or_error = result

    header = (
        f'✅ <b>سفارش فردی ثبت شد!</b>\n\n'
        f'🔖 کد سفارش: <code>{order.order_code}</code>\n'
        f'📌 عنوان: {order.title}\n'
        f'📦 نوع نسخه: {tier_label(order.service_tier)}\n'
        f'📄 تعداد صفحات: {order.pages_count}\n'
        f'◉ وضعیت: ⏳ در انتظار پرداخت\n\n'
        f'<i>✔️ بعد از تأیید پرداخت توسط ادمین، سفارش وارد مرحله تولید می‌شه.</i>'
    )
    footer = f'{ORDER_DELIVERY_TIME_NOTE}\n\n{ORDER_REFUND_POLICY_NOTE}'
    await send_payment_instructions(
        message, payment, success, url_or_error,
        header_text=header, footer_text=footer,
    )


# ─── Cancel via inline button ─────────────────────────────────────────────────

@router.callback_query(F.data == 'cancel_order')
async def cancel_order_inline(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer('❌ سفارش لغو شد.', reply_markup=await main_menu_keyboard())
    await callback.answer()


# ─── Pricing guide ───────────────────────────────────────────────────────────

@router.message(LabelFilter('btn.pricing_guide'))
async def pricing_guide(message: Message):
    review_pp = get_review_price_per_page()
    full_pp = get_full_price_per_page()
    discount = get_group_discount_percent()
    review_name = await aget_label('tier.review')
    full_name = await aget_label('tier.full')
    await message.answer(
        '💰 <b>راهنمای قیمت‌گذاری MedCardy</b>\n\n'
        f'📘 <b>{review_name}:</b>\n'
        f'هر صفحه = {format_toman(review_pp)}\n'
        f'نمونه — ۱۰۰ صفحه = {format_toman(100 * review_pp)}\n\n'
        f'📗 <b>{full_name}:</b>\n'
        f'هر صفحه = {format_toman(full_pp)}\n'
        f'نمونه — ۱۰۰ صفحه = {format_toman(100 * full_pp)}\n\n'
        f'🎁 <b>سفارش گروهی (۵+ نفر): {discount}٪ تخفیف</b> روی هر دو نوع\n\n'
        '<i>📎 بعد از آپلود فایل، بات تعداد صفحات رو آنالیز می‌کنه.\n'
        'قیمت نهایی ممکنه بسته به کیفیت فایل کمی تفاوت داشته باشه.</i>',
        parse_mode='HTML',
        reply_markup=await order_type_keyboard(),
    )


# ─── DB helpers ──────────────────────────────────────────────────────────────

@sync_to_async
def _get_categories():
    from apps.catalog.models import Category
    return list(Category.objects.filter(is_active=True, parent=None).order_by('sort_order'))


@sync_to_async
def _get_lessons(cat_id: int):
    from apps.catalog.models import Lesson
    return list(Lesson.objects.filter(category_id=cat_id, is_active=True).order_by('sort_order'))


@sync_to_async
def _get_category_title(cat_id) -> str:
    if not cat_id:
        return '—'
    from apps.catalog.models import Category
    try:
        return Category.objects.get(id=cat_id).title
    except Category.DoesNotExist:
        return '—'


@sync_to_async
def _get_lesson_title(lesson_id) -> str:
    if not lesson_id:
        return '—'
    from apps.catalog.models import Lesson
    try:
        return Lesson.objects.get(id=lesson_id).title
    except Lesson.DoesNotExist:
        return '—'


@sync_to_async
def _create_individual_order(telegram_id: int, data: dict):
    from apps.users.models import TelegramUser
    from apps.catalog.models import Category, Lesson
    from apps.orders.services import create_individual_order

    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
    except TelegramUser.DoesNotExist:
        return None

    category = None
    lesson = None
    if data.get('category_id'):
        try:
            category = Category.objects.get(id=data['category_id'])
        except Category.DoesNotExist:
            pass
    if data.get('lesson_id'):
        try:
            lesson = Lesson.objects.get(id=data['lesson_id'])
        except Lesson.DoesNotExist:
            pass

    order, payment, success, url_or_error = create_individual_order(
        user=user,
        title=data['title'],
        category=category,
        lesson=lesson,
        pages_count=data['pages'],
        service_tier=data.get('service_tier', ServiceOrder.TIER_FULL),
        university=data.get('university', ''),
        user_note=data.get('notes', ''),
        detected_pages=data.get('detected_pages', 0),
        detected_char_count=data.get('detected_char_count', 0),
    )
    save_uploaded_file_to_order(order, data)
    return order, payment, success, url_or_error
