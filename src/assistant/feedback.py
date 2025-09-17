from __future__ import annotations
import json, os
from .config import FEEDBACK_PATH

def _load() -> dict:
    if os.path.exists(FEEDBACK_PATH):
        with open(FEEDBACK_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"item_bias": {}, "token_bias": {}}

def _save(d: dict) -> None:
    with open(FEEDBACK_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def mark_item(path: str, positive: bool):
    data = _load()
    entry = data["item_bias"].setdefault(path, {"pos": 0, "neg": 0})
    if positive: entry["pos"] += 1
    else: entry["neg"] += 1
    _save(data)

def mark_tokens(tokens: list[str], positive: bool):
    data = _load()
    for t in tokens:
        e = data["token_bias"].setdefault(t, {"pos": 0, "neg": 0})
        if positive: e["pos"] += 1
        else: e["neg"] += 1
    _save(data)

def get_bias_for_item(path: str) -> float:
    d = _load()
    e = d["item_bias"].get(path)
    if not e: return 1.0
    # 簡單比值：正向越多→>1；負向越多→<1（帶平滑）
    return (1.0 + e["pos"]) / (1.0 + e["neg"])

def get_bias_for_tokens(tokens: list[str]) -> float:
    d = _load()
    pos = neg = 0
    for t in tokens:
        e = d["token_bias"].get(t)
        if e:
            pos += e["pos"]; neg += e["neg"]
    return (1.0 + pos) / (1.0 + neg)
