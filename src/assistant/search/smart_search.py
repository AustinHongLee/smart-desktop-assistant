# -*- coding: utf-8 -*-
"""
SmartSearch (改良版)
- 將偏置檔搬到使用者目錄 ~/.smart_desktop_assistant/smartsearch_bias.json
- 搜尋時使用單次載入的偏置快照（避免每筆結果重讀檔）
- 基本語意支援：斷詞、同義詞展開、簡單打分（字串重合 + 新鮮度 + 路徑深度 + 副檔名提示 + 偏置）
"""
from __future__ import annotations
import os
import re
import json
import math
import time
from typing import List, Tuple, Dict, Any

# -------------------------------
# 路徑與偏置資料位置（使用者目錄）
# -------------------------------
APP_DIR = os.path.join(os.path.expanduser("~"), ".smart_desktop_assistant")
os.makedirs(APP_DIR, exist_ok=True)
BIAS_PATH = os.path.join(APP_DIR, "smartsearch_bias.json")

# -------------------------------
# 簡單的同義詞庫（可自行擴充）
# -------------------------------
SYNONYMS: Dict[str, set[str]] = {
    "預製圖": {"預製圖", "預製", "預製配管圖", "shop drawing", "prefab", "pre-fab"},
    "dwg": {"dwg", "autocad"},
    "管線": {"管線", "piping", "line", "line no", "line number"},
}

# token 切分（含駝峰、數字/字母分離、中文逐字）
_SPLIT_RE = re.compile(r"[^\w\u4e00-\u9fff]+")
_CAMEL_RE = re.compile(r"[A-Z]?[a-z]+|\d+|[A-Z]+(?=[A-Z][a-z]|$)|[\u4e00-\u9fff]")

def _split_mixed_token(tok: str) -> List[str]:
    return [p for p in _CAMEL_RE.findall(tok) if p]

def tokenize(text: str) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    raw = [t for t in _SPLIT_RE.split(text) if t]
    out: List[str] = []
    for t in raw:
        out.append(t.lower())
        out.extend(p.lower() for p in _split_mixed_token(t))
    # 去重保序
    seen, uniq = set(), []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq

def expand_query(q: str) -> List[str]:
    toks = tokenize(q)
    expanded = set([q])
    for t in toks:
        if t in SYNONYMS:
            expanded |= SYNONYMS[t]
    for k, vs in SYNONYMS.items():
        if any(t in vs for t in toks) or q in vs:
            expanded |= vs
            expanded.add(k)
    return [e for e in expanded if e.strip()]

# -------------------------------
# 偏置：讀寫與快取
# -------------------------------
def _load_bias_all() -> Dict[str, Dict[str, Dict[str, int]]]:
    if os.path.exists(BIAS_PATH):
        try:
            with open(BIAS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 基本結構防禦
            if not isinstance(data, dict):
                raise ValueError
            data.setdefault("item_bias", {})
            data.setdefault("token_bias", {})
            return data
        except Exception:
            pass
    return {"item_bias": {}, "token_bias": {}}

def _save_bias_all(d: Dict[str, Dict[str, Dict[str, int]]]) -> None:
    tmp = BIAS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, BIAS_PATH)

def _get_item_bias_from_snapshot(snapshot: dict, path: str) -> float:
    e = snapshot.get("item_bias", {}).get(path)
    if not e:
        return 1.0
    return (1.0 + int(e.get("pos", 0))) / (1.0 + int(e.get("neg", 0)))

def _get_tokens_bias_from_snapshot(snapshot: dict, tokens: List[str]) -> float:
    tb = snapshot.get("token_bias", {})
    pos = neg = 0
    for t in tokens:
        e = tb.get(t)
        if e:
            pos += int(e.get("pos", 0))
            neg += int(e.get("neg", 0))
    return (1.0 + pos) / (1.0 + neg)

def _mark_item(path: str, positive: bool) -> None:
    data = _load_bias_all()
    ib = data.setdefault("item_bias", {})
    entry = ib.setdefault(path, {"pos": 0, "neg": 0})
    if positive:
        entry["pos"] = int(entry["pos"]) + 1
    else:
        entry["neg"] = int(entry["neg"]) + 1
    _save_bias_all(data)

