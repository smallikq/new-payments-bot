import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import API_TOKEN
from core.database import init_database
from services.alerts.scheduler import schedule_auto_reset
from services.alerts import emergency
from userbot.client import init_userbot

from bot.handlers.commands import setup_command_handlers
from bot.handlers.callbacks import setup_callback_handlers
from bot.handlers.messages import handle_private_text_message
from bot.handlers.media import setup_media_handlers
from bot.handlers.settings import setup_settings_handlers
from bot.middleware.auth import is_admin

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8")
    ],
)
logger = logging.getLogger("payments-bot")


async def main():
    """Основная функция запуска бота"""
    try:
        logger.info("🚀 Запуск Payments Bot v2.0...")

        # Инициализация БД
        logger.info("🔧 Инициализация базы данных...")
        init_database()

        # Инициализация aiogram-бота
        logger.info("🤖 Инициализация Telegram бота...")
        bot = Bot(token=API_TOKEN, parse_mode="HTML")
        dp = Dispatcher(storage=MemoryStorage())

        # Передаём bot в emergency для рассылки
        emergency.bot = bot

        # === Регистрация всех хендлеров ===

        logger.info("📝 Регистрация обработчиков...")

        # Команды
        setup_command_handlers(dp)

        # Callback хендлеры (кнопки)
        setup_callback_handlers(dp)

        # Settings хендлеры (FSM)
        setup_settings_handlers(dp)

        # Media хендлеры (фото, документы, и т.д.)
        setup_media_handlers(dp)

        # Текстовые сообщения (должны быть в конце, чтобы не перехватывали команды)
        dp.message.register(
            handle_private_text_message,
            lambda m: (
                    m.chat.type == "private" and
                    is_admin(m.from_user.id) and
                    m.text and
                    not m.text.startswith('/') and
                    not m.photo and
                    not m.document and
                    not m.voice and
                    not m.video and
                    not m.sticker
            )
        )

        # === Запуск компонентов ===

        # Запуск userbot
        logger.info("📱 Инициализация userbot...")
        try:
            userbot = await init_userbot()
            if userbot:
                asyncio.create_task(userbot.run_until_disconnected())
                logger.info("✅ Userbot запущен успешно")
            else:
                logger.warning("⚠️ Userbot не инициализирован (проверьте API_ID/API_HASH)")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска userbot: {e}")

        # Запуск планировщика автосброса
        logger.info("⏰ Запуск планировщика автосброса...")
        try:
            asyncio.create_task(schedule_auto_reset())
            logger.info("✅ Планировщик запущен")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска планировщика: {e}")

        # Финальный статус
        logger.info("🎉 Все компоненты инициализированы!")
        logger.info("📡 Бот готов к приему сообщений...")

        # Запуск бота
        await dp.start_polling(bot, skip_updates=True)

    except Exception as e:
        logger.error(f"💥 Критическая ошибка при запуске: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Неожиданная ошибка: {e}")
        exit(1)