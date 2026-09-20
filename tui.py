"""
Antigravity Bot Hub - Cross-Platform Terminal UI Module (Linux & Windows)
Supports ANSI styling, 256-color palettes, box-drawing, and arrow-key navigation.
"""

import sys
import os
import re
import unicodedata
from typing import List, Tuple, Optional, Callable, Any

# ANSI Color Palette
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# 256-Color Neon Accents
CYAN = "\033[38;5;51m"
PURPLE = "\033[38;5;141m"
PINK = "\033[38;5;206m"
YELLOW = "\033[38;5;220m"
GREEN = "\033[38;5;48m"
BLUE = "\033[38;5;75m"
RED = "\033[38;5;196m"
GRAY = "\033[38;5;244m"
DARK_GRAY = "\033[38;5;238m"
WHITE = "\033[38;5;255m"

BG_HIGHLIGHT = "\033[48;5;236m"
BG_PURPLE = "\033[48;5;55m"
BG_CYAN = "\033[48;5;24m"

def init_terminal() -> None:
    """Initialize terminal for proper ANSI code and UTF-8 support on Windows and Linux."""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            # ENABLE_PROCESSED_OUTPUT = 0x0001
            # ENABLE_WRAP_AT_EOL_OUTPUT = 0x0002
            h_out = kernel32.GetStdHandle(-11) # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(h_out, ctypes.byref(mode))
            kernel32.SetConsoleMode(h_out, mode.value | 0x0004 | 0x0001)
            os.system('') # Fallback trigger for cmd ANSI
        except Exception:
            pass
            
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass

