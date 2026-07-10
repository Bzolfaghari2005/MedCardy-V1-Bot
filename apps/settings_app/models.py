from django.db import models


class Setting(models.Model):
    key = models.CharField(max_length=100, unique=True, verbose_name='کلید')
    value = models.TextField(verbose_name='مقدار')
    description = models.CharField(max_length=512, blank=True, verbose_name='توضیح')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'تنظیم'
        verbose_name_plural = 'تنظیمات'
        ordering = ['key']

    def __str__(self):
        return f'{self.key} = {self.value[:50]}'
