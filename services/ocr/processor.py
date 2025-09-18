import io
import numpy as np
from PIL import Image
from telethon import TelegramClient
from rapidocr_onnxruntime import RapidOCR
from aiogram import Bot
from services.ocr.preprocessor import preprocess_for_ocr, credit_agricole_crops
from services.ocr.extractors import extract_bank_payment
from utils.logger import logger

rapid_ocr = RapidOCR()

def _rapidocr_read(img: Image.Image) -> list[str]:
    """Выполняет OCR с помощью RapidOCR"""
    arr = np.array(img.convert("RGB"))
    if arr.ndim == 3 and arr.shape[2] == 3:
        arr = arr[:, :, ::-1]  # RGB -> BGR

    result, _ = rapid_ocr(arr)
    return [item[1] for item in result] if result else []


async def process_check_image_aiogram(bot: Bot, file_id: str):
    """OCR через aiogram"""
    try:
        file = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file.file_path)
        image = Image.open(io.BytesIO(file_bytes)).convert("RGB")

        images_to_process = [image, preprocess_for_ocr(image)]
        for crop in credit_agricole_crops(image):
            images_to_process.append(crop)
            images_to_process.append(preprocess_for_ocr(crop))

        all_text = []
        for img in images_to_process:
            all_text.extend(_rapidocr_read(img))

        full_text = "\n".join(all_text)
        amount = extract_bank_payment(full_text)
        return amount, full_text
    except Exception as e:
        logger.error(f"OCR aiogram error: {e}")
        return None, f"OCR error: {e}"


async def process_check_image_telethon(client: TelegramClient, message):
    """OCR через telethon"""
    try:
        if not (message.photo or message.document):
            return None, "Нет медиафайла"

        file = await client.download_media(message, file=io.BytesIO())
        image = Image.open(file).convert("RGB")

        images_to_process = [image, preprocess_for_ocr(image)]
        for crop in credit_agricole_crops(image):
            images_to_process.append(crop)
            images_to_process.append(preprocess_for_ocr(crop))

        all_text = []
        for img in images_to_process:
            all_text.extend(_rapidocr_read(img))

        full_text = "\n".join(all_text)
        amount = extract_bank_payment(full_text)
        return amount, full_text
    except Exception as e:
        logger.error(f"OCR telethon error: {e}")
        return None, f"OCR error: {e}"
