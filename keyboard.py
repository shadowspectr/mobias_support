import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton ,ReplyKeyboardMarkup


def get_start_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏬 Адреса магазинов")],
            [KeyboardButton(text="🎁 Актуальные акции")],
            [KeyboardButton(text="❓ Обратиться в поддержку")]
        ],
        resize_keyboard=True,   # кнопки под размер экрана
        one_time_keyboard=False # клавиатура будет постоянно на экране
    )
    return keyboard


def get_app_keyboard():
    buttons = [
        [InlineKeyboardButton(text="App Store", url="https://apps.apple.com/us/app/%D0%BE%D0%B7%D0%BE%D0%BD-%D0%BE%D0%BD%D0%BB%D0%B0%D0%B9%D0%BD-%D0%B8%D0%BD%D1%82%D0%B5%D1%80%D0%BD%D0%B5%D1%82-%D0%BC%D0%B0%D0%B3%D0%B0%D0%B7%D0%B8%D0%BD/id407804998")],
        [InlineKeyboardButton(text="Google Play", url="https://play.google.com/store/apps/details?id=ru.ozon.app.android")],
        [InlineKeyboardButton(text="AppGallery", url="https://appgallery.huawei.com/#/app/C100847609")],
        [InlineKeyboardButton(text="RuStore", url="https://apps.rustore.ru/app/ru.ozon.app.android")],
        [InlineKeyboardButton(text="Вернуться на главную", callback_data="open_main")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_pay_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Привязать банковскую карту", callback_data="set_bank_card")],
        [InlineKeyboardButton(text="СПБ", callback_data= "set_sbp_card")],
        [InlineKeyboardButton(text="По карте Озон Банка", callback_data="set_ozon_bank_card")],
        [InlineKeyboardButton(text="Вернуться на главную", callback_data="open_main")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_location_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Отправить геопозицию", callback_data="send_geo")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

