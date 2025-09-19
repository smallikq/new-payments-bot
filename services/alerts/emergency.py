import asyncio
from datetime import datetime
import pytz
from typing import Optional

from core.config import ALERT_CHAT_IDS
from core.database import get_balance, withdrawals_without_check, get_settings_safe
from utils.logger import logger
from aiogram import Bot

# Глобальные переменные
emergency_task: Optional[asyncio.Task] = None
bot: Optional[Bot] = None  # устанавливается из main.py
last_alert_time: Optional[datetime] = None
alert_count = 0


async def check_emergency_conditions():
    """Проверяет условия активации системы тревог"""
    try:
        _, critical_withdrawals, critical_balance, alert_rate, emergency_enabled = get_settings_safe()

        if not emergency_enabled:
            await stop_emergency_alerts()
            return

        incoming, checks, _ = get_balance()
        current_balance = incoming - checks

        # Проверяем условия
        withdrawal_trigger = withdrawals_without_check >= critical_withdrawals
        balance_trigger = current_balance >= critical_balance

        triggered = withdrawal_trigger or balance_trigger

        if triggered:
            # Логируем причину тревоги
            reasons = []
            if withdrawal_trigger:
                reasons.append(f"выводов подряд: {withdrawals_without_check} ≥ {critical_withdrawals}")
            if balance_trigger:
                reasons.append(f"баланс: {current_balance:.2f} ≥ {critical_balance:.2f}")

            logger.warning(f"🚨 Тревога активирована! Причины: {'; '.join(reasons)}")
            await start_emergency_alerts(alert_rate, reasons)
        else:
            await stop_emergency_alerts()

    except Exception as e:
        logger.error(f"❌ Ошибка проверки условий тревоги: {e}")


async def start_emergency_alerts(messages_per_minute: int, reasons: list):
    """Запускает рассылку тревожных уведомлений"""
    global emergency_task, alert_count

    # Останавливаем предыдущую задачу если есть
    if emergency_task and not emergency_task.done():
        emergency_task.cancel()
        try:
            await emergency_task
        except asyncio.CancelledError:
            pass

    alert_count = 0
    emergency_task = asyncio.create_task(send_emergency_alerts(messages_per_minute, reasons))


async def send_emergency_alerts(messages_per_minute: int, reasons: list):
    """Отправляет тревожные уведомления с указанной частотой"""
    global last_alert_time, alert_count

    try:
        interval = 60.0 / max(1, int(messages_per_minute))
        logger.info(f"🚨 Запущена рассылка тревог (интервал {interval:.1f} сек)")

        while True:
            try:
                if bot:
                    alert_count += 1
                    last_alert_time = datetime.now(pytz.timezone("Europe/Kiev"))

                    # Получаем актуальные данные
                    incoming, checks, _ = get_balance()
                    current_balance = incoming - checks

                    # Формируем сообщение тревоги
                    message_text = create_alert_message(current_balance, reasons, alert_count)

                    # Отправляем во все чаты тревог
                    for chat_id in ALERT_CHAT_IDS:
                        try:
                            await bot.send_message(chat_id, message_text, parse_mode="HTML")
                            logger.debug(f"📤 Тревога отправлена в чат {chat_id}")
                        except Exception as e:
                            logger.error(f"❌ Ошибка отправки в чат {chat_id}: {e}")
                else:
                    logger.warning("⚠️ Bot не инициализирован для рассылки тревог")

            except Exception as e:
                logger.error(f"❌ Ошибка при рассылке тревог: {e}")

            await asyncio.sleep(interval)

    except asyncio.CancelledError:
        logger.info("✅ Рассылка тревог остановлена")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в рассылке тревог: {e}")


