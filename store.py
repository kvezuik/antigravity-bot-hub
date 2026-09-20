"""
Antigravity 2.0 - Projects & Chats Store
Manages persistent projects, individual chats, custom names, icons, and message histories.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STORE_FILE = os.path.join(DATA_DIR, "store.json")

os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_STORE: Dict[str, Any] = {
    "active_project_id": "proj_default",
    "active_chat_id": "chat_default",
    "projects": [
        {
            "id": "proj_default",
            "name": "Основной проект",
            "icon": "📁",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    ],
    "chats": [
        {
            "id": "chat_default",
            "project_id": "proj_default",
            "name": "Новый диалог",
            "icon": "💬",
            "model": "gemini-3.8-flash-high",
            "effort": "high",
            "messages": [
                {
                    "role": "assistant",
                    "content": "Привет! Я ассистент Antigravity 2.0. Чем могу помочь по коду, архитектуре или задачам?",
                    "thoughts": "",
                    "time": time.strftime("%H:%M:%S")
                }
            ],
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
}


def load_store() -> Dict[str, Any]:
    if not os.path.exists(STORE_FILE):
        save_store(DEFAULT_STORE)
        return DEFAULT_STORE
    try:
        with open(STORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "projects" not in data or not data["projects"]:
                data["projects"] = DEFAULT_STORE["projects"]
            if "chats" not in data or not data["chats"]:
                data["chats"] = DEFAULT_STORE["chats"]
            if "active_project_id" not in data:
                data["active_project_id"] = data["projects"][0]["id"]
            if "active_chat_id" not in data:
                data["active_chat_id"] = data["chats"][0]["id"]
            return data
    except Exception:
        save_store(DEFAULT_STORE)
        return DEFAULT_STORE


def save_store(data: Dict[str, Any]) -> None:
    with open(STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ================= PROJECTS =================

def get_projects() -> List[Dict[str, Any]]:
    store = load_store()
    return store.get("projects", [])


def create_project(name: str, icon: str = "📁") -> Dict[str, Any]:
    store = load_store()
    proj_id = f"proj_{int(time.time() * 1000)}"
    new_proj = {
        "id": proj_id,
        "name": name.strip() or "Новый проект",
        "icon": icon.strip() or "📁",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    store["projects"].append(new_proj)
    store["active_project_id"] = proj_id

    # Automatically create initial chat for new project
    chat_id = f"chat_{int(time.time() * 1000)}"
    initial_chat = {
        "id": chat_id,
        "project_id": proj_id,
        "name": "Основной диалог",
        "icon": "💬",
        "model": "gemini-3.8-flash-high",
        "effort": "high",
        "messages": [
            {
                "role": "assistant",
                "content": f"Создан проект «{new_proj['name']}». Чем могу помочь?",
                "thoughts": "",
                "time": time.strftime("%H:%M:%S")
            }
        ],
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    store["chats"].append(initial_chat)
    store["active_chat_id"] = chat_id

    save_store(store)
    return new_proj


def rename_project(proj_id: str, new_name: str, new_icon: Optional[str] = None) -> Optional[Dict[str, Any]]:
    store = load_store()
    for p in store["projects"]:
        if p["id"] == proj_id:
            if new_name:
                p["name"] = new_name.strip()
            if new_icon:
                p["icon"] = new_icon.strip()
            save_store(store)
            return p
    return None


def delete_project(proj_id: str) -> bool:
    store = load_store()
    if len(store["projects"]) <= 1:
        return False  # Do not delete the last project

    store["projects"] = [p for p in store["projects"] if p["id"] != proj_id]
    store["chats"] = [c for c in store["chats"] if c["project_id"] != proj_id]

    if store["active_project_id"] == proj_id:
        store["active_project_id"] = store["projects"][0]["id"]
        # Find chats for new active project
        proj_chats = [c for c in store["chats"] if c["project_id"] == store["active_project_id"]]
        if proj_chats:
            store["active_chat_id"] = proj_chats[0]["id"]
        else:
            # Create a chat if project has none
            chat_id = f"chat_{int(time.time() * 1000)}"
            new_chat = {
                "id": chat_id,
                "project_id": store["active_project_id"],
                "name": "Новый диалог",
                "icon": "💬",
                "model": "gemini-3.8-flash-high",
                "effort": "high",
                "messages": [],
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            store["chats"].append(new_chat)
            store["active_chat_id"] = chat_id

    save_store(store)
    return True


# ================= CHATS =================

def get_chats(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    store = load_store()
    pid = project_id or store.get("active_project_id")
    return [c for c in store.get("chats", []) if c.get("project_id") == pid]


def get_chat(chat_id: str) -> Optional[Dict[str, Any]]:
    store = load_store()
    for c in store.get("chats", []):
        if c["id"] == chat_id:
            return c
    return None


def create_chat(project_id: str, name: str = "Новый диалог", icon: str = "💬", model: str = "gemini-3.8-flash-high") -> Dict[str, Any]:
    store = load_store()
    chat_id = f"chat_{int(time.time() * 1000)}"
    new_chat = {
        "id": chat_id,
        "project_id": project_id,
        "name": name.strip() or "Новый диалог",
        "icon": icon.strip() or "💬",
        "model": model or "gemini-3.8-flash-high",
        "effort": "high",
        "messages": [
            {
                "role": "assistant",
                "content": f"Диалог «{name.strip()}» открыт. Чем могу помочь?",
                "thoughts": "",
                "time": time.strftime("%H:%M:%S")
            }
        ],
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    store["chats"].append(new_chat)
    store["active_chat_id"] = chat_id
    save_store(store)
    return new_chat


def update_chat(chat_id: str, name: Optional[str] = None, icon: Optional[str] = None, model: Optional[str] = None, effort: Optional[str] = None) -> Optional[Dict[str, Any]]:
    store = load_store()
    for c in store["chats"]:
        if c["id"] == chat_id:
            if name is not None:
                c["name"] = name.strip()
            if icon is not None:
                c["icon"] = icon.strip()
            if model is not None:
                c["model"] = model.strip()
            if effort is not None:
                c["effort"] = effort.strip()
            save_store(store)
            return c
    return None


def add_message_to_chat(chat_id: str, role: str, content: str, thoughts: str = "") -> None:
    store = load_store()
    for c in store["chats"]:
        if c["id"] == chat_id:
            c.setdefault("messages", []).append({
                "role": role,
                "content": content,
                "thoughts": thoughts,
                "time": time.strftime("%H:%M:%S")
            })
            save_store(store)
            return


def clear_chat_history(chat_id: str) -> None:
    store = load_store()
    for c in store["chats"]:
        if c["id"] == chat_id:
            c["messages"] = [
                {
                    "role": "assistant",
                    "content": "Диалог очищен. Готов к новым вопросам!",
                    "thoughts": "",
                    "time": time.strftime("%H:%M:%S")
                }
            ]
            save_store(store)
            return


def delete_chat(chat_id: str) -> bool:
    store = load_store()
    active_pid = store.get("active_project_id")
    proj_chats = [c for c in store["chats"] if c.get("project_id") == active_pid]
    if len(proj_chats) <= 1 and any(c["id"] == chat_id for c in proj_chats):
        # Don't delete the only chat in project, just clear it
        clear_chat_history(chat_id)
        return True

    store["chats"] = [c for c in store["chats"] if c["id"] != chat_id]
    if store.get("active_chat_id") == chat_id:
        remaining = [c for c in store["chats"] if c.get("project_id") == active_pid]
        if remaining:
            store["active_chat_id"] = remaining[0]["id"]
    save_store(store)
    return True
