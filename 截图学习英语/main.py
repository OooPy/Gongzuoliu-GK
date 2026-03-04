import sys
import pystray
from PIL import Image, ImageDraw, ImageFont
from config import load_config, logger
from clipboard_monitor import ClipboardMonitor
from sync_backend import build_sync_backend


def create_icon_image():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([2, 2, 62, 62], radius=12, fill=(59, 130, 246))
    try:
        font = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), "EN", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((64 - tw) / 2, (64 - th) / 2 - 2), "EN", fill="white", font=font)
    return img


def main():
    logger.info("=" * 50)
    logger.info("截图学英语 - 启动中...")
    logger.info("=" * 50)

    try:
        config = load_config()
    except FileNotFoundError:
        input("按回车键退出...")
        sys.exit(1)

    language_config = config.get("language", {})
    source_lang = language_config.get("source", "en")
    target_lang = language_config.get("target", "zh-CN")
    logger.info(f"翻译语言: {source_lang} -> {target_lang}")

    try:
        sync_backend = build_sync_backend(config)
    except Exception as e:
        logger.error(f"初始化同步后端失败: {e}")
        input("按回车键退出...")
        sys.exit(1)

    logger.info("正在加载已有记录...")
    count = sync_backend.load_all_records()
    logger.info(f"已有 {count} 条记录在缓存中")

    icon_ref = [None]

    def on_result(msg):
        if icon_ref[0]:
            try:
                icon_ref[0].notify(msg, "截图学英语")
            except Exception:
                pass

    monitor = ClipboardMonitor(sync_backend, config, on_result=on_result)
    monitor.start()

    def toggle_pause(icon, item):
        if monitor.is_paused:
            monitor.resume()
        else:
            monitor.pause()

    def refresh_cache(icon, item):
        logger.info("正在刷新缓存...")
        sync_backend.load_all_records()
        try:
            icon.notify("缓存已刷新", "截图学英语")
        except Exception:
            pass

    def quit_app(icon, item):
        monitor.stop()
        icon.stop()
        logger.info("应用已退出")

    def get_pause_text(item):
        return "▶ 继续监控" if monitor.is_paused else "⏸ 暂停监控"

    menu = pystray.Menu(
        pystray.MenuItem(get_pause_text, toggle_pause),
        pystray.MenuItem("🔄 刷新缓存", refresh_cache),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("❌ 退出", quit_app),
    )

    icon = pystray.Icon("clip_en_learner", create_icon_image(), "截图学英语", menu)
    icon_ref[0] = icon

    logger.info("✅ 启动成功！在系统托盘可以看到蓝色 EN 图标")
    logger.info("现在截图即可自动识别英文并同步")
    logger.info("-" * 50)

    icon.run()


if __name__ == "__main__":
    main()
