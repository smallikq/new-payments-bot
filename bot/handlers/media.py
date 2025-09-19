from aiogram.types import Message
from aiogram import Bot
import asyncio

from services.ocr.processor import process_check_image_aiogram
from core.database import add_check, save_check_screenshot, get_balance
from bot.ui.keyboards import create_main_menu
from bot.middleware.auth import is_admin
from utils.logger import logger


async def handle_check_private(message: Message, bot: Bot):
    """Обработка изображений чеков в приватном чате"""
    if not is_admin(message.from_user.id):
        logger.warning(f"❌ Попытка отправки чека от неавторизованного пользователя: {message.from_user.id}")
        return

    # Определяем тип медиафайла
    if message.photo:
        file_id = message.photo[-1].file_id  # Берем самое большое качество
        file_type = "фото"
    elif message.document and message.document.mime_type and message.document.mime_type.startswith('image/'):
        file_id = message.document.file_id
        file_type = "изображение"
    else:
        await message.answer(
            "❌ <b>Неподдерживаемый формат</b>\n\n"
            "Отправьте фото или изображение в формате JPG, PNG, WebP.",
            parse_mode="HTML"
        )
        return

    # Показываем статус обработки
    processing_msg = await message.reply(
        "🔄 <b>Обработка чека...</b>\n\n"
        f"📁 Тип: {file_type}\n"
        f"🔍 Запуск OCR распознавания...",
        parse_mode="HTML"
    )

    try:
        # Обрабатываем изображение через OCR
        amount, full_text = await process_check_image_aiogram(bot, file_id)

        # Получаем текущий баланс для отображения
        incoming, checks, _ = get_balance()
        current_balance = incoming - checks

        if amount and amount > 0:
            # Успешно распознали сумму
            add_check(amount)
            save_check_screenshot(file_id, amount, full_text or "")

            # Обновляем баланс после добавления чека
            new_incoming, new_checks, _ = get_balance()
            new_balance = new_incoming - new_checks
            balance_change = new_balance - current_balance

            success_text = f"""
✅ <b>ЧЕК ДОБАВЛЕН</b>

🧾 Сумма: <code>{amount:.2f} ₴</code>
💰 Новый баланс: <code>{new_balance:,.2f} ₴</code>
📊 Изменение: <code>{balance_change:,.2f} ₴</code>

📈 Всего чеков: <code>{new_checks:.2f} ₴</code>
🔍 OCR: Распознано успешно
"""

            await processing_msg.edit_text(
                success_text,
                parse_mode="HTML",
                reply_markup=create_main_menu()
            )

            logger.info(f"✅ Чек добавлен: {amount:.2f} ₴ (файл: {file_id})")

        else:
            # Не удалось распознать сумму
            save_check_screenshot(file_id, 0, full_text or "Ошибка OCR")

            # Обрезаем текст OCR для отображения
            display_text = (full_text[:500] + "...") if full_text and len(full_text) > 500 else (
                        full_text or "Текст не распознан")

            error_text = f"""
⚠️ <b>СУММА НЕ РАСПОЗНАНА</b>

🔍 <b>Распознанный текст:</b>
<pre>{display_text}</pre>

💡 <b>Возможные причины:</b>
• Нечеткое изображение
• Сумма написана нестандартно
• Помехи на фото

<b>Рекомендации:</b>
• Сделайте более четкое фото
• Убедитесь, что сумма хорошо видна
• Попробуйте другой ракурс
"""

            await processing_msg.edit_text(
                error_text,
                parse_mode="HTML",
                reply_markup=create_main_menu()
            )

            logger.warning(f"⚠️ Чек не распознан (файл: {file_id})")

    except Exception as e:
        # Ошибка при обработке
        error_msg = f"❌ Ошибка обработки: {str(e)}"
        logger.error(f"❌ Ошибка обработки чека: {e}")

        try:
            await processing_msg.edit_text(
                f"""
❌ <b>ОШИБКА ОБРАБОТКИ</b>

🔧 Детали: <code>{str(e)}</code>

Попробуйте еще раз или обратитесь к администратору.
""",
                parse_mode="HTML",
                reply_markup=create_main_menu()
            )
        except:
            # Если не удается отредактировать, отправляем новое сообщение
            await message.answer(
                f"❌ <b>Критическая ошибка обработки</b>\n\n{error_msg}",
                parse_mode="HTML",
                reply_markup=create_main_menu()
            )


