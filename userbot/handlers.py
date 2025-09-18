from telethon import events
from core.config import TOP_UP_CHAT_ID, CHECKS_CHAT_ID, ALLOWED_CHATS
from core.database import add_income, add_withdrawal, add_check, save_check_screenshot
from services.banking.parser import extract_bank_payment
from services.ocr.processor import process_check_image_telethon
from utils.logger import logger
from .client import userbot

if userbot:
    @userbot.on(events.NewMessage(chats=ALLOWED_CHATS))
    async def handle_userbot_message(event):
        chat_id = event.chat_id
        message_text = event.raw_text or ""

        try:
            if chat_id == TOP_UP_CHAT_ID:
                await handle_income_message(event, message_text)

            elif chat_id == CHECKS_CHAT_ID:
                if not (event.photo or (event.document and getattr(event.document, "mime_type", "").startswith("image/"))):
                    logger.debug("Пропущено сообщение в чате чеков (не изображение)")
                    return
                await handle_check_message(event, message_text)

        except Exception as e:
            logger.error(f"Ошибка userbot: {e}")


async def handle_income_message(event, message_text: str):
    """Обработка сообщений в канале пополнений"""
    try:
        amount = extract_bank_payment(message_text)

        if amount is None and (event.photo or event.document):
            ocr_amount, full_text = await process_check_image_telethon(userbot, event.message)
            amount = extract_bank_payment(full_text or "") or ocr_amount

        if amount is None:
            logger.debug("Не удалось определить сумму")
            return

        if amount > 0:
            add_income(amount)
            logger.info(f"💰 Пополнение: {amount} UAH")
        elif amount < 0:
            add_withdrawal(amount)
            logger.info(f"💸 Вывод: {amount} UAH")

    except Exception as e:
        logger.error(f"Ошибка обработки пополнения: {e}")


async def handle_check_message(event, message_text: str):
    """Обработка сообщений с чеками"""
    try:
        amount, full_text = await process_check_image_telethon(userbot, event.message)

        if amount and 1 <= amount <= 50000:
            add_check(amount)
            save_check_screenshot(str(event.id), amount, full_text or "")
            logger.info(f"🧾 Чек: {amount} UAH")
        else:
            save_check_screenshot(str(event.id), 0, full_text or "Ошибка OCR")
            logger.warning("⚠️ Чек не распознан")
    except Exception as e:
        logger.error(f"Ошибка обработки чека: {e}")
