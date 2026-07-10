"""
Phase 6: Group order FSM flow.
Collects: title → category → lesson → university → file → pages → tier → notes → confirm → creates order → show invite link
Group join link handler: /start G...
"""
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from asgiref.sync import sync_to_async

from apps.telegram_bot.states.order_states import GroupOrderStates
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
    back_keyboard, skip_keyboard, confirm_keyboard,
    main_menu_keyboard, select_category_inline, select_lesson_inline,
    pay_my_share_keyboard, group_join_keyboard,
)
from apps.telegram_bot.utils import (
    format_toman, is_cancel_nav, is_label_text, tier_label,
)
from apps.orders.models import ServiceOrder
from apps.orders.services import get_group_discount_percent

logger = logging.getLogger(__name__)
router = Router()


@router.message(LabelFilter('btn.group_order'))
async def start_group_order(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(GroupOrderStates.waiting_title)
    await message.answer(
        '👥 <b>سفارش گروهی</b>\n\n'
        'یه سفارش بساز، لینکش رو برای همکلاسی‌ها بفرست و هزینه رو بینتون تقسیم کنید.\n\n'
        '✔️ هر نفر جداگانه پرداخت می‌کنه\n'
        '✔️ بعد از تکمیل حداقل ۵ نفر، سفارش وارد تولید می‌شه\n'
        '🎁 تخفیف ویژه گروهی اعمال می‌شه!\n\n'
        'یه عنوان برای سفارش انتخاب کن:',
        parse_mode='HTML',
        reply_markup=await back_keyboard(),
    )


@router.message(GroupOrderStates.waiting_title)
async def group_title(message: Message, state: FSMContext):
    if await is_cancel_nav(message.text):
        await state.clear()
        await message.answer('❌ سفارش لغو شد.', reply_markup=await main_menu_keyboard())
        return
    await state.update_data(title=message.text.strip())
    categories = await _get_categories()
    await state.set_state(GroupOrderStates.waiting_category)
    await message.answer(
        '📂 دسته‌بندی تحصیلی سفارشت رو انتخاب کن:',
        reply_markup=await select_category_inline(categories),
    )


@router.callback_query(GroupOrderStates.waiting_category, F.data.startswith('ord_cat:'))
async def group_category(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split(':')[1])
    await state.update_data(category_id=cat_id)
    lessons = await _get_lessons(cat_id)
    await state.set_state(GroupOrderStates.waiting_lesson)
    await callback.message.edit_text(
        '📖 درس مربوطه رو انتخاب کن:',
        reply_markup=await select_lesson_inline(lessons),
    )
    await callback.answer()


@router.callback_query(GroupOrderStates.waiting_lesson, F.data.startswith('ord_les:'))
async def group_lesson(callback: CallbackQuery, state: FSMContext):
    lesson_id = int(callback.data.split(':')[1])
    await state.update_data(lesson_id=lesson_id)
    await state.set_state(GroupOrderStates.waiting_university)
    await callback.message.delete()
    await callback.message.answer(
        '🏫 نام دانشگاه یا منبع جزوه رو وارد کن (اختیاری):',
        reply_markup=await skip_keyboard(),
    )
    await callback.answer()


@router.message(GroupOrderStates.waiting_university)
async def group_university(message: Message, state: FSMContext):
    if await is_cancel_nav(message.text):
        await state.clear()
        await message.answer('❌ سفارش لغو شد.', reply_markup=await main_menu_keyboard())
        return
    university = '' if await is_label_text(message.text, 'btn.skip') else message.text.strip()
    await state.update_data(university=university)
    await state.set_state(GroupOrderStates.waiting_file)
    await message.answer(
        '📎 فایل جزوه یا کتابت رو اینجا آپلود کن:\n'
        '<i>فرمت‌های پشتیبانی‌شده: PDF، Word، تصویر</i>',
        parse_mode='HTML',
        reply_markup=await back_keyboard(),
    )


@router.message(GroupOrderStates.waiting_file)
async def group_file(message: Message, state: FSMContext):
    if await is_cancel_nav(message.text):
        await state.clear()
        await message.answer('❌ سفارش لغو شد.', reply_markup=await main_menu_keyboard())
        return

    file_id, file_name = None, None
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
        GroupOrderStates.waiting_pages_confirm,
        GroupOrderStates.waiting_pages,
        GroupOrderStates.waiting_service_tier,
        is_group=True,
    )