def clear_screen() -> None:
    """Clear terminal screen in cross-platform way."""
    if os.name == "nt":
        os.system("cls")
    else:
        # Clear screen and scrollback buffer
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from string."""
    return re.sub(r'\033\[[0-9;]*[a-zA-Z]', '', text)

def char_width(c: str) -> int:
    """Return display column width of a single unicode character."""
    if c in ('\u200d', '\ufe0f', '\u200b'):
        return 0
    w = unicodedata.east_asian_width(c)
    if w in ('W', 'F'):
        return 2
    return 1

def str_width(text: str) -> int:
    """Calculate terminal display width of text taking emojis and ANSI into account."""
    clean = strip_ansi(text)
    return sum(char_width(c) for c in clean)

def pad_str(text: str, width: int, align: str = "left") -> str:
    """Pad string to target display width respecting ANSI and double-width chars."""
    cur_w = str_width(text)
    if cur_w >= width:
        return text
    diff = width - cur_w
    if align == "right":
        return (" " * diff) + text
    elif align == "center":
        left = diff // 2
        right = diff - left
        return (" " * left) + text + (" " * right)
    else:
        return text + (" " * diff)

def print_header(title: str = "ANTIGRAVITY BOT HUB", subtitle: str = "Генератор и Мастерская Grok-Ботов") -> None:
    """Print glowing cyber banner header."""
    init_terminal()
    width = 68
    
    banner = f"""
{PURPLE}╭{'─' * (width - 2)}╮
│{CYAN}{BOLD}{pad_str('✦  ' + title.upper() + '  ✦', width - 2, 'center')}{RESET}{PURPLE}│
│{GRAY}{pad_str(subtitle, width - 2, 'center')}{RESET}{PURPLE}│
╰{'─' * (width - 2)}╯{RESET}"""
    print(banner)

def print_box(
    lines: List[str],
    title: str = "",
    border_color: str = PURPLE,
    width: int = 68,
    align: str = "left"
) -> None:
    """Render a card with rounded corners and custom styling."""
    title_str = f" {BOLD}{WHITE}{title}{RESET}{border_color} " if title else ""
    t_width = str_width(title) + 2 if title else 0
    rem_w = max(0, width - 2 - t_width)
    top = f"{border_color}╭─{title_str}{'─' * rem_w}╮{RESET}"
    bottom = f"{border_color}╰{'─' * (width - 2)}╯{RESET}"
    
    print(top)
    for line in lines:
        padded = pad_str(line, width - 4, align)
        print(f"{border_color}│{RESET} {padded} {border_color}│{RESET}")
    print(bottom)

def print_divider(width: int = 68, char: str = "─", color: str = DARK_GRAY) -> None:
    """Print horizontal line divider."""
    print(f"{color}{char * width}{RESET}")

def read_key() -> str:
    """
    Cross-platform single keypress reader.
    Returns: 'UP', 'DOWN', 'LEFT', 'RIGHT', 'ENTER', 'ESC', 'BACKSPACE',
    or the single character string ('1', 'q', etc.).
    """
    if sys.platform == "win32":
        import msvcrt
        ch = msvcrt.getch()
        if ch in (b'\x00', b'\xe0'):
            sub = msvcrt.getch()
            if sub == b'H':
                return "UP"
            elif sub == b'P':
                return "DOWN"
            elif sub == b'K':
                return "LEFT"
            elif sub == b'M':
                return "RIGHT"
            return "UNKNOWN"
        elif ch in (b'\r', b'\n'):
            return "ENTER"
        elif ch == b'\x1b':
            return "ESC"
        elif ch == b'\x08':
            return "BACKSPACE"
        else:
            try:
                return ch.decode("utf-8", errors="ignore")
            except Exception:
                return ""
    else:
        # POSIX (Linux, macOS, BSD)
        import tty
        import termios
        import select
        
        if not sys.stdin.isatty():
            line = sys.stdin.readline()
            return line.strip()
            
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch1 = sys.stdin.read(1)
            if ch1 == '\x1b':
                # Check if more characters are queued (escape sequence)
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    ch2 = sys.stdin.read(1)
                    if ch2 == '[':
                        ch3 = sys.stdin.read(1)
                        if ch3 == 'A':
                            return "UP"
                        elif ch3 == 'B':
                            return "DOWN"
                        elif ch3 == 'C':
                            return "RIGHT"
                        elif ch3 == 'D':
                            return "LEFT"
                return "ESC"
            elif ch1 in ('\r', '\n'):
                return "ENTER"
            elif ch1 in ('\x7f', '\x08'):
                return "BACKSPACE"
            elif ch1 == '\x03': # Ctrl+C
                raise KeyboardInterrupt()
            return ch1
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def select_menu_item(
    items: List[Tuple[str, str, str]], # [(key, title, description)]
    header_title: str = "ГЛАВНОЕ МЕНЮ",
    active_idx: int = 0,
    width: int = 68
) -> int:
    """
    Interactive menu selector with Arrow-Key navigation, number shortcuts, and graceful fallback.
    Returns index of selected item, or -1 on Escape/Quit.
    """
    # Check if we are in interactive mode
    is_interactive = sys.stdin.isatty()
    
    if not is_interactive:
        # Fallback non-raw mode
        print(f"\n{PURPLE}=== {header_title} ==={RESET}")
        for idx, (key, title, desc) in enumerate(items):
            print(f"[{idx + 1}] {title} - {desc}")
        try:
            choice = input(f"{CYAN}Выберите номер [1-{len(items)}]: {RESET}").strip()
            if choice.isdigit():
                val = int(choice) - 1
                if 0 <= val < len(items):
                    return val
            return 0
        except (EOFError, KeyboardInterrupt):
            return -1

    curr_idx = active_idx
    total = len(items)

    while True:
        clear_screen()
        print_header("ANTIGRAVITY BOT HUB", "Генератор и Мастерская Grok-Ботов")
        
        # Render menu box
        print(f"{PURPLE}╭─ {BOLD}{WHITE}{header_title}{RESET}{PURPLE} {'─' * max(0, width - str_width(header_title) - 6)}╮{RESET}")
        
        for idx, (shortcut, title, desc) in enumerate(items):
            is_active = (idx == curr_idx)
            num_str = f"[{idx + 1}]"
            
            if is_active:
                cursor = f"{YELLOW}▶{RESET}"
                line_title = f"{BG_HIGHLIGHT}{CYAN}{BOLD} {cursor} {num_str} {title}{RESET}"
                print(f"{PURPLE}│{RESET} {pad_str(line_title, width - 4)} {PURPLE}│{RESET}")
                if desc:
                    line_desc = f"{BG_HIGHLIGHT}{GRAY}      ↳ {desc}{RESET}"
                    print(f"{PURPLE}│{RESET} {pad_str(line_desc, width - 4)} {PURPLE}│{RESET}")
            else:
                cursor = " "
                line_title = f"{WHITE}  {num_str} {title}{RESET}"
                print(f"{PURPLE}│{RESET} {pad_str(line_title, width - 4)} {PURPLE}│{RESET}")
                if desc:
                    line_desc = f"{DARK_GRAY}      ↳ {desc}{RESET}"
                    print(f"{PURPLE}│{RESET} {pad_str(line_desc, width - 4)} {PURPLE}│{RESET}")

        print(f"{PURPLE}╰{'─' * (width - 2)}╯{RESET}")
        
        # Navigation hints
        hints = f"{GRAY}Навигация: {CYAN}↑/↓{GRAY} или цифры {CYAN}[1-{total}]{GRAY} | {GREEN}Enter{GRAY} выбор | {RED}Esc/Q{GRAY} выход{RESET}"
        print(f" {hints}\n")
        
        key = read_key()
        
        if key == "UP":
            curr_idx = (curr_idx - 1) % total
        elif key == "DOWN":
            curr_idx = (curr_idx + 1) % total
        elif key == "ENTER":
            return curr_idx
        elif key in ("ESC", "q", "Q"):
            return -1
        elif key.isdigit():
            val = int(key)
            if 1 <= val <= total:
                return val - 1

def prompt_text(label: str, default: str = "", help_text: str = "") -> str:
    """Prompt user for text with clean styling and default fallback."""
    if help_text:
        print(f"{DARK_GRAY}ℹ {help_text}{RESET}")
    def_str = f" {DARK_GRAY}[{default}]{RESET}" if default else ""
    prompt = f"{CYAN}{BOLD}▸ {label}{def_str}: {RESET}"
    
    try:
        val = input(prompt).strip()
        return val if val else default
    except (KeyboardInterrupt, EOFError):
        return default

def prompt_slider(label: str, min_v: int = 0, max_v: int = 100, default: int = 50) -> int:
    """Prompt user for a numeric value with bounds checking."""
    prompt = f"{CYAN}{BOLD}▸ {label} [{min_v}-{max_v}%] (По умолч. {default}%): {RESET}"
    try:
        val = input(prompt).strip()
        if not val:
            return default
        num = int(val)
        return max(min_v, min(max_v, num))
    except Exception:
        return default

def press_any_key(msg: str = "Нажмите любую клавишу для продолжения...") -> None:
    """Wait for a single keypress before proceeding."""
    print(f"\n{GRAY}{msg}{RESET}", end="", flush=True)
    try:
        read_key()
    except Exception:
        input()
    print()
