from django.db import migrations


START_MESSAGE_TEXT = (
    '✨ سلام، خوش اومدی به MedCardy!\n\n'
    '🎙️ MedCardy جزوه‌های پزشکی رو به پادکست‌های آموزشی حرفه‌ای تبدیل می‌کنه.\n\n'
    'از منوی پایین می‌تونی:\n'
    '📚 دوره‌های آماده رو مشاهده کنی\n'
    '🎙️ جزوه‌ات رو برای ساخت پادکست اختصاصی بفرستی\n'
    '👥 با همکلاسی‌هات سفارش گروهی بدی\n'
    '💳 کیف پولت رو مدیریت کنی\n\n'
    '⬇️ یه گزینه انتخاب کن:'
)

REPLACEMENTS = [
    ('دوره‌های رایگان و پولی', 'دوره‌های آماده'),
    ('دوره‌های پولی', 'دوره‌ها'),
    ('دوره پولی', 'دوره'),
    ('پیام پرداخت دوره پولی', 'پیام خرید دوره'),
]


def _apply_replacements(text: str) -> str:
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    return text


def remove_poli_wording(apps, schema_editor):
    BotMessage = apps.get_model('bot_messages', 'BotMessage')
    BotLabel = apps.get_model('bot_messages', 'BotLabel')

    BotMessage.objects.filter(key='start_message').update(
        title='پیام خوش‌آمدگویی',
        text=START_MESSAGE_TEXT,
    )

    for msg in BotMessage.objects.all():
        updated_title = _apply_replacements(msg.title)
        updated_text = _apply_replacements(msg.text)
        if updated_title != msg.title or updated_text != msg.text:
            msg.title = updated_title
            msg.text = updated_text
            msg.save(update_fields=['title', 'text'])

    for label in BotLabel.objects.all():
        updated_title = _apply_replacements(label.title)
        updated_text = _apply_replacements(label.text)
        if updated_title != label.title or updated_text != label.text:
            label.title = updated_title
            label.text = updated_text
            label.save(update_fields=['title', 'text'])


class Migration(migrations.Migration):

    dependencies = [
        ('bot_messages', '0005_update_delivery_time_wording'),
    ]

    operations = [
        migrations.RunPython(remove_poli_wording, migrations.RunPython.noop),
    ]
