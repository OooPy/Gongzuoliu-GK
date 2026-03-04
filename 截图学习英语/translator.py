from deep_translator import GoogleTranslator
from config import logger

_translators = {}


def get_translator(source_lang="en", target_lang="zh-CN"):
    key = f"{source_lang}->{target_lang}"
    if key not in _translators:
        _translators[key] = GoogleTranslator(source=source_lang, target=target_lang)
    return _translators[key]


def translate_batch(items, source_lang="en", target_lang="zh-CN"):
    if not items:
        return items

    translator = get_translator(source_lang=source_lang, target_lang=target_lang)
    texts = [item["english"] for item in items]

    batch_size = 20
    translations = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            result = translator.translate_batch(batch)
            translations.extend(result)
        except Exception as e:
            logger.warning(f"批量翻译失败，切换逐条翻译: {e}")
            for text in batch:
                try:
                    tr = translator.translate(text)
                    translations.append(tr)
                except Exception as e2:
                    logger.warning(f"翻译失败 [{text}]: {e2}")
                    translations.append("")

    for i, item in enumerate(items):
        item["chinese"] = translations[i] if i < len(translations) else ""

    return items
