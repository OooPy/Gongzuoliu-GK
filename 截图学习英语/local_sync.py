import json
import os
from config import BASE_DIR, logger


class LocalSync:
    def __init__(self, output_path="data/learning_items.jsonl"):
        self.output_path = os.path.join(BASE_DIR, output_path)
        self.cache = {}

    def load_all_records(self):
        self.cache = {}
        if not os.path.exists(self.output_path):
            return 0

        total = 0
        try:
            with open(self.output_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    english = item.get("english", "").strip().lower()
                    if not english:
                        continue
                    count = int(item.get("count", 1) or 1)
                    self.cache[english] = {
                        "english": item.get("english", ""),
                        "chinese": item.get("chinese", ""),
                        "category": item.get("category", "日常"),
                        "length_type": item.get("length_type", "单词"),
                        "count": count,
                    }
                    total += 1
        except Exception as e:
            logger.warning(f"加载本地记录失败: {e}")
            return 0

        return total

    def sync_items(self, items):
        created = 0
        updated = 0

        for item in items:
            key = item["english"].strip().lower()
            if not key:
                continue

            if key in self.cache:
                self.cache[key]["count"] += 1
                if item.get("chinese"):
                    self.cache[key]["chinese"] = item.get("chinese", "")
                updated += 1
            else:
                self.cache[key] = {
                    "english": item["english"],
                    "chinese": item.get("chinese", ""),
                    "category": item.get("category", "日常"),
                    "length_type": item.get("length_type", "单词"),
                    "count": 1,
                }
                created += 1

        self._persist()
        return created, updated

    def _persist(self):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            for _, item in sorted(self.cache.items(), key=lambda x: x[0]):
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
