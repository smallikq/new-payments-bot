import asyncio
from core.config import ALERT_CHAT_IDS
from core.database import get_balance, withdrawals_without_check
from utils.logger import logger
from aiogram import Bot
from core.database import get_settings_safe

# Глобальная задача рассылки тревог
emergency_task = None
bot: Bot | None = None  # будет установлен из main.py


async def check_emergency_conditions():
    """Проверяет условия активации тревоги"""
    _, critical_withdrawals, critical_balance, alert_rate, emergency_enabled = get_settings_safe()
    incoming, checks, _ = get_balance()
    balance = incoming - checks

    if not emergency_enabled:
        await stop_emergency_alerts()
        return

    triggered = False
    if withdrawals_without_check >= critical_withdrawals:
        triggered = True
        logger.warning(f"Тревога: выводов подряд {withdrawals_without_check} >= {critical_withdrawals}")

    if balance >= critical_balance:
        triggered = True
        logger.warning(f"Тревога: баланс {balance:.2f} >= {critical_balance:.2f}")

    if triggered:
        await start_emergency_alerts(alert_rate)
    else:
        await stop_emergency_alerts()


async def start_emergency_alerts(messages_per_minute: int):
    """Запускает рассылку тревожных уведомлений"""
    global emergency_task
    if emergency_task and not emergency_task.done():
        emergency_task.cancel()
    emergency_task = asyncio.create_task(send_emergency_alerts(messages_per_minute))


async def send_emergency_alerts(messages_per_minute: int):
    """Отправляет тревожные уведомления"""
    try:
        interval = 60 / max(1, int(messages_per_minute))
        logger.info(f"Запущена рассылка тревог (интервал {interval:.1f} сек)")

        while True:
            try:
                message_text = (
                    "🚨 <b>@trn_a СТОПАЙ ТРАФИК!</b> 🚨\n\n"
                    "⛔️ <b>(пока Алексей не напишет не запускать)</b> ⛔️\n\n"
                )
                if bot:
                    for chat_id in ALERT_CHAT_IDS:
                        await bot.send_message(chat_id, message_text, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Ошибка при рассылке тревог: {e}")
            await asyncio.sleep(interval)

    except asyncio.CancelledError:
        logger.info("Рассылка тревог остановлена")


async def stop_emergency_alerts():
    """Останавливает тревогу"""
    global emergency_task
    if emergency_task and not emergency_task.done():
        emergency_task.cancel()
        emergency_task = None
        logger.info("Система тревоги остановлена")
