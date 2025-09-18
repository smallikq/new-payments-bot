from aiogram.types import Message
from services.banking.parser import extract_bank_payment
from core.database import add_income, get_balance
from bot.ui.keyboards import create_main_menu
from bot.middleware.auth import is_admin

async def handle_private_text_message(message: Message):
    if not is_admin(message.from_user.id):
        return

    amount = extract_bank_payment(message.text)
    if amount is not None:
        add_income(amount)
        incoming, _, _ = get_balance()
        await message.reply(
            f"✅ Пополнение {amount:.2f} UAH\n"
            f"💰 Всего: {incoming:.2f} UAH",
            parse_mode="HTML"
        )
        return

    await message.reply("❓ Не удалось распознать сообщение", reply_markup=create_main_menu())
