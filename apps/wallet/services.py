import logging
from django.db import transaction
from django.db.models import F

from apps.wallet.models import WalletTransaction

logger = logging.getLogger(__name__)


def create_wallet_charge_payment(user, amount_toman: int):
    """
    Create a payment for wallet charge (manual receipt or gateway).
    Returns (payment, success, url_or_payment_code).
    """
    from apps.payments.models import Payment
    from apps.payments.services.payment_service import create_payment

    payment, success, result = create_payment(
        user=user,
        amount_toman=amount_toman,
        payment_for_type=Payment.FOR_TYPE_WALLET_CHARGE,
        payment_for_id=0,
        description=f'شارژ کیف پول MedCardy - {user.user_code}',
    )
    if success:
        payment.payment_for_id = payment.id
        payment.save(update_fields=['payment_for_id'])
    return payment, success, result


def create_wallet_transaction(user, amount_toman, transaction_type, payment=None, description=''):
    return WalletTransaction.objects.create(
        user=user,
        amount_toman=amount_toman,
        transaction_type=transaction_type,
        payment=payment,
        description=description,
    )


@transaction.atomic
def refund_payment_to_wallet(payment) -> bool:
    """
    Credit a verified payment back to the user's wallet.
    Returns True if a new refund was processed, False if already refunded or not eligible.
    """
    from apps.payments.models import Payment
    from apps.users.models import TelegramUser

    if payment.status == Payment.STATUS_REFUNDED:
        return False

    if payment.status not in (Payment.STATUS_VERIFIED, Payment.STATUS_ALREADY_VERIFIED):
        return False

    if WalletTransaction.objects.filter(
        payment=payment,
        transaction_type=WalletTransaction.TYPE_REFUND,
    ).exists():
        payment.status = Payment.STATUS_REFUNDED
        payment.save(update_fields=['status'])
        return False

    TelegramUser.objects.filter(id=payment.user_id).update(
        wallet_balance=F('wallet_balance') + payment.amount_toman
    )
    WalletTransaction.objects.create(
        user=payment.user,
        amount_toman=payment.amount_toman,
        transaction_type=WalletTransaction.TYPE_REFUND,
        payment=payment,
        description=f'بازگشت وجه سفارش - {payment.payment_code}',
    )
    payment.status = Payment.STATUS_REFUNDED
    payment.save(update_fields=['status'])
    logger.info(f'Payment {payment.payment_code} refunded to wallet for user {payment.user.user_code}')
    return True
