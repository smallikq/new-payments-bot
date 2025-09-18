from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.states import SettingsStates
from core.database import update_setting
from bot.ui.keyboards import create_main_menu

async def handle_time_input(message: Message, state: FSMContext):
    update_setting("auto_reset_time", message.text)
    await state.clear()
    await message.answer("⏰ Время автосброса обновлено", reply_markup=create_main_menu())

async def handle_checks_limit_input(message: Message, state: FSMContext):
    update_setting("critical_checks_count", int(message.text))
    await state.clear()
    await message.answer("📋 Лимит выводов обновлён", reply_markup=create_main_menu())

async def handle_balance_limit_input(message: Message, state: FSMContext):
    update_setting("critical_balance_amount", float(message.text))
    await state.clear()
    await message.answer("💸 Критический баланс обновлён", reply_markup=create_main_menu())

async def handle_alert_rate_input(message: Message, state: FSMContext):
    update_setting("alert_messages_per_minute", int(message.text))
    await state.clear()
    await message.answer("📢 Частота уведомлений обновлена", reply_markup=create_main_menu())
