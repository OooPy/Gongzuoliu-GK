import requests
from config import logger
from auth import FeishuAuth


class FeishuSync:
    BASE_URL = "https://open.feishu.cn/open-apis"

    def __init__(self, app_id, app_secret, app_token, table_id):
        self.app_token = app_token
        self.table_id = table_id
        self.auth = FeishuAuth(app_id, app_secret)
        self.cache = {}

    def _headers(self):
        token = self.auth.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _extract_text(self, field_value):
        if isinstance(field_value, str):
            return field_value.strip()
        if isinstance(field_value, list):
            parts = []
            for seg in field_value:
                if isinstance(seg, dict):
                    parts.append(seg.get("text", ""))
                elif isinstance(seg, str):
                    parts.append(seg)
            return "".join(parts).strip()
        return str(field_value).strip() if field_value else ""

    def load_all_records(self):
        self.cache = {}
        page_token = None
        total = 0

        while True:
            url = f"{self.BASE_URL}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/search"
            params = {"page_size": 500}
            if page_token:
                params["page_token"] = page_token

            try:
                resp = requests.post(url, headers=self._headers(), json={}, params=params, timeout=15)
                data = resp.json().get("data", {})
            except Exception as e:
                logger.error(f"加载飞书记录失败: {e}")
                break

            for item in data.get("items", []):
                fields = item.get("fields", {})
                english = self._extract_text(fields.get("英语", ""))
                english_key = english.lower()
                if english_key:
                    count = fields.get("出现次数", 1)
                    if isinstance(count, str):
                        count = int(float(count)) if count else 1
                    self.cache[english_key] = {
                        "record_id": item.get("record_id"),
                        "count": count,
                    }
                    total += 1

            if not data.get("has_more", False):
                break
            page_token = data.get("page_token")

        logger.info(f"已加载 {total} 条飞书记录到本地缓存")
        return total

    def sync_items(self, items):
        created = 0
        updated = 0

        for item in items:
            english_key = item["english"].lower().strip()

            if english_key in self.cache:
                cached = self.cache[english_key]
                new_count = cached["count"] + 1
                if self._update_record(cached["record_id"], new_count):
                    cached["count"] = new_count
                    updated += 1
            else:
                record_id = self._create_record(item)
                if record_id:
                    self.cache[english_key] = {
                        "record_id": record_id,
                        "count": 1,
                    }
                    created += 1

        return created, updated

    def _create_record(self, item):
        url = f"{self.BASE_URL}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        fields = {
            "英语": item["english"],
            "中文": item.get("chinese", ""),
            "类别": item["category"],
            "长短": item["length_type"],
            "出现次数": 1,
        }
        try:
            resp = requests.post(url, headers=self._headers(), json={"fields": fields}, timeout=10)
            data = resp.json()
            if data.get("code") != 0:
                logger.warning(f"创建记录失败 [{item['english']}]: {data.get('msg')}")
                return None
            record_id = data.get("data", {}).get("record", {}).get("record_id")
            logger.info(f"✅ 新增: {item['english']} → {item.get('chinese', '')}")
            return record_id
        except Exception as e:
            logger.error(f"创建记录异常 [{item['english']}]: {e}")
            return None

    def _update_record(self, record_id, new_count):
        url = f"{self.BASE_URL}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/{record_id}"
        try:
            resp = requests.put(url, headers=self._headers(), json={
                "fields": {"出现次数": new_count}
            }, timeout=10)
            data = resp.json()
            if data.get("code") != 0:
                logger.warning(f"更新记录失败 [record_id={record_id}]: {data.get('msg')}")
                return False
            logger.info(f"🔄 更新次数: record_id={record_id} → {new_count}")
            return True
        except Exception as e:
            logger.error(f"更新记录异常: {e}")
            return False
