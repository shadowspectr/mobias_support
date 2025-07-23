from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any
import logging
import os

USER_IDS_FILE = "user_ids.txt"

def load_user_ids():
    if not os.path.exists(USER_IDS_FILE):
        with open(USER_IDS_FILE, "w") as f:
            pass
        logging.info("Создан новый файл user_ids.txt")
        return set()
    with open(USER_IDS_FILE, "r") as file:
        return set(line.strip() for line in file if line.strip().isdigit())

def save_user_id(user_id: int):
    try:
        user_ids = load_user_ids()
        if str(user_id) not in user_ids:
            with open(USER_IDS_FILE, "a") as file:
                file.write(f"{user_id}\n")
            logging.info(f"Добавлен новый user_id: {user_id}")
        else:
            logging.info(f"user_id {user_id} уже в списке")
    except Exception as e:
        logging.error(f"Ошибка при сохранении user_id {user_id}: {e}")


class UserLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Any],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = getattr(event, 'from_user', None)
        if user:
            save_user_id(user.id)
        return await handler(event, data)
