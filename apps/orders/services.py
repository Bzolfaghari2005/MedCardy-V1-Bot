import logging
from django.conf import settings

from apps.orders.models import ServiceOrder, ServiceOrderMember
from apps.telegram_bot.utils import get_setting

logger = logging.getLogger(__name__)

DEFAULT_FULL_PRICE_PER_PAGE = 2500
DEFAULT_REVIEW_PRICE_PER_PAGE = 1250
DEFAULT_GROUP_DISCOUNT_PERCENT = 30


def _int_setting(key: str, default: int) -> int:
    try:
        return int(get_setting(key, str(default)))
    except (TypeError, ValueError):
        return default


def get_full_price_per_page() -> int:
    full = _int_setting('full_price_per_page_toman', 0)
    if full > 0:
        return full
    return _int_setting('price_per_page_toman', DEFAULT_FULL_PRICE_PER_PAGE)


def get_review_price_per_page() -> int:
    return _int_setting('review_price_per_page_toman', DEFAULT_REVIEW_PRICE_PER_PAGE)


def get_group_discount_percent() -> int:
    return _int_setting('group_discount_percent', DEFAULT_GROUP_DISCOUNT_PERCENT)


def get_price_per_page_for_tier(tier: str) -> int:
    if tier == ServiceOrder.TIER_REVIEW:
        return get_review_price_per_page()
    return get_full_price_per_page()


# Backward-compatible alias used in handlers
PRICE_PER_PAGE_TOMAN = DEFAULT_FULL_PRICE_PER_PAGE
GROUP_DISCOUNT_PERCENT = DEFAULT_GROUP_DISCOUNT_PERCENT


def calculate_individual_price(pages_count: int, tier: str = ServiceOrder.TIER_FULL) -> int:
    return pages_count * get_price_per_page_for_tier(tier)


def calculate_group_price(
    pages_count: int,
    tier: str = ServiceOrder.TIER_FULL,
    discount_percent: int | None = None,
) -> int:
    if discount_percent is None:
        discount_percent = get_group_discount_percent()
    base = calculate_individual_price(pages_count, tier)
    discount = int(base * discount_percent / 100)
    return base - discount


def create_individual_order(
    user,
    title: str,
    category,
    lesson,
    pages_count: int,
    service_tier: str = ServiceOrder.TIER_FULL,
    uploaded_file=None,
    university: str = '',
    user_note: str = '',
    detected_pages: int = 0,
    detected_char_count: int = 0,
):
    """Create ServiceOrder (individual) and payment."""
    from apps.payments.models import Payment
    from apps.payments.services.payment_service import create_payment

    base_price = calculate_individual_price(pages_count, service_tier)

    order = ServiceOrder.objects.create(
        creator_user=user,
        order_type=ServiceOrder.TYPE_INDIVIDUAL,
        title=title,
        category=category,
        lesson=lesson,
        university=university,
        uploaded_file=uploaded_file,
        pages_count=pages_count,
        service_tier=service_tier,
        detected_pages=detected_pages,
        detected_char_count=detected_char_count,
        base_price_toman=base_price,
        discount_percent=0,
        final_price_per_user_toman=base_price,
        status=ServiceOrder.STATUS_PENDING_PAYMENT,
        payment_status=ServiceOrder.PAYMENT_STATUS_PENDING,
        user_note=user_note,
    )

    payment, success, url = create_payment(
        user=user,
        amount_toman=base_price,
        payment_for_type=Payment.FOR_TYPE_INDIVIDUAL_ORDER,
        payment_for_id=order.id,
        description=f'سفارش فردی: {title}',
    )

    if not success:
        order.status = ServiceOrder.STATUS_CANCELLED
        order.save(update_fields=['status'])

    return order, payment, success, url


