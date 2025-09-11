from __future__ import annotations
import json, os
from typing import List, Dict, Any

BASE_DIR = os.path.dirname(__file__)
MEMORY_JSON = os.path.join(BASE_DIR, "memory_data.json")

def load_memory() -> List[Dict[str, Any]]:
    if not os.path.exists(MEMORY_JSON):
        return []
    with open(MEMORY_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for it in data:
        out.append({
            "trigger": list(it.get("trigger") or []),
            "description": it.get("description") or "",
            "path": it.get("path") or "",
            "action": it.get("action") or "open_folder"
        })
    return out

def save_memory(items: List[Dict[str, Any]]) -> None:
    with open(MEMORY_JSON, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
