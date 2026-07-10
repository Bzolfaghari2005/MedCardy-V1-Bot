from django.db import models
from django.utils import timezone


def _generate_purchase_code():
    from apps.courses.models import CoursePurchase
    today = timezone.localdate()
    date_str = today.strftime('%y%m%d')
    prefix = f'MCC-{date_str}-'
    count = CoursePurchase.objects.filter(purchase_code__startswith=prefix).count()
    return f'{prefix}{str(count + 1).zfill(4)}'


class Course(models.Model):
    TYPE_FREE = 'free'
    TYPE_PAID = 'paid'
    TYPE_CHOICES = [
        (TYPE_FREE, 'رایگان'),
        (TYPE_PAID, 'دوره'),
    ]

    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_COMING_SOON = 'coming_soon'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'فعال'),
        (STATUS_INACTIVE, 'غیرفعال'),
        (STATUS_COMING_SOON, 'به‌زودی'),
    ]

    title = models.CharField(max_length=255, verbose_name='عنوان دوره')
    category = models.ForeignKey(
        'catalog.Category', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='courses', verbose_name='دسته‌بندی'
    )
    lesson = models.ForeignKey(
        'catalog.Lesson', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='courses', verbose_name='درس'
    )
    course_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_FREE, verbose_name='نوع دوره')
    price_toman = models.DecimalField(
        max_digits=12, decimal_places=0, default=0, verbose_name='قیمت (تومان)'
    )
    short_description = models.TextField(blank=True, verbose_name='توضیح کوتاه')
    full_description = models.TextField(blank=True, verbose_name='توضیح کامل')
    university = models.CharField(max_length=255, blank=True, verbose_name='دانشگاه')
    source_title = models.CharField(max_length=255, blank=True, verbose_name='منبع / مرجع')
    pages_count = models.PositiveIntegerField(default=0, verbose_name='تعداد صفحات')
    duration_text = models.CharField(max_length=100, blank=True, verbose_name='مدت زمان پادکست')
    episodes_count = models.PositiveIntegerField(default=0, verbose_name='تعداد قسمت‌ها')
    public_channel_post_link = models.URLField(blank=True, verbose_name='لینک پست کانال عمومی')
    default_private_source_link = models.URLField(blank=True, verbose_name='لینک منبع خصوصی پیش‌فرض')
    cover_image = models.ImageField(upload_to='courses/covers/', blank=True, null=True, verbose_name='تصویر کاور')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE, verbose_name='وضعیت')
    is_featured = models.BooleanField(default=False, verbose_name='ویژه')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'دوره'
        verbose_name_plural = 'دوره‌ها'
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return self.title

    def is_free(self):
        return self.course_type == self.TYPE_FREE

    def is_paid(self):
        return self.course_type == self.TYPE_PAID


class CoursePurchase(models.Model):
    PAYMENT_STATUS_CREATED = 'payment_created'
    PAYMENT_STATUS_WAITING = 'waiting_payment'
    PAYMENT_STATUS_PAID = 'paid'
    PAYMENT_STATUS_FAILED = 'failed'
    PAYMENT_STATUS_CANCELLED = 'cancelled'
    PAYMENT_STATUS_REFUNDED = 'refunded'
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_CREATED, 'ساخته شده'),
        (PAYMENT_STATUS_WAITING, 'در انتظار پرداخت'),
        (PAYMENT_STATUS_PAID, 'پرداخت موفق'),
        (PAYMENT_STATUS_FAILED, 'پرداخت ناموفق'),
        (PAYMENT_STATUS_CANCELLED, 'لغو شده'),
        (PAYMENT_STATUS_REFUNDED, 'مسترد شده'),
    ]

    ACCESS_STATUS_WAITING_PAYMENT = 'waiting_payment'
    ACCESS_STATUS_PAYMENT_FAILED = 'payment_failed'
    ACCESS_STATUS_PAYMENT_VERIFIED = 'payment_verified'
    ACCESS_STATUS_WAITING_PANEL = 'waiting_personal_panel'
    ACCESS_STATUS_WAITING_CONTENT = 'waiting_content_addition'
    ACCESS_STATUS_DELIVERED = 'delivered'
    ACCESS_STATUS_PROBLEM = 'problem'
    ACCESS_STATUS_CANCELLED = 'cancelled'
    ACCESS_STATUS_CHOICES = [
        (ACCESS_STATUS_WAITING_PAYMENT, 'در انتظار پرداخت'),
        (ACCESS_STATUS_PAYMENT_FAILED, 'پرداخت ناموفق'),
        (ACCESS_STATUS_PAYMENT_VERIFIED, 'پرداخت تأیید شده'),
        (ACCESS_STATUS_WAITING_PANEL, 'در انتظار ساخت پنل شخصی'),
        (ACCESS_STATUS_WAITING_CONTENT, 'در انتظار افزودن محتوا به پنل شخصی'),
        (ACCESS_STATUS_DELIVERED, 'آماده / تحویل داده شده'),
        (ACCESS_STATUS_PROBLEM, 'دارای مشکل'),
        (ACCESS_STATUS_CANCELLED, 'لغو شده'),
    ]

    purchase_code = models.CharField(max_length=30, unique=True, editable=False, verbose_name='کد خرید')
    user = models.ForeignKey(
        'users.TelegramUser', on_delete=models.PROTECT, related_name='course_purchases', verbose_name='کاربر'
    )
    course = models.ForeignKey(
        Course, on_delete=models.PROTECT, related_name='purchases', verbose_name='دوره'
    )
    payment = models.ForeignKey(
        'payments.Payment', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='course_purchase', verbose_name='پرداخت'
    )
    payment_status = models.CharField(
        max_length=30, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_CREATED, verbose_name='وضعیت پرداخت'
    )
    access_status = models.CharField(
        max_length=30, choices=ACCESS_STATUS_CHOICES, default=ACCESS_STATUS_WAITING_PAYMENT, verbose_name='وضعیت دسترسی'
    )
    personal_panel = models.ForeignKey(
        'users.PersonalPanel', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='course_purchases', verbose_name='پنل شخصی'
    )
    access_link = models.URLField(blank=True, verbose_name='لینک دسترسی')
    admin_note = models.TextField(blank=True, verbose_name='یادداشت ادمین')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'خرید دوره'
        verbose_name_plural = 'خریدهای دوره'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.purchase_code} - {self.user.user_code} - {self.course.title}'

    def save(self, *args, **kwargs):
        if not self.purchase_code:
            self.purchase_code = _generate_purchase_code()
        super().save(*args, **kwargs)
