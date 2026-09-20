#!/usr/bin/env python3
"""
Antigravity 2.0 - Desktop GUI Server & Launcher
Provides modern, native-feeling desktop interface for Projects and Individual Chats.
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
from typing import Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

WEB_DIR = os.path.join(BASE_DIR, "web")

import store
from engine import ChatEngine, check_google_auth_and_subscription, find_agy_binary


class AntigravityGUIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def log_message(self, format, *args):
        # Keep terminal quiet
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/status":
            force_refresh = "refresh" in query
            status = check_google_auth_and_subscription(force_refresh=force_refresh)
            self._send_json(status)
            return

        elif path == "/api/projects":
            projects = store.get_projects()
            active_id = store.load_store().get("active_project_id")
            self._send_json({"projects": projects, "active_id": active_id})
            return

        elif path == "/api/chats":
            pid = query.get("project_id", [None])[0]
            chats = store.get_chats(project_id=pid)
            active_id = store.load_store().get("active_chat_id")
            self._send_json({"chats": chats, "active_id": active_id})
            return

        elif path == "/api/chats/messages":
            chat_id = query.get("id", [None])[0]
            if not chat_id:
                chat_id = store.load_store().get("active_chat_id")
            chat = store.get_chat(chat_id)
            if chat:
                self._send_json({
                    "id": chat["id"],
                    "name": chat["name"],
                    "icon": chat["icon"],
                    "model": chat.get("model", "gemini-3.8-flash-high"),
                    "effort": chat.get("effort", "high"),
                    "messages": chat.get("messages", [])
                })
            else:
                self._send_json({"error": "not_found"}, status=404)
            return

        elif path == "/api/chats/export":
            chat_id = query.get("id", [None])[0]
            chat = store.get_chat(chat_id)
            if chat:
                engine = ChatEngine(chat_id=chat["id"])
                engine.set_history(chat.get("messages", []))
                filepath = engine.save_session_markdown(title=chat.get("name", "Диалог"))
                self._send_json({"ok": True, "path": filepath})
            else:
                self._send_json({"error": "not_found"}, status=404)
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

        # --- Projects ---
        if path == "/api/projects":
            name = data.get("name", "Новый проект")
            icon = data.get("icon", "📁")
            new_proj = store.create_project(name, icon)
            self._send_json(new_proj)
            return

        elif path == "/api/projects/select":
            pid = data.get("id")
            if pid:
                st = store.load_store()
                st["active_project_id"] = pid
                # Set active chat to first chat in this project
                proj_chats = [c for c in st["chats"] if c.get("project_id") == pid]
                if proj_chats:
                    st["active_chat_id"] = proj_chats[0]["id"]
                store.save_store(st)
                self._send_json({"ok": True, "active_project_id": pid})
            else:
                self._send_json({"error": "missing_id"}, status=400)
            return

        elif path == "/api/projects/update":
            pid = data.get("id")
            name = data.get("name")
            icon = data.get("icon")
            updated = store.rename_project(pid, name, icon)
            if updated:
                self._send_json(updated)
            else:
                self._send_json({"error": "not_found"}, status=404)
            return

        elif path == "/api/projects/delete":
            pid = data.get("id")
            ok = store.delete_project(pid)
            self._send_json({"ok": ok})
            return

        # --- Chats ---
        elif path == "/api/chats":
            pid = data.get("project_id") or store.load_store().get("active_project_id")
            name = data.get("name", "Новый диалог")
            icon = data.get("icon", "💬")
            model = data.get("model", "gemini-3.8-flash-high")
            new_chat = store.create_chat(pid, name, icon, model)
            self._send_json(new_chat)
            return

        elif path == "/api/chats/select":
            chat_id = data.get("id")
            if chat_id:
                st = store.load_store()
                st["active_chat_id"] = chat_id
                store.save_store(st)
                self._send_json({"ok": True, "active_chat_id": chat_id})
            else:
                self._send_json({"error": "missing_id"}, status=400)
            return

        elif path == "/api/chats/update":
            chat_id = data.get("id")
            name = data.get("name")
            icon = data.get("icon")
            model = data.get("model")
            effort = data.get("effort")
            updated = store.update_chat(chat_id, name, icon, model, effort)
            if updated:
                self._send_json(updated)
            else:
                self._send_json({"error": "not_found"}, status=404)
            return

        elif path == "/api/chats/delete":
            chat_id = data.get("id")
            ok = store.delete_chat(chat_id)
            self._send_json({"ok": ok})
            return

        elif path == "/api/chats/clear":
            chat_id = data.get("id")
            if chat_id:
                store.clear_chat_history(chat_id)
                self._send_json({"ok": True})
            else:
                self._send_json({"error": "missing_id"}, status=400)
            return

        elif path == "/api/chat":
            chat_id = data.get("chat_id")
            user_msg = data.get("message", "").strip()
            model = data.get("model", "gemini-3.8-flash-high")
            effort = data.get("effort", "high")

            if not user_msg:
                self._send_json({"error": "empty_message", "message": "Пустое сообщение"}, status=400)
                return

            chat = store.get_chat(chat_id)
            if not chat:
                chat = store.get_chats()[0]
                chat_id = chat["id"]

            engine = ChatEngine(chat_id=chat_id)
            engine.set_history(list(chat.get("messages", [])))

            # Append user message to store and engine
            engine.add_message("user", user_msg)

            # Generate model response
            reply, thoughts = engine.generate_response(user_msg, model_override=model, effort_override=effort)

            self._send_json({
                "reply": reply,
                "thoughts": thoughts,
                "chat_id": chat_id,
                "model": model,
                "effort": effort
            })
            return

        elif path == "/api/open-external":
            ext_url = data.get("url", "").strip()
            if ext_url and (ext_url.startswith("http://") or ext_url.startswith("https://")):
                open_in_default_browser(ext_url)
                self._send_json({"ok": True, "opened": ext_url})
            else:
                self._send_json({"error": "invalid_url"}, status=400)
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


def open_in_default_browser(url: str) -> None:
    """Open URL strictly in the user's default system browser. Never force Edge or open borderless window."""
    try:
        if sys.platform == "win32":
            # On Windows, os.startfile uses Win32 ShellExecute directly (no cmd.exe escaping issues)
            if hasattr(os, "startfile"):
                os.startfile(url)
                return
            os.system(f'start "" "{url}"')
            return
        elif sys.platform == "darwin":
            subprocess.Popen(["open", url])
            return
        else:
            if shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
    except Exception as e:
        print(f"Error opening system browser: {e}")

    try:
        webbrowser.open(url)
    except Exception:
        pass


