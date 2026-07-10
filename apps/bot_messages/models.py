from django.db import models


class BotLabel(models.Model):
    CATEGORY_MENU = 'menu'
    CATEGORY_BUTTON = 'button'
    CATEGORY_STATUS = 'status'
    CATEGORY_WALLET = 'wallet'
    CATEGORY_TIER = 'tier'
    CATEGORY_CHOICES = [
        (CATEGORY_MENU, 'منوی اصلی'),
        (CATEGORY_BUTTON, 'دکمه'),
        (CATEGORY_STATUS, 'وضعیت'),
        (CATEGORY_WALLET, 'کیف پول'),
        (CATEGORY_TIER, 'نوع نسخه'),
    ]

    key = models.CharField(max_length=100, unique=True, verbose_name='کلید')
    text = models.CharField(max_length=255, verbose_name='متن نمایشی')
    title = models.CharField(max_length=255, verbose_name='عنوان (برای ادمین)')
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_BUTTON, verbose_name='دسته',
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name='ترتیب')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'برچسب بات'
        verbose_name_plural = 'برچسب‌های بات'
        ordering = ['category', 'sort_order', 'key']

    def __str__(self):
        return f'{self.key} — {self.text}'


class BotMessage(models.Model):
    key = models.CharField(max_length=100, unique=True, verbose_name='کلید')
    title = models.CharField(max_length=255, verbose_name='عنوان (برای ادمین)')
    text = models.TextField(verbose_name='متن پیام')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'پیام بات'
        verbose_name_plural = 'پیام‌های بات'
        ordering = ['key']

    def __str__(self):
        return f'{self.key} - {self.title}'
