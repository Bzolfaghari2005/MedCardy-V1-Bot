from django.contrib import admin
from apps.settings_app.models import Setting


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value_preview', 'description', 'updated_at']
    search_fields = ['key', 'description', 'value']
    list_per_page = 50
    ordering = ['key']
    fieldsets = (
        (None, {
            'fields': ('key', 'value', 'description', 'updated_at'),
            'description': (
                '<b>تنظیمات پرداخت:</b> payment_card_number, payment_card_holder, '
                'payment_bank_name, payment_sheba_number, payment_transfer_note, '
                'payment_review_hours, enable_payment_gateway'
            ),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['key', 'updated_at']
        return ['updated_at']

    def value_preview(self, obj):
        return obj.value[:80] + '...' if len(obj.value) > 80 else obj.value
    value_preview.short_description = 'مقدار'
