from django.db import models
from django.utils import timezone


class TelegramUser(models.Model):
    user_code = models.CharField(max_length=20, unique=True, editable=False, verbose_name='کد کاربر')
    telegram_id = models.BigIntegerField(unique=True, db_index=True, verbose_name='شناسه تلگرام')
    username = models.CharField(max_length=255, blank=True, null=True, verbose_name='نام کاربری')
    first_name = models.CharField(max_length=255, blank=True, verbose_name='نام')
    last_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='نام خانوادگی')
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='شماره موبایل')
    wallet_balance = models.DecimalField(
        max_digits=12, decimal_places=0, default=0, verbose_name='موجودی کیف پول (تومان)'
    )
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_blocked = models.BooleanField(default=False, verbose_name='بلاک شده')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت‌نام')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'کاربر تلگرام'
        verbose_name_plural = 'کاربران تلگرام'
        ordering = ['-created_at']

    def __str__(self):
        name = self.first_name or ''
        if self.last_name:
            name = f'{name} {self.last_name}'.strip()
        return f'{self.user_code} - {name or self.username or str(self.telegram_id)}'

    def save(self, *args, **kwargs):
        if not self.user_code:
            self.user_code = self._generate_user_code()
        super().save(*args, **kwargs)

    @classmethod
    def _generate_user_code(cls):
        last = cls.objects.order_by('-id').first()
        next_num = (last.id + 1) if last else 1
        return f'MCU-{str(next_num).zfill(6)}'

    def get_full_name(self):
        parts = [p for p in [self.first_name, self.last_name] if p]
        return ' '.join(parts) or self.username or str(self.telegram_id)


class PersonalPanel(models.Model):
    STATUS_NOT_CREATED = 'not_created'
    STATUS_NEEDS_CREATION = 'needs_creation'
    STATUS_CREATED = 'created'
    STATUS_ACTIVE = 'active'
    STATUS_PROBLEM = 'problem'

    STATUS_CHOICES = [
        (STATUS_NOT_CREATED, 'ساخته نشده'),
        (STATUS_NEEDS_CREATION, 'نیازمند ساخت توسط ادمین'),
        (STATUS_CREATED, 'ساخته شده'),
        (STATUS_ACTIVE, 'فعال'),
        (STATUS_PROBLEM, 'دارای مشکل'),
    ]

    user = models.OneToOneField(
        TelegramUser, on_delete=models.CASCADE, related_name='personal_panel', verbose_name='کاربر'
    )
    panel_code = models.CharField(max_length=30, unique=True, editable=False, verbose_name='کد پنل')
    title = models.CharField(max_length=255, verbose_name='عنوان پنل')
    channel_link = models.URLField(blank=True, null=True, verbose_name='لینک کانال')
    invite_link = models.URLField(blank=True, null=True, verbose_name='لینک دعوت')
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default=STATUS_NEEDS_CREATION, verbose_name='وضعیت'
    )
    admin_note = models.TextField(blank=True, verbose_name='یادداشت ادمین')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'پنل شخصی'
        verbose_name_plural = 'پنل‌های شخصی'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.panel_code} - {self.user.user_code}'

    def save(self, *args, **kwargs):
        if not self.panel_code:
            self.panel_code = f'PP-{self.user.user_code}'
        if not self.title:
            self.title = f'MedCardy | پنل شخصی {self.user.user_code}'
        super().save(*args, **kwargs)

    def get_status_display_persian(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
