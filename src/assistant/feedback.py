from __future__ import annotations
import json, os
from .config import FEEDBACK_PATH

def load_all() -> dict:
    if os.path.exists(FEEDBACK_PATH):
        with open(FEEDBACK_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"item_bias": {}, "token_bias": {}}

def save_all(d: dict) -> None:
    with open(FEEDBACK_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def mark_item(path: str, positive: bool):
    data = load_all()
    entry = data.setdefault("item_bias", {}).setdefault(path, {"pos": 0, "neg": 0})
    if positive: entry["pos"] += 1
    else: entry["neg"] += 1
    save_all(data)

def mark_tokens(tokens: list[str], positive: bool):
    data = load_all()
    tb = data.setdefault("token_bias", {})
    for t in tokens:
        e = tb.setdefault(t, {"pos": 0, "neg": 0})
        if positive: e["pos"] += 1
        else: e["neg"] += 1
    save_all(data)

def get_bias_for_item_from_snapshot(snapshot: dict, path: str) -> float:
    e = snapshot.get("item_bias", {}).get(path)
    if not e: return 1.0
    return (1.0 + e.get("pos", 0)) / (1.0 + e.get("neg", 0))

def get_bias_for_tokens_from_snapshot(snapshot: dict, tokens: list[str]) -> float:
    tb = snapshot.get("token_bias", {})
    pos = neg = 0
    for t in tokens:
        e = tb.get(t)
        if e:
            pos += e.get("pos", 0)
            neg += e.get("neg", 0)
    return (1.0 + pos) / (1.0 + neg)
