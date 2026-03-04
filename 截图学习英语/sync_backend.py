from config import logger
from feishu_sync import FeishuSync
from local_sync import LocalSync


def build_sync_backend(config):
    sync_config = config.get("sync", {})
    provider = sync_config.get("provider", "feishu").strip().lower()

    if provider == "local":
        output_path = sync_config.get("local_output", "data/learning_items.jsonl")
        logger.info(f"同步后端: local ({output_path})")
        return LocalSync(output_path=output_path)

    if provider == "feishu":
        fs_config = config.get("feishu", {})
        required_fields = ["app_id", "app_secret", "app_token", "table_id"]
        missing = [field for field in required_fields if not fs_config.get(field)]
        if missing:
            raise ValueError(f"飞书配置缺失: {', '.join(missing)}")

        logger.info("同步后端: feishu")
        return FeishuSync(
            app_id=fs_config["app_id"],
            app_secret=fs_config["app_secret"],
            app_token=fs_config["app_token"],
            table_id=fs_config["table_id"],
        )

    raise ValueError(f"不支持的 sync.provider: {provider}，可选 feishu/local")
