"""Download files from Telegram Bot API."""
import logging
import tempfile
from pathlib import Path

from aiogram import Bot
from django.core.files import File

logger = logging.getLogger(__name__)


async def download_telegram_file(bot: Bot, file_id: str, file_name: str = 'upload') -> Path:
    """Download a Telegram file to a temporary path and return the path."""
    tg_file = await bot.get_file(file_id)
    suffix = Path(file_name).suffix or ''
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = Path(tmp.name)
    tmp.close()
    await bot.download_file(tg_file.file_path, destination=tmp_path)
    return tmp_path


def save_file_to_order(order, local_path: Path, file_name: str):
    """Attach a local file to ServiceOrder.uploaded_file."""
    with open(local_path, 'rb') as f:
        order.uploaded_file.save(file_name, File(f), save=True)
