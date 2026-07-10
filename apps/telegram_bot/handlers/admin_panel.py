"""
Telegram admin panel handlers.
Accessible only to users listed in ADMIN_TELEGRAM_IDS.
"""
import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command, BaseFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.conf import settings

from apps.telegram_bot.states.admin_states import AdminStates
from apps.telegram_bot.utils import format_toman

logger = logging.getLogger(__name__)
router = Router()


class IsAdminFilter(BaseFilter):
    async def __call__(self, event) -> bool:
        user = getattr(event, 'from_user', None)
        return bool(user and user.id in settings.ADMIN_TELEGRAM_IDS)


def _admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='💳 پرداخت‌های در انتظار تأیید', callback_data='admin:pending_payments')],
        [InlineKeyboardButton(text='📋 سفارش‌های در انتظار بررسی', callback_data='admin:pending')],
        [InlineKeyboardButton(text='🔧 حالت تعمیر و نگهداری', callback_data='admin:maintenance')],
    ])


def _order_actions_keyboard(order_id: int, status: str) -> InlineKeyboardMarkup:
    buttons = []
    if status == 'waiting_admin_review':
        buttons.append([
            InlineKeyboardButton(text='⚙️ در حال تولید', callback_data=f'admin:production:{order_id}'),
            InlineKeyboardButton(text='✅ تحویل داده شد', callback_data=f'admin:deliver:{order_id}'),
        ])
    elif status == 'in_production':
        buttons.append([
            InlineKeyboardButton(text='✅ تحویل داده شد', callback_data=f'admin:deliver:{order_id}'),
        ])
    buttons.append([InlineKeyboardButton(text='🔙 بازگشت به لیست', callback_data='admin:pending')])
    buttons.append([InlineKeyboardButton(text='🏠 منوی ادمین', callback_data='admin:menu')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command('admin'), IsAdminFilter())
async def cmd_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        '🛠️ <b>پنل ادمین MedCardy</b>\n\nیک گزینه انتخاب کنید:',
        reply_markup=_admin_menu_keyboard(),
        parse_mode='HTML',
    )


@router.callback_query(F.data == 'admin:menu', IsAdminFilter())
async def cb_admin_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        '🛠️ <b>پنل ادمین MedCardy</b>\n\nیک گزینه انتخاب کنید:',
        reply_markup=_admin_menu_keyboard(),
        parse_mode='HTML',
    )
    await callback.answer()


def _payment_actions_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='✅ تأیید پرداخت', callback_data=f'admin:approve_payment:{payment_id}'),
            InlineKeyboardButton(text='❌ رد رسید', callback_data=f'admin:reject_payment:{payment_id}'),
        ],
        [InlineKeyboardButton(text='🔙 بازگشت به لیست', callback_data='admin:pending_payments')],
        [InlineKeyboardButton(text='🏠 منوی ادمین', callback_data='admin:menu')],
    ])


@router.callback_query(F.data == 'admin:pending_payments', IsAdminFilter())
async def cb_pending_payments(callback: CallbackQuery):
    payments = await _get_pending_payments()
    if not payments:
        await callback.message.edit_text(
            '💳 <b>پرداخت‌های در انتظار تأیید</b>\n\n✅ پرداختی در انتظار تأیید نیست.',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='🏠 منوی ادمین', callback_data='admin:menu')],
            ]),
            parse_mode='HTML',
        )
        await callback.answer()
        return

    buttons = []
    for payment in payments[:20]:
        type_label = _payment_type_label(payment.payment_for_type)
        buttons.append([
            InlineKeyboardButton(
                text=f'{payment.payment_code} | {type_label}',
                callback_data=f'admin:payment:{payment.id}',
            )
        ])
    buttons.append([InlineKeyboardButton(text='🏠 منوی ادمین', callback_data='admin:menu')])

    await callback.message.edit_text(
        f'💳 <b>پرداخت‌های در انتظار تأیید</b>\n\n'
        f'تعداد: {len(payments)} پرداخت\n'
        f'برای مشاهده جزئیات، یک پرداخت را انتخاب کنید:',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode='HTML',
    )
    await callback.answer()


