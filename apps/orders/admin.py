from django.contrib import admin
from django.utils.html import format_html
from apps.orders.models import ServiceOrder, ServiceOrderMember


class ServiceOrderMemberInline(admin.TabularInline):
    model = ServiceOrderMember
    extra = 0
    readonly_fields = ['joined_at', 'updated_at']
    fields = ['user', 'payment', 'amount_paid_toman', 'status', 'access_status', 'joined_at']
    can_delete = False


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_code', 'creator_link', 'order_type', 'service_tier', 'title',
        'payment_status', 'status', 'production_status',
        'paid_members_count', 'created_at',
    ]
    list_filter = ['order_type', 'service_tier', 'status', 'payment_status', 'production_status', 'created_at']
    search_fields = [
        'order_code', 'title', 'creator_user__user_code', 'creator_user__username',
    ]
    readonly_fields = ['order_code', 'created_at', 'updated_at', 'paid_members_count']
    inlines = [ServiceOrderMemberInline]
    actions = ['mark_in_production', 'mark_delivered', 'cancel_with_refund']
    list_per_page = 30

    fieldsets = (
        ('اطلاعات سفارش', {
            'fields': ('order_code', 'creator_user', 'order_type', 'title', 'short_title'),
        }),
        ('محتوا', {
            'fields': (
                'category', 'lesson', 'university', 'uploaded_file',
                'service_tier', 'pages_count', 'detected_pages', 'detected_char_count',
            ),
        }),
        ('قیمت‌گذاری', {
            'fields': ('base_price_toman', 'discount_percent', 'final_price_per_user_toman'),
        }),
        ('سفارش گروهی', {
            'fields': ('min_group_members', 'paid_members_count', 'group_join_code', 'group_join_link'),
            'classes': ('collapse',),
        }),
        ('وضعیت', {
            'fields': ('payment_status', 'status', 'production_status'),
        }),
        ('تحویل', {
            'fields': ('personal_panel', 'private_channel_link'),
        }),
        ('یادداشت‌ها', {
            'fields': ('user_note', 'admin_note'),
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def creator_link(self, obj):
        return format_html(
            '<a href="/admin/users/telegramuser/{}/change/">{}</a>',
            obj.creator_user_id, obj.creator_user.user_code
        )
    creator_link.short_description = 'سازنده'

    def save_model(self, request, obj, form, change):
        old_status = None
        if change and obj.pk:
            old_status = ServiceOrder.objects.filter(pk=obj.pk).values_list('status', flat=True).first()
        super().save_model(request, obj, form, change)
        if (
            change
            and old_status != ServiceOrder.STATUS_CANCELLED
            and obj.status == ServiceOrder.STATUS_CANCELLED
        ):
            from apps.orders.services import cancel_service_order_with_refund
            cancel_service_order_with_refund(obj)

    @admin.action(description='در حال تولید')
    def mark_in_production(self, request, queryset):
        queryset.update(status=ServiceOrder.STATUS_IN_PRODUCTION, production_status=ServiceOrder.PRODUCTION_STATUS_IN_PROGRESS)

    @admin.action(description='تحویل داده شده')
    def mark_delivered(self, request, queryset):
        queryset.update(status=ServiceOrder.STATUS_DELIVERED, production_status=ServiceOrder.PRODUCTION_STATUS_DONE)

    @admin.action(description='لغو سفارش و بازگشت وجه به کیف پول')
    def cancel_with_refund(self, request, queryset):
        from apps.orders.services import cancel_service_order_with_refund
        total_refunds = 0
        for order in queryset:
            refunded = cancel_service_order_with_refund(order)
            total_refunds += len(refunded)
        self.message_user(
            request,
            f'{queryset.count()} سفارش لغو شد. {total_refunds} بازگشت وجه به کیف پول انجام شد.',
        )


@admin.register(ServiceOrderMember)
class ServiceOrderMemberAdmin(admin.ModelAdmin):
    list_display = [
        'order_link', 'user_link', 'amount_paid_toman',
        'status', 'access_status', 'joined_at',
    ]
    list_filter = ['status', 'access_status', 'joined_at']
    search_fields = ['order__order_code', 'user__user_code', 'user__username']
    readonly_fields = ['joined_at', 'updated_at']
    list_per_page = 50

    def order_link(self, obj):
        return format_html(
            '<a href="/admin/orders/serviceorder/{}/change/">{}</a>',
            obj.order_id, obj.order.order_code
        )
    order_link.short_description = 'سفارش'

    def user_link(self, obj):
        return format_html(
            '<a href="/admin/users/telegramuser/{}/change/">{}</a>',
            obj.user_id, obj.user.user_code
        )
    user_link.short_description = 'کاربر'