def open_desktop_window(url: str, on_close: Optional[Callable[[], None]] = None) -> bool:
    """Launch clean, dedicated native application window (PyQt6 / pywebview with clean fallback)."""
    try:
        from app_window import run_native_desktop_app
        if run_native_desktop_app(url, on_close=on_close):
            return True
    except Exception as e:
        print(f"[Desktop] Native window error: {e}")

    # Fallback: open in default system browser
    open_in_default_browser(url)
    return False


def start_gui(port: int = 0, open_window: bool = True) -> None:
    if port == 0:
        port = find_free_port(8990)

    server = HTTPServer(("127.0.0.1", port), AntigravityGUIHandler)
    url = f"http://127.0.0.1:{port}"

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    print(f"🚀 Antigravity 2.0 Desktop Studio запущен на: {url}")

    def stop_server():
        print("\nОстановка локального сервера...")
        try:
            server.shutdown()
        except Exception:
            pass

    if open_window:
        is_native_event_loop = open_desktop_window(url, on_close=stop_server)
        if not is_native_event_loop:
            # If opened via external browser, keep main thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                stop_server()
    else:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop_server()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Antigravity 2.0 Desktop Studio")
    parser.add_argument("--port", type=int, default=0, help="Port to listen on")
    parser.add_argument("--no-window", action="store_true", help="Do not open desktop window")
    args = parser.parse_args()
    start_gui(port=args.port, open_window=not args.no_window)