@router.callback_query(F.data.startswith('admin:payment:'), IsAdminFilter())
async def cb_payment_detail(callback: CallbackQuery, bot: Bot):
    payment_id = int(callback.data.split(':')[-1])
    payment = await _get_payment(payment_id)
    if not payment:
        await callback.answer('پرداخت یافت نشد.', show_alert=True)
        return

    text = _format_payment_detail(payment)
    await callback.message.edit_text(
        text,
        reply_markup=_payment_actions_keyboard(payment.id),
        parse_mode='HTML',
    )
    if payment.receipt_file:
        try:
            from aiogram.types import FSInputFile
            await bot.send_photo(
                callback.from_user.id,
                photo=FSInputFile(payment.receipt_file.path),
                caption=f'📸 رسید پرداخت {payment.payment_code}',
            )
        except Exception as exc:
            logger.warning(f'Failed to send receipt to admin: {exc}')
    await callback.answer()


@router.callback_query(F.data.startswith('admin:approve_payment:'), IsAdminFilter())
async def cb_approve_payment(callback: CallbackQuery):
    payment_id = int(callback.data.split(':')[-1])
    result = await _approve_payment(payment_id)
    if not result:
        await callback.answer('پرداخت یافت نشد.', show_alert=True)
        return

    payment, success, msg = result
    if not success:
        await callback.answer(msg, show_alert=True)
        return

    await callback.message.edit_text(
        f'✅ <b>پرداخت تأیید شد</b>\n\n'
        f'🔑 کد: <code>{payment.payment_code}</code>\n'
        f'💰 مبلغ: {format_toman(payment.amount_toman)}\n\n'
        f'کاربر مطلع شد و فرآیند مرتبط فعال شد.',
        reply_markup=_admin_menu_keyboard(),
        parse_mode='HTML',
    )
    await callback.answer('پرداخت تأیید شد.')


@router.callback_query(F.data.startswith('admin:reject_payment:'), IsAdminFilter())
async def cb_reject_payment_start(callback: CallbackQuery, state: FSMContext):
    payment_id = int(callback.data.split(':')[-1])
    payment = await _get_payment(payment_id)
    if not payment:
        await callback.answer('پرداخت یافت نشد.', show_alert=True)
        return

    await state.set_state(AdminStates.waiting_reject_reason)
    await state.update_data(payment_id=payment_id)
    await callback.message.answer(
        f'❌ رد رسید پرداخت <code>{payment.payment_code}</code>\n\n'
        f'دلیل رد را بنویس (اختیاری — برای رد بدون دلیل «-» بفرست):\n'
        f'<i>برای لغو: /admin</i>',
        parse_mode='HTML',
    )
    await callback.answer()


@router.message(AdminStates.waiting_reject_reason, IsAdminFilter())
async def handle_reject_reason(message: Message, state: FSMContext):
    data = await state.get_data()
    payment_id = data.get('payment_id')
    if not payment_id:
        await state.clear()
        await message.answer('❌ خطا: پرداخت مشخص نیست. /admin را دوباره بزنید.')
        return

    reason = (message.text or '').strip()
    if reason == '-':
        reason = ''

    result = await _reject_payment(payment_id, reason)
    await state.clear()

    if not result:
        await message.answer('❌ پرداخت یافت نشد یا رد ناموفق بود.')
        return

    payment, success, msg = result
    await message.answer(
        f'❌ <b>رسید رد شد</b>\n\n'
        f'🔑 کد: <code>{payment.payment_code}</code>\n'
        f'کاربر مطلع شد.',
        reply_markup=_admin_menu_keyboard(),
        parse_mode='HTML',
    )


def _payment_type_label(payment_for_type: str) -> str:
    labels = {
        'course_purchase': 'دوره',
        'individual_service_order': 'فردی',
        'group_order_member': 'گروهی',
        'wallet_charge': 'کیف پول',
    }
    return labels.get(payment_for_type, payment_for_type)


