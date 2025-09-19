from telethon import events, TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from core.config import TOP_UP_CHAT_ID, CHECKS_CHAT_ID, ALLOWED_CHATS
from core.database import add_income, add_withdrawal, add_check, save_check_screenshot
from services.banking.parser import extract_bank_payment
from services.ocr.processor import process_check_image_telethon
from utils.logger import logger
import asyncio


def setup_userbot_handlers(client: TelegramClient):
    """Регистрирует все обработчики для userbot"""

    @client.on(events.NewMessage(chats=ALLOWED_CHATS))
    async def handle_userbot_message(event):
        """Главный обработчик сообщений userbot"""
        chat_id = event.chat_id
        message_text = event.raw_text or ""

        try:
            # Логируем получение сообщения
            if chat_id == TOP_UP_CHAT_ID:
                logger.debug(f"📥 Новое сообщение в чате пополнений: {message_text[:50]}...")
                await handle_income_message(event, message_text, client)

            elif chat_id == CHECKS_CHAT_ID:
                # Проверяем, что это изображение
                is_photo = event.photo is not None
                is_image_doc = (event.document and
                                hasattr(event.document, 'mime_type') and
                                event.document.mime_type and
                                event.document.mime_type.startswith('image/'))

                if not (is_photo or is_image_doc):
                    logger.debug(f"📝 Пропущено сообщение в чате чеков (не изображение): {message_text[:50]}...")
                    return

                logger.debug("🖼️ Новое изображение в чате чеков")
                await handle_check_message(event, message_text, client)

        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения userbot: {e}")

    @client.on(events.MessageEdited(chats=ALLOWED_CHATS))
    async def handle_edited_message(event):
        """Обработка отредактированных сообщений"""
        try:
            chat_id = event.chat_id
            message_text = event.raw_text or ""

            if chat_id == TOP_UP_CHAT_ID:
                logger.info(f"✏️ Сообщение отредактировано в чате пополнений")
                # Можно переобработать сообщение если нужно
                await handle_income_message(event, message_text, client)

        except Exception as e:
            logger.error(f"❌ Ошибка обработки редактирования: {e}")

    @client.on(events.MessageDeleted(chats=ALLOWED_CHATS))
    async def handle_deleted_message(event):
        """Обработка удаленных сообщений"""
        try:
            logger.info(f"🗑️ Сообщение удалено в отслеживаемом чате")
            # Здесь можно добавить логику отмены транзакций

        except Exception as e:
            logger.error(f"❌ Ошибка обработки удаления: {e}")

    logger.info("✅ Обработчики userbot зарегистрированы")


async def handle_income_message(event, message_text: str, client: TelegramClient):
    """Обработка сообщений в канале пополнений"""
    try:
        # Сначала пытаемся извлечь сумму из текста
        amount = extract_bank_payment(message_text)

        # Если в сообщении есть изображение и сумма не найдена
        if amount is None and (event.photo or event.document):
            logger.info("🔍 Текст не содержит суммы, пробуем OCR...")

            try:
                ocr_amount, full_text = await process_check_image_telethon(client, event.message)

                # Пытаемся найти сумму в распознанном тексте
                if full_text:
                    amount = extract_bank_payment(full_text)

                # Если не нашли в тексте, используем сумму из OCR
                if amount is None:
                    amount = ocr_amount

                if amount:
                    logger.info(f"✅ OCR распознал сумму: {amount:.2f} UAH")

            except Exception as ocr_error:
                logger.error(f"❌ Ошибка OCR: {ocr_error}")

        if amount is None:
            logger.debug(f"❓ Не удалось определить сумму в сообщении")
            return

        # Обрабатываем найденную сумму
        if amount > 0:
            add_income(amount)
            logger.info(f"💰 Добавлено пополнение: {amount:.2f} UAH")

            # Уведомляем админа о крупных пополнениях
            if amount >= 1000:
                await notify_admin_about_large_transaction(client, "income", amount)

        elif amount < 0:
            add_withdrawal(amount)
            logger.info(f"💸 Зафиксирован вывод: {amount:.2f} UAH")

            # Уведомляем админа о крупных выводах
            if abs(amount) >= 500:
                await notify_admin_about_large_transaction(client, "withdrawal", amount)

    except Exception as e:
        logger.error(f"❌ Ошибка обработки пополнения: {e}")


