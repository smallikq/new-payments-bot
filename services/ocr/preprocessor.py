import numpy as np
from PIL import Image, ImageOps, ImageFilter

def _otsu_threshold(gray_array: np.ndarray) -> int:
    """Вычисляет оптимальный порог бинаризации по методу Оцу"""
    hist, _ = np.histogram(gray_array, bins=256, range=(0, 256))
    total = gray_array.size
    sum_total = np.dot(np.arange(256), hist)
    sumB = wB = 0
    varMax, thresh = 0.0, 127

    for t in range(256):
        wB += hist[t]
        if wB == 0:
            continue
        wF = total - wB
        if wF == 0:
            break
        sumB += t * hist[t]
        mB = sumB / wB
        mF = (sum_total - sumB) / wF
        varBetween = wB * wF * (mB - mF) ** 2
        if varBetween > varMax:
            varMax = varBetween
            thresh = t
    return thresh


def preprocess_for_ocr(img: Image.Image) -> Image.Image:
    """Предобработка изображения для OCR"""
    W, H = img.size
    long_side = max(W, H)
    scale = max(1, 1600 // max(1, long_side))

    if scale > 1:
        img = img.resize((W * scale, H * scale), Image.LANCZOS)

    gray = img.convert("L")
    gray = ImageOps.equalize(gray)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

    gamma = 0.85
    lut = [int((i / 255.0) ** gamma * 255) for i in range(256)]
    gray = gray.point(lut)

    np_gray = np.array(gray)
    threshold = _otsu_threshold(np_gray)
    binary = (np_gray > threshold).astype(np.uint8) * 255
    binary_img = Image.fromarray(binary)

    inverted = ImageOps.invert(binary_img)
    thick = inverted.filter(ImageFilter.MaxFilter(3))
    result = ImageOps.invert(thick)

    return result


def credit_agricole_crops(img: Image.Image) -> list[Image.Image]:
    """Создает обрезки изображения для банка Crédit Agricole"""
    W, H = img.size

    def relative_crop(x1, y1, x2, y2):
        return img.crop((int(W*x1), int(H*y1), int(W*x2), int(H*y2)))

    table_area = relative_crop(0.55, 0.28, 0.98, 0.72)
    amount_row1 = relative_crop(0.60, 0.33, 0.96, 0.41)
    amount_row2 = relative_crop(0.60, 0.35, 0.96, 0.43)

    return [amount_row1, amount_row2, table_area]