def create_alert_message(balance: float, reasons: list, count: int) -> str:
    """Создает текст тревожного сообщения"""

    # Эмодзи в зависимости от серьезности
    if balance < -5000:
        urgency_emoji = "💀"
        urgency_text = "КРИТИЧЕСКАЯ"
    elif balance < -2000:
        urgency_emoji = "🔴"
        urgency_text = "ВЫСОКАЯ"
    elif balance < -500:
        urgency_emoji = "⚠️"
        urgency_text = "СРЕДНЯЯ"
    else:
        urgency_emoji = "🚨"
        urgency_text = "НИЗКАЯ"

    # Основной текст
    timestamp = datetime.now(pytz.timezone("Europe/Kiev")).strftime('%H:%M:%S')

    message = f"""
{urgency_emoji} <b>ТРЕВОГА! ОСТАНОВИТЕ ТРАФИК!</b> {urgency_emoji}

⛔ <b>@trn_a СРОЧНО ПРОВЕРЬТЕ СИТУАЦИЮ!</b>
🚨 Приоритет: <b>{urgency_text}</b>

💰 Баланс: <code>{balance:,.2f} ₴</code>
📊 Выводов без чеков: <code>{withdrawals_without_check}</code>

🔍 <b>Причины тревоги:</b>
"""

    for i, reason in enumerate(reasons, 1):
        message += f"└ {reason}\n"

    message += f"""
🕐 Время: <code>{timestamp}</code> (Киев)
🔢 Уведомление: <code>#{count}</code>

⚡ <b>ТРЕБУЮТСЯ НЕМЕДЛЕННЫЕ ДЕЙСТВИЯ!</b>
"""

    return message


async def stop_emergency_alerts():
    """Останавливает систему тревог"""
    global emergency_task, alert_count, last_alert_time

    if emergency_task and not emergency_task.done():
        emergency_task.cancel()
        try:
            await emergency_task
        except asyncio.CancelledError:
            pass

        emergency_task = None
        final_count = alert_count
        alert_count = 0
        last_alert_time = None

        logger.info(f"✅ Система тревог остановлена (отправлено {final_count} уведомлений)")


async def send_test_alert():
    """Отправляет тестовое уведомление"""
    if not bot:
        logger.warning("⚠️ Bot не инициализирован для теста")
        return False

    test_message = f"""
🧪 <b>ТЕСТ СИСТЕМЫ УВЕДОМЛЕНИЙ</b>

✅ Система работает корректно
🕐 Время: <code>{datetime.now(pytz.timezone('Europe/Kiev')).strftime('%H:%M:%S')}</code>
📡 Статус: Все чаты доступны

<i>Это тестовое сообщение для проверки рассылки тревог.</i>
"""

    success_count = 0
    for chat_id in ALERT_CHAT_IDS:
        try:
            await bot.send_message(chat_id, test_message, parse_mode="HTML")
            success_count += 1
            logger.info(f"✅ Тест отправлен в чат {chat_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки теста в чат {chat_id}: {e}")

    logger.info(f"🧪 Тест завершен: {success_count}/{len(ALERT_CHAT_IDS)} чатов доступны")
    return success_count > 0


def get_emergency_status() -> dict:
    """Возвращает статус системы тревог"""
    global emergency_task, alert_count, last_alert_time

    is_active = emergency_task and not emergency_task.done()

    return {
        'active': is_active,
        'enabled': get_settings_safe()[4],  # emergency_enabled
        'alert_count': alert_count,
        'last_alert': last_alert_time.isoformat() if last_alert_time else None,
        'task_status': 'running' if is_active else 'stopped'
    }


async def force_stop_all_alerts():
    """Принудительно останавливает все тревоги (для экстренных случаев)"""
    global emergency_task, alert_count, last_alert_time

    try:
        if emergency_task:
            emergency_task.cancel()
            try:
                await emergency_task
            except asyncio.CancelledError:
                pass
            emergency_task = None

        alert_count = 0
        last_alert_time = None

        logger.warning("🛑 ПРИНУДИТЕЛЬНАЯ ОСТАНОВКА ВСЕХ ТРЕВОГ")

        # Отправляем уведомление об остановке
        if bot:
            stop_message = f"""
🛑 <b>СИСТЕМА ТРЕВОГ ОСТАНОВЛЕНА</b>

⏹️ Все уведомления приостановлены
🕐 Время: <code>{datetime.now(pytz.timezone('Europe/Kiev')).strftime('%H:%M:%S')}</code>
👤 Причина: Принудительная остановка

<i>Система готова к повторному запуску при необходимости.</i>
"""

            for chat_id in ALERT_CHAT_IDS:
                try:
                    await bot.send_message(chat_id, stop_message, parse_mode="HTML")
                except:
                    pass  # игнорируем ошибки при принудительной остановке

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка принудительной остановки: {e}")
        return False