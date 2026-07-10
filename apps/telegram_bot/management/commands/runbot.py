"""
Management command to run the Telegram bot.
Usage: python manage.py runbot
"""
import asyncio
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run the MedCardy Telegram bot (polling mode)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🤖 Starting MedCardy Telegram bot...'))
        asyncio.run(self._run())

    async def _run(self):
        from apps.telegram_bot.bot import create_bot, create_dispatcher
        bot = create_bot()
        dp = create_dispatcher()

        bot_info = await bot.get_me()
        logger.info(f'Bot started: @{bot_info.username} (id={bot_info.id})')
        self.stdout.write(self.style.SUCCESS(f'✅ Bot running: @{bot_info.username}'))

        try:
            await dp.start_polling(bot, allowed_updates=['message', 'callback_query'])
        finally:
            await bot.session.close()
            logger.info('Bot stopped.')