def _format_payment_detail(payment) -> str:
    username = f'@{payment.user.username}' if payment.user.username else '—'
    lines = [
        f'💳 <b>جزئیات پرداخت</b>',
        f'',
        f'🔑 کد: <code>{payment.payment_code}</code>',
        f'👤 کاربر: {payment.user.user_code} ({username})',
        f'📂 نوع: {_payment_type_label(payment.payment_for_type)}',
        f'💰 مبلغ: {format_toman(payment.amount_toman)}',
        f'📊 وضعیت: {payment.get_status_display()}',
    ]
    if payment.description:
        lines.append(f'📝 توضیح: {payment.description[:200]}')
    if payment.receipt_submitted_at:
        lines.append(f'📅 زمان ارسال رسید: {payment.receipt_submitted_at.strftime("%Y/%m/%d %H:%M")}')
    return '\n'.join(lines)


@router.callback_query(F.data == 'admin:pending', IsAdminFilter())
async def cb_pending_orders(callback: CallbackQuery):
    orders = await _get_pending_orders()
    if not orders:
        await callback.message.edit_text(
            '📋 <b>سفارش‌های در انتظار بررسی</b>\n\n✅ سفارشی در انتظار بررسی نیست.',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='🏠 منوی ادمین', callback_data='admin:menu')],
            ]),
            parse_mode='HTML',
        )
        await callback.answer()
        return

    buttons = []
    for order in orders[:20]:
        type_label = 'فردی' if order.order_type == 'individual' else 'گروهی'
        buttons.append([
            InlineKeyboardButton(
                text=f'{order.order_code} | {type_label}',
                callback_data=f'admin:order:{order.id}',
            )
        ])
    buttons.append([InlineKeyboardButton(text='🏠 منوی ادمین', callback_data='admin:menu')])

    await callback.message.edit_text(
        f'📋 <b>سفارش‌های در انتظار بررسی</b>\n\n'
        f'تعداد: {len(orders)} سفارش\n'
        f'برای مشاهده جزئیات، یک سفارش را انتخاب کنید:',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode='HTML',
    )
    await callback.answer()


@router.callback_query(F.data.startswith('admin:order:'), IsAdminFilter())
async def cb_order_detail(callback: CallbackQuery):
    order_id = int(callback.data.split(':')[-1])
    order = await _get_order(order_id)
    if not order:
        await callback.answer('سفارش یافت نشد.', show_alert=True)
        return

    text = _format_order_detail(order)
    await callback.message.edit_text(
        text,
        reply_markup=_order_actions_keyboard(order.id, order.status),
        parse_mode='HTML',
    )
    await callback.answer()


@router.callback_query(F.data.startswith('admin:production:'), IsAdminFilter())
async def cb_mark_production(callback: CallbackQuery):
    order_id = int(callback.data.split(':')[-1])
    order = await _mark_in_production(order_id)
    if not order:
        await callback.answer('سفارش یافت نشد.', show_alert=True)
        return

    await callback.message.edit_text(
        _format_order_detail(order),
        reply_markup=_order_actions_keyboard(order.id, order.status),
        parse_mode='HTML',
    )
    await callback.answer('⚙️ وضعیت به «در حال تولید» تغییر کرد.')


@router.callback_query(F.data.startswith('admin:deliver:'), IsAdminFilter())
async def cb_start_deliver(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(':')[-1])
    order = await _get_order(order_id)
    if not order:
        await callback.answer('سفارش یافت نشد.', show_alert=True)
        return

    await state.set_state(AdminStates.waiting_channel_link)
    await state.update_data(order_id=order_id)

    await callback.message.answer(
        f'🔗 لینک کانال یا دعوت برای سفارش <code>{order.order_code}</code> را ارسال کنید:\n\n'
        f'<i>برای لغو: /admin</i>',
        parse_mode='HTML',
    )
    await callback.answer()


@router.message(AdminStates.waiting_channel_link, IsAdminFilter())
async def handle_channel_link(message: Message, state: FSMContext, bot: Bot):
    link = (message.text or '').strip()
    if not link.startswith(('http://', 'https://', 't.me/')):
        await message.answer('❌ لینک معتبر نیست. لطفاً یک URL یا لینک t.me ارسال کنید.')
        return

    if link.startswith('t.me/'):
        link = f'https://{link}'

    data = await state.get_data()
    order_id = data.get('order_id')
    if not order_id:
        await state.clear()
        await message.answer('❌ خطا: سفارش مشخص نیست. /admin را دوباره بزنید.')
        return

    result = await _deliver_order(order_id, link)
    await state.clear()

    if not result:
        await message.answer('❌ سفارش یافت نشد یا تحویل ناموفق بود.')
        return

    order, notified_count = result
    await message.answer(
        f'✅ سفارش <code>{order.order_code}</code> تحویل داده شد.\n'
        f'📨 پیام به {notified_count} کاربر ارسال شد.',
        reply_markup=_admin_menu_keyboard(),
        parse_mode='HTML',
    )


