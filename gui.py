#!/usr/bin/env python3
"""
Antigravity 2.0 • Grok Bot Studio - Desktop GUI Server & Launcher
Provides modern, native-feeling desktop window powered by Antigravity core engine.
"""

import os
import sys
import json
import time
import socket
import shutil
import subprocess
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

WEB_DIR = os.path.join(BASE_DIR, "web")

from bots import load_bots, get_bot, create_bot, update_bot, PRESET_BOTS
from engine import ChatEngine, check_google_auth_and_subscription, find_agy_binary
from exporter import export_to_antigravity_rule

_ACTIVE_ENGINES: Dict[str, ChatEngine] = {}

def get_chat_engine(bot_id: str) -> ChatEngine:
    global _ACTIVE_ENGINES
    if bot_id not in _ACTIVE_ENGINES:
        bot = get_bot(bot_id) or PRESET_BOTS[0]
        _ACTIVE_ENGINES[bot_id] = ChatEngine(bot)
    return _ACTIVE_ENGINES[bot_id]


class AntigravityGUIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def log_message(self, format, *args):
        # Keep terminal quiet
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            query = parse_qs(parsed.query)
            force_refresh = "refresh" in query
            status = check_google_auth_and_subscription(force_refresh=force_refresh)
            self._send_json(status)
            return
        elif path == "/api/bots":
            bots = load_bots()
            self._send_json(bots)
            return
        elif path == "/api/export-chat":
            query = parse_qs(parsed.query)
            bot_id = query.get("bot_id", ["grok_fun"])[0]
            engine = get_chat_engine(bot_id)
            filepath = engine.save_session_markdown()
            self._send_json({"ok": True, "path": filepath})
            return
        elif path == "/" or not os.path.exists(os.path.join(WEB_DIR, path.lstrip("/"))):
            self.path = "/index.html"
            return super().do_GET()

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        if path == "/api/chat":
            bot_id = data.get("bot_id", "grok_fun")
            user_msg = data.get("message", "").strip()
            model = data.get("model", "gemini-3.8-flash-high")
            effort = data.get("effort", "high")

            if not user_msg:
                self._send_json({"error": "empty_message", "message": "Пустое сообщение"}, status=400)
                return

            engine = get_chat_engine(bot_id)
            reply, thoughts = engine.generate_response(user_msg, model_override=model, effort_override=effort)

            self._send_json({
                "reply": reply,
                "thoughts": thoughts,
                "bot_id": bot_id,
                "model": model,
                "effort": effort
            })
            return

        elif path == "/api/bots":
            name = data.get("name", "Custom Bot")
            emoji = data.get("emoji", "🤖")
            tagline = data.get("tagline", "")
            archetype = data.get("archetype", "grok_rebel")
            humor = data.get("humor_level", 75)
            prompt = data.get("system_prompt", "Ты полезный ассистент.")

            bot_id = f"custom_{int(time.time())}"
            new_bot = {
                "id": bot_id,
                "name": name,
                "emoji": emoji,
                "tagline": tagline,
                "archetype": archetype,
                "humor_level": humor,
                "system_prompt": prompt,
                "model": "gemini-3.8-flash-high"
            }
            create_bot(new_bot)
            self._send_json(new_bot)
            return

        elif path == "/api/export-rules":
            bot_id = data.get("bot_id", "grok_fun")
            bot = get_bot(bot_id) or PRESET_BOTS[0]
            rule_path = export_to_antigravity_rule(bot)
            self._send_json({"ok": True, "path": rule_path})
            return

        self._send_json({"error": "not_found"}, status=404)

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def find_free_port(preferred: int = 8990) -> int:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", preferred))
        s.close()
        return preferred
    except OSError:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        return port


def open_desktop_window(url: str) -> None:
    """Launch clean, dedicated application window without browser toolbar."""
    temp_profile = "/tmp/antigravity_hub_profile"
    
    # Priority browser list for application window mode
    candidates = [
        "chromium",
        "google-chrome",
        "google-chrome-stable",
        "brave-browser",
        "brave",
        "microsoft-edge",
        "msedge"
    ]
    
    for browser in candidates:
        browser_bin = shutil.which(browser)
        if browser_bin:
            try:
                cmd = [
                    browser_bin,
                    f"--app={url}",
                    "--class=AntigravityBotHub",
                    "--name=Antigravity 2.0",
                    f"--user-data-dir={temp_profile}",
                    "--no-first-run",
                    "--no-default-browser-check"
                ]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except Exception:
                pass

    # Windows fallback
    if sys.platform == "win32":
        try:
            os.system(f'start msedge --app="{url}"')
            return
        except Exception:
            pass

    # Standard browser fallback
    webbrowser.open(url)


def start_gui(port: int = 0, open_window: bool = True) -> None:
    if port == 0:
        port = find_free_port(8990)

    server = HTTPServer(("127.0.0.1", port), AntigravityGUIHandler)
    url = f"http://127.0.0.1:{port}"

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    print(f"🚀 Antigravity 2.0 Desktop Studio запущен на: {url}")

    if open_window:
        open_desktop_window(url)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nОстановка сервера...")
        server.shutdown()


if __name__ == "__main__":
    start_gui()
