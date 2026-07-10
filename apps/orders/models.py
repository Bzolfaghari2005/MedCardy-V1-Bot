import uuid
from django.db import models
from django.utils import timezone


def _generate_order_code(order_type):
    from apps.orders.models import ServiceOrder
    today = timezone.localdate()
    date_str = today.strftime('%y%m%d')
    type_char = 'I' if order_type == 'individual' else 'G'
    prefix = f'MCS-{type_char}-{date_str}-'
    count = ServiceOrder.objects.filter(order_code__startswith=prefix).count()
    return f'{prefix}{str(count + 1).zfill(4)}'


class ServiceOrder(models.Model):
    TYPE_INDIVIDUAL = 'individual'
    TYPE_GROUP = 'group'
    TYPE_CHOICES = [
        (TYPE_INDIVIDUAL, 'فردی'),
        (TYPE_GROUP, 'گروهی'),
    ]

    PAYMENT_STATUS_PENDING = 'pending_payment'
    PAYMENT_STATUS_PAID = 'paid'
    PAYMENT_STATUS_FAILED = 'failed'
    PAYMENT_STATUS_PARTIAL = 'partial'
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, 'در انتظار پرداخت'),
        (PAYMENT_STATUS_PAID, 'پرداخت موفق'),
        (PAYMENT_STATUS_FAILED, 'پرداخت ناموفق'),
        (PAYMENT_STATUS_PARTIAL, 'پرداخت جزئی (گروهی)'),
    ]

    STATUS_PENDING_PAYMENT = 'pending_payment'
    STATUS_WAITING_MEMBERS = 'waiting_group_members'
    STATUS_WAITING_ADMIN = 'waiting_admin_review'
    STATUS_IN_PRODUCTION = 'in_production'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_PROBLEM = 'problem'
    STATUS_CHOICES = [
        (STATUS_PENDING_PAYMENT, 'در انتظار پرداخت'),
        (STATUS_WAITING_MEMBERS, 'در انتظار تکمیل اعضا'),
        (STATUS_WAITING_ADMIN, 'در انتظار بررسی ادمین'),
        (STATUS_IN_PRODUCTION, 'در حال تولید'),
        (STATUS_DELIVERED, 'تحویل داده شده'),
        (STATUS_CANCELLED, 'لغو شده'),
        (STATUS_PROBLEM, 'دارای مشکل'),
    ]

    PRODUCTION_STATUS_PENDING = 'not_started'
    PRODUCTION_STATUS_WAITING_ADMIN = 'waiting_admin_review'
    PRODUCTION_STATUS_IN_PROGRESS = 'in_progress'
    PRODUCTION_STATUS_DONE = 'done'
    PRODUCTION_STATUS_CHOICES = [
        (PRODUCTION_STATUS_PENDING, 'شروع نشده'),
        (PRODUCTION_STATUS_WAITING_ADMIN, 'در انتظار بررسی ادمین'),
        (PRODUCTION_STATUS_IN_PROGRESS, 'در حال تولید'),
        (PRODUCTION_STATUS_DONE, 'تولید شده'),
    ]

    TIER_REVIEW = 'review'
    TIER_FULL = 'full'
    SERVICE_TIER_CHOICES = [
        (TIER_REVIEW, 'نسخه مروری'),
        (TIER_FULL, 'آموزش کامل'),
    ]

    order_code = models.CharField(max_length=30, unique=True, editable=False, verbose_name='کد سفارش')
    creator_user = models.ForeignKey(
        'users.TelegramUser', on_delete=models.PROTECT,
        related_name='created_orders', verbose_name='سازنده سفارش'
    )
    order_type = models.CharField(max_length=15, choices=TYPE_CHOICES, verbose_name='نوع سفارش')
    title = models.CharField(max_length=255, verbose_name='عنوان سفارش')
    short_title = models.CharField(max_length=100, blank=True, verbose_name='عنوان کوتاه')
    category = models.ForeignKey(
        'catalog.Category', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='service_orders', verbose_name='دسته‌بندی'
    )
    lesson = models.ForeignKey(
        'catalog.Lesson', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='service_orders', verbose_name='درس'
    )
    university = models.CharField(max_length=255, blank=True, verbose_name='دانشگاه')
    uploaded_file = models.FileField(
        upload_to='orders/files/', blank=True, null=True, verbose_name='فایل آپلود شده'
    )
    pages_count = models.PositiveIntegerField(default=0, verbose_name='تعداد صفحات')
    service_tier = models.CharField(
        max_length=10, choices=SERVICE_TIER_CHOICES, default=TIER_FULL,
        verbose_name='نوع نسخه'
    )
    detected_pages = models.PositiveIntegerField(default=0, verbose_name='صفحات شناسایی‌شده')
    detected_char_count = models.PositiveIntegerField(default=0, verbose_name='کاراکتر شناسایی‌شده')
    base_price_toman = models.DecimalField(
        max_digits=12, decimal_places=0, default=0, verbose_name='قیمت پایه (تومان)'
    )
    discount_percent = models.PositiveIntegerField(default=0, verbose_name='درصد تخفیف')
    final_price_per_user_toman = models.DecimalField(
        max_digits=12, decimal_places=0, default=0, verbose_name='قیمت نهایی هر نفر (تومان)'
    )
    min_group_members = models.PositiveIntegerField(default=5, verbose_name='حداقل اعضای گروه')
    paid_members_count = models.PositiveIntegerField(default=0, verbose_name='تعداد اعضای پرداخت موفق')
    group_join_code = models.CharField(max_length=50, blank=True, unique=True, null=True, verbose_name='کد ورود گروه')
    group_join_link = models.URLField(blank=True, verbose_name='لینک ورود گروه')
    payment_status = models.CharField(
        max_length=30, choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_STATUS_PENDING, verbose_name='وضعیت پرداخت'
    )
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES,
        default=STATUS_PENDING_PAYMENT, verbose_name='وضعیت سفارش'
    )
    production_status = models.CharField(
        max_length=30, choices=PRODUCTION_STATUS_CHOICES,
        default=PRODUCTION_STATUS_PENDING, verbose_name='وضعیت تولید'
    )
    personal_panel = models.ForeignKey(
        'users.PersonalPanel', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='individual_orders', verbose_name='پنل شخصی'
    )
    private_channel_link = models.URLField(blank=True, verbose_name='لینک کانال اختصاصی')
    user_note = models.TextField(blank=True, verbose_name='یادداشت کاربر')
    admin_note = models.TextField(blank=True, verbose_name='یادداشت ادمین')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'سفارش سرویس'
        verbose_name_plural = 'سفارش‌های سرویس'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order_code} - {self.title}'

    def save(self, *args, **kwargs):
        if not self.order_code:
            self.order_code = _generate_order_code(self.order_type)
        if not self.short_title:
            self.short_title = self.title[:50]
        super().save(*args, **kwargs)


