"""
Core payment business logic.
Handles Zibal callback, verification, and post-payment actions.
"""
import logging
from django.db import transaction
from django.utils import timezone
from apps.payments.models import Payment
from apps.payments.services.zibal_service import ZibalPaymentService

logger = logging.getLogger(__name__)

zibal = ZibalPaymentService()


def is_payment_gateway_enabled() -> bool:
    from apps.settings_app.models import Setting
    try:
        value = Setting.objects.get(key='enable_payment_gateway').value
    except Setting.DoesNotExist:
        value = 'false'
    return value.lower() in ('true', '1', 'yes')


def create_payment(
    user,
    amount_toman: int,
    payment_for_type: str,
    payment_for_id: int,
    description: str = '',
) -> tuple[Payment, bool, str]:
    """Create payment via gateway or manual receipt based on settings."""
    if is_payment_gateway_enabled():
        return create_zibal_payment(
            user, amount_toman, payment_for_type, payment_for_id, description
        )
    return create_manual_payment(
        user, amount_toman, payment_for_type, payment_for_id, description
    )


def create_manual_payment(
    user,
    amount_toman: int,
    payment_for_type: str,
    payment_for_id: int,
    description: str = '',
) -> tuple[Payment, bool, str]:
    """
    Create a manual receipt-based Payment record.
    Returns (payment, success, payment_code).
    """
    payment = Payment.objects.create(
        user=user,
        amount_toman=amount_toman,
        provider=Payment.PROVIDER_MANUAL,
        payment_method=Payment.METHOD_MANUAL_RECEIPT,
        payment_for_type=payment_for_type,
        payment_for_id=payment_for_id,
        description=description,
        status=Payment.STATUS_WAITING_USER,
    )
    logger.info(f'Manual payment created: {payment.payment_code}')
    return payment, True, payment.payment_code


def create_zibal_payment(
    user,
    amount_toman: int,
    payment_for_type: str,
    payment_for_id: int,
    description: str = '',
) -> tuple[Payment, bool, str]:
    """
    Create a Payment record and call Zibal request API.
    Returns (payment, success, payment_url_or_error_msg).
    """
    if not is_payment_gateway_enabled():
        return create_manual_payment(
            user, amount_toman, payment_for_type, payment_for_id, description
        )

    payment = Payment.objects.create(
        user=user,
        amount_toman=amount_toman,
        provider=Payment.PROVIDER_ZIBAL,
        payment_method=Payment.METHOD_ZIBAL_IPG,
        payment_for_type=payment_for_type,
        payment_for_id=payment_for_id,
        description=description,
        status=Payment.STATUS_CREATED,
    )

    result = zibal.request_payment(payment)

    if result.success:
        payment.zibal_track_id = result.track_id
        payment.zibal_result = result.result_code
        payment.status = Payment.STATUS_WAITING_USER
        payment.save(update_fields=['zibal_track_id', 'zibal_result', 'status'])
        url = zibal.build_start_url(result.track_id)
        logger.info(f'Zibal payment created: {payment.payment_code}, trackId={result.track_id}')
        return payment, True, url
    else:
        payment.zibal_result = result.result_code
        payment.status = Payment.STATUS_REQUEST_FAILED
        payment.save(update_fields=['zibal_result', 'status'])
        logger.warning(f'Zibal payment request failed: {payment.payment_code}, msg={result.message}')
        return payment, False, result.message


@transaction.atomic
def handle_zibal_callback(params: dict) -> tuple[Payment, bool, str]:
    """
    Process Zibal callback GET parameters.
    Returns (payment, verified, message).
    """
    track_id = str(params.get('trackId', ''))
    success_flag = params.get('success', '0')
    status_flag = params.get('status')
    order_id = params.get('orderId', '')

    # Find payment by trackId or orderId
    payment = None
    if track_id:
        payment = Payment.objects.filter(zibal_track_id=track_id).select_for_update().first()
    if not payment and order_id:
        payment = Payment.objects.filter(payment_code=order_id).select_for_update().first()

    if not payment:
        logger.error(f'No payment found for callback: trackId={track_id}, orderId={order_id}')
        return None, False, 'پرداخت یافت نشد'

    # Store callback data
    payment.callback_success = int(success_flag) if str(success_flag).isdigit() else 0
    payment.callback_status = int(status_flag) if str(status_flag).lstrip('-').isdigit() else None
    payment.callback_payload = dict(params)

    if not track_id and payment.zibal_track_id:
        track_id = payment.zibal_track_id

    # Idempotency: already terminal
    if payment.status == Payment.STATUS_VERIFIED:
        payment.save(update_fields=['callback_success', 'callback_status', 'callback_payload'])
        logger.info(f'Payment {payment.payment_code} already verified. Skipping.')
        return payment, True, 'پرداخت قبلاً تأیید شده است'

    payment.status = Payment.STATUS_CALLBACK_RECEIVED
    payment.save(update_fields=['callback_success', 'callback_status', 'callback_payload', 'status'])

    if str(success_flag) != '1':
        payment.status = Payment.STATUS_CANCELLED
        payment.save(update_fields=['status'])
        logger.info(f'Payment {payment.payment_code} cancelled by user (success=0)')
        _handle_cancelled(payment)
        return payment, False, 'پرداخت توسط کاربر لغو شد'

    return handle_verify(payment)


