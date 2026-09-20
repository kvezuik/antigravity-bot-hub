#!/usr/bin/env python3
"""
Antigravity Bot Hub - Main Application
Cross-platform Desktop Studio and Multi-Agent Manager for Antigravity 2.0.
Works seamlessly on Linux and Windows.
"""

import sys
import os
import argparse
import time
import glob
from typing import Optional, Dict, Any, List

# Add parent directory to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tui import (
    init_terminal, clear_screen, print_header, print_box, print_divider,
    select_menu_item, prompt_text, prompt_slider, press_any_key, pad_str, str_width,
    CYAN, PURPLE, PINK, YELLOW, GREEN, RED, GRAY, DARK_GRAY, WHITE, BOLD, RESET, BG_HIGHLIGHT
)
from emojis import (
    EMOJI_PACKS, MOOD_PRESETS, AVATAR_STYLES, format_avatar,
    get_all_emojis_flat, get_default_moods
)
from bots import (
    load_bots, save_bots, get_bot, create_bot, update_bot, delete_bot,
    duplicate_bot, PRESET_BOTS
)
from engine import ChatEngine, HISTORY_DIR
from exporter import export_to_antigravity_rule, export_to_standalone_runner

AVAILABLE_MODELS = [
    ("gemini-3.8-flash-high", "Gemini 3.8 Flash (High) - Быстрый и мощный [Рекомендуется]"),
    ("gemini-3.8-flash-medium", "Gemini 3.8 Flash (Medium) - Баланс скорости и точности"),
    ("gemini-3.7-flash-high", "Gemini 3.7 Flash (High) - Проверенный и надежный"),
    ("gemini-3.1-pro-high", "Gemini 3.1 Pro (High) - Глубокие рассуждения и сложный код"),
    ("claude-sonnet-4-6", "Claude Sonnet 4.6 - Анализ текста и архитектура"),
    ("gpt-oss-120b-medium", "GPT-OSS 120B - Открытая мощная модель")
]

CURRENT_BOT_ID = "antigravity_assistant"

