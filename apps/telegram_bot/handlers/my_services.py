import logging
from aiogram import Router, F
from aiogram.types import Message
from asgiref.sync import sync_to_async

from apps.telegram_bot.filters import LabelFilter
from apps.telegram_bot.utils import tier_label, get_status_label

logger = logging.getLogger(__name__)
router = Router()


@router.message(LabelFilter('menu.my_services'))
async def my_services(message: Message):
    telegram_id = message.from_user.id
    data = await _get_user_services(telegram_id)
    orders, memberships = data['orders'], data['memberships']

    if not orders and not memberships:
        await message.answer(
            '🗂️ <b>سرویس‌های من</b>\n\n'
            '📭 هنوز سفارشی ثبت نکردی.\n\n'
            'از منوی «سفارش ساخت پادکست» می‌تونی اولین سفارشت رو ثبت کنی.',
            parse_mode='HTML'
        )
        return

    text_lines = ['🗂️ <b>سرویس‌های من:</b>\n']
    idx = 1

    for order in orders:
        order_type = 'فردی' if order.order_type == 'individual' else 'گروهی'
        status = get_status_label('status.order', order.status)
        prod_status = get_status_label('status.production', order.production_status)

        lines = [
            f'<b>{idx}. 🎙️ سفارش {order_type}</b>',
            f'🔖 کد سفارش: <code>{order.order_code}</code>',
            f'📌 عنوان: {order.title}',
            f'📦 نوع نسخه: {tier_label(order.service_tier)}',
            f'◉ وضعیت: {status}',
            f'🎙️ وضعیت تولید: {prod_status}',
        ]

        if order.order_type == 'group':
            lines.append(f'👥 اعضای پرداخت موفق: {order.paid_members_count} از {order.min_group_members} نفر')
            if order.group_join_link:
                lines.append(f'🔗 لینک دعوت: {order.group_join_link}')
            if order.private_channel_link:
                lines.append(f'📺 لینک کانال: {order.private_channel_link}')
        else:
            delivery_loc = 'پنل شخصی MedCardy'
            if order.personal_panel and order.personal_panel.channel_link:
                delivery_loc = order.personal_panel.channel_link
            lines.append(f'📥 محل تحویل: {delivery_loc}')

        text_lines.append('\n'.join(lines))
        text_lines.append('')
        idx += 1

    for membership in memberships:
        order = membership.order
        if any(o.id == order.id for o in orders):
            continue
        status = get_status_label('status.order', order.status)
        my_status = get_status_label('status.member', membership.status)

        lines = [
            f'<b>{idx}. 👥 سفارش گروهی (عضو)</b>',
            f'🔖 کد سفارش: <code>{order.order_code}</code>',
            f'📌 عنوان: {order.title}',
            f'📦 نوع نسخه: {tier_label(order.service_tier)}',
            f'🙋 نقش: عضو سفارش',
            f'💳 وضعیت پرداخت تو: {my_status}',
            f'👥 اعضای پرداخت موفق: {order.paid_members_count} از {order.min_group_members} نفر',
            f'◉ وضعیت سفارش: {status}',
        ]
        if membership.status == 'paid' and order.private_channel_link:
            lines.append(f'📺 لینک کانال: {order.private_channel_link}')

        text_lines.append('\n'.join(lines))
        text_lines.append('')
        idx += 1

    await message.answer('\n'.join(text_lines), parse_mode='HTML')


@sync_to_async
def _get_user_services(telegram_id: int):
    from apps.users.models import TelegramUser
    from apps.orders.models import ServiceOrder, ServiceOrderMember
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        orders = list(
            ServiceOrder.objects.filter(creator=user)
            .select_related('personal_panel')
            .order_by('-created_at')[:20]
        )
        memberships = list(
            ServiceOrderMember.objects.filter(user=user)
            .select_related('order', 'order__personal_panel')
            .order_by('-created_at')[:20]
        )
        return {'orders': orders, 'memberships': memberships}
    except TelegramUser.DoesNotExist:
        return {'orders': [], 'memberships': []}
