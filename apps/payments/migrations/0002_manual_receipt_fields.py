from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='receipt_file',
            field=models.FileField(blank=True, upload_to='payment_receipts/%Y/%m/', verbose_name='فایل رسید پرداخت'),
        ),
        migrations.AddField(
            model_name='payment',
            name='receipt_submitted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='زمان ارسال رسید'),
        ),
        migrations.AddField(
            model_name='payment',
            name='receipt_reviewed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='زمان بررسی رسید'),
        ),
        migrations.AddField(
            model_name='payment',
            name='receipt_rejected_reason',
            field=models.CharField(blank=True, max_length=512, verbose_name='دلیل رد رسید'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='payment_method',
            field=models.CharField(
                choices=[
                    ('zibal_ipg', 'درگاه زیبال'),
                    ('wallet', 'کیف پول'),
                    ('manual_receipt', 'رسید پرداخت'),
                ],
                default='zibal_ipg',
                max_length=20,
                verbose_name='روش پرداخت',
            ),
        ),
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.CharField(
                choices=[
                    ('created', 'ساخته شده'),
                    ('request_failed', 'خطا در ساخت درخواست پرداخت'),
                    ('waiting_user_payment', 'در انتظار پرداخت کاربر'),
                    ('callback_received', 'callback دریافت شد'),
                    ('verifying', 'در حال تأیید پرداخت'),
                    ('verified', 'پرداخت موفق و تأیید شده'),
                    ('failed', 'پرداخت ناموفق'),
                    ('cancelled', 'لغو شده'),
                    ('verification_failed', 'خطا در تأیید پرداخت'),
                    ('already_verified', 'قبلاً تأیید شده'),
                    ('refunded', 'مسترد شده'),
                    ('manual_review', 'نیازمند بررسی دستی'),
                    ('receipt_submitted', 'رسید ارسال شده — در انتظار تأیید'),
                    ('receipt_rejected', 'رسید رد شده'),
                ],
                default='created',
                max_length=30,
                verbose_name='وضعیت',
            ),
        ),
    ]
