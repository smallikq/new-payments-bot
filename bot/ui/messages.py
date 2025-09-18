from core.database import get_balance, withdrawals_without_check, get_settings_safe
from services.alerts.emergency import emergency_task

def format_balance_message(incoming: float, checks: float):
    balance = incoming - checks
    if balance > 1000:
        status_emoji, status_text = "🟢", "Отличный"
    elif balance >= 0:
        status_emoji, status_text = "✅", "Положительный"
    elif balance >= -500:
        status_emoji, status_text = "⚠️", "Низкий"
    else:
        status_emoji, status_text = "🔴", "Критический"

    return f"""
🏦 <b>ФИНАНСОВЫЙ БАЛАНС</b>
{'═'*35}

💵 Пополнения: <code>{incoming:.2f} UAH</code>
🧾 Расходы: <code>{checks:.2f} UAH</code>
📊 Выводов без чеков: <code>{withdrawals_without_check}</code>

{status_emoji} Баланс: <code>{balance:.2f} UAH</code>
📈 Статус: {status_text}
"""

def format_settings_info():
    auto_reset_time, critical_checks, critical_balance, alert_rate, emergency_enabled = get_settings_safe()
    enabled_status = "✅ Включена" if emergency_enabled else "❌ Отключена"
    reset_time_display = auto_reset_time or "⚠️ Не задано"
    return f"""
⚙️ <b>НАСТРОЙКИ</b>
{'═'*35}

⏰ Автосброс: {reset_time_display}
🚨 Тревога: {enabled_status}
📋 Лимит выводов: <code>{critical_checks}</code>
💸 Критический баланс: <code>{critical_balance:.2f} UAH</code>
📢 Частота уведомлений: <code>{alert_rate}</code>/мин
"""

def format_help_message():
    return """
🤖 <b>СПРАВКА</b>

📥 Пополнения: автоматическое распознавание
🧾 Чеки: отправьте фото квитанции
🚨 Тревога: активируется при критических условиях
⚙️ Дополнительно: статистика, сброс, отчёты
"""

def format_system_status():
    incoming, checks, _ = get_balance()
    balance = incoming - checks
    _, _, _, _, emergency_enabled = get_settings_safe()

    emergency_status = "🟢 Включена" if emergency_enabled else "🔴 Отключена"
    alerts_status = "🚨 Активна" if emergency_task and not emergency_task.done() else "💤 Неактивна"

    return f"""
🛠️ <b>СТАТУС</b>
{'═'*35}

Баланс: <code>{balance:.2f} UAH</code>
Система тревоги: {emergency_status}
Рассылка уведомлений: {alerts_status}
"""
