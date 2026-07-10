"""Shared helpers for individual and group order FSM flows."""
from pathlib import Path

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from asgiref.sync import sync_to_async

from apps.orders.file_analysis import FileAnalysisResult, analyze_file
from apps.orders.models import ServiceOrder
from apps.orders.services import (
    calculate_group_price,
    calculate_individual_price,
    get_group_discount_percent,
)
from apps.telegram_bot.keyboards import (
    confirm_pages_inline,
    select_service_tier_group_inline,
    select_service_tier_inline,
    back_keyboard,
)
from apps.telegram_bot.services.telegram_files import download_telegram_file
from apps.telegram_bot.utils import format_toman, tier_label

ORDER_REFUND_POLICY_NOTE = (
    '<i>⚠️ در صورت عدم امکان ساخت فایل یا رد سفارش توسط ادمین، '
    'مبلغ پرداختی به کیف پول شما برمی‌گرده و لغو سفارش از طریق بات به شما اطلاع داده می‌شه.</i>'
)

ORDER_DELIVERY_TIME_NOTE = (
    '<i>⏰ آماده‌سازی سفارش فردی یا گروهی بسته به حجم و کیفیت فایل، '
    'ممکنه <b>۴۸ ساعت یا بیشتر</b> طول بکشه.\n'
    'برای اینکه به موقع به محتوا برسی، هر چه زودتر سفارش بده.</i>'
)

COURSE_DELIVERY_TIME_NOTE = (
    '<i>⏳ بعد از پرداخت موفق:\n'
    '• پنل نداری؟ ظرف چند ساعت برات ساخته می‌شه\n'
    '• پنل داری؟ دوره ظرف چند ساعت به پنلت اضافه می‌شه\n'
    'لطفاً کمی صبر کن 🙏</i>'
)


def format_analysis_message(result: FileAnalysisResult) -> str:
    if result.analysis_method == 'fallback':
        return (
            '📄 آنالیز خودکار این فایل ممکن نشد.\n'
            'تعداد تقریبی صفحات جزوه رو وارد کن:\n'
            '<i>مثال: 100</i>'
        )
    return (
        f'🔍 <b>فایل با موفقیت آنالیز شد!</b>\n'
        f'📄 تعداد صفحات تشخیص‌داده‌شده: <b>{result.page_count}</b>\n\n'
        f'<i>اگر درسته تأیید کن؛ اگر نه «ویرایش» بزن یا عدد صحیح رو وارد کن.</i>'
    )


async def handle_order_file_upload(
    message: Message,
    state: FSMContext,
    file_id: str,
    file_name: str,
    pages_confirm_state,
    pages_state,
    tier_state,
    is_group: bool = False,
) -> None:
    """Download, analyze file, then prompt for page count confirmation or manual entry."""
    await message.answer('⏳ در حال آنالیز فایل، لطفاً صبر کن...')

    local_path = await download_telegram_file(message.bot, file_id, file_name)
    result = await sync_to_async(analyze_file)(local_path, file_name)

    suggested_pages = result.page_count if result.analysis_method != 'fallback' else 0
    await state.update_data(
        file_id=file_id,
        file_name=file_name,
        temp_file_path=str(local_path),
        detected_pages=suggested_pages,
        detected_char_count=0,
        suggested_pages=suggested_pages,
        analysis_method=result.analysis_method,
    )

    if result.analysis_method == 'fallback':
        await state.set_state(pages_state)
        await message.answer(
            format_analysis_message(result),
            parse_mode='HTML',
            reply_markup=await back_keyboard(),
        )
        return

    await state.set_state(pages_confirm_state)
    await message.answer(
        format_analysis_message(result),
        parse_mode='HTML',
        reply_markup=await confirm_pages_inline(suggested_pages),
    )


async def proceed_with_pages(
    message: Message,
    state: FSMContext,
    pages: int,
    tier_state,
    is_group: bool,
) -> None:
    """Continue order flow after page count is confirmed or entered."""
    await prompt_service_tier(message, state, pages, tier_state, is_group)


async def prompt_service_tier(message: Message, state: FSMContext, pages: int, tier_state, is_group: bool):
    """Show inline keyboard for review vs full tier selection."""
    await state.update_data(pages=pages)
    await state.set_state(tier_state)
    keyboard_fn = select_service_tier_group_inline if is_group else select_service_tier_inline
    keyboard = await keyboard_fn(pages)
    order_type = 'گروهی' if is_group else 'فردی'
    await message.answer(
        f'📦 نوع نسخه سفارش {order_type} رو انتخاب کن:\n'
        f'<i>📄 تعداد صفحات: {pages}</i>',
        parse_mode='HTML',
        reply_markup=keyboard,
    )


def compute_order_prices(pages: int, tier: str) -> dict:
    base_price = calculate_individual_price(pages, tier)
    group_price = calculate_group_price(pages, tier)
    return {
        'base_price': base_price,
        'group_price': group_price,
        'service_tier': tier,
    }


async def apply_tier_selection(
    callback_data: str,
    state: FSMContext,
    is_group: bool,
) -> tuple[str, dict] | None:
    """Parse tier callback and update FSM data with prices. Returns (tier, updated_data) or None."""
    if not callback_data.startswith('ord_tier:'):
        return None
    tier = callback_data.split(':')[1]
    if tier not in (ServiceOrder.TIER_REVIEW, ServiceOrder.TIER_FULL):
        return None
    data = await state.get_data()
    pages = data.get('pages', 0)
    prices = await sync_to_async(compute_order_prices)(pages, tier)
    await state.update_data(**prices)
    data = await state.get_data()
    return tier, data


def save_uploaded_file_to_order(order, data: dict):
    """Persist temp Telegram file to ServiceOrder.uploaded_file."""
    temp_path = data.get('temp_file_path')
    file_name = data.get('file_name', 'upload')
    if not temp_path:
        return
    path = Path(temp_path)
    if not path.exists():
        return
    from apps.telegram_bot.services.telegram_files import save_file_to_order
    save_file_to_order(order, path, file_name)
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def format_tier_price_confirmation(tier: str, data: dict, is_group: bool) -> str:
    label = tier_label(tier)
    if is_group:
        discount = get_group_discount_percent()
        return (
            f'✅ <b>{label}</b> انتخاب شد.\n\n'
            f'💵 قیمت پایه: {format_toman(data["base_price"])}\n'
            f'🎁 تخفیف گروهی {discount}٪: -{format_toman(int(data["base_price"]) - int(data["group_price"]))}\n'
            f'💳 <b>قیمت هر نفر: {format_toman(data["group_price"])}</b>'
        )
    return (
        f'✅ <b>{label}</b> انتخاب شد.\n\n'
        f'💰 <b>مبلغ قابل پرداخت: {format_toman(data["base_price"])}</b>'
    )
