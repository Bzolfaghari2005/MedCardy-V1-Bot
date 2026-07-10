from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.bot_messages.models import BotLabel


@receiver([post_save, post_delete], sender=BotLabel)
def invalidate_bot_label_cache(sender, **kwargs):
    from apps.telegram_bot.utils import invalidate_label_cache
    invalidate_label_cache()