async def handle_check_message(event, message_text: str, client: TelegramClient):
    """Обработка сообщений с чеками"""
    try:
        # Запускаем OCR для изображения
        logger.info("🔍 Запуск OCR для чека...")
        amount, full_text = await process_check_image_telethon(client, event.message)

        # Сохраняем ID сообщения как идентификатор файла
        file_id = str(event.message.id)

        # Проверяем валидность суммы
        if amount and 1 <= amount <= 50000:
            add_check(amount)
            save_check_screenshot(file_id, amount, full_text or "")
            logger.info(f"🧾 Добавлен чек: {amount:.2f} UAH (ID: {file_id})")

            # Отправляем подтверждение в чат
            try:
                await event.message.reply(f"✅ Чек распознан: {amount:.2f} UAH")
            except:
                pass  # Игнорируем ошибки отправки

        else:
            # Сохраняем нераспознанный чек
            save_check_screenshot(file_id, 0, full_text or "OCR failed")
            logger.warning(f"⚠️ Чек не распознан или некорректная сумма: {amount}")

            # Пытаемся найти сумму в тексте
            if full_text:
                text_amount = extract_bank_payment(full_text)
                if text_amount and text_amount > 0:
                    add_check(text_amount)
                    save_check_screenshot(file_id, text_amount, full_text)
                    logger.info(f"🧾 Сумма найдена в тексте: {text_amount:.2f} UAH")

                    try:
                        await event.message.reply(f"✅ Сумма из текста: {text_amount:.2f} UAH")
                    except:
                        pass

    except Exception as e:
        logger.error(f"❌ Ошибка обработки чека: {e}")

        # Пытаемся отправить уведомление об ошибке
        try:
            await event.message.reply(f"❌ Ошибка распознавания: {str(e)[:100]}")
        except:
            pass


async def notify_admin_about_large_transaction(client: TelegramClient, transaction_type: str, amount: float):
    """Уведомляет администратора о крупных транзакциях"""
    try:
        from core.config import ADMIN_CHAT_ID
        from core.database import get_balance

        incoming, checks, _ = get_balance()
        balance = incoming - checks

        if transaction_type == "income":
            emoji = "💰"
            action = "Крупное пополнение"
            color = "🟢"
        else:
            emoji = "💸"
            action = "Крупный вывод"
            color = "🔴"
            amount = abs(amount)

        message = f"""
{color} <b>{action}!</b>

{emoji} Сумма: <code>{amount:,.2f} UAH</code>
💼 Новый баланс: <code>{balance:,.2f} UAH</code>

<i>Автоматическое уведомление</i>
"""

        await client.send_message(ADMIN_CHAT_ID, message, parse_mode='html')

    except Exception as e:
        logger.error(f"❌ Не удалось отправить уведомление админу: {e}")


async def periodic_stats_report(client: TelegramClient):
    """Периодическая отправка статистики (запускается отдельной задачей)"""
    while True:
        try:
            # Ждем до следующего часа
            await asyncio.sleep(3600)  # 1 час

            from core.database import get_statistics
            from core.config import ADMIN_CHAT_ID
            from datetime import datetime
            import pytz

            stats = get_statistics()

            # Отправляем только если есть активность
            if stats['income_count'] > 0 or stats['check_count'] > 0:
                time_now = datetime.now(pytz.timezone('Europe/Kiev')).strftime('%H:%M')

                message = f"""
📊 <b>Часовой отчет ({time_now})</b>

💰 Баланс: <code>{stats['balance']:,.2f} UAH</code>
📈 Пополнений: {stats['income_count']} на {stats['incoming']:,.2f} UAH
📉 Чеков: {stats['check_count']} на {stats['checks']:,.2f} UAH

<i>Автоматический отчет</i>
"""

                await client.send_message(ADMIN_CHAT_ID, message, parse_mode='html')

        except Exception as e:
            logger.error(f"❌ Ошибка отправки периодического отчета: {e}")