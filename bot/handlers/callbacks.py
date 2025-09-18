from aiogram.types import CallbackQuery
from bot.ui.messages import (
    format_balance_message, format_settings_info,
    format_help_message, format_system_status
)
from bot.ui.keyboards import create_main_menu, create_settings_menu
from core.database import get_balance
from bot.middleware.auth import is_admin

async def handle_balance_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    incoming, checks, _ = get_balance()
    await callback.message.answer(
        format_balance_message(incoming, checks),
        parse_mode="HTML",
        reply_markup=create_main_menu()
    )
    await callback.answer()

async def handle_settings_callback(callback: CallbackQuery):
    await callback.message.answer(
        format_settings_info(),
        parse_mode="HTML",
        reply_markup=create_settings_menu()
    )
    await callback.answer()

async def handle_help_callback(callback: CallbackQuery):
    await callback.message.answer(
        format_help_message(),
        parse_mode="HTML",
        reply_markup=create_main_menu()
    )
    await callback.answer()

async def handle_status_callback(callback: CallbackQuery):
    await callback.message.answer(
        format_system_status(),
        parse_mode="HTML",
        reply_markup=create_main_menu()
    )
    await callback.answer()
