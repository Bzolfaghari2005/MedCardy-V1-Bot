import logging
from apps.courses.models import Course, CoursePurchase

logger = logging.getLogger(__name__)


def create_course_purchase(user, course: Course):
    """
    Create a CoursePurchase and payment (manual receipt or gateway).
    Returns (purchase, payment, success, url_or_payment_code).
    """
    from apps.payments.models import Payment
    from apps.payments.services.payment_service import create_payment, is_payment_gateway_enabled

    existing = CoursePurchase.objects.filter(
        user=user, course=course,
        payment_status__in=[
            CoursePurchase.PAYMENT_STATUS_CREATED,
            CoursePurchase.PAYMENT_STATUS_WAITING,
        ]
    ).first()
    if existing and existing.payment and existing.payment.status == Payment.STATUS_WAITING_USER:
        if is_payment_gateway_enabled() and existing.payment.zibal_track_id:
            from apps.payments.services.zibal_service import ZibalPaymentService
            zibal = ZibalPaymentService()
            return existing, existing.payment, True, zibal.build_start_url(existing.payment.zibal_track_id)
        return existing, existing.payment, True, existing.payment.payment_code

    purchase = CoursePurchase.objects.create(
        user=user,
        course=course,
        payment_status=CoursePurchase.PAYMENT_STATUS_CREATED,
        access_status=CoursePurchase.ACCESS_STATUS_WAITING_PAYMENT,
    )

    payment, success, result = create_payment(
        user=user,
        amount_toman=int(course.price_toman),
        payment_for_type=Payment.FOR_TYPE_COURSE_PURCHASE,
        payment_for_id=purchase.id,
        description=f'خرید دوره: {course.title}',
    )

    purchase.payment = payment
    if success:
        purchase.payment_status = CoursePurchase.PAYMENT_STATUS_WAITING
    else:
        purchase.payment_status = CoursePurchase.PAYMENT_STATUS_FAILED
    purchase.save(update_fields=['payment', 'payment_status'])

    return purchase, payment, success, result
