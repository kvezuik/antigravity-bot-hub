"""
Antigravity Bot Hub - Exporter Module
Exports bots to Antigravity Rules (.agents/rules/), global configs, and standalone CLI scripts.
"""

import os
import json
from typing import Dict, Any, Tuple

def export_to_antigravity_rule(bot: Dict[str, Any], workspace_dir: str = "/home/kvezik") -> Tuple[bool, str]:
    """
    Exports bot persona as an Antigravity Rule into .agents/rules/<bot_id>.md.
    Antigravity automatically discovers and activates rules from .agents/rules/.
    """
    rules_dir = os.path.join(workspace_dir, ".agents", "rules")
    os.makedirs(rules_dir, exist_ok=True)
    
    file_path = os.path.join(rules_dir, f"persona_{bot.get('id', 'bot')}.md")
    
    content = f"""---
description: "Antigravity Persona: {bot.get('name')} {bot.get('emoji')}"
globs: "*"
always_on: false
---

# Роль и Персона: {bot.get('emoji')} {bot.get('name')}

> **Теглайн:** {bot.get('tagline')}  
> **Архетип:** `{bot.get('archetype')}` | **Юмор/Сарказм:** {bot.get('humor_level')}%  
> **Фирменный стиль:** {bot.get('avatar_style')}

## Системная Инструкция:
{bot.get('system_prompt')}

## Настройки статуса и эмодзи:
- Ожидание: {bot.get('moods', {}).get('idle', '💤')}
- Анализ: {bot.get('moods', {}).get('thinking', '🧠')}
- Ответ: {bot.get('moods', {}).get('typing', '🔥')}
- Успех: {bot.get('moods', {}).get('done', '🎯')}

При обращении соблюдай этот характер, тон и визуальную идентификацию.
"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True, file_path
    except Exception as e:
        return False, str(e)

def export_to_standalone_runner(bot: Dict[str, Any], export_dir: str = "/home/kvezik") -> Tuple[str, str]:
    """
    Generates single-click runner scripts for Linux (.sh) and Windows (.bat)
    to launch this specific bot directly from terminal.
    """
    bot_id = bot.get("id", "bot")
    sh_path = os.path.join(export_dir, f"run_{bot_id}.sh")
    bat_path = os.path.join(export_dir, f"run_{bot_id}.bat")
    
    # Linux Bash script
    sh_content = f"""#!/usr/bin/env bash
# Runner for {bot.get('name')} ({bot.get('emoji')})
python3 /home/kvezik/antigravity-bot-hub/main.py --bot "{bot_id}"
"""
    with open(sh_path, "w", encoding="utf-8") as f:
        f.write(sh_content)
    os.chmod(sh_path, 0o755)

    # Windows Batch file
    bat_content = f"""@echo off
REM Windows Runner for {bot.get('name')} ({bot.get('emoji')})
python main.py --bot "{bot_id}"
pause
"""
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)

    return sh_path, bat_path
