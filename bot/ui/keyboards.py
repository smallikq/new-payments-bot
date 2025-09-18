from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database import get_settings_safe

def create_main_menu():
    """Главное меню"""
    _, _, _, _, emergency_enabled = get_settings_safe()
    emergency_emoji = "🟢" if emergency_enabled else "🔴"
    emergency_text = f"{emergency_emoji} Тревога: {'Включена' if emergency_enabled else 'Отключена'}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Текущий баланс", callback_data="balance"),
         InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
         InlineKeyboardButton(text="🛠️ Статус системы", callback_data="status")],
        [InlineKeyboardButton(text=emergency_text, callback_data="toggle_emergency")],
        [InlineKeyboardButton(text="🔄 Сброс данных", callback_data="reset"),
         InlineKeyboardButton(text="❓ Справка", callback_data="help")]
    ])

def create_settings_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏰ Автосброс по времени", callback_data="set_time")],
        [InlineKeyboardButton(text="🚨 Настройки тревоги", callback_data="emergency_settings")],
        [InlineKeyboardButton(text="📢 Частота уведомлений", callback_data="alert_settings")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
    ])

def create_emergency_settings_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Лимит выводов подряд", callback_data="set_checks_limit")],
        [InlineKeyboardButton(text="💸 Критический баланс", callback_data="set_balance_limit")],
        [InlineKeyboardButton(text="⚙️ Назад к настройкам", callback_data="settings")]
    ])

def create_reset_confirmation():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, сбросить", callback_data="confirm_reset"),
         InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_reset")]
    ])