def _mark_tokens(tokens: List[str], positive: bool) -> None:
    data = _load_bias_all()
    tb = data.setdefault("token_bias", {})
    for t in tokens:
        e = tb.setdefault(t, {"pos": 0, "neg": 0})
        if positive:
            e["pos"] = int(e["pos"]) + 1
        else:
            e["neg"] = int(e["neg"]) + 1
    _save_bias_all(data)

# -------------------------------
# 打分輔助
# -------------------------------
def _freshness_boost(path: str) -> float:
    """根據檔案最近修改時間給輕微加權（不存在或錯誤則 1.0）"""
    try:
        mtime = os.path.getmtime(path)
        days = max(0.0, (time.time() - mtime) / 86400.0)
        return 1.0 + 0.25 * math.exp(-days / 30.0)  # 30 天半衰期，最高 +25%
    except Exception:
        return 1.0

def _depth_penalty(path: str) -> float:
    """路徑過深給一點懲罰，避免奇怪 cache 排很前"""
    depth = path.count(os.sep)
    return 1.0 / (1.0 + max(0, depth - 6) * 0.08)

def _ext_bonus(path: str, tokens: List[str]) -> float:
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    if not ext:
        return 1.0
    hints = {"dwg": 1.2, "pdf": 1.1, "xlsx": 1.05}
    return hints.get(ext, 1.1) if ext in tokens else 1.0

def _text_haystack_of(item: dict) -> str:
    desc = item.get("description") or ""
    path = item.get("path") or ""
    name = item.get("name") or os.path.basename(path)
    parent = os.path.dirname(path) if path else ""
    return f"{desc} {name} {path} {parent}".lower()

def _base_overlap_score(tokens: List[str], hay: str) -> float:
    score = 0.0
    for t in tokens:
        if not t:
            continue
        if t in hay:
            score += hay.count(t) * 1.0
    return score

# -------------------------------
# SmartSearch 主體
# -------------------------------
class SmartSearch:
    """
    與你原始程式相容的介面：
      - SmartSearch(items)
      - search(query, top_k=10) -> List[(score, item)]
      - learn_positive(query, item) / learn_negative(query, item)
    items: 你 load_memory() 回來的 list[dict]，需含至少 description/path/action 等欄位
    """
    def __init__(self, items: List[Dict[str, Any]]):
        self.items = items or []

    def search(self, query: str, top_k: int = 10) -> List[Tuple[float, Dict[str, Any]]]:
        # 1) 取得一次性的偏置快照（避免 O(n) 讀檔）
        fb_snapshot = _load_bias_all()

        # 2) 查詢斷詞 + 同義展開
        expanded = expand_query(query)
        query_tokens = tokenize(" ".join(expanded))  # 合併後再斷一次
        token_bias = _get_tokens_bias_from_snapshot(fb_snapshot, query_tokens)

        results: List[Tuple[float, Dict[str, Any]]] = []
        for it in self.items:
            hay = _text_haystack_of(it)
            base = _base_overlap_score(query_tokens, hay)
            if base <= 0:
                continue

            path = (it.get("path") or "").strip()
            s = base
            if path:
                s *= _freshness_boost(path)
                s *= _depth_penalty(path)
                s *= _ext_bonus(path, query_tokens)
                s *= _get_item_bias_from_snapshot(fb_snapshot, path)

            s *= token_bias
            results.append((s, it))

        results.sort(key=lambda x: x[0], reverse=True)
        return results[:top_k]

    def learn_positive(self, query: str, item: Dict[str, Any]) -> None:
        _mark_item((item.get("path") or ""), positive=True)
        _mark_tokens(tokenize(query), positive=True)

    def learn_negative(self, query: str, item: Dict[str, Any]) -> None:
        _mark_item((item.get("path") or ""), positive=False)
        _mark_tokens(tokenize(query), positive=False)
