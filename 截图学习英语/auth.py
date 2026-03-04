import json
import os
import time
import webbrowser
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from config import logger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, "tokens.json")

AUTHORIZE_URL = "https://open.feishu.cn/open-apis/authen/v1/authorize"
ACCESS_TOKEN_URL = "https://open.feishu.cn/open-apis/authen/v1/oidc/access_token"
REFRESH_TOKEN_URL = "https://open.feishu.cn/open-apis/authen/v1/oidc/refresh_access_token"
APP_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"

CALLBACK_PORT = 9876
REDIRECT_URI = f"http://localhost:{CALLBACK_PORT}/callback"


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if "code" in params:
            self.server.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = "<html><body style='text-align:center;padding-top:80px;font-family:sans-serif;'>"
            html += "<h1>✅ 授权成功</h1><p>可以关闭此页面了</p></body></html>"
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        pass


class FeishuAuth:
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self._tokens = self._load_tokens()

    def _load_tokens(self):
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_tokens(self):
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(self._tokens, f, indent=2, ensure_ascii=False)

    def _get_app_access_token(self):
        resp = requests.post(APP_TOKEN_URL, json={
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }, timeout=10)
        data = resp.json()
        return data.get("app_access_token")

    def get_access_token(self):
        if self._tokens.get("access_token"):
            if time.time() < self._tokens.get("expire_time", 0):
                return self._tokens["access_token"]
            if self._tokens.get("refresh_token"):
                if time.time() < self._tokens.get("refresh_expire_time", 0):
                    if self._refresh():
                        return self._tokens["access_token"]

        self._authorize()
        return self._tokens.get("access_token")

    def _authorize(self):
        logger.info("需要飞书授权，正在打开浏览器...")

        server = HTTPServer(("localhost", CALLBACK_PORT), _CallbackHandler)
        server.auth_code = None
        server.timeout = 120

        auth_url = (
            f"{AUTHORIZE_URL}"
            f"?app_id={self.app_id}"
            f"&redirect_uri={REDIRECT_URI}"
            f"&response_type=code"
            f"&scope=bitable:app"
        )

        webbrowser.open(auth_url)
        logger.info(f"请在浏览器中完成授权（120秒超时）")

        while server.auth_code is None:
            server.handle_request()

        code = server.auth_code
        server.server_close()
        logger.info("收到授权码，正在获取 token...")

        app_token = self._get_app_access_token()
        resp = requests.post(
            ACCESS_TOKEN_URL,
            headers={"Authorization": f"Bearer {app_token}", "Content-Type": "application/json"},
            json={"grant_type": "authorization_code", "code": code},
            timeout=10,
        )
        result = resp.json()
        data = result.get("data", {})

        if not data.get("access_token"):
            logger.error(f"获取 user_access_token 失败: {result}")
            return

        self._tokens = {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", ""),
            "expire_time": time.time() + data.get("expires_in", 7200) - 300,
            "refresh_expire_time": time.time() + data.get("refresh_expires_in", 2592000) - 300,
        }
        self._save_tokens()
        logger.info("✅ 用户授权成功，token 已保存")

    def _refresh(self):
        try:
            app_token = self._get_app_access_token()
            resp = requests.post(
                REFRESH_TOKEN_URL,
                headers={"Authorization": f"Bearer {app_token}", "Content-Type": "application/json"},
                json={
                    "grant_type": "refresh_token",
                    "refresh_token": self._tokens["refresh_token"],
                },
                timeout=10,
            )
            data = resp.json().get("data", {})
            if data.get("access_token"):
                self._tokens = {
                    "access_token": data["access_token"],
                    "refresh_token": data.get("refresh_token", ""),
                    "expire_time": time.time() + data.get("expires_in", 7200) - 300,
                    "refresh_expire_time": time.time() + data.get("refresh_expires_in", 2592000) - 300,
                }
                self._save_tokens()
                logger.info("✅ token 自动刷新成功")
                return True
        except Exception as e:
            logger.warning(f"token 刷新失败: {e}")
        return False