def handle_verify(payment: Payment) -> tuple[Payment, bool, str]:
    """
    Call Zibal verify and process the result.
    Idempotent: safe to call multiple times.
    """
    if payment.status == Payment.STATUS_VERIFIED:
        return payment, True, 'قبلاً تأیید شده'

    track_id = payment.zibal_track_id
    if not track_id:
        payment.status = Payment.STATUS_VERIFICATION_FAILED
        payment.save(update_fields=['status'])
        return payment, False, 'trackId موجود نیست'

    payment.status = Payment.STATUS_VERIFYING
    payment.save(update_fields=['status'])

    verify_result = zibal.verify_payment(track_id)

    payment.zibal_result = verify_result.result_code
    payment.zibal_status = verify_result.status
    payment.zibal_message = verify_result.message
    payment.verify_payload = verify_result.raw_response

    if verify_result.ref_number:
        payment.zibal_ref_number = verify_result.ref_number
    if verify_result.card_number:
        payment.zibal_card_number = verify_result.card_number
    if verify_result.hashed_card_number:
        payment.zibal_hashed_card_number = verify_result.hashed_card_number

    if verify_result.success:
        if verify_result.result_code == 201:
            payment.status = Payment.STATUS_ALREADY_VERIFIED
        else:
            payment.status = Payment.STATUS_VERIFIED
        payment.verified_at = timezone.now()
        payment.paid_at = timezone.now()
        payment.save(update_fields=[
            'zibal_result', 'zibal_status', 'zibal_message', 'verify_payload',
            'zibal_ref_number', 'zibal_card_number', 'zibal_hashed_card_number',
            'status', 'verified_at', 'paid_at',
        ])
        logger.info(f'Payment {payment.payment_code} verified successfully (result={verify_result.result_code})')
        _process_after_verification(payment)
        return payment, True, 'پرداخت با موفقیت تأیید شد'
    else:
        payment.status = Payment.STATUS_VERIFICATION_FAILED
        payment.save(update_fields=[
            'zibal_result', 'zibal_status', 'zibal_message', 'verify_payload', 'status',
        ])
        logger.warning(f'Payment {payment.payment_code} verification failed (result={verify_result.result_code})')
        _notify_failed(payment)
        return payment, False, verify_result.message


def _process_after_verification(payment: Payment) -> None:
    """Dispatch to the correct handler after successful verification."""
    from apps.payments.services import notification_service as notif
    try:
        if payment.payment_for_type == Payment.FOR_TYPE_COURSE_PURCHASE:
            _handle_course_purchase(payment)
        elif payment.payment_for_type == Payment.FOR_TYPE_INDIVIDUAL_ORDER:
            _handle_individual_order(payment)
        elif payment.payment_for_type == Payment.FOR_TYPE_GROUP_MEMBER:
            _handle_group_order_member(payment)
        elif payment.payment_for_type == Payment.FOR_TYPE_WALLET_CHARGE:
            _handle_wallet_charge(payment)
    except Exception as exc:
        logger.error(f'Post-verification handler failed for {payment.payment_code}: {exc}', exc_info=True)
        payment.admin_note += f'\nPost-verify error: {exc}'
        payment.status = Payment.STATUS_MANUAL_REVIEW
        payment.save(update_fields=['admin_note', 'status'])


