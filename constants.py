# constants.py (ОБНОВЛЕННАЯ ВЕРСИЯ)

# --- ID Чатов ---
SUPPORT_TICKETS_CHAT_ID = -4961897884
ADMIN_USER_ID = 12345678 # Замените на ваш ID для отладки

# --- Таймаут ---
DIALOG_TIMEOUT_SECONDS = 5 * 3600  # 5 часов

# --- Тексты кнопок ---
PROMOTION_BUTTON_TEXT = "🎁 Актуальные акции"
ADDRESS_BUTTON_TEXT = "🏬 Адреса магазинов"
SUPPORT_BUTTON_TEXT = "❓ Задать вопрос"
END_DIALOG_BUTTON_TEXT = "❌ Завершить диалог"

# --- Множество для быстрой проверки ---
KNOWN_BUTTONS = {
    PROMOTION_BUTTON_TEXT,
    ADDRESS_BUTTON_TEXT,
    SUPPORT_BUTTON_TEXT,
}