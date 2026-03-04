from rapidocr_onnxruntime import RapidOCR
from config import logger

_ocr_instance = None


def get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        logger.info("正在加载 OCR 模型（首次启动较慢）...")
        _ocr_instance = RapidOCR()
        logger.info("OCR 模型加载完成")
    return _ocr_instance


def recognize(image):
    ocr = get_ocr()
    result, _ = ocr(image)
    if not result:
        return []
    texts = []
    for line in result:
        text = line[1] if isinstance(line, (list, tuple)) and len(line) >= 2 else None
        if text and isinstance(text, str):
            texts.append(text.strip())
    return texts