def create_group_order(
    user,
    title: str,
    category,
    lesson,
    pages_count: int,
    service_tier: str = ServiceOrder.TIER_FULL,
    uploaded_file=None,
    university: str = '',
    user_note: str = '',
    min_members: int = 5,
    discount_percent: int | None = None,
    detected_pages: int = 0,
    detected_char_count: int = 0,
):
    """Create ServiceOrder (group) with join link."""
    if discount_percent is None:
        discount_percent = get_group_discount_percent()

    base_price = calculate_individual_price(pages_count, service_tier)
    final_price = calculate_group_price(pages_count, service_tier, discount_percent)
    join_code = _generate_group_join_code()
    bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'MedCardyBot')
    join_link = f'https://t.me/{bot_username}?start={join_code}'

    order = ServiceOrder.objects.create(
        creator_user=user,
        order_type=ServiceOrder.TYPE_GROUP,
        title=title,
        category=category,
        lesson=lesson,
        university=university,
        uploaded_file=uploaded_file,
        pages_count=pages_count,
        service_tier=service_tier,
        detected_pages=detected_pages,
        detected_char_count=detected_char_count,
        base_price_toman=base_price,
        discount_percent=discount_percent,
        final_price_per_user_toman=final_price,
        min_group_members=min_members,
        paid_members_count=0,
        group_join_code=join_code,
        group_join_link=join_link,
        status=ServiceOrder.STATUS_WAITING_MEMBERS,
        payment_status=ServiceOrder.PAYMENT_STATUS_PARTIAL,
        user_note=user_note,
    )
    return order


def join_group_order(user, order: ServiceOrder):
    """
    Add user as a member and create Zibal payment.
    Returns (member, payment, success, url).
    """
    from apps.payments.models import Payment
    from apps.payments.services.payment_service import create_payment

    member, created = ServiceOrderMember.objects.get_or_create(
        order=order, user=user,
        defaults={
            'status': ServiceOrderMember.STATUS_PAYMENT_CREATED,
            'amount_paid_toman': order.final_price_per_user_toman,
        }
    )
    if not created and member.status == ServiceOrderMember.STATUS_PAID:
        return member, None, True, 'already_paid'

    payment, success, url = create_payment(
        user=user,
        amount_toman=int(order.final_price_per_user_toman),
        payment_for_type=Payment.FOR_TYPE_GROUP_MEMBER,
        payment_for_id=member.id,
        description=f'عضویت در سفارش گروهی: {order.title}',
    )

    member.payment = payment
    if success:
        member.status = ServiceOrderMember.STATUS_WAITING_PAYMENT
    else:
        member.status = ServiceOrderMember.STATUS_FAILED
    member.save(update_fields=['payment', 'status'])

    return member, payment, success, url


def cancel_service_order_with_refund(order) -> list[tuple]:
    """
    Refund all verified payments for a cancelled service order.
    Returns list of (user, amount_toman) tuples for users who received a refund.
    Idempotent — safe to call multiple times.
    """
    from apps.orders.models import ServiceOrderMember
    from apps.payments.models import Payment
    from apps.payments.services.notification_service import notify_order_cancelled_with_refund
    from apps.wallet.services import refund_payment_to_wallet

    if order.status != ServiceOrder.STATUS_CANCELLED:
        order.status = ServiceOrder.STATUS_CANCELLED
        order.save(update_fields=['status'])

    refunded: list[tuple] = []

    if order.order_type == ServiceOrder.TYPE_INDIVIDUAL:
        payments = Payment.objects.filter(
            payment_for_type=Payment.FOR_TYPE_INDIVIDUAL_ORDER,
            payment_for_id=order.id,
            status__in=[Payment.STATUS_VERIFIED, Payment.STATUS_ALREADY_VERIFIED],
        ).select_related('user')
        for payment in payments:
            if refund_payment_to_wallet(payment):
                refunded.append((payment.user, int(payment.amount_toman)))
    else:
        members = ServiceOrderMember.objects.filter(
            order=order,
            status=ServiceOrderMember.STATUS_PAID,
        ).select_related('user', 'payment')
        for member in members:
            if member.payment and refund_payment_to_wallet(member.payment):
                member.status = ServiceOrderMember.STATUS_CANCELLED
                member.save(update_fields=['status'])
                refunded.append((member.user, int(member.payment.amount_toman)))

    for user, amount in refunded:
        notify_order_cancelled_with_refund(user, order, amount)

    if refunded:
        logger.info(
            f'Order {order.order_code} cancelled with {len(refunded)} refund(s).'
        )
    return refunded


def _generate_group_join_code() -> str:
    from django.utils import timezone
    today = timezone.localdate()
    date_str = today.strftime('%y%m%d')
    count = ServiceOrder.objects.filter(
        order_type=ServiceOrder.TYPE_GROUP,
        group_join_code__startswith=f'G{date_str}'
    ).count()
    return f'G{date_str}{str(count + 1).zfill(4)}'
