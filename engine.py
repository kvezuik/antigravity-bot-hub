"""
Antigravity Bot Hub - Execution Engine & Chat Runner
Connects to Antigravity CLI (agy) or fallback engine, manages multi-turn history.
"""

import subprocess
import os
import sys
import time
import json
import threading
from typing import List, Dict, Any, Optional, Callable

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from bots import record_message

HISTORY_DIR = os.path.expanduser("/home/kvezik/antigravity-bot-hub/history")

class ChatEngine:
    def __init__(self, bot: Dict[str, Any]):
        self.bot = bot
        self.history: List[Dict[str, str]] = []
        os.makedirs(HISTORY_DIR, exist_ok=True)

    def add_message(self, role: str, content: str) -> None:
        self.history.append({
            "role": role,
            "content": content,
            "time": time.strftime("%H:%M:%S")
        })
        if role == "assistant":
            record_message(self.bot.get("id", ""))

    def clear_history(self) -> None:
        self.history = []

    def build_prompt(self, user_text: str) -> str:
        """Construct full prompt with persona instructions and recent dialog context."""
        parts = []
        parts.append(f"### СИСТЕМНАЯ ДИРЕКТИВА ДЛЯ ИИ-ПЕРСОНЫ:")
        parts.append(self.bot.get("system_prompt", "Ты полезный ассистент."))
        parts.append(f"\nПАРАМЕТРЫ ЛИЧНОСТИ:")
        parts.append(f"- Имя: {self.bot.get('name')}")
        parts.append(f"- Главный эмодзи: {self.bot.get('emoji')}")
        parts.append(f"- Уровень сарказма/юмора: {self.bot.get('humor_level', 50)}%")
        parts.append(f"- Креативность: {self.bot.get('creativity_temp', 0.7)}")
        parts.append(f"- Архетип: {self.bot.get('archetype', 'general')}")
        
        if self.bot.get("humor_level", 50) > 70:
            parts.append("ВАЖНО: Добавляй в общение фирменный сарказм, остроумные подколки, живую речь и эмодзи в духе Grok.")

        parts.append("\n### ИСТОРИЯ ДИАЛОГА:")
        # Keep last 8 messages for context
        recent = self.history[-8:]
        if not recent:
            parts.append("(Начало разговора)")
        else:
            for msg in recent:
                speaker = "Пользователь" if msg["role"] == "user" else self.bot.get("name", "Бот")
                parts.append(f"{speaker}: {msg['content']}")

        parts.append(f"\nПользователь: {user_text}")
        parts.append(f"{self.bot.get('name', 'Бот')}:")
        return "\n".join(parts)

    def generate_response(
        self,
        user_text: str,
        spinner_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """Send prompt to Antigravity CLI and get response."""
        full_prompt = self.build_prompt(user_text)
        model = self.bot.get("model", "gemini-3.8-flash-high")
        
        # Check if agy binary is available
        agy_cmd = ["agy", "--model", model, "--print", full_prompt]
        
        try:
            # Run agy command
            process = subprocess.Popen(
                agy_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            
            stdout, stderr = process.communicate(timeout=45)
            
            if process.returncode == 0 and stdout.strip():
                response_text = stdout.strip()
                self.add_message("user", user_text)
                self.add_message("assistant", response_text)
                return response_text
            else:
                err_msg = stderr.strip() if stderr else "Неизвестная ошибка"
                # Fallback to simulation mode if agy had an issue
                return self._simulate_fallback(user_text, f"Agy error: {err_msg}")
        except FileNotFoundError:
            return self._simulate_fallback(user_text, "Agy CLI не найден в PATH. Запущен автономный демо-режим.")
        except subprocess.TimeoutExpired:
            process.kill()
            return f"{self.bot.get('emoji', '🤖')} [Таймаут]: Antigravity отвечал слишком долго. Попробуйте сформулировать вопрос короче."
        except Exception as e:
            return self._simulate_fallback(user_text, str(e))

    def _simulate_fallback(self, user_text: str, reason: str) -> str:
        """Fallback response generator if Antigravity CLI is temporarily unavailable."""
        emoji = self.bot.get("emoji", "🤖")
        name = self.bot.get("name", "Бот")
        archetype = self.bot.get("archetype", "grok_rebel")
        
        self.add_message("user", user_text)
        
        if "rebel" in archetype:
            reply = (
                f"{emoji} О, вижу твой запрос «{user_text}»! "
                f"Я бы выдал сейчас квантовую дозу сарказма и гениальности, но Antigravity CLI дал сбой ({reason}). "
                f"Тем не менее, суть ясна: не бойся ломать шаблоны и кодить красиво! 🏴‍☠️🔥"
            )
        elif "thinker" in archetype:
            reply = (
                f"{emoji} Анализируя предпосылку вопроса «{user_text}», я вижу фундаментальное противоречие. "
                f"(Локальный движок переключен в безопасный режим: {reason}). "
                f"Мысль — это первый шаг к архитектуре. 🧠💡"
            )
        elif "coder" in archetype:
            reply = (
                f"{emoji} Запрос принят: `{user_text}`.\n"
                f"```bash\n# Рекомендация CyberCoder:\npython3 main.py --check-system\n```\n"
                f"Код должен быть чистым, а зависимости — минимальными! 💻⚡"
            )
        else:
            reply = f"{emoji} {name} на связи! Ответ на «{user_text}» принят в обработку. (Статус: {reason})"
            
        self.add_message("assistant", reply)
        return reply

    def save_session_markdown(self) -> str:
        """Export current session history to a Markdown file."""
        if not self.history:
            return ""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{self.bot.get('id', 'bot')}_{timestamp}.md"
        filepath = os.path.join(HISTORY_DIR, filename)
        
        lines = [
            f"# Диалог с {self.bot.get('emoji', '')} {self.bot.get('name', 'Бот')}",
            f"- **Дата**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Модель**: `{self.bot.get('model', 'gemini-3.8-flash-high')}`",
            f"- **Юмор**: {self.bot.get('humor_level', 50)}%",
            f"- **Теглайн**: {self.bot.get('tagline', '')}",
            "",
            "---",
            ""
        ]
        
        for msg in self.history:
            if msg["role"] == "user":
                lines.append(f"### 👤 Вы ({msg.get('time', '')})")
                lines.append(msg["content"])
                lines.append("")
            else:
                lines.append(f"### {self.bot.get('emoji', '🤖')} {self.bot.get('name', 'Бот')} ({msg.get('time', '')})")
                lines.append(msg["content"])
                lines.append("")
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            
        return filepath