def _handle_course_purchase(payment: Payment) -> None:
    from apps.courses.models import CoursePurchase
    from apps.users.services import get_or_create_personal_panel
    from apps.payments.services.notification_service import notify_payment_success_course

    try:
        purchase = CoursePurchase.objects.get(id=payment.payment_for_id)
    except CoursePurchase.DoesNotExist:
        logger.error(f'CoursePurchase {payment.payment_for_id} not found for payment {payment.payment_code}')
        return

    purchase.payment_status = CoursePurchase.PAYMENT_STATUS_PAID
    panel, created = get_or_create_personal_panel(payment.user)
    purchase.personal_panel = panel

    if panel.status == 'active':
        purchase.access_status = CoursePurchase.ACCESS_STATUS_WAITING_CONTENT
    else:
        purchase.access_status = CoursePurchase.ACCESS_STATUS_WAITING_PANEL

    purchase.save(update_fields=['payment_status', 'access_status', 'personal_panel'])
    notify_payment_success_course(payment, purchase)


def _handle_individual_order(payment: Payment) -> None:
    from apps.orders.models import ServiceOrder
    from apps.users.services import get_or_create_personal_panel
    from apps.payments.services.notification_service import notify_payment_success_individual_order

    try:
        order = ServiceOrder.objects.get(id=payment.payment_for_id)
    except ServiceOrder.DoesNotExist:
        logger.error(f'ServiceOrder {payment.payment_for_id} not found for payment {payment.payment_code}')
        return

    order.payment_status = ServiceOrder.PAYMENT_STATUS_PAID
    order.status = ServiceOrder.STATUS_WAITING_ADMIN
    order.production_status = ServiceOrder.PRODUCTION_STATUS_WAITING_ADMIN
    panel, created = get_or_create_personal_panel(payment.user)
    order.personal_panel = panel
    order.save(update_fields=['payment_status', 'status', 'production_status', 'personal_panel'])
    notify_payment_success_individual_order(payment, order)
    from apps.payments.services.notification_service import notify_admins_new_order_waiting_review
    notify_admins_new_order_waiting_review(order)


def _handle_group_order_member(payment: Payment) -> None:
    from apps.orders.models import ServiceOrderMember, ServiceOrder
    from apps.payments.services.notification_service import (
        notify_payment_success_group_member, notify_group_minimum_reached
    )

    try:
        member = ServiceOrderMember.objects.select_related('order').get(id=payment.payment_for_id)
    except ServiceOrderMember.DoesNotExist:
        logger.error(f'ServiceOrderMember {payment.payment_for_id} not found for payment {payment.payment_code}')
        return

    member.status = ServiceOrderMember.STATUS_PAID
    member.access_status = ServiceOrderMember.ACCESS_STATUS_WAITING_DELIVERY
    member.amount_paid_toman = payment.amount_toman
    member.save(update_fields=['status', 'access_status', 'amount_paid_toman'])

    order = member.order
    paid_count = ServiceOrderMember.objects.filter(
        order=order, status=ServiceOrderMember.STATUS_PAID
    ).count()
    order.paid_members_count = paid_count
    order.save(update_fields=['paid_members_count'])

    notify_payment_success_group_member(payment, member, order)

    if paid_count >= order.min_group_members and order.status == ServiceOrder.STATUS_WAITING_MEMBERS:
        order.status = ServiceOrder.STATUS_WAITING_ADMIN
        order.production_status = ServiceOrder.PRODUCTION_STATUS_WAITING_ADMIN
        order.save(update_fields=['status', 'production_status'])
        notify_group_minimum_reached(order)
        from apps.payments.services.notification_service import notify_admins_new_order_waiting_review
        notify_admins_new_order_waiting_review(order)


def _handle_wallet_charge(payment: Payment) -> None:
    from django.db.models import F
    from apps.users.models import TelegramUser
    from apps.wallet.models import WalletTransaction
    from apps.payments.services.notification_service import notify_wallet_charge_success

    TelegramUser.objects.filter(id=payment.user_id).update(
        wallet_balance=F('wallet_balance') + payment.amount_toman
    )
    WalletTransaction.objects.create(
        user=payment.user,
        amount_toman=payment.amount_toman,
        transaction_type=WalletTransaction.TYPE_CHARGE,
        payment=payment,
        description=f'شارژ کیف پول - {payment.payment_code}',
    )
    notify_wallet_charge_success(payment)


