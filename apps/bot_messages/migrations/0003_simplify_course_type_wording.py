from django.db import migrations


def update_bot_messages(apps, schema_editor):
    BotMessage = apps.get_model('bot_messages', 'BotMessage')
    replacements = [
        ('دوره‌های اختصاصی', 'دوره‌ها'),
        ('دوره اختصاصی', 'دوره'),
        ('پیام خرید دوره اختصاصی', 'پیام خرید دوره'),
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
        ('دوره‌ها: بعد از خرید', 'دوره‌های اختصاصی: بعد از خرید'),
        ('پیام خرید دوره', 'پیام خرید دوره اختصاصی'),
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
        ('bot_messages', '0002_update_paid_course_wording'),
    ]

    operations = [
        migrations.RunPython(update_bot_messages, reverse_update),
    ]
