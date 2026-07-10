import logging
from django.contrib import admin
from django.utils.html import format_html
from apps.payments.models import Payment

logger = logging.getLogger(__name__)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'payment_code', 'user_link', 'amount_toman', 'provider',
        'payment_for_type', 'status', 'zibal_track_id', 'created_at',
    ]
    list_filter = ['status', 'provider', 'payment_for_type', 'payment_method', 'created_at']
    search_fields = [
        'payment_code', 'user__user_code', 'user__username',
        'zibal_track_id', 'order_id',
    ]
    readonly_fields = [
        'payment_code', 'amount_rial', 'order_id', 'zibal_track_id',
        'zibal_result', 'zibal_status', 'zibal_message',
        'zibal_ref_number', 'zibal_card_number', 'zibal_hashed_card_number',
        'callback_success', 'callback_status', 'callback_payload',
        'request_payload', 'request_response', 'verify_payload', 'inquiry_payload',
        'receipt_submitted_at', 'receipt_reviewed_at',
        'created_at', 'updated_at', 'paid_at', 'verified_at',
    ]
    actions = ['mark_manual_review', 'retry_verify', 'approve_receipt', 'reject_receipt']
    list_per_page = 50

    fieldsets = (
        ('اطلاعات پرداخت', {
            'fields': (
                'payment_code', 'user', 'amount_toman', 'amount_rial',
                'provider', 'payment_method', 'payment_for_type', 'payment_for_id',
                'description', 'order_id',
            ),
        }),
        ('وضعیت', {
            'fields': ('status', 'admin_note'),
        }),
        ('رسید پرداخت', {
            'fields': (
                'receipt_file', 'receipt_submitted_at', 'receipt_reviewed_at',
                'receipt_rejected_reason',
            ),
        }),
        ('زیبال', {
            'fields': (
                'zibal_track_id', 'zibal_result', 'zibal_status', 'zibal_message',
                'zibal_ref_number', 'zibal_card_number', 'zibal_hashed_card_number',
            ),
        }),
        ('Callback', {
            'fields': ('callback_success', 'callback_status', 'callback_payload'),
            'classes': ('collapse',),
        }),
        ('Payloads', {
            'fields': ('request_payload', 'request_response', 'verify_payload', 'inquiry_payload'),
            'classes': ('collapse',),
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at', 'paid_at', 'verified_at'),
            'classes': ('collapse',),
        }),
    )

    def user_link(self, obj):
        return format_html(
            '<a href="/admin/users/telegramuser/{}/change/">{}</a>',
            obj.user_id, obj.user.user_code
        )
    user_link.short_description = 'کاربر'

    @admin.action(description='نیازمند بررسی دستی')
    def mark_manual_review(self, request, queryset):
        queryset.update(status=Payment.STATUS_MANUAL_REVIEW)

    @admin.action(description='تلاش مجدد برای تأیید زیبال')
    def retry_verify(self, request, queryset):
        from apps.payments.services.payment_service import handle_verify
        success_count = 0
        for payment in queryset.filter(
            provider=Payment.PROVIDER_ZIBAL,
            status__in=[
                Payment.STATUS_CALLBACK_RECEIVED,
                Payment.STATUS_VERIFICATION_FAILED,
                Payment.STATUS_MANUAL_REVIEW,
            ],
        ):
            try:
                _, verified, _ = handle_verify(payment)
                if verified:
                    success_count += 1
            except Exception as e:
                logger.error(f'Retry verify failed for {payment.payment_code}: {e}')
        self.message_user(request, f'{success_count} پرداخت با موفقیت بررسی شد.')

    @admin.action(description='تأیید رسید پرداخت')
    def approve_receipt(self, request, queryset):
        from apps.payments.services.payment_service import approve_manual_payment
        success_count = 0
        for payment in queryset.filter(status=Payment.STATUS_RECEIPT_SUBMITTED):
            try:
                _, success, _ = approve_manual_payment(payment)
                if success:
                    success_count += 1
            except Exception as e:
                logger.error(f'Approve receipt failed for {payment.payment_code}: {e}')
        self.message_user(request, f'{success_count} رسید تأیید شد.')

    @admin.action(description='رد رسید پرداخت')
    def reject_receipt(self, request, queryset):
        from apps.payments.services.payment_service import reject_manual_payment
        success_count = 0
        for payment in queryset.filter(status=Payment.STATUS_RECEIPT_SUBMITTED):
            try:
                _, success, _ = reject_manual_payment(payment, reason='رد شده از پنل ادمین')
                if success:
                    success_count += 1
            except Exception as e:
                logger.error(f'Reject receipt failed for {payment.payment_code}: {e}')
        self.message_user(request, f'{success_count} رسید رد شد.')