@router.callback_query(GroupOrderStates.waiting_pages_confirm, F.data == 'ord_pages:confirm')
async def group_pages_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    pages = data.get('suggested_pages', 0)
    if pages < 1:
        await callback.answer('خطا در تشخیص صفحات.', show_alert=True)
        return
    await callback.message.edit_reply_markup(reply_markup=None)
    await proceed_with_pages(
        callback.message, state, pages,
        GroupOrderStates.waiting_service_tier,
        is_group=True,
    )
    await callback.answer()


@router.callback_query(GroupOrderStates.waiting_pages_confirm, F.data == 'ord_pages:edit')
async def group_pages_edit(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GroupOrderStates.waiting_pages)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        '✏️ تعداد صفحات واقعی جزوه رو وارد کن:',
        reply_markup=await back_keyboard(),
    )
    await callback.answer()


@router.message(GroupOrderStates.waiting_pages_confirm)
async def group_pages_confirm_message(message: Message, state: FSMContext):
    if await is_cancel_nav(message.text):
        await state.clear()
        await message.answer('❌ سفارش لغو شد.', reply_markup=await main_menu_keyboard())
        return
    if message.text and message.text.isdigit() and int(message.text) >= 1:
        await proceed_with_pages(
            message, state, int(message.text),
            GroupOrderStates.waiting_service_tier,
            is_group=True,
        )
        return
    await message.answer(
        '⚠️ از دکمه تأیید استفاده کن یا تعداد صفحات رو به عدد وارد کن.',
        reply_markup=await back_keyboard(),
    )


@router.message(GroupOrderStates.waiting_pages)
async def group_pages(message: Message, state: FSMContext):
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
        GroupOrderStates.waiting_service_tier,
        is_group=True,
    )


@router.callback_query(GroupOrderStates.waiting_service_tier, F.data.startswith('ord_tier:'))
async def group_service_tier(callback: CallbackQuery, state: FSMContext):
    result = await apply_tier_selection(callback.data, state, is_group=True)
    if not result:
        await callback.answer('گزینه نامعتبر.', show_alert=True)
        return
    tier, data = result
    await state.set_state(GroupOrderStates.waiting_notes)
    await callback.message.edit_text(
        format_tier_price_confirmation(tier, data, is_group=True),
        parse_mode='HTML',
    )
    await callback.message.answer(
        '📝 اگه توضیح خاصی داری بنویس (اختیاری):',
        reply_markup=await skip_keyboard(),
    )
    await callback.answer()


@router.message(GroupOrderStates.waiting_notes)
async def group_notes(message: Message, state: FSMContext):
    if await is_cancel_nav(message.text):
        await state.clear()
        await message.answer('❌ سفارش لغو شد.', reply_markup=await main_menu_keyboard())
        return
    notes = '' if await is_label_text(message.text, 'btn.skip') else message.text.strip()
    await state.update_data(notes=notes)
    data = await state.get_data()
    await state.set_state(GroupOrderStates.waiting_confirm)

    category_title = await _get_category_title(data.get('category_id'))
    lesson_title = await _get_lesson_title(data.get('lesson_id'))
    discount = get_group_discount_percent()

    text = (
        f'📋 <b>خلاصه سفارش گروهی</b>\n\n'
        f'📌 عنوان: {data["title"]}\n'
        f'📂 دسته‌بندی: {category_title}\n'
        f'📖 درس: {lesson_title}\n'
        f'🏫 دانشگاه: {data.get("university") or "—"}\n'
        f'📦 نوع نسخه: {tier_label(data.get("service_tier", ServiceOrder.TIER_FULL))}\n'
        f'📄 تعداد صفحات: {data["pages"]}\n'
    )
    text += (
        f'📝 یادداشت: {notes or "—"}\n\n'
        f'💵 قیمت پایه: {format_toman(data["base_price"])}\n'
        f'🎁 تخفیف گروهی {discount}٪: -{format_toman(int(data["base_price"]) - int(data["group_price"]))}\n'
        f'💳 <b>قیمت هر نفر: {format_toman(data["group_price"])}</b>\n'
        f'👥 حداقل تعداد لازم: ۵ نفر\n\n'
        f'<i>✔️ بعد از ساخت سفارش، یه لینک اختصاصی برای دعوت همکلاسی‌ها دریافت می‌کنی.</i>\n\n'
        f'{ORDER_DELIVERY_TIME_NOTE}\n\n'
        f'{ORDER_REFUND_POLICY_NOTE}'
    )
    await message.answer(text, parse_mode='HTML', reply_markup=await confirm_keyboard())