def run_chat_session(bot: Dict[str, Any]) -> None:
    """Run interactive terminal chat with selected bot."""
    global CURRENT_BOT_ID
    CURRENT_BOT_ID = bot.get("id", "antigravity_assistant")
    
    engine = ChatEngine(bot)
    moods = bot.get("moods", {})
    idle_emoji = moods.get("idle", "💤")
    think_emoji = moods.get("thinking", "🧠")
    type_emoji = moods.get("typing", "🔥")
    done_emoji = moods.get("done", "🎯")
    
    avatar = format_avatar(bot.get("emoji", "🤖"), bot.get("name", "Бот"), bot.get("avatar_style", "boxed"))
    
    clear_screen()
    print_header(f"ЧАТ: {bot.get('name')}", bot.get("tagline", ""))
    
    info_lines = [
        f"{CYAN}Модель:{RESET} {bot.get('model', 'gemini-3.8-flash-high')} | {PINK}Сарказм/Юмор:{RESET} {bot.get('humor_level', 50)}% | {YELLOW}Креативность:{RESET} {bot.get('creativity_temp', 0.7)}",
        f"{GRAY}Команды: {CYAN}/help{GRAY}, {CYAN}/emoji{GRAY}, {CYAN}/model{GRAY}, {CYAN}/roast{GRAY}, {CYAN}/save{GRAY}, {CYAN}/clear{GRAY}, {RED}/exit{RESET}"
    ]
    print_box(info_lines, title="Параметры сессии", border_color=PURPLE, width=68)
    print()
    
    # Greeting
    greeting = f"{bot.get('emoji')} Привет! Я на связи. Чем займемся?"
    if "rebel" in bot.get("archetype", ""):
        greeting = f"{bot.get('emoji')} Ну что, готов к порции правды и бодрого кода? Выкладывай свой вопрос! 🏴‍☠️"
    elif "thinker" in bot.get("archetype", ""):
        greeting = f"{bot.get('emoji')} Рад приветствовать. Какую идею или задачу разберем по первым принципам? 🧠"
    elif "coder" in bot.get("archetype", ""):
        greeting = f"{bot.get('emoji')} Терминал готов. Жду код, задачу или лог ошибки. 💻⚡"
        
    print(f"{PURPLE}{avatar}{RESET}\n{WHITE}{greeting}{RESET}\n")
    
    while True:
        try:
            prompt_label = f"{GREEN}👤 Вы{RESET} › "
            user_input = input(prompt_label).strip()
            
            if not user_input:
                continue
                
            # Handle Slash Commands
            if user_input.startswith("/"):
                cmd_parts = user_input.split(maxsplit=1)
                cmd = cmd_parts[0].lower()
                arg = cmd_parts[1].strip() if len(cmd_parts) > 1 else ""
                
                if cmd in ("/exit", "/quit", "/q"):
                    break
                elif cmd == "/help":
                    print(f"\n{YELLOW}Доступные команды в чате:{RESET}")
                    print(f"  {CYAN}/emoji <символ>{RESET} - Быстро сменить смайлик бота прямо сейчас")
                    print(f"  {CYAN}/model <название>{RESET} - Переключить модель (напр. gemini-3.8-flash-high)")
                    print(f"  {CYAN}/roast <текст>{RESET} - Включить мгновенный режим прожарки темы")
                    print(f"  {CYAN}/clear{RESET} - Очистить память текущего диалога")
                    print(f"  {CYAN}/save{RESET} - Сохранить диалог в Markdown файл")
                    print(f"  {CYAN}/export{RESET} - Экспортировать бота в Antigravity Rule")
                    print(f"  {RED}/exit{RESET} - Вернуться в главное меню\n")
                    continue
                elif cmd == "/clear":
                    engine.clear_history()
                    print(f"{GRAY}✔ История диалога очищена.{RESET}\n")
                    continue
                elif cmd == "/emoji":
                    if arg:
                        bot["emoji"] = arg
                        update_bot(bot["id"], {"emoji": arg})
                        avatar = format_avatar(bot.get("emoji"), bot.get("name"), bot.get("avatar_style", "boxed"))
                        print(f"{GREEN}✔ Смайлик бота изменен на {arg}{RESET}\n")
                    else:
                        print(f"{YELLOW}Укажите смайлик, например: /emoji ⚡ или /emoji 🚀{RESET}\n")
                    continue
                elif cmd == "/model":
                    if arg:
                        bot["model"] = arg
                        update_bot(bot["id"], {"model": arg})
                        print(f"{GREEN}✔ Модель переключена на {arg}{RESET}\n")
                    else:
                        print(f"{YELLOW}Пример: /model gemini-3.1-pro-high{RESET}\n")
                    continue
                elif cmd == "/roast":
                    user_input = f"[ВКЛЮЧИ РЕЖИМ ЖЕСТКОЙ ПРОЖАРКИ И ЮМОРА]: {arg if arg else 'прожарь текущее состояние технологий'}"
                elif cmd == "/save":
                    path = engine.save_session_markdown()
                    if path:
                        print(f"{GREEN}✔ Диалог сохранен в: {path}{RESET}\n")
                    else:
                        print(f"{YELLOW}Диалог пока пуст.{RESET}\n")
                    continue
                elif cmd == "/export":
                    ok, res = export_to_antigravity_rule(bot)
                    if ok:
                        print(f"{GREEN}✔ Бот успешно экспортирован в правило Antigravity: {res}{RESET}\n")
                    else:
                        print(f"{RED}Ошибка экспорта: {res}{RESET}\n")
                    continue

            # Generate Response with animated status
            print(f"{DARK_GRAY}{think_emoji} {bot.get('name')} думает...{RESET}", end="\r", flush=True)
            t0 = time.time()
            reply = engine.generate_response(user_input)
            elapsed = time.time() - t0
            
            # Clear thinking line
            print(" " * 60, end="\r")
            
            # Print bot answer
            print(f"{PURPLE}{avatar}{RESET} {DARK_GRAY}({done_emoji} {elapsed:.1f}с){RESET}")
            print(f"{WHITE}{reply}{RESET}\n")
            
        except (KeyboardInterrupt, EOFError):
            print(f"\n{GRAY}Сессия завершена.{RESET}")
            break

