import os
import json
import random
import logging
from aiogram import Bot
from aiogram.types import FSInputFile
from src.user_storage import load_user_ids

ADS_FOLDER = "ads"

def load_ads():
    try:
        with open(os.path.join(ADS_FOLDER, "ads_metadata.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка при загрузке рекламы: {e}")
        return []

async def send_random_ad(bot: Bot):
    user_ids = load_user_ids()
    ads = load_ads()

    if not ads:
        logging.warning("Нет рекламных материалов для отправки")
        return

    ad = random.choice(ads)
    image_path = os.path.join(ADS_FOLDER, ad["image"])
    caption = ad["text"]

    for user_id in user_ids:
        try:
            photo = FSInputFile(image_path)
            await bot.send_photo(chat_id=int(user_id), photo=photo, caption=caption, parse_mode="HTML")
            logging.info(f"Реклама отправлена пользователю {user_id}")
        except Exception as e:
            logging.error(f"Ошибка отправки рекламы пользователю {user_id}: {e}")

async def send_ad_to_user(bot: Bot, user_id: int):
    ads = load_ads()

    if not ads:
        logging.warning("Нет рекламных материалов для отправки")
        return

    ad = random.choice(ads)
    image_path = os.path.join(ADS_FOLDER, ad["image"])
    caption = ad["text"]

    try:
        photo = FSInputFile(image_path)
        await bot.send_photo(chat_id=user_id, photo=photo, caption=caption, parse_mode="HTML")
        logging.info(f"Акция отправлена пользователю {user_id}")
    except Exception as e:
        logging.error(f"Ошибка при отправке акции пользователю {user_id}: {e}")
