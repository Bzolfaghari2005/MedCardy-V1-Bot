from django.contrib import admin
from django.utils.html import format_html
from apps.courses.models import Course, CoursePurchase


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'lesson', 'course_type', 'price_toman',
        'status', 'is_featured', 'sort_order', 'created_at',
    ]
    list_filter = ['course_type', 'status', 'is_featured', 'category', 'lesson']
    search_fields = ['title', 'short_description', 'university']
    list_editable = ['status', 'is_featured', 'sort_order']
    ordering = ['sort_order', '-created_at']
    list_per_page = 50

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'category', 'lesson', 'course_type', 'price_toman', 'status', 'is_featured', 'sort_order'),
        }),
        ('توضیحات', {
            'fields': ('short_description', 'full_description'),
        }),
        ('اطلاعات تکمیلی', {
            'fields': ('university', 'source_title', 'pages_count', 'duration_text', 'episodes_count'),
        }),
        ('لینک‌ها', {
            'fields': ('public_channel_post_link', 'default_private_source_link'),
        }),
        ('رسانه', {
            'fields': ('cover_image',),
        }),
    )


class CoursePurchaseAdmin(admin.ModelAdmin):
    list_display = [
        'purchase_code', 'user_link', 'course_link', 'payment_status',
        'access_status', 'panel_status', 'created_at',
    ]
    list_filter = ['payment_status', 'access_status', 'created_at']
    search_fields = [
        'purchase_code', 'user__user_code', 'user__username',
        'user__first_name', 'course__title',
    ]
    readonly_fields = ['purchase_code', 'created_at', 'updated_at']
    actions = ['mark_delivered']
    list_per_page = 50

    fieldsets = (
        ('اطلاعات خرید', {
            'fields': ('purchase_code', 'user', 'course', 'payment'),
        }),
        ('وضعیت', {
            'fields': ('payment_status', 'access_status', 'personal_panel', 'access_link'),
        }),
        ('یادداشت', {
            'fields': ('admin_note',),
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

    def course_link(self, obj):
        return format_html(
            '<a href="/admin/courses/course/{}/change/">{}</a>',
            obj.course_id, obj.course.title
        )
    course_link.short_description = 'دوره'

    def panel_status(self, obj):
        if obj.personal_panel:
            return obj.personal_panel.get_status_display()
        return '—'
    panel_status.short_description = 'وضعیت پنل'

    @admin.action(description='علامت‌گذاری به عنوان تحویل داده شده')
    def mark_delivered(self, request, queryset):
        queryset.update(access_status=CoursePurchase.ACCESS_STATUS_DELIVERED)


admin.site.register(CoursePurchase, CoursePurchaseAdmin)