def screen_select_bot() -> None:
    """Screen to browse, inspect, and select active bot."""
    global CURRENT_BOT_ID
    bots = load_bots()
    
    items = []
    for b in bots:
        emoji = b.get("emoji", "🤖")
        name = b.get("name", "Бот")
        tagline = b.get("tagline", "")
        cat = b.get("category", "")
        msgs = b.get("stats", {}).get("messages_count", 0)
        items.append((b["id"], f"{emoji} {name}", f"[{cat}] {tagline} ({msgs} сообщ.)"))
        
    idx = select_menu_item(items, header_title="ВЫБОР АКТИВНОГО БОТА")
    if idx >= 0 and idx < len(bots):
        selected = bots[idx]
        CURRENT_BOT_ID = selected["id"]
        print(f"\n{GREEN}✔ Активный бот переключен на: {selected.get('emoji')} {selected.get('name')}{RESET}")
        time.sleep(0.6)

def screen_emoji_customizer() -> None:
    """Emoji and Avatar Customization Hub."""
    bot = get_bot(CURRENT_BOT_ID)
    if not bot:
        bot = load_bots()[0]
        
    while True:
        clear_screen()
        avatar = format_avatar(bot.get('emoji', '🤖'), bot.get('name', 'Бот'), bot.get('avatar_style', 'boxed'))
        print_header(f"КАСТОМИЗАЦИЯ СМАЙЛИКОВ: {bot.get('name')}", f"Текущий аватар: {avatar}")
        
        menu_items = [
            ("1", "Выбрать из тематических наборов (Cyber, Mind, Creative...)", "Готовые коллекции крутых смайликов"),
            ("2", "Ввести свой смайлик вручную", "Любой Unicode эмодзи или текстовый тег [⚡], 💀, 👾"),
            ("3", "Настроить эмодзи статусов и настроения (Moods)", f"Ожидание: {bot.get('moods',{}).get('idle')} | Мысль: {bot.get('moods',{}).get('thinking')} | Ответ: {bot.get('moods',{}).get('typing')}"),
            ("4", "Выбрать стиль рамки аватара", f"Текущий стиль: {bot.get('avatar_style', 'boxed')}"),
            ("5", "Случайный эпичный смайлик", "Удачный выбор из всех доступных"),
            ("0", "Назад в главное меню", "Сохранить изменения и вернуться")
        ]
        
        choice = select_menu_item(menu_items, header_title="МЕНЮ КАСТОМИЗАЦИИ СМАЙЛИКОВ")
        if choice == 0:
            # Choose from pack
            pack_keys = list(EMOJI_PACKS.keys())
            pack_items = [(k, EMOJI_PACKS[k]["title"], " ".join(EMOJI_PACKS[k]["emojis"][:8])) for k in pack_keys]
            p_idx = select_menu_item(pack_items, header_title="ВЫБЕРИТЕ ТЕМАТИЧЕСКИЙ НАБОР")
            if 0 <= p_idx < len(pack_keys):
                pack = EMOJI_PACKS[pack_keys[p_idx]]
                emoji_items = [(e, f"{e}  (Символ)", "") for e in pack["emojis"]]
                e_idx = select_menu_item(emoji_items, header_title=f"НАБОР: {pack['title']}")
                if 0 <= e_idx < len(pack["emojis"]):
                    chosen = pack["emojis"][e_idx]
                    bot["emoji"] = chosen
                    update_bot(bot["id"], {"emoji": chosen})
                    print(f"\n{GREEN}✔ Новый смайлик установлен: {chosen}{RESET}")
                    time.sleep(0.8)
        elif choice == 1:
            # Manual emoji
            print(f"\n{CYAN}Введите любой эмодзи или текстовый значок (например: 🏴‍☠️, 🦾, 🚀, [✦], ⚡):{RESET}")
            custom = prompt_text("Смайлик", default=bot.get("emoji", "🤖"))
            if custom:
                bot["emoji"] = custom
                update_bot(bot["id"], {"emoji": custom})
                print(f"\n{GREEN}✔ Смайлик обновлен на: {custom}{RESET}")
                time.sleep(0.8)
        elif choice == 2:
            # Customize moods
            mood_keys = list(MOOD_PRESETS.keys())
            m_items = [(k, MOOD_PRESETS[k]["name"], f"Мысль: {MOOD_PRESETS[k]['thinking']} | Ответ: {MOOD_PRESETS[k]['typing']} | Финиш: {MOOD_PRESETS[k]['done']}") for k in mood_keys]
            m_idx = select_menu_item(m_items, header_title="ВЫБОР ПРЕСЕТА НАСТРОЕНИЙ")
            if 0 <= m_idx < len(mood_keys):
                chosen_mood = dict(MOOD_PRESETS[mood_keys[m_idx]])
                del chosen_mood["name"]
                bot["moods"] = chosen_mood
                update_bot(bot["id"], {"moods": chosen_mood})
                print(f"\n{GREEN}✔ Настроения обновлены!{RESET}")
                time.sleep(0.8)
        elif choice == 3:
            # Avatar style
            styles = list(AVATAR_STYLES.keys())
            s_items = [(s, format_avatar(bot.get('emoji', '🤖'), bot.get('name'), s), f"Стиль {s}") for s in styles]
            s_idx = select_menu_item(s_items, header_title="ВЫБОР СТИЛЯ РАМКИ")
            if 0 <= s_idx < len(styles):
                chosen_style = styles[s_idx]
                bot["avatar_style"] = chosen_style
                update_bot(bot["id"], {"avatar_style": chosen_style})
                print(f"\n{GREEN}✔ Стиль аватара изменен на {chosen_style}!{RESET}")
                time.sleep(0.8)
        elif choice == 4:
            # Random emoji
            import random
            all_e = get_all_emojis_flat()
            r_emoji = random.choice(all_e)
            bot["emoji"] = r_emoji
            update_bot(bot["id"], {"emoji": r_emoji})
            print(f"\n{GREEN}✔ Выпал случайный смайлик: {r_emoji}{RESET}")
            time.sleep(0.8)
        else:
            break

