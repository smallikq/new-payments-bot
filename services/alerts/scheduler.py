import asyncio
from datetime import datetime, timedelta
import pytz
from utils.logger import logger
from core.database import get_settings_safe, reset_all_data
from services.alerts.emergency import stop_emergency_alerts

async def schedule_auto_reset():
    """Планировщик ежедневного сброса"""
    try:
        tz = pytz.timezone("Europe/Kyiv")
    except Exception:
        tz = pytz.timezone("Europe/Kiev")

    while True:
        auto_reset_time, _, _, _, _ = get_settings_safe()

        if not auto_reset_time:
            logger.info("⏳ Автосброс не настроен. Проверю снова через минуту.")
            await asyncio.sleep(60)
            continue

        try:
            hour, minute = map(int, auto_reset_time.split(":"))
        except Exception:
            logger.error(f"Некорректный формат auto_reset_time='{auto_reset_time}'. Ожидается HH:MM.")
            await asyncio.sleep(60)
            continue

        now = datetime.now(tz)
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target_time <= now:
            target_time += timedelta(days=1)

        sleep_seconds = max(1, int((target_time - now).total_seconds()))
        logger.info(f"Автосброс запланирован на {target_time} (через {sleep_seconds//60} мин).")

        try:
            await asyncio.sleep(sleep_seconds)
        except asyncio.CancelledError:
            logger.info("Задача автосброса отменена (изменили время).")
            return

        try:
            reset_all_data()
            await stop_emergency_alerts()
            logger.info(f"✅ Выполнен автосброс в {datetime.now(tz)}")
        except Exception as e:
            logger.error(f"Ошибка при автосбросе: {e}")
