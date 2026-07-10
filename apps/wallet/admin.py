from django.contrib import admin
from django.utils.html import format_html
from apps.wallet.models import WalletTransaction


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'amount_toman', 'transaction_type',
        'payment_code_display', 'description', 'created_at',
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__user_code', 'user__username', 'description']
    readonly_fields = ['created_at']
    list_per_page = 50

    def user_link(self, obj):
        return format_html(
            '<a href="/admin/users/telegramuser/{}/change/">{}</a>',
            obj.user_id, obj.user.user_code
        )
    user_link.short_description = 'کاربر'

    def payment_code_display(self, obj):
        if obj.payment:
            return obj.payment.payment_code
        return '—'
    payment_code_display.short_description = 'کد پرداخت'