def screen_create_wizard() -> None:
    """Interactive wizard to create a brand new custom bot for anything."""
    global CURRENT_BOT_ID
    clear_screen()
    print_header("МАСТЕР СОЗДАНИЯ БОТА", "Создай собственного ИИ-агента для любой задачи")
    
    print(f"{WHITE}Шаг 1 из 6: Базовая информация{RESET}")
    name = prompt_text("Имя бота (напр. DevSecOps Бот, Английский Собеседник, Шеф-Повар)")
    if not name:
        name = "Мой Кастомный Бот"
        
    tagline = prompt_text("Краткий теглайн/девиз", default=f"Персональный ИИ-ассистент {name}")
    category = prompt_text("Категория", default="Специалисты")
    
    # Emoji selection
    print(f"\n{WHITE}Шаг 2 из 6: Фирменный смайлик бота{RESET}")
    emoji = prompt_text("Смайлик (напр. 🏴‍☠️, ⚡, 🧠, 💻, 🎯, 🚀, 🦉)", default="🤖")
    
    # Archetype selection
    print(f"\n{WHITE}Шаг 3 из 6: Характер и Архетип{RESET}")
    archetype_choices = [
        ("cyber_rebel", "Cyber Rebel (Остроумный и живой язык, честность)", "Острые подколки, живой язык, честность"),
        ("deep_thinker", "Deep Thinker (Философ и Архитектор мысли)", "Первые принципы, глубокая логика"),
        ("cyber_ninja", "Cyber Coder (Хакер и программист Antigravity)", "Чистый код, архитектура, скрипты"),
        ("roaster", "Brutal Roaster (Беспощадная прожарка)", "Юморная критика и профессиональное исправление"),
        ("eli5", "ELI5 Mentor (Объяснение на пальцах)", "Простые аналогии для сложных понятий"),
        ("custom", "Свой свободный промпт", "Любая нестандартная роль")
    ]
    arch_idx = select_menu_item(archetype_choices, header_title="ВЫБОР АРХЕТИПА")
    chosen_arch = archetype_choices[arch_idx][0] if 0 <= arch_idx < len(archetype_choices) else "custom"
    
    # System Prompt
    print(f"\n{WHITE}Шаг 4 из 6: Системная инструкция (System Prompt){RESET}")
    def_prompt = f"Ты — {name}, высококвалифицированный специалист в своей области. Отвечай качественно, интересно и по существу."
    if chosen_arch == "cyber_rebel":
        def_prompt = f"Ты — {name}, остроумный и энергичный ассистент. Отвечай живо, сочно, умно, но по делу всегда давай точную и полезную суть!"
    elif chosen_arch == "deep_thinker":
        def_prompt = f"Ты — {name}, глубокий аналитик. Разбирай вопросы по первым принципам и помогай принимать системные решения."
    elif chosen_arch == "cyber_ninja":
        def_prompt = f"Ты — {name}, системный инженер. Пиши чистый, надежный код и автоматизируй всё возможное."
    elif chosen_arch == "roaster":
        def_prompt = f"Ты — {name}, прожарщик кода и идей. Смешно высмеивай ошибки, но в конце всегда давай безупречное решение."
        
    print(f"{DARK_GRAY}Подсказка: нажмите Enter для использования шаблона или введите свой промпт{RESET}")
    system_prompt = prompt_text("Промпт личности", default=def_prompt)
    
    # Humor Slider
    print(f"\n{WHITE}Шаг 5 из 6: Настройки поведения{RESET}")
    humor = prompt_slider("Уровень юмора и сарказма", min_v=0, max_v=100, default=70 if chosen_arch in ("cyber_rebel", "roaster") else 30)
    
    # Model Selection
    print(f"\n{WHITE}Шаг 6 из 6: Выбор модели Antigravity{RESET}")
    m_items = [(m[0], m[1], "") for m in AVAILABLE_MODELS]
    m_idx = select_menu_item(m_items, header_title="ВЫБЕРИТЕ МОДЕЛЬ")
    selected_model = AVAILABLE_MODELS[m_idx][0] if 0 <= m_idx < len(AVAILABLE_MODELS) else "gemini-3.8-flash-high"
    
    # Create bot
    new_bot = create_bot(
        name=name,
        emoji=emoji,
        tagline=tagline,
        category=category,
        system_prompt=system_prompt,
        archetype=chosen_arch,
        humor_level=humor,
        creativity_temp=0.75,
        model=selected_model,
        avatar_style="boxed"
    )
    
    CURRENT_BOT_ID = new_bot["id"]
    
    clear_screen()
    print_header("БОТ УСПЕШНО СОЗДАН! 🎉", f"{new_bot.get('emoji')} {new_bot.get('name')}")
    summary = [
        f"{CYAN}Имя:{RESET} {new_bot.get('name')} | {YELLOW}Смайлик:{RESET} {new_bot.get('emoji')}",
        f"{PINK}Категория:{RESET} {new_bot.get('category')} | {GREEN}Архетип:{RESET} {new_bot.get('archetype')}",
        f"{PURPLE}Модель:{RESET} {new_bot.get('model')} | {WHITE}Юмор:{RESET} {new_bot.get('humor_level')}%",
        f"{GRAY}Промпт:{RESET} {new_bot.get('system_prompt')[:60]}..."
    ]
    print_box(summary, title="Карточка бота", border_color=GREEN, width=68)
    
    next_choices = [
        ("1", "Запустить чат с новым ботом прямо сейчас", "Протестировать характер в диалоге"),
        ("2", "Экспортировать бота в Antigravity Rule", "Добавить в .agents/rules/"),
        ("3", "Вернуться в главное меню", "")
    ]
    act = select_menu_item(next_choices, header_title="ЧТО ДЕЛАТЬ ДАЛЬШЕ?")
    if act == 0:
        run_chat_session(new_bot)
    elif act == 1:
        ok, res = export_to_antigravity_rule(new_bot)
        if ok:
            print(f"\n{GREEN}✔ Экспортировано в: {res}{RESET}")
        press_any_key()