def _handle_cancelled(payment: Payment) -> None:
    """
    Called when user cancels payment on the gateway (success=0).
    Updates the related object's status and sends a context-aware notification.
    """
    try:
        if payment.payment_for_type == Payment.FOR_TYPE_INDIVIDUAL_ORDER:
            _cancel_individual_order(payment)
        elif payment.payment_for_type == Payment.FOR_TYPE_GROUP_MEMBER:
            _cancel_group_member(payment)
        elif payment.payment_for_type == Payment.FOR_TYPE_COURSE_PURCHASE:
            _cancel_course_purchase(payment)
        else:
            # wallet charge or unknown — just notify
            _notify_failed(payment)
    except Exception as exc:
        logger.error(f'Cancel handler failed for {payment.payment_code}: {exc}', exc_info=True)
        _notify_failed(payment)


def _cancel_individual_order(payment: Payment) -> None:
    from apps.orders.models import ServiceOrder
    from apps.payments.services.notification_service import notify_payment_cancelled_individual_order
    try:
        order = ServiceOrder.objects.get(id=payment.payment_for_id)
        order.payment_status = ServiceOrder.PAYMENT_STATUS_FAILED
        order.status = ServiceOrder.STATUS_CANCELLED
        order.save(update_fields=['payment_status', 'status'])
        logger.info(f'Individual order {order.order_code} cancelled due to payment cancellation.')
        notify_payment_cancelled_individual_order(payment, order)
    except ServiceOrder.DoesNotExist:
        logger.error(f'ServiceOrder {payment.payment_for_id} not found for cancelled payment {payment.payment_code}')
        _notify_failed(payment)


def _cancel_group_member(payment: Payment) -> None:
    from apps.orders.models import ServiceOrderMember
    from apps.payments.services.notification_service import notify_payment_cancelled_group_member
    try:
        member = ServiceOrderMember.objects.select_related('order').get(id=payment.payment_for_id)
        member.status = ServiceOrderMember.STATUS_CANCELLED
        member.save(update_fields=['status'])
        logger.info(f'Group member {member.id} (order {member.order.order_code}) cancelled due to payment cancellation.')
        notify_payment_cancelled_group_member(payment, member, member.order)
    except ServiceOrderMember.DoesNotExist:
        logger.error(f'ServiceOrderMember {payment.payment_for_id} not found for cancelled payment {payment.payment_code}')
        _notify_failed(payment)


def _cancel_course_purchase(payment: Payment) -> None:
    from apps.courses.models import CoursePurchase
    from apps.payments.services.notification_service import notify_payment_cancelled_course
    try:
        purchase = CoursePurchase.objects.select_related('course').get(id=payment.payment_for_id)
        purchase.payment_status = CoursePurchase.PAYMENT_STATUS_CANCELLED
        purchase.access_status = CoursePurchase.ACCESS_STATUS_CANCELLED
        purchase.save(update_fields=['payment_status', 'access_status'])
        logger.info(f'CoursePurchase {purchase.purchase_code} cancelled due to payment cancellation.')
        notify_payment_cancelled_course(payment, purchase)
    except CoursePurchase.DoesNotExist:
        logger.error(f'CoursePurchase {payment.payment_for_id} not found for cancelled payment {payment.payment_code}')
        _notify_failed(payment)


def _notify_failed(payment: Payment) -> None:
    from apps.payments.services.notification_service import notify_payment_failed
    try:
        notify_payment_failed(payment)
    except Exception as exc:
        logger.error(f'Failed to send failure notification for {payment.payment_code}: {exc}')


@transaction.atomic
def submit_payment_receipt(payment: Payment, receipt_file) -> tuple[Payment, bool, str]:
    """Save uploaded receipt and mark payment as awaiting admin review."""
    if payment.provider != Payment.PROVIDER_MANUAL:
        return payment, False, 'این پرداخت از نوع رسید نیست'

    if payment.status == Payment.STATUS_RECEIPT_SUBMITTED:
        return payment, False, 'رسید قبلاً ارسال شده و در انتظار تأیید است'

    if payment.status == Payment.STATUS_VERIFIED:
        return payment, False, 'پرداخت قبلاً تأیید شده است'

    if payment.status not in (
        Payment.STATUS_WAITING_USER,
        Payment.STATUS_RECEIPT_REJECTED,
    ):
        return payment, False, 'وضعیت پرداخت برای ارسال رسید مناسب نیست'

    payment.receipt_file = receipt_file
    payment.receipt_submitted_at = timezone.now()
    payment.status = Payment.STATUS_RECEIPT_SUBMITTED
    payment.receipt_rejected_reason = ''
    payment.save(update_fields=[
        'receipt_file', 'receipt_submitted_at', 'status', 'receipt_rejected_reason',
    ])
    logger.info(f'Receipt submitted for payment {payment.payment_code}')

    from apps.payments.services.notification_service import notify_admins_pending_receipt
    notify_admins_pending_receipt(payment)
    return payment, True, 'رسید دریافت شد'