@router.callback_query(F.data == 'admin:maintenance', IsAdminFilter())
async def cb_maintenance(callback: CallbackQuery):
    is_on = await _get_maintenance_mode()
    status_text = '🟢 فعال' if is_on else '⚪ غیرفعال'
    toggle_text = '🔴 خاموش کن' if is_on else '🟢 روشن کن'

    await callback.message.edit_text(
        f'🔧 <b>حالت تعمیر و نگهداری</b>\n\n'
        f'وضعیت فعلی: {status_text}\n\n'
        f'در حالت فعال، کاربران عادی نمی‌توانند از ربات استفاده کنند.',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data='admin:maintenance:toggle')],
            [InlineKeyboardButton(text='🏠 منوی ادمین', callback_data='admin:menu')],
        ]),
        parse_mode='HTML',
    )
    await callback.answer()


@router.callback_query(F.data == 'admin:maintenance:toggle', IsAdminFilter())
async def cb_maintenance_toggle(callback: CallbackQuery):
    new_value, is_on = await _toggle_maintenance_mode()
    status_text = '🟢 فعال' if is_on else '⚪ غیرفعال'
    toggle_text = '🔴 خاموش کن' if is_on else '🟢 روشن کن'

    await callback.message.edit_text(
        f'🔧 <b>حالت تعمیر و نگهداری</b>\n\n'
        f'وضعیت فعلی: {status_text}\n\n'
        f'✅ تنظیم به <code>{new_value}</code> تغییر کرد.',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data='admin:maintenance:toggle')],
            [InlineKeyboardButton(text='🏠 منوی ادمین', callback_data='admin:menu')],
        ]),
        parse_mode='HTML',
    )
    await callback.answer('وضعیت تعمیر به‌روزرسانی شد.')


def _format_order_detail(order) -> str:
    type_label = 'فردی' if order.order_type == 'individual' else 'گروهی'
    tier_label = 'نسخه مروری' if order.service_tier == 'review' else 'آموزش کامل'
    username = f'@{order.creator_user.username}' if order.creator_user.username else '—'

    lines = [
        f'📦 <b>جزئیات سفارش</b>',
        f'',
        f'🔖 کد: <code>{order.order_code}</code>',
        f'📌 عنوان: {order.title}',
        f'👤 کاربر: {order.creator_user.user_code} ({username})',
        f'📂 نوع: {type_label} | {tier_label}',
        f'📄 صفحات: {order.pages_count}',
        f'💰 قیمت: {format_toman(order.final_price_per_user_toman)}',
        f'📊 وضعیت: {order.get_status_display()}',
        f'🎙️ تولید: {order.get_production_status_display()}',
    ]

    if order.order_type == 'group':
        lines.append(f'👥 اعضای پرداخت‌شده: {order.paid_members_count}/{order.min_group_members}')

    if order.user_note:
        lines.append(f'📝 یادداشت کاربر: {order.user_note[:200]}')

    if order.private_channel_link:
        lines.append(f'🔗 لینک کانال: {order.private_channel_link}')

    return '\n'.join(lines)


@sync_to_async
def _get_pending_orders():
    from apps.orders.models import ServiceOrder
    return list(
        ServiceOrder.objects.filter(status=ServiceOrder.STATUS_WAITING_ADMIN)
        .select_related('creator_user')
        .order_by('-created_at')
    )


@sync_to_async
def _get_pending_payments():
    from apps.payments.models import Payment
    return list(
        Payment.objects.filter(status=Payment.STATUS_RECEIPT_SUBMITTED)
        .select_related('user')
        .order_by('-receipt_submitted_at')
    )


