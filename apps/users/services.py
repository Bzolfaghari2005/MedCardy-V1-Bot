import logging
from apps.users.models import TelegramUser, PersonalPanel

logger = logging.getLogger(__name__)


def get_or_create_telegram_user(telegram_id: int, username: str = None,
                                 first_name: str = '', last_name: str = None) -> TelegramUser:
    user, created = TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            'username': username,
            'first_name': first_name or '',
            'last_name': last_name,
        }
    )
    if not created:
        changed = False
        if username is not None and user.username != username:
            user.username = username
            changed = True
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if last_name is not None and user.last_name != last_name:
            user.last_name = last_name
            changed = True
        if changed:
            user.save(update_fields=['username', 'first_name', 'last_name', 'updated_at'])
    return user


def get_or_create_personal_panel(user: TelegramUser) -> tuple[PersonalPanel, bool]:
    """Return (panel, created). Sets status=needs_creation on new panels."""
    try:
        return user.personal_panel, False
    except PersonalPanel.DoesNotExist:
        panel = PersonalPanel.objects.create(
            user=user,
            status=PersonalPanel.STATUS_NEEDS_CREATION,
            title=f'MedCardy | پنل شخصی {user.user_code}',
        )
        logger.info(f'PersonalPanel created for user {user.user_code}')
        return panel, True


def get_setting_value(key: str, default: str = '') -> str:
    from apps.settings_app.models import Setting
    try:
        return Setting.objects.get(key=key).value
    except Setting.DoesNotExist:
        return default


def get_bot_message_text(key: str, default: str = '') -> str:
    from apps.bot_messages.models import BotMessage
    try:
        msg = BotMessage.objects.get(key=key, is_active=True)
        return msg.text
    except BotMessage.DoesNotExist:
        return default