def screen_manage_bots() -> None:
    """Edit, clone, delete, or reset bots."""
    global CURRENT_BOT_ID
    while True:
        bots = load_bots()
        items = []
        for b in bots:
            items.append((b["id"], f"{b.get('emoji')} {b.get('name')}", f"[{b.get('category')}] {b.get('tagline')}"))
        items.append(("back", "← Назад в главное меню", ""))
        
        idx = select_menu_item(items, header_title="УПРАВЛЕНИЕ БОТАМИ (ВЫБЕРИТЕ БОТА ДЛЯ ДЕЙСТВИЯ)")
        if idx < 0 or idx >= len(bots):
            break
            
        bot = bots[idx]
        clear_screen()
        print_header(f"БОТ: {bot.get('emoji')} {bot.get('name')}", bot.get("tagline", ""))
        
        actions = [
            ("1", "Редактировать системный промпт и описание", "Изменить поведение бота"),
            ("2", "Изменить смайлик и стиль аватара", "Кастомизация визуала"),
            ("3", "Изменить уровень юмора / сарказма", f"Текущий уровень: {bot.get('humor_level')}%"),
            ("4", "Сменить модель Antigravity", f"Текущая: {bot.get('model')}"),
            ("5", "Клонировать бота (сделать копию)", "Создать дубликат для экспериментов"),
            ("6", "Удалить бота", "Безвозвратное удаление"),
            ("0", "Назад к списку ботов", "")
        ]
        
        act = select_menu_item(actions, header_title=f"ДЕЙСТВИЯ С «{bot.get('name')}»")
        if act == 0:
            new_prompt = prompt_text("Новый системный промпт", default=bot.get("system_prompt", ""))
            new_tag = prompt_text("Новый теглайн", default=bot.get("tagline", ""))
            update_bot(bot["id"], {"system_prompt": new_prompt, "tagline": new_tag})
            print(f"\n{GREEN}✔ Данные бота обновлены!{RESET}")
            time.sleep(0.8)
        elif act == 1:
            CURRENT_BOT_ID = bot["id"]
            screen_emoji_customizer()
        elif act == 2:
            new_humor = prompt_slider("Новый уровень юмора", default=bot.get("humor_level", 50))
            update_bot(bot["id"], {"humor_level": new_humor})
            print(f"\n{GREEN}✔ Уровень юмора обновлен!{RESET}")
            time.sleep(0.8)
        elif act == 3:
            m_items = [(m[0], m[1], "") for m in AVAILABLE_MODELS]
            m_idx = select_menu_item(m_items, header_title="ВЫБЕРИТЕ НОВУЮ МОДЕЛЬ")
            if 0 <= m_idx < len(AVAILABLE_MODELS):
                update_bot(bot["id"], {"model": AVAILABLE_MODELS[m_idx][0]})
                print(f"\n{GREEN}✔ Модель обновлена!{RESET}")
                time.sleep(0.8)
        elif act == 4:
            clone = duplicate_bot(bot["id"])
            if clone:
                print(f"\n{GREEN}✔ Создан клон: {clone.get('name')}{RESET}")
                time.sleep(0.8)
        elif act == 5:
            confirm = prompt_text(f"Точно удалить бота «{bot.get('name')}»? (yes/no)", default="no")
            if confirm.lower() in ("yes", "y", "да"):
                delete_bot(bot["id"])
                print(f"\n{YELLOW}✔ Бот удален.{RESET}")
                time.sleep(0.8)
        else:
            continue