@sync_to_async
def _get_payment(payment_id: int):
    from apps.payments.models import Payment
    try:
        return Payment.objects.select_related('user').get(id=payment_id)
    except Payment.DoesNotExist:
        return None


@sync_to_async
def _approve_payment(payment_id: int):
    from apps.payments.models import Payment
    from apps.payments.services.payment_service import approve_manual_payment
    try:
        payment = Payment.objects.select_related('user').get(id=payment_id)
    except Payment.DoesNotExist:
        return None
    return approve_manual_payment(payment)


@sync_to_async
def _reject_payment(payment_id: int, reason: str = ''):
    from apps.payments.models import Payment
    from apps.payments.services.payment_service import reject_manual_payment
    try:
        payment = Payment.objects.select_related('user').get(id=payment_id)
    except Payment.DoesNotExist:
        return None
    return reject_manual_payment(payment, reason=reason)


@sync_to_async
def _get_order(order_id: int):
    from apps.orders.models import ServiceOrder
    try:
        return ServiceOrder.objects.select_related('creator_user', 'personal_panel').get(id=order_id)
    except ServiceOrder.DoesNotExist:
        return None


@sync_to_async
def _mark_in_production(order_id: int):
    from apps.orders.models import ServiceOrder
    try:
        order = ServiceOrder.objects.select_related('creator_user').get(id=order_id)
    except ServiceOrder.DoesNotExist:
        return None
    order.status = ServiceOrder.STATUS_IN_PRODUCTION
    order.production_status = ServiceOrder.PRODUCTION_STATUS_IN_PROGRESS
    order.save(update_fields=['status', 'production_status'])
    return order


@sync_to_async
def _deliver_order(order_id: int, channel_link: str):
    from apps.orders.models import ServiceOrder, ServiceOrderMember
    from apps.users.models import PersonalPanel
    from apps.payments.services.notification_service import send_telegram_message

    try:
        order = ServiceOrder.objects.select_related('creator_user', 'personal_panel').get(id=order_id)
    except ServiceOrder.DoesNotExist:
        return None

    order.private_channel_link = channel_link
    order.status = ServiceOrder.STATUS_DELIVERED
    order.production_status = ServiceOrder.PRODUCTION_STATUS_DONE
    order.save(update_fields=['private_channel_link', 'status', 'production_status'])

    if order.personal_panel_id:
        panel = order.personal_panel
        panel.channel_link = channel_link
        panel.invite_link = channel_link
        panel.status = PersonalPanel.STATUS_ACTIVE
        panel.save(update_fields=['channel_link', 'invite_link', 'status'])

    delivery_text = (
        f'🎉 <b>سفارش شما آماده است!</b>\n\n'
        f'🔖 کد سفارش: <code>{order.order_code}</code>\n'
        f'📌 عنوان: {order.title}\n\n'
        f'🔗 لینک دسترسی:\n{channel_link}'
    )

    notified_count = 0
    if order.order_type == ServiceOrder.TYPE_GROUP:
        members = ServiceOrderMember.objects.filter(
            order=order,
            status=ServiceOrderMember.STATUS_PAID,
        ).select_related('user')
        for member in members:
            if send_telegram_message(member.user.telegram_id, delivery_text):
                notified_count += 1
            member.access_status = ServiceOrderMember.ACCESS_STATUS_DELIVERED
            member.save(update_fields=['access_status'])
    else:
        if send_telegram_message(order.creator_user.telegram_id, delivery_text):
            notified_count = 1

    return order, notified_count


@sync_to_async
def _get_maintenance_mode() -> bool:
    from apps.settings_app.models import Setting
    try:
        return Setting.objects.get(key='maintenance_mode').value.lower() in ('true', '1', 'yes')
    except Setting.DoesNotExist:
        return False


@sync_to_async
def _toggle_maintenance_mode() -> tuple[str, bool]:
    from apps.settings_app.models import Setting
    setting, _ = Setting.objects.get_or_create(
        key='maintenance_mode',
        defaults={'value': 'false', 'description': 'حالت تعمیر'},
    )
    is_on = setting.value.lower() in ('true', '1', 'yes')
    new_value = 'false' if is_on else 'true'
    setting.value = new_value
    setting.save(update_fields=['value'])
    return new_value, new_value == 'true'
