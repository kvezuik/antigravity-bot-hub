"""
Antigravity Bot Hub - Emoji Management & Customization Module
Provides curated emoji packs, customizable mood states, avatar badges, and styling.
"""

from typing import Dict, List, Any

# Themed Emoji Packs
EMOJI_PACKS = {
    "cyber_rebel": {
        "title": "🏴‍☠️ Cyber Rebel & Sarcasm",
        "description": "Острые, дерзкие и живые символы",
        "emojis": ["🏴‍☠️", "🤪", "😈", "🔥", "🕶️", "🍿", "🗿", "🚀", "💣", "🦾", "👾", "🤡", "💀", "🌪️", "🌶️"]
    },
    "cyber_tech": {
        "title": "⚡ Cyberpunk & Tech",
        "description": "Хакерские, футуристичные и системные символы",
        "emojis": ["🤖", "💻", "⚡", "👾", "🛠️", "🛸", "🧬", "🌐", "🛰️", "🔬", "💾", "📡", "🔋", "🖥️", "⚙️"]
    },
    "deep_mind": {
        "title": "🧠 Deep Mind & Wisdom",
        "description": "Философия, глубокий анализ, интеллект и логика",
        "emojis": ["🧠", "🦉", "📜", "🔮", "☕", "🔭", "💡", "💎", "🧙‍♂️", "🎯", "🌌", "⚖️", "🏛️", "🔑", "🧭"]
    },
    "creative": {
        "title": "🎨 Creative & Storytelling",
        "description": "Творчество, вдохновение, арт и магия слова",
        "emojis": ["🎨", "🎭", "🦄", "🌈", "🪄", "🎧", "🪶", "✨", "🪩", "🌟", "🎬", "🎤", "🎹", "📖", "🦋"]
    },
    "devops_ops": {
        "title": "🛡️ DevOps & Systems",
        "description": "Инфраструктура, безопасность, Linux, сети и базы данных",
        "emojis": ["🛡️", "⚙️", "🔒", "📦", "🐳", "🐧", "🪟", "🚦", "🚨", "🔧", "🧱", "🗄️", "🔍", "⚡", "🏗️"]
    },
    "mascots_gaming": {
        "title": "🎮 Gaming & Mascots",
        "description": "Игровые маскоты, RPG-символы и фантастические спутники",
        "emojis": ["🦊", "🐱", "🐉", "🐼", "👻", "⭐", "🍥", "⚔️", "🕹️", "🎮", "🎲", "👑", "🗡️", "🏹", "🛡️"]
    },
    "cyber_badges": {
        "title": "✦ Cyber Badges & ASCII",
        "description": "Текстовые и минималистичные техно-символы",
        "emojis": ["[✦]", "[⚡]", "[⚔️]", "[★]", "[AI]", "[#]", "[//]", "<sys>", "(•_•)", "(¬_¬)", "⟦✦⟧", "◈"]
    }
}

# Mood Presets: defines dynamic status emojis during conversation
MOOD_PRESETS = {
    "cyber_dynamic": {
        "name": "Динамический Режим",
        "idle": "🕶️",
        "thinking": "🌀",
        "typing": "🔥",
        "done": "🏴‍☠️",
        "error": "💥"
    },
    "deep_thinker": {
        "name": "Глубокий Аналитик",
        "idle": "☕",
        "thinking": "🧠",
        "typing": "📜",
        "done": "💡",
        "error": "⚠️"
    },
    "cyber_ninja": {
        "name": "Кибер-Хакер",
        "idle": "💤",
        "thinking": "⚡",
        "typing": "💻",
        "done": "🎯",
        "error": "🚨"
    },
    "magic_spark": {
        "name": "Магическая Искра",
        "idle": "✨",
        "thinking": "🔮",
        "typing": "🪄",
        "done": "🌟",
        "error": "🌧️"
    },
    "system_sentinel": {
        "name": "Страж Системы",
        "idle": "🛡️",
        "thinking": "⚙️",
        "typing": "🔧",
        "done": "✅",
        "error": "❌"
    }
}

# Avatar badge formatting styles
AVATAR_STYLES = {
    "boxed": "[ {emoji} {name} ]",
    "neon": "✦ {emoji} {name} »",
    "cyber": "⟦ {emoji} {name} ⟧",
    "minimal": "{emoji} {name}:",
    "bubble": "( {emoji} {name} )",
    "sharp": "► {emoji} {name} ◄"
}

def get_all_emojis_flat() -> List[str]:
    """Returns a deduplicated list of all available emojis from packs."""
    items = []
    for pack in EMOJI_PACKS.values():
        for e in pack["emojis"]:
            if e not in items:
                items.append(e)
    return items

def format_avatar(emoji: str, name: str, style_key: str = "boxed") -> str:
    """Format avatar badge with chosen style."""
    template = AVATAR_STYLES.get(style_key, AVATAR_STYLES["boxed"])
    return template.format(emoji=emoji, name=name)

def get_default_moods(archetype: str = "cyber_rebel") -> Dict[str, str]:
    """Return default mood set based on archetype."""
    if "thinker" in archetype.lower() or "mind" in archetype.lower():
        return dict(MOOD_PRESETS["deep_thinker"])
    elif "coder" in archetype.lower() or "tech" in archetype.lower() or "cyber" in archetype.lower():
        return dict(MOOD_PRESETS["cyber_ninja"])
    elif "magic" in archetype.lower() or "creative" in archetype.lower():
        return dict(MOOD_PRESETS["magic_spark"])
    elif "devops" in archetype.lower() or "hunter" in archetype.lower():
        return dict(MOOD_PRESETS["system_sentinel"])
    else:
        return dict(MOOD_PRESETS["cyber_dynamic"])