@transaction.atomic
def approve_manual_payment(payment: Payment, admin_note: str = '') -> tuple[Payment, bool, str]:
    """Approve a manual receipt payment and run post-verification handlers."""
    payment = Payment.objects.select_for_update().get(pk=payment.pk)

    if payment.status in (Payment.STATUS_VERIFIED, Payment.STATUS_ALREADY_VERIFIED):
        return payment, True, 'قبلاً تأیید شده'

    if payment.status != Payment.STATUS_RECEIPT_SUBMITTED:
        return payment, False, 'این پرداخت در انتظار تأیید رسید نیست'

    if admin_note:
        payment.admin_note = (payment.admin_note + '\n' + admin_note).strip()

    payment.status = Payment.STATUS_VERIFIED
    payment.verified_at = timezone.now()
    payment.paid_at = timezone.now()
    payment.receipt_reviewed_at = timezone.now()
    payment.save(update_fields=[
        'status', 'verified_at', 'paid_at', 'receipt_reviewed_at', 'admin_note',
    ])
    logger.info(f'Manual payment {payment.payment_code} approved by admin')
    _process_after_verification(payment)
    return payment, True, 'پرداخت تأیید شد'


@transaction.atomic
def reject_manual_payment(payment: Payment, reason: str = '') -> tuple[Payment, bool, str]:
    """Reject a manual receipt payment."""
    payment = Payment.objects.select_for_update().get(pk=payment.pk)

    if payment.status != Payment.STATUS_RECEIPT_SUBMITTED:
        return payment, False, 'این پرداخت در انتظار تأیید رسید نیست'

    payment.status = Payment.STATUS_RECEIPT_REJECTED
    payment.receipt_rejected_reason = reason
    payment.receipt_reviewed_at = timezone.now()
    payment.save(update_fields=[
        'status', 'receipt_rejected_reason', 'receipt_reviewed_at',
    ])
    logger.info(f'Manual payment {payment.payment_code} rejected: {reason}')
    _handle_receipt_rejected(payment)

    from apps.payments.services.notification_service import notify_receipt_rejected
    notify_receipt_rejected(payment)
    return payment, True, 'رسید رد شد'


def _handle_receipt_rejected(payment: Payment) -> None:
    """Update related objects when a receipt is rejected."""
    try:
        if payment.payment_for_type == Payment.FOR_TYPE_INDIVIDUAL_ORDER:
            from apps.orders.models import ServiceOrder
            order = ServiceOrder.objects.get(id=payment.payment_for_id)
            if order.status == ServiceOrder.STATUS_PENDING_PAYMENT:
                order.payment_status = ServiceOrder.PAYMENT_STATUS_FAILED
                order.save(update_fields=['payment_status'])
        elif payment.payment_for_type == Payment.FOR_TYPE_GROUP_MEMBER:
            from apps.orders.models import ServiceOrderMember
            member = ServiceOrderMember.objects.get(id=payment.payment_for_id)
            if member.status == ServiceOrderMember.STATUS_WAITING_PAYMENT:
                member.status = ServiceOrderMember.STATUS_FAILED
                member.save(update_fields=['status'])
        elif payment.payment_for_type == Payment.FOR_TYPE_COURSE_PURCHASE:
            from apps.courses.models import CoursePurchase
            purchase = CoursePurchase.objects.get(id=payment.payment_for_id)
            if purchase.payment_status in (
                CoursePurchase.PAYMENT_STATUS_CREATED,
                CoursePurchase.PAYMENT_STATUS_WAITING,
            ):
                purchase.payment_status = CoursePurchase.PAYMENT_STATUS_FAILED
                purchase.save(update_fields=['payment_status'])
    except Exception as exc:
        logger.error(f'Receipt reject handler failed for {payment.payment_code}: {exc}', exc_info=True)
