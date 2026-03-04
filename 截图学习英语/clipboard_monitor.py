import hashlib
import io
import time
import threading
from PIL import ImageGrab, Image
from config import logger
import ocr_engine
import text_processor
import translator
import numpy as np


class ClipboardMonitor:
    def __init__(self, sync_backend, config, on_result=None):
        self.sync_backend = sync_backend
        self.poll_interval = config.get("monitor", {}).get("poll_interval", 3)
        self.min_word_length = config.get("monitor", {}).get("min_word_length", 3)
        self.max_phrase_words = config.get("monitor", {}).get("max_phrase_words", 8)
        self.source_lang = config.get("language", {}).get("source", "en")
        self.target_lang = config.get("language", {}).get("target", "zh-CN")
        self.on_result = on_result
        self._last_hash = None
        self._running = False
        self._paused = False
        self._thread = None

    def start(self):
        self._prime_clipboard_baseline()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("剪切板监控已启动")

    def _prime_clipboard_baseline(self):
        img = self._get_clipboard_image()
        if img is None:
            self._last_hash = None
            logger.info("启动时剪切板无图片，等待新截图进入剪切板")
            return
        self._last_hash = self._image_hash(img)
        logger.info("已忽略启动前剪切板中的旧截图，仅处理后续新截图")

    def stop(self):
        self._running = False
        logger.info("剪切板监控已停止")

    def pause(self):
        self._paused = True
        logger.info("剪切板监控已暂停")

    def resume(self):
        self._paused = False
        logger.info("剪切板监控已恢复")

    @property
    def is_paused(self):
        return self._paused

    def _loop(self):
        while self._running:
            try:
                if not self._paused:
                    self._check_clipboard()
            except Exception as e:
                logger.error(f"剪切板检查异常: {e}")
            time.sleep(self.poll_interval)

    def _check_clipboard(self):
        img = self._get_clipboard_image()
        if img is None:
            return

        img_hash = self._image_hash(img)
        if img_hash == self._last_hash:
            return

        self._last_hash = img_hash
        logger.info(f"检测到新截图 ({img.size[0]}x{img.size[1]})")

        threading.Thread(target=self._process_image, args=(img,), daemon=True).start()

    def _process_image(self, img):
        try:
            img_array = np.array(img)
            ocr_lines = ocr_engine.recognize(img_array)
            if not ocr_lines:
                logger.info("截图中未识别到文字")
                return

            logger.info(f"OCR 识别到 {len(ocr_lines)} 行文字")

            items = text_processor.extract_items(
                ocr_lines,
                min_word_length=self.min_word_length,
                max_phrase_words=self.max_phrase_words,
            )
            if not items:
                logger.info("未提取到有效英文内容")
                return

            logger.info(f"提取到 {len(items)} 个英文词条，开始翻译...")
            items = translator.translate_batch(
                items,
                source_lang=self.source_lang,
                target_lang=self.target_lang,
            )

            logger.info("翻译完成，开始同步...")
            created, updated = self.sync_backend.sync_items(items)

            msg = f"识别 {len(items)} 个词条 | 新增 {created} | 更新 {updated}"
            logger.info(f"✅ {msg}")

            if self.on_result:
                self.on_result(msg)

        except Exception as e:
            logger.error(f"处理截图出错: {e}")

    def _get_clipboard_image(self):
        try:
            content = ImageGrab.grabclipboard()
            if isinstance(content, Image.Image):
                return content.convert("RGB")
            if isinstance(content, list):
                for path in content:
                    if isinstance(path, str) and path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")):
                        return Image.open(path).convert("RGB")
        except Exception:
            pass
        return None

    def _image_hash(self, img):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return hashlib.md5(buf.getvalue()).hexdigest()