async def handle_document_private(message: Message, bot: Bot):
    """Обработка документов (расширенная проверка)"""
    if not is_admin(message.from_user.id):
        return

    document = message.document

    if not document:
        return

    # Проверяем MIME тип
    if document.mime_type and document.mime_type.startswith('image/'):
        # Это изображение в виде документа
        await handle_check_private(message, bot)
        return

    # Проверяем расширение файла
    if document.file_name:
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff'}
        file_extension = document.file_name.lower().split('.')[-1]

        if f'.{file_extension}' in image_extensions:
            await handle_check_private(message, bot)
            return

    # Не изображение
    await message.answer(
        "📄 <b>Обнаружен документ</b>\n\n"
        f"📁 Файл: <code>{document.file_name or 'без имени'}</code>\n"
        f"📊 Размер: <code>{document.file_size or 0} байт</code>\n"
        f"🏷️ Тип: <code>{document.mime_type or 'неизвестно'}</code>\n\n"
        "💡 Для обработки чеков отправьте изображение.",
        parse_mode="HTML"
    )


async def handle_voice_private(message: Message):
    """Обработка голосовых сообщений (пока не поддерживается)"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "🎤 <b>Голосовое сообщение получено</b>\n\n"
        "В текущей версии голосовые сообщения не обрабатываются.\n\n"
        "📝 Отправьте текст или 📷 фото чека для распознавания.",
        parse_mode="HTML"
    )


async def handle_video_private(message: Message):
    """Обработка видео (пока не поддерживается)"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "🎬 <b>Видео получено</b>\n\n"
        "Обработка видео пока не поддерживается.\n\n"
        "📷 Сделайте скриншот чека и отправьте как изображение.",
        parse_mode="HTML"
    )


async def handle_sticker_private(message: Message):
    """Обработка стикеров"""
    if not is_admin(message.from_user.id):
        return

    sticker_emojis = {
        "👍": "Отлично!",
        "👎": "Понятно...",
        "❤️": "Спасибо!",
        "🔥": "Круто!",
        "💯": "Идеально!",
        "😊": "Хорошо!",
        "🤔": "Понял...",
        "😢": "Сочувствую...",
        "😂": "Смешно!",
        "🎉": "Поздравляю!",
    }

    emoji = message.sticker.emoji if message.sticker and message.sticker.emoji else "🤖"
    response = sticker_emojis.get(emoji, "Интересный стикер!")

    await message.answer(f"{emoji} {response}")


def setup_media_handlers(dp):
    """Регистрирует все обработчики медиафайлов"""

    # Изображения (фото)
    dp.message.register(
        lambda m, bot: handle_check_private(m, bot),
        lambda m: m.chat.type == "private" and is_admin(m.from_user.id) and m.photo
    )

    # Документы
    dp.message.register(
        lambda m, bot: handle_document_private(m, bot),
        lambda m: m.chat.type == "private" and is_admin(m.from_user.id) and m.document
    )

    # Голосовые сообщения
    dp.message.register(
        handle_voice_private,
        lambda m: m.chat.type == "private" and is_admin(m.from_user.id) and m.voice
    )

    # Видео
    dp.message.register(
        handle_video_private,
        lambda m: m.chat.type == "private" and is_admin(m.from_user.id) and m.video
    )

    # Стикеры
    dp.message.register(
        handle_sticker_private,
        lambda m: m.chat.type == "private" and is_admin(m.from_user.id) and m.sticker
    )