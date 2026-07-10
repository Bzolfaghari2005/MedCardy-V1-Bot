from django.db import models


class Favorite(models.Model):
    OBJECT_TYPE_COURSE = 'course'
    OBJECT_TYPE_SERVICE_ORDER = 'service_order'
    OBJECT_TYPE_CHOICES = [
        (OBJECT_TYPE_COURSE, 'دوره'),
        (OBJECT_TYPE_SERVICE_ORDER, 'سفارش سرویس'),
    ]

    user = models.ForeignKey(
        'users.TelegramUser', on_delete=models.CASCADE,
        related_name='favorites', verbose_name='کاربر'
    )
    object_type = models.CharField(max_length=30, choices=OBJECT_TYPE_CHOICES, verbose_name='نوع آبجکت')
    object_id = models.PositiveIntegerField(verbose_name='شناسه آبجکت')
    title_snapshot = models.CharField(max_length=255, blank=True, verbose_name='عنوان (نسخه ذخیره‌شده)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ افزودن')

    class Meta:
        verbose_name = 'علاقه‌مندی'
        verbose_name_plural = 'علاقه‌مندی‌ها'
        unique_together = [('user', 'object_type', 'object_id')]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.user_code} - {self.get_object_type_display()} #{self.object_id}'
