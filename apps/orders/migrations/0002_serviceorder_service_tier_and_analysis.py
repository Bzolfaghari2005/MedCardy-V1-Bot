from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceorder',
            name='detected_char_count',
            field=models.PositiveIntegerField(default=0, verbose_name='کاراکتر شناسایی‌شده'),
        ),
        migrations.AddField(
            model_name='serviceorder',
            name='detected_pages',
            field=models.PositiveIntegerField(default=0, verbose_name='صفحات شناسایی‌شده'),
        ),
        migrations.AddField(
            model_name='serviceorder',
            name='service_tier',
            field=models.CharField(
                choices=[('review', 'نسخه مروری'), ('full', 'آموزش کامل')],
                default='full',
                max_length=10,
                verbose_name='نوع نسخه',
            ),
        ),
    ]
