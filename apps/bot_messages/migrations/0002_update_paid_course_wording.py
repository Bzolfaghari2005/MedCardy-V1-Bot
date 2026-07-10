from django.db import migrations


def update_bot_messages(apps, schema_editor):
    BotMessage = apps.get_model('bot_messages', 'BotMessage')
    replacements = [
        ('دوره‌های پولی', 'دوره‌های اختصاصی'),
        ('دوره پولی', 'دوره اختصاصی'),
        ('پیام پرداخت دوره پولی', 'پیام خرید دوره اختصاصی'),
    ]
    for msg in BotMessage.objects.all():
        updated = False
        for old, new in replacements:
            if old in msg.title:
                msg.title = msg.title.replace(old, new)
                updated = True
            if old in msg.text:
                msg.text = msg.text.replace(old, new)
                updated = True
        if updated:
            msg.save(update_fields=['title', 'text'])


def reverse_update(apps, schema_editor):
    BotMessage = apps.get_model('bot_messages', 'BotMessage')
    replacements = [
        ('دوره‌های اختصاصی', 'دوره‌های پولی'),
        ('دوره اختصاصی', 'دوره پولی'),
        ('پیام خرید دوره اختصاصی', 'پیام پرداخت دوره پولی'),
    ]
    for msg in BotMessage.objects.all():
        updated = False
        for old, new in replacements:
            if old in msg.title:
                msg.title = msg.title.replace(old, new)
                updated = True
            if old in msg.text:
                msg.text = msg.text.replace(old, new)
                updated = True
        if updated:
            msg.save(update_fields=['title', 'text'])


class Migration(migrations.Migration):

    dependencies = [
        ('bot_messages', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(update_bot_messages, reverse_update),
    ]
