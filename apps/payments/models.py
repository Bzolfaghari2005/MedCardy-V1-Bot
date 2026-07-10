from django.db import models
from django.utils import timezone


def _generate_payment_code():
    from apps.payments.models import Payment
    today = timezone.localdate()
    date_str = today.strftime('%y%m%d')
    prefix = f'MCP-{date_str}-'
    count = Payment.objects.filter(payment_code__startswith=prefix).count()
    return f'{prefix}{str(count + 1).zfill(4)}'


class Payment(models.Model):
    PROVIDER_ZIBAL = 'zibal'
    PROVIDER_WALLET = 'wallet'
    PROVIDER_MANUAL = 'manual'
    PROVIDER_CHOICES = [
        (PROVIDER_ZIBAL, 'زیبال'),
        (PROVIDER_WALLET, 'کیف پول'),
        (PROVIDER_MANUAL, 'دستی'),
    ]

    METHOD_ZIBAL_IPG = 'zibal_ipg'
    METHOD_WALLET = 'wallet'
    METHOD_MANUAL_RECEIPT = 'manual_receipt'
    METHOD_CHOICES = [
        (METHOD_ZIBAL_IPG, 'درگاه زیبال'),
        (METHOD_WALLET, 'کیف پول'),
        (METHOD_MANUAL_RECEIPT, 'رسید پرداخت'),
    ]

    FOR_TYPE_COURSE_PURCHASE = 'course_purchase'
    FOR_TYPE_INDIVIDUAL_ORDER = 'individual_service_order'
    FOR_TYPE_GROUP_MEMBER = 'group_order_member'
    FOR_TYPE_WALLET_CHARGE = 'wallet_charge'
    FOR_TYPE_CHOICES = [
        (FOR_TYPE_COURSE_PURCHASE, 'خرید دوره'),
        (FOR_TYPE_INDIVIDUAL_ORDER, 'سفارش فردی'),
        (FOR_TYPE_GROUP_MEMBER, 'عضویت سفارش گروهی'),
        (FOR_TYPE_WALLET_CHARGE, 'شارژ کیف پول'),
    ]

    STATUS_CREATED = 'created'
    STATUS_REQUEST_FAILED = 'request_failed'
    STATUS_WAITING_USER = 'waiting_user_payment'
    STATUS_CALLBACK_RECEIVED = 'callback_received'
    STATUS_VERIFYING = 'verifying'
    STATUS_VERIFIED = 'verified'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_VERIFICATION_FAILED = 'verification_failed'
    STATUS_ALREADY_VERIFIED = 'already_verified'
    STATUS_REFUNDED = 'refunded'
    STATUS_MANUAL_REVIEW = 'manual_review'
    STATUS_RECEIPT_SUBMITTED = 'receipt_submitted'
    STATUS_RECEIPT_REJECTED = 'receipt_rejected'
    STATUS_CHOICES = [
        (STATUS_CREATED, 'ساخته شده'),
        (STATUS_REQUEST_FAILED, 'خطا در ساخت درخواست پرداخت'),
        (STATUS_WAITING_USER, 'در انتظار پرداخت کاربر'),
        (STATUS_CALLBACK_RECEIVED, 'callback دریافت شد'),
        (STATUS_VERIFYING, 'در حال تأیید پرداخت'),
        (STATUS_VERIFIED, 'پرداخت موفق و تأیید شده'),
        (STATUS_FAILED, 'پرداخت ناموفق'),
        (STATUS_CANCELLED, 'لغو شده'),
        (STATUS_VERIFICATION_FAILED, 'خطا در تأیید پرداخت'),
        (STATUS_ALREADY_VERIFIED, 'قبلاً تأیید شده'),
        (STATUS_REFUNDED, 'مسترد شده'),
        (STATUS_MANUAL_REVIEW, 'نیازمند بررسی دستی'),
        (STATUS_RECEIPT_SUBMITTED, 'رسید ارسال شده — در انتظار تأیید'),
        (STATUS_RECEIPT_REJECTED, 'رسید رد شده'),
    ]

    payment_code = models.CharField(max_length=30, unique=True, editable=False, verbose_name='کد پرداخت')
    user = models.ForeignKey(
        'users.TelegramUser', on_delete=models.PROTECT, related_name='payments', verbose_name='کاربر'
    )
    amount_toman = models.DecimalField(
        max_digits=12, decimal_places=0, verbose_name='مبلغ (تومان)'
    )
    amount_rial = models.DecimalField(
        max_digits=14, decimal_places=0, verbose_name='مبلغ (ریال)', editable=False
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default=PROVIDER_ZIBAL, verbose_name='درگاه')
    payment_method = models.CharField(
        max_length=20, choices=METHOD_CHOICES, default=METHOD_ZIBAL_IPG, verbose_name='روش پرداخت'
    )
    payment_for_type = models.CharField(
        max_length=30, choices=FOR_TYPE_CHOICES, verbose_name='نوع تراکنش'
    )
    payment_for_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='شناسه آبجکت مرتبط')
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default=STATUS_CREATED, verbose_name='وضعیت'
    )
    description = models.CharField(max_length=512, blank=True, verbose_name='توضیح')
    order_id = models.CharField(max_length=50, blank=True, verbose_name='شناسه سفارش (ارسالی به زیبال)')

    # Zibal-specific fields
    zibal_track_id = models.CharField(max_length=50, blank=True, db_index=True, verbose_name='trackId زیبال')
    zibal_result = models.IntegerField(null=True, blank=True, verbose_name='result زیبال')
    zibal_status = models.IntegerField(null=True, blank=True, verbose_name='status زیبال')
    zibal_message = models.CharField(max_length=255, blank=True, verbose_name='پیام زیبال')
    zibal_ref_number = models.CharField(max_length=100, blank=True, verbose_name='شماره مرجع زیبال')
    zibal_card_number = models.CharField(max_length=20, blank=True, verbose_name='شماره کارت')
    zibal_hashed_card_number = models.CharField(max_length=255, blank=True, verbose_name='هش شماره کارت')

    # Callback fields
    callback_success = models.IntegerField(null=True, blank=True, verbose_name='callback success')
    callback_status = models.IntegerField(null=True, blank=True, verbose_name='callback status')
    callback_payload = models.JSONField(null=True, blank=True, verbose_name='callback payload')

    # Request/Response payloads
    request_payload = models.JSONField(null=True, blank=True, verbose_name='request payload')
    request_response = models.JSONField(null=True, blank=True, verbose_name='request response')
    verify_payload = models.JSONField(null=True, blank=True, verbose_name='verify payload')
    inquiry_payload = models.JSONField(null=True, blank=True, verbose_name='inquiry payload')

    admin_note = models.TextField(blank=True, verbose_name='یادداشت ادمین')

    # Manual receipt fields
    receipt_file = models.FileField(
        upload_to='payment_receipts/%Y/%m/', blank=True, verbose_name='فایل رسید پرداخت'
    )
    receipt_submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان ارسال رسید')
    receipt_reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان بررسی رسید')
    receipt_rejected_reason = models.CharField(max_length=512, blank=True, verbose_name='دلیل رد رسید')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ پرداخت')
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تأیید')

    class Meta:
        verbose_name = 'پرداخت'
        verbose_name_plural = 'پرداخت‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.payment_code} - {self.user.user_code} - {self.amount_toman} تومان'

    def save(self, *args, **kwargs):
        if not self.payment_code:
            self.payment_code = _generate_payment_code()
            self.order_id = self.payment_code
        # Always recompute amount_rial from amount_toman
        self.amount_rial = int(self.amount_toman) * 10
        super().save(*args, **kwargs)

    def is_terminal_status(self):
        return self.status in [
            self.STATUS_VERIFIED, self.STATUS_FAILED, self.STATUS_CANCELLED,
            self.STATUS_REFUNDED, self.STATUS_ALREADY_VERIFIED,
            self.STATUS_RECEIPT_REJECTED,
        ]
