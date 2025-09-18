from aiogram import F
from aiogram.types import Message
from aiogram.filters import Command
from bot.ui.keyboards import create_main_menu
from bot.middleware.auth import is_admin

async def handle_start_private(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа.")
        return

    welcome_text = f"""
👋 Привет, {message.from_user.first_name}!
Я помогу отслеживать пополнения и чеки.
"""
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=create_main_menu())