@router.message(GroupOrderStates.waiting_confirm)
async def group_confirm(message: Message, state: FSMContext):
    if await is_label_text(message.text, 'btn.cancel') or await is_cancel_nav(message.text):
        await state.clear()
        await message.answer('❌ سفارش لغو شد.', reply_markup=await main_menu_keyboard())
        return
    if not await is_label_text(message.text, 'btn.confirm_pay'):
        await message.answer('⚠️ لطفاً یکی از دکمه‌های موجود رو انتخاب کن.')
        return

    data = await state.get_data()
    await state.clear()
    await message.answer('⏳ در حال ساخت سفارش گروهی...')

    order = await _create_group_order(message.from_user.id, data)
    if not order:
        await message.answer('❌ در ثبت سفارش مشکلی پیش اومد. لطفاً دوباره تلاش کن.', reply_markup=await main_menu_keyboard())
        return

    text = (
        f'✅ <b>سفارش گروهی ساخته شد!</b>\n\n'
        f'🔖 کد سفارش: <code>{order.order_code}</code>\n'
        f'📌 عنوان: {order.title}\n'
        f'📦 نوع نسخه: {tier_label(order.service_tier)}\n'
        f'👥 حداقل اعضا برای شروع: {order.min_group_members} نفر\n'
        f'✅ پرداخت‌های موفق: ۰ نفر\n'
        f'💳 <b>قیمت هر نفر: {format_toman(order.final_price_per_user_toman)}</b>\n'
        f'◉ وضعیت: ⏳ در انتظار تکمیل اعضا\n\n'
        f'🔗 <b>لینک دعوت:</b>\n'
        f'<code>{order.group_join_link}</code>\n\n'
        f'<i>این لینک رو برای همکلاسی‌هات بفرست. هر نفر سهمش رو با کارت‌به‌کارت پرداخت می‌کنه و رسید ارسال می‌کنه.\n'
        f'بعد از پرداخت {order.min_group_members} نفر، سفارش وارد مرحله تولید می‌شه.</i>\n\n'
        f'{ORDER_DELIVERY_TIME_NOTE}'
    )
    keyboard = await pay_my_share_keyboard(order.order_code)
    await message.answer(text, parse_mode='HTML', reply_markup=keyboard)
    await message.answer(
        '💳 می‌خوای سهم خودت رو الان پرداخت کنی؟',
        reply_markup=await main_menu_keyboard()
    )


# ─── Group join via deep link ─────────────────────────────────────────────────

async def handle_group_join_deep_link(message: Message, user, join_code: str):
    order = await _get_order_by_join_code(join_code)
    if not order:
        await message.answer('❌ این لینک معتبر نیست یا منقضی شده. لطفاً لینک رو دوباره از سازنده سفارش بخواه.')
        return
    await _show_group_order_invite(message, user, order)