def screen_export_hub() -> None:
    """Export bots to Antigravity Rules or standalone scripts."""
    bots = load_bots()
    options = [
        ("1", "Экспортировать всех ботов в Antigravity Rules", "Создает .agents/rules/ для каждого бота"),
        ("2", "Экспортировать активного бота в Antigravity Rule", f"Экспорт только {CURRENT_BOT_ID}"),
        ("3", "Создать скрипты быстрого запуска (.sh и .bat)", "Запуск бота одной командой в Linux и Windows"),
        ("0", "Назад в главное меню", "")
    ]
    
    choice = select_menu_item(options, header_title="ЭКСПОРТ В СИСТЕМУ ANTIGRAVITY")
    if choice == 0:
        count = 0
        for b in bots:
            ok, _ = export_to_antigravity_rule(b)
            if ok:
                count += 1
        print(f"\n{GREEN}✔ Успешно экспортировано {count} ботов в папку .agents/rules/{RESET}")
        press_any_key()
    elif choice == 1:
        bot = get_bot(CURRENT_BOT_ID) or bots[0]
        ok, res = export_to_antigravity_rule(bot)
        if ok:
            print(f"\n{GREEN}✔ Бот {bot.get('name')} сохранен в {res}{RESET}")
        else:
            print(f"\n{RED}Ошибка экспорта: {res}{RESET}")
        press_any_key()
    elif choice == 2:
        bot = get_bot(CURRENT_BOT_ID) or bots[0]
        sh, bat = export_to_standalone_runner(bot)
        print(f"\n{GREEN}✔ Скрипты запуска созданы:{RESET}")
        print(f"  Linux/macOS: {CYAN}{sh}{RESET}")
        print(f"  Windows:     {CYAN}{bat}{RESET}")
        press_any_key()

