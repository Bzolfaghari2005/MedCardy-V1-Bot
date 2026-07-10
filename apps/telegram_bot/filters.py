from aiogram.filters import BaseFilter
from aiogram.types import Message

from apps.telegram_bot.utils import aget_label


class LabelFilter(BaseFilter):
    """Match incoming message text against a bot label key from the admin panel."""

    def __init__(self, key: str):
        self.key = key

    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        return message.text == await aget_label(self.key)


class LabelInFilter(BaseFilter):
    """Match message text against any of the given label keys."""

    def __init__(self, *keys: str):
        self.keys = keys

    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        for key in self.keys:
            if message.text == await aget_label(key):
                return True
        return False


class WalletAmountFilter(BaseFilter):
    """Match predefined wallet charge amount buttons."""

    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        from apps.telegram_bot.utils import aget_wallet_amounts
        amounts = await aget_wallet_amounts()
        return message.text in amounts
