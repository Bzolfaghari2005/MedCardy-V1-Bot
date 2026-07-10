from django.db import models


class WalletTransaction(models.Model):
    TYPE_CHARGE = 'charge'
    TYPE_PURCHASE = 'purchase'
    TYPE_REFUND = 'refund'
    TYPE_ADMIN_ADJUSTMENT = 'admin_adjustment'
    TYPE_CHOICES = [
        (TYPE_CHARGE, 'شارژ'),
        (TYPE_PURCHASE, 'خرید'),
        (TYPE_REFUND, 'بازگشت وجه'),
        (TYPE_ADMIN_ADJUSTMENT, 'تعدیل ادمین'),
    ]

    user = models.ForeignKey(
        'users.TelegramUser', on_delete=models.PROTECT,
        related_name='wallet_transactions', verbose_name='کاربر'
    )
    amount_toman = models.DecimalField(
        max_digits=12, decimal_places=0, verbose_name='مبلغ (تومان)'
    )
    transaction_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, verbose_name='نوع تراکنش'
    )
    payment = models.ForeignKey(
        'payments.Payment', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='wallet_transactions', verbose_name='پرداخت مرتبط'
    )
    description = models.CharField(max_length=512, blank=True, verbose_name='توضیح')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ')

    class Meta:
        verbose_name = 'تراکنش کیف پول'
        verbose_name_plural = 'تراکنش‌های کیف پول'
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.transaction_type in [self.TYPE_CHARGE, self.TYPE_REFUND, self.TYPE_ADMIN_ADJUSTMENT] else '-'
        return f'{self.user.user_code} {sign}{self.amount_toman} تومان ({self.get_transaction_type_display()})'