class ServiceOrderMember(models.Model):
    STATUS_PAYMENT_CREATED = 'payment_created'
    STATUS_WAITING_PAYMENT = 'waiting_payment'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PAYMENT_CREATED, 'ساخته شده'),
        (STATUS_WAITING_PAYMENT, 'در انتظار پرداخت'),
        (STATUS_PAID, 'پرداخت موفق'),
        (STATUS_FAILED, 'پرداخت ناموفق'),
        (STATUS_CANCELLED, 'لغو شده'),
    ]

    ACCESS_STATUS_WAITING_DELIVERY = 'waiting_delivery'
    ACCESS_STATUS_DELIVERED = 'delivered'
    ACCESS_STATUS_PROBLEM = 'problem'
    ACCESS_STATUS_CHOICES = [
        (ACCESS_STATUS_WAITING_DELIVERY, 'در انتظار تحویل'),
        (ACCESS_STATUS_DELIVERED, 'تحویل داده شده'),
        (ACCESS_STATUS_PROBLEM, 'دارای مشکل'),
    ]

    order = models.ForeignKey(
        ServiceOrder, on_delete=models.PROTECT, related_name='members', verbose_name='سفارش'
    )
    user = models.ForeignKey(
        'users.TelegramUser', on_delete=models.PROTECT,
        related_name='group_order_memberships', verbose_name='کاربر'
    )
    payment = models.ForeignKey(
        'payments.Payment', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='group_order_member', verbose_name='پرداخت'
    )
    amount_paid_toman = models.DecimalField(
        max_digits=12, decimal_places=0, default=0, verbose_name='مبلغ پرداختی (تومان)'
    )
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default=STATUS_PAYMENT_CREATED, verbose_name='وضعیت'
    )
    access_status = models.CharField(
        max_length=30, choices=ACCESS_STATUS_CHOICES,
        default=ACCESS_STATUS_WAITING_DELIVERY, verbose_name='وضعیت دسترسی'
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ عضویت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'عضو سفارش گروهی'
        verbose_name_plural = 'اعضای سفارش گروهی'
        unique_together = [('order', 'user')]
        ordering = ['-joined_at']

    def __str__(self):
        return f'{self.order.order_code} - {self.user.user_code}'
