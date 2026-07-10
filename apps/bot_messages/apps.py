from django.apps import AppConfig


class BotMessagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.bot_messages'
    label = 'bot_messages'
    verbose_name = 'پیام‌های بات'

    def ready(self):
        import apps.bot_messages.signals  # noqa: F401
