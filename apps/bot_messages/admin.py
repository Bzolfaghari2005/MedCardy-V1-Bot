from django.contrib import admin
from apps.bot_messages.models import BotMessage, BotLabel

PAYMENT_MESSAGE_KEYS = {
    'manual_payment_instructions',
    'receipt_upload_prompt',
    'receipt_received',
    'receipt_rejected',
    'payment_request_failed',
    'gateway_payment_instructions',
    'course_paid_payment_message',
}

PAYMENT_MESSAGE_HELP = (
    'متغیرهای قابل استفاده در پیام‌های پرداخت:\n'
    '{payment_code} {amount} {amount_copy} {card_number} {card_number_copy} '
    '{card_holder} {bank_name} {sheba_number} {transfer_note} {review_hours} {reason}\n\n'
    'مقادیر داخل <code> در تلگرام با یک لمس کپی می‌شوند.\n'
    'amount_copy = مبلغ عددی خالص | card_number_copy = شماره کارت بدون خط تیره'
)


@admin.register(BotLabel)
class BotLabelAdmin(admin.ModelAdmin):
    list_display = ['key', 'text', 'title', 'category', 'sort_order', 'is_active', 'updated_at']
    list_filter = ['category', 'is_active']
    search_fields = ['key', 'text', 'title']
    list_editable = ['text', 'sort_order', 'is_active']
    list_per_page = 100
    ordering = ['category', 'sort_order', 'key']
    fieldsets = (
        (None, {'fields': ('key', 'title', 'text', 'category', 'sort_order', 'is_active')}),
    )


@admin.register(BotMessage)
class BotMessageAdmin(admin.ModelAdmin):
    list_display = ['key', 'title', 'is_active', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['key', 'title', 'text']
    list_editable = ['is_active']
    list_per_page = 50
    ordering = ['key']
    readonly_fields = ['payment_placeholders_help']
    fieldsets = (
        (None, {
            'fields': ('key', 'title', 'text', 'is_active'),
        }),
        ('راهنمای پرداخت', {
            'fields': ('payment_placeholders_help',),
            'classes': ('collapse',),
            'description': PAYMENT_MESSAGE_HELP,
        }),
    )

    def payment_placeholders_help(self, obj):
        if obj and obj.key in PAYMENT_MESSAGE_KEYS:
            return PAYMENT_MESSAGE_HELP
        return 'این پیام مربوط به پرداخت نیست.'
    payment_placeholders_help.short_description = 'متغیرهای پرداخت'
