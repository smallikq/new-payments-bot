from telethon import TelegramClient
from core.config import API_ID, API_HASH, SESSION, TOP_UP_CHAT_ID, CHECKS_CHAT_ID
from utils.logger import logger

userbot: TelegramClient | None = None

async def init_userbot():
    """Инициализирует Telethon userbot"""
    global userbot
    if not (API_ID and API_HASH):
        logger.error("❌ Не заданы API_ID/API_HASH, userbot не будет инициализирован")
        return None

    userbot = TelegramClient(SESSION, API_ID, API_HASH)

    try:
        await userbot.start()
        me = await userbot.get_me()
        logger.info(f"✅ Userbot запущен: {me.first_name} (@{me.username or 'без username'})")

        try:
            topup_entity = await userbot.get_entity(TOP_UP_CHAT_ID)
            logger.info(f"Доступ к чату пополнений: {getattr(topup_entity, 'title', TOP_UP_CHAT_ID)}")
        except Exception as e:
            logger.warning(f"Нет доступа к чату пополнений: {e}")

        try:
            checks_entity = await userbot.get_entity(CHECKS_CHAT_ID)
            logger.info(f"Доступ к чату чеков: {getattr(checks_entity, 'title', CHECKS_CHAT_ID)}")
        except Exception as e:
            logger.warning(f"Нет доступа к чату чеков: {e}")

    except Exception as e:
        logger.error(f"Ошибка запуска userbot: {e}")
        userbot = None

    return userbot