def screen_history() -> None:
    """View saved chat history logs."""
    files = glob.glob(os.path.join(HISTORY_DIR, "*.md"))
    if not files:
        clear_screen()
        print_header("ИСТОРИЯ ДИАЛОГОВ", "Сохраненные сессии общения")
        print(f"\n{YELLOW}Сохраненных диалогов пока нет. Пообщайтесь с ботом и используйте команду /save.{RESET}\n")
        press_any_key()
        return
        
    files.sort(key=os.path.getmtime, reverse=True)
    items = []
    for f in files[:12]:
        name = os.path.basename(f)
        size = os.path.getsize(f)
        items.append((f, name, f"{size} байт"))
    items.append(("back", "← Назад", ""))
    
    idx = select_menu_item(items, header_title="СОХРАНЕННЫЕ ДИАЛОГИ (ВЫБЕРИТЕ ДЛЯ ПРОСМОТРА)")
    if 0 <= idx < len(files):
        clear_screen()
        with open(files[idx], "r", encoding="utf-8") as file:
            content = file.read()
        print(f"{CYAN}=== СОДЕРЖИМОЕ ФАЙЛА: {os.path.basename(files[idx])} ==={RESET}\n")
        print(content)
        press_any_key()

def screen_help() -> None:
    """Show help and information."""
    clear_screen()
    print_header("СПРАВКА И ВОЗМОЖНОСТИ", "Antigravity 2.0 Desktop Studio")
    
    help_text = [
        f"{BOLD}{WHITE}О проекте:{RESET}",
        "Antigravity Bot Hub — это десктопная студия и среда управления проектами",
        "и диалогами для Antigravity 2.0 CLI.",
        "",
        f"{BOLD}{WHITE}Ключевые фичи:{RESET}",
        f"• {CYAN}Любые роли:{RESET} от системного архитектора до детектора багов и ментора",
        f"• {PINK}Кастомизация смайликов:{RESET} готовые паки (Cyber, Mind, Systems) + свои символы",
        f"• {YELLOW}Кроссплатформенность:{RESET} красивый интерфейс для Linux и Windows",
        f"• {GREEN}Интеграция с Antigravity:{RESET} прямой запуск через agy и экспорт в .agents/rules",
        "",
        f"{BOLD}{WHITE}Быстрый запуск из терминала:{RESET}",
        f"  {CYAN}python3 ~/antigravity-bot-hub/main.py{RESET}",
        f"  {CYAN}agybots{RESET}  (если настроен alias)"
    ]
    print_box(help_text, title="Инфо", border_color=PURPLE, width=68)
    press_any_key()

