import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Основные настройки бота
API_TOKEN = os.getenv("BOT_TOKEN", "")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_NAME", "payments_userbot.session")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "7305514955"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "payments.db")

# ID чатов для мониторинга
TOP_UP_CHAT_ID = int(os.getenv("TOP_UP_CHAT_ID", "-1002957591744"))
CHECKS_CHAT_ID = int(os.getenv("CHECKS_CHAT_ID", "-1002994974354"))
ALLOWED_CHATS = {TOP_UP_CHAT_ID, CHECKS_CHAT_ID}

# ID чатов для тревог
ALERT_CHAT_IDS = [
    int(os.getenv("ALERT_CHAT_1", "-1003062201623")),  # чат 1
    int(os.getenv("ALERT_CHAT_2", "-1002720363713"))   # чат 2
]
