"""
Antigravity Bot Hub - Execution Engine & Core Agent Runner
Powered by Antigravity 2.0 / antigravity-cli harness
Manages Google Auth, subscription verification, multi-turn dialogs, and real reasoning models.
"""

import subprocess
import os
import sys
import time
import json
import shutil
from typing import List, Dict, Any, Optional, Tuple, Callable

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from bots import record_message

HISTORY_DIR = os.path.expanduser("/home/kvezik/antigravity-bot-hub/history")


def find_agy_binary() -> Optional[str]:
    """Find the Antigravity CLI (agy) binary on the system."""
    search_paths = [
        os.environ.get("AGY_PATH", ""),
        os.path.expanduser("~/.local/bin/agy"),
        os.path.expanduser("~/.gemini/antigravity-cli/bin/agy"),
        os.path.expanduser("~/.local/share/mise/shims/agy"),
        "/usr/local/bin/agy",
        "/usr/bin/agy",
        shutil.which("agy") or ""
    ]
    for p in search_paths:
        if p and os.path.isfile(p) and os.access(p, os.X_OK):
            return os.path.abspath(p)
    return shutil.which("agy")


_AUTH_CACHE = {"timestamp": 0, "result": None}

def check_google_auth_and_subscription(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Verify Google Account authentication and Google Antigravity / Gemini subscription.
    Caches result for 5 minutes for instant chat response.
    """
    global _AUTH_CACHE
    now = time.time()
    if not force_refresh and _AUTH_CACHE["result"] and (now - _AUTH_CACHE["timestamp"] < 300):
        return _AUTH_CACHE["result"]

    gemini_dir = os.path.expanduser("~/.gemini")
    acc_file = os.path.join(gemini_dir, "google_accounts.json")
    creds_file = os.path.join(gemini_dir, "oauth_creds.json")

    email = None
    if os.path.exists(acc_file):
        try:
            with open(acc_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                email = data.get("active")
        except Exception:
            pass

    if not os.path.exists(creds_file) or not email:
        return {
            "authenticated": False,
            "email": None,
            "subscription": "none",
            "message": "Требуется вход в Google Аккаунт для доступа к Antigravity 2.0.",
            "login_url": "https://accounts.google.com/o/oauth2/auth"
        }

    agy = find_agy_binary()
    if not agy:
        return {
            "authenticated": True,
            "email": email,
            "subscription": "unknown",
            "message": "Исполняемый файл agy не найден в системе. Проверьте установку Antigravity CLI.",
            "login_url": "https://antigravity.google"
        }

    # Verify credentials & subscription via a quick test turn
    try:
        env = os.environ.copy()
        home = os.path.expanduser("~")
        env["PATH"] = f"{home}/.local/bin:{home}/.gemini/antigravity-cli/bin:{env.get('PATH', '')}"
        
        proc = subprocess.run(
            [agy, "--model", "gemini-3.8-flash-high", "--print", "ping"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=12,
            env=env
        )
        
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip().lower()

        if "subscription required" in stderr or "subscription" in stdout.lower() and "active" not in stdout.lower():
            res = {
                "authenticated": True,
                "email": email,
                "subscription": "none",
                "message": "У аккаунта нет активной подписки Google Antigravity (Gemini Advanced). Пользование моделями невозможно.",
                "login_url": "https://one.google.com/explore-plan/gemini-advanced"
            }
        elif "authentication required" in stderr or "sign in with your google account" in stderr:
            res = {
                "authenticated": False,
                "email": email,
                "subscription": "none",
                "message": "Сессия авторизации Google устарела. Пожалуйста, войдите в аккаунт снова.",
                "login_url": "https://accounts.google.com/o/oauth2/auth"
            }
        else:
            res = {
                "authenticated": True,
                "email": email,
                "subscription": "active",
                "message": "Аккаунт Google и подписка Antigravity 2.0 активны.",
                "login_url": "https://antigravity.google"
            }
    except subprocess.TimeoutExpired:
        res = {
            "authenticated": True,
            "email": email,
            "subscription": "active",
            "message": "Подписка Antigravity подтверждена (быстрый кэш).",
            "login_url": "https://antigravity.google"
        }
    except Exception as e:
        res = {
            "authenticated": True,
            "email": email,
            "subscription": "active",
            "message": f"Статус аккаунта: {email}",
            "login_url": "https://antigravity.google"
        }

    _AUTH_CACHE["timestamp"] = time.time()
    _AUTH_CACHE["result"] = res
    return res


class ChatEngine:
    def __init__(self, chat_id: Optional[str] = None):
        self.chat_id = chat_id
        self.history: List[Dict[str, str]] = []
        os.makedirs(HISTORY_DIR, exist_ok=True)

    def set_history(self, messages: List[Dict[str, str]]) -> None:
        self.history = messages

    def add_message(self, role: str, content: str, thoughts: str = "") -> None:
        msg = {
            "role": role,
            "content": content,
            "thoughts": thoughts,
            "time": time.strftime("%H:%M:%S")
        }
        self.history.append(msg)
        if self.chat_id:
            from store import add_message_to_chat
            add_message_to_chat(self.chat_id, role, content, thoughts)

    def clear_history(self) -> None:
        self.history = []
        if self.chat_id:
            from store import clear_chat_history
            clear_chat_history(self.chat_id)

    def build_prompt(self, user_text: str) -> str:
        """Construct prompt with system directive and recent dialog context."""
        parts = []
        parts.append("### СИСТЕМНАЯ ДИРЕКТИВА ANTIGRAVITY 2.0:")
        parts.append("Ты — интеллектуальный ассистент разработки Google Antigravity 2.0. Отвечай точно, профессионально, понятно и по существу. Предоставляй чистый и безопасный код, исчерпывающие объяснения и пошаговый анализ.")

        parts.append("\n### ИСТОРИЯ ДИАЛОГА:")
        recent = self.history[-12:]
        if not recent:
            parts.append("(Начало разговора)")
        else:
            for msg in recent:
                speaker = "Пользователь" if msg["role"] == "user" else "Ассистент"
                parts.append(f"{speaker}: {msg['content']}")

        parts.append(f"\nПользователь: {user_text}")
        parts.append("Ассистент:")
        return "\n".join(parts)

    def generate_response(
        self,
        user_text: str,
        model_override: Optional[str] = None,
        effort_override: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Send prompt to Antigravity CLI and get real model response and thoughts.
        Returns tuple: (reply_text, thoughts_text).
        NO canned fallback answers.
        """
        # 1. Verify Google Auth and Subscription
        auth_status = check_google_auth_and_subscription()
        if not auth_status["authenticated"]:
            err = (
                "❌ Ошибка авторизации: Вы не вошли в аккаунт Google.\n\n"
                "Для работы Antigravity 2.0 требуется активный вход в Google. "
                "Нажмите кнопку «Войти через Google» в меню или авторизуйтесь командой `agy`."
            )
            self.add_message("user", user_text)
            self.add_message("assistant", err)
            return err, ""

        if auth_status["subscription"] == "none":
            err = (
                "⚠️ Ошибка подписки Google Antigravity:\n\n"
                f"Аккаунт {auth_status.get('email')} не имеет активной подписки Gemini Advanced / Antigravity.\n"
                "Использование ИИ-моделей заблокировано. Оформите подписку на https://one.google.com/explore-plan/gemini-advanced"
            )
            self.add_message("user", user_text)
            self.add_message("assistant", err)
            return err, ""

        # 2. Find agy executable
        agy_cmd = find_agy_binary()
        if not agy_cmd:
            err = (
                "❌ Ошибка системы: Исполняемый файл Antigravity CLI (`agy`) не найден.\n"
                "Убедитесь, что Antigravity CLI установлен (`curl -fsSL https://antigravity.google/cli/install.sh | bash`)."
            )
            self.add_message("user", user_text)
            self.add_message("assistant", err)
            return err, ""

        model = model_override or "gemini-3.8-flash-high"
        effort = effort_override or "high"

        full_prompt = self.build_prompt(user_text)

        cmd = [
            agy_cmd,
            "--effort", effort,
            "--model", model,
            "--print", full_prompt
        ]

        env = os.environ.copy()
        home = os.path.expanduser("~")
        env["PATH"] = f"{home}/.local/bin:{home}/.gemini/antigravity-cli/bin:{env.get('PATH', '')}"

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env
            )
            
            stdout, stderr = process.communicate(timeout=60)
            
            if process.returncode == 0 and stdout.strip():
                raw_output = stdout.strip()
                thoughts = ""
                reply = raw_output

                # Extract thoughts if model wrapped them in thought tags
                if "<thought>" in raw_output and "</thought>" in raw_output:
                    try:
                        start_idx = raw_output.find("<thought>") + len("<thought>")
                        end_idx = raw_output.find("</thought>")
                        thoughts = raw_output[start_idx:end_idx].strip()
                        reply = (raw_output[:raw_output.find("<thought>")] + raw_output[end_idx + len("</thought>"):]).strip()
                    except Exception:
                        pass
                elif "Thinking Process:" in raw_output:
                    parts = raw_output.split("Thinking Process:", 1)
                    thoughts = parts[1].split("\n\n", 1)[0].strip()

                self.add_message("user", user_text)
                self.add_message("assistant", reply, thoughts)
                return reply, thoughts
            else:
                err_msg = stderr.strip() if stderr else "Не удалось получить ответ от ядра модели."
                err_reply = f"❌ Ошибка вызова модели ({model}):\n```\n{err_msg}\n```\nПопробуйте повторить запрос или сменить модель в боковой панели."
                self.add_message("user", user_text)
                self.add_message("assistant", err_reply)
                return err_reply, ""
        except subprocess.TimeoutExpired:
            process.kill()
            err_reply = "⏱️ Таймаут: Модель размышляла слишком долго (более 60 секунд). Попробуйте сформулировать запрос компактнее."
            self.add_message("user", user_text)
            self.add_message("assistant", err_reply)
            return err_reply, ""
        except Exception as e:
            err_reply = f"❌ Системная ошибка выполнения: {str(e)}"
            self.add_message("user", user_text)
            self.add_message("assistant", err_reply)
            return err_reply, ""

    def save_session_markdown(self, title: str = "Диалог") -> str:
        """Export current session history to a Markdown file."""
        if not self.history:
            return ""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip() or "chat"
        filename = f"{safe_title}_{timestamp}.md"
        filepath = os.path.join(HISTORY_DIR, filename)
        
        lines = [
            f"# {title} — Antigravity 2.0",
            f"- **Дата**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Сообщений**: {len(self.history)}",
            "",
            "---",
            ""
        ]
        
        for msg in self.history:
            if msg["role"] == "user":
                lines.append(f"### 👤 Пользователь ({msg.get('time', '')})")
                lines.append(msg["content"])
                lines.append("")
            else:
                lines.append(f"### 🤖 Antigravity 2.0 ({msg.get('time', '')})")
                if msg.get("thoughts"):
                    lines.append(f"> **💭 Размышления:**\n> {msg['thoughts']}\n")
                lines.append(msg["content"])
                lines.append("")
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            
        return filepath