@router.callback_query(F.data.startswith('join_group:'))
async def join_group_order(callback: CallbackQuery):
    order_code = callback.data.split('join_group:')[1]
    user = await _get_user(callback.from_user.id)
    if not user:
        await callback.answer('⚠️ ابتدا /start رو بزن تا بات رو فعال کنی.', show_alert=True)
        return

    order = await _get_order_by_code(order_code)
    if not order:
        await callback.answer('⚠️ سفارش پیدا نشد. لطفاً دوباره تلاش کن.', show_alert=True)
        return

    already_paid = await _is_paid_member(user, order)
    if already_paid:
        if order.private_channel_link:
            await callback.message.answer(
                f'✅ <b>شما قبلاً پرداخت کردی.</b>\n\n'
                f'🔗 لینک کانال گروه:\n{order.private_channel_link}',
                parse_mode='HTML',
            )
        else:
            await callback.message.answer(
                '✅ پرداخت قبلاً انجام شده. منتظر آماده شدن سفارش باش.'
            )
        await callback.answer()
        return

    await callback.answer('⏳ در حال پردازش...')
    result = await _join_group_order(user, order)
    if not result:
        await callback.message.answer('❌ مشکلی پیش اومد. لطفاً دوباره تلاش کن.')
        return

    member, payment, success, url_or_error = result

    header = (
        f'✅ <b>برای پرداخت سهم خودت در سفارش گروهی:</b>\n\n'
        f'🔖 کد سفارش: <code>{order.order_code}</code>\n'
        f'📌 عنوان: {order.title}\n'
        f'💳 <b>مبلغ قابل پرداخت: {format_toman(order.final_price_per_user_toman)}</b>\n'
        f'◉ وضعیت: ⏳ در انتظار پرداخت'
    )
    footer = f'{ORDER_DELIVERY_TIME_NOTE}\n\n{ORDER_REFUND_POLICY_NOTE}'
    await send_payment_instructions(
        callback.message, payment, success, url_or_error,
        header_text=header, footer_text=footer,
    )


async def _show_group_order_invite(message: Message, user, order):
    text = (
        f'👥 <b>دعوتنامه سفارش گروهی MedCardy</b>\n\n'
        f'🔖 کد سفارش: <code>{order.order_code}</code>\n'
        f'📌 عنوان: {order.title}\n'
        f'📦 نوع نسخه: {tier_label(order.service_tier)}\n'
        f'👥 حداقل اعضا: {order.min_group_members} نفر\n'
        f'✅ پرداخت‌های موفق: {order.paid_members_count} نفر\n'
        f'💳 <b>قیمت هر نفر: {format_toman(order.final_price_per_user_toman)}</b>\n'
        f'◉ وضعیت: ⏳ در انتظار تکمیل اعضا\n\n'
        f'<i>🔐 برای عضویت در این سفارش، روی دکمه زیر بزن، واریز کنی و رسید ارسال کنی.</i>\n\n'
        f'{ORDER_DELIVERY_TIME_NOTE}\n\n'
        f'{ORDER_REFUND_POLICY_NOTE}'
    )
    keyboard = await group_join_keyboard(order.order_code)
    await message.answer(text, parse_mode='HTML', reply_markup=keyboard)


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
def _create_group_order(telegram_id: int, data: dict):
    from apps.users.models import TelegramUser
    from apps.catalog.models import Category, Lesson
    from apps.orders.services import create_group_order
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
    order = create_group_order(
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
    return order


@sync_to_async
def _get_order_by_join_code(join_code: str):
    from apps.orders.models import ServiceOrder
    try:
        return ServiceOrder.objects.get(group_join_code=join_code)
    except ServiceOrder.DoesNotExist:
        return None


@sync_to_async
def _get_order_by_code(order_code: str):
    from apps.orders.models import ServiceOrder
    try:
        return ServiceOrder.objects.get(order_code=order_code)
    except ServiceOrder.DoesNotExist:
        return None


@sync_to_async
def _get_user(telegram_id: int):
    from apps.users.models import TelegramUser
    try:
        return TelegramUser.objects.get(telegram_id=telegram_id)
    except TelegramUser.DoesNotExist:
        return None


@sync_to_async
def _is_paid_member(user, order) -> bool:
    from apps.orders.models import ServiceOrderMember
    return ServiceOrderMember.objects.filter(
        order=order, user=user, status=ServiceOrderMember.STATUS_PAID
    ).exists()


@sync_to_async
def _join_group_order(user, order):
    from apps.orders.services import join_group_order
    return join_group_order(user, order)
