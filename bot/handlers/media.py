from aiogram.types import Message
from services.ocr.processor import process_check_image_aiogram
from core.database import add_check, save_check_screenshot, get_balance
from bot.ui.keyboards import create_main_menu
from bot.middleware.auth import is_admin

async def handle_check_private(message: Message, bot):
    if not is_admin(message.from_user.id):
        return

    processing = await message.reply("🔄 Обработка чека...")

    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    amount, full_text = await process_check_image_aiogram(bot, file_id)

    if amount:
        add_check(amount)
        save_check_screenshot(file_id, amount, full_text or "")
        incoming, checks, _ = get_balance()
        await processing.edit_text(
            f"✅ Чек: {amount:.2f} UAH\n"
            f"📊 Баланс: {incoming - checks:.2f} UAH",
            parse_mode="HTML",
            reply_markup=create_main_menu()
        )
    else:
        await processing.edit_text(
            f"⚠️ Сумма не распознана.\n\nТекст OCR:\n<pre>{full_text}</pre>",
            parse_mode="HTML",
            reply_markup=create_main_menu()
        )