def main() -> None:
    """Main entry point: launches Antigravity 2.0 Desktop Studio by default, or CLI if requested."""
    parser = argparse.ArgumentParser(description="Antigravity 2.0 - Desktop Studio & AI Projects")
    parser.add_argument("--gui", action="store_true", help="Launch Antigravity 2.0 Desktop Studio (Default)")
    parser.add_argument("--cli", action="store_true", help="Launch interactive Terminal TUI mode")
    parser.add_argument("--port", type=int, default=0, help="Port for Desktop GUI server")
    parser.add_argument("--no-window", action="store_true", help="Start GUI server without opening window")
    parser.add_argument("--bot", type=str, help="Launch chat directly with specified bot ID")
    parser.add_argument("--list", action="store_true", help="List all available bots and exit")
    parser.add_argument("--create", action="store_true", help="Launch create bot wizard directly")
    parser.add_argument("--export-all", action="store_true", help="Export all bots to .agents/rules/ and exit")
    args = parser.parse_args()

    # If no flags or --gui is specified, launch Desktop GUI Studio
    if not args.cli and not args.bot and not args.list and not args.create and not args.export_all:
        from gui import start_gui
        start_gui(port=args.port, open_window=not args.no_window)
        sys.exit(0)

    init_terminal()
    
    # Handle direct arguments
    if args.list:
        bots = load_bots()
        print(f"\n{BOLD}{CYAN}СПИСОК БОТОВ ANTIGRAVITY BOT HUB:{RESET}")
        for b in bots:
            print(f" • {b.get('emoji')} {BOLD}{b.get('name')}{RESET} ({b.get('id')}) - {b.get('tagline')}")
        sys.exit(0)
        
    if args.export_all:
        bots = load_bots()
        for b in bots:
            export_to_antigravity_rule(b)
        print(f"{GREEN}✔ Все боты экспортированы в .agents/rules/{RESET}")
        sys.exit(0)

    if args.create:
        screen_create_wizard()
        sys.exit(0)

    if args.bot:
        bot = get_bot(args.bot)
        if bot:
            run_chat_session(bot)
            sys.exit(0)
        else:
            print(f"{RED}Бот с ID '{args.bot}' не найден.{RESET}")
            sys.exit(1)

    # Main Interactive Menu Loop
    global CURRENT_BOT_ID
    while True:
        cur_bot = get_bot(CURRENT_BOT_ID)
        if not cur_bot:
            cur_bot = load_bots()[0]
            CURRENT_BOT_ID = cur_bot["id"]
            
        cur_emoji = cur_bot.get("emoji", "🤖")
        cur_name = cur_bot.get("name", "Бот")
        
        main_menu = [
            ("1", f"💬 Начать чат с активным ботом ({cur_emoji} {cur_name})", "Открыть интерактивную сессию диалога"),
            ("2", "🤖 Выбрать другого бота из каталога", "Переключить активного персонажа"),
            ("3", "➕ Создать нового бота для любой задачи", "Мастер создания уникального ИИ-специалиста"),
            ("4", "🎨 Кастомизировать смайлики и аватары", "Выбор паков, настроений, рамок и личных значков"),
            ("5", "🛠️ Управление ботами (Промпты, Юмор, Клоны)", "Редактирование, клонирование и удаление"),
            ("6", "🚀 Экспорт в Antigravity Rules & Scripts", "Связать с agy CLI или создать ярлыки запуска"),
            ("7", "📜 История диалогов", "Просмотр сохраненных бесед"),
            ("8", "❓ Справка и возможности", "О возможностях системы и командах"),
            ("0", "🚪 Выход", "Завершить работу утилиты")
        ]
        
        choice = select_menu_item(main_menu, header_title=f"ГЛАВНОЕ МЕНЮ [АКТИВЕН: {cur_emoji} {cur_name}]")
        
        if choice == 0:
            run_chat_session(cur_bot)
        elif choice == 1:
            screen_select_bot()
        elif choice == 2:
            screen_create_wizard()
        elif choice == 3:
            screen_emoji_customizer()
        elif choice == 4:
            screen_manage_bots()
        elif choice == 5:
            screen_export_hub()
        elif choice == 6:
            screen_history()
        elif choice == 7:
            screen_help()
        elif choice in (8, -1):
            clear_screen()
            print(f"\n{CYAN}Спасибо за использование Antigravity Bot Hub! Удачного кодинга! 🚀{RESET}\n")
            break

if __name__ == "__main__":
    main()
