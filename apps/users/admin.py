from django.contrib import admin
from django.utils.html import format_html
from apps.users.models import TelegramUser, PersonalPanel


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = [
        'user_code', 'telegram_id', 'username', 'first_name', 'last_name',
        'wallet_balance', 'is_active', 'is_blocked', 'created_at',
    ]
    list_filter = ['is_active', 'is_blocked', 'created_at']
    search_fields = ['user_code', 'telegram_id', 'username', 'first_name', 'last_name']
    readonly_fields = ['user_code', 'created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 50

    fieldsets = (
        ('اطلاعات تلگرام', {
            'fields': ('user_code', 'telegram_id', 'username', 'first_name', 'last_name', 'phone_number'),
        }),
        ('کیف پول', {
            'fields': ('wallet_balance',),
        }),
        ('وضعیت', {
            'fields': ('is_active', 'is_blocked'),
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(PersonalPanel)
class PersonalPanelAdmin(admin.ModelAdmin):
    list_display = [
        'panel_code', 'user_link', 'title', 'status', 'channel_link_display',
        'created_at', 'updated_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['panel_code', 'user__user_code', 'user__username', 'user__first_name']
    readonly_fields = ['panel_code', 'created_at', 'updated_at']
    list_per_page = 50
    actions = ['mark_active', 'mark_needs_creation']

    fieldsets = (
        ('اطلاعات', {
            'fields': ('panel_code', 'user', 'title'),
        }),
        ('لینک‌ها', {
            'fields': ('channel_link', 'invite_link'),
        }),
        ('وضعیت', {
            'fields': ('status', 'admin_note'),
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def user_link(self, obj):
        return format_html(
            '<a href="/admin/users/telegramuser/{}/change/">{}</a>',
            obj.user_id, obj.user.user_code
        )
    user_link.short_description = 'کاربر'

    def channel_link_display(self, obj):
        if obj.channel_link:
            return format_html('<a href="{}" target="_blank">مشاهده کانال</a>', obj.channel_link)
        return '—'
    channel_link_display.short_description = 'لینک کانال'

    @admin.action(description='علامت‌گذاری به عنوان فعال')
    def mark_active(self, request, queryset):
        queryset.update(status=PersonalPanel.STATUS_ACTIVE)

    @admin.action(description='نیازمند ساخت توسط ادمین')
    def mark_needs_creation(self, request, queryset):
        queryset.update(status=PersonalPanel.STATUS_NEEDS_CREATION)
