from __future__ import annotations
import json, os, math, time
from typing import List, Tuple, Dict, Any
from .config import MAPPING_PATH
from .semantics import tokenize, expand_query
from .feedback import get_bias_for_item, get_bias_for_tokens

def _load_mapping() -> dict:
    if not os.path.exists(MAPPING_PATH):
        return {"items": []}
    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _base_score(tokens: list[str], item: dict) -> float:
    # 名稱/路徑 的 token overlap
    hay = (item.get("name","") + " " + item.get("path","") + " " + item.get("parent","")).lower()
    score = 0.0
    for t in tokens:
        if t in hay:
            # 出現越多次略加分
            score += hay.count(t) * 1.0
    return score

def _freshness_boost(item: dict) -> float:
    # 最近 30 天：+30% → 指數衰減
    days = max(0.0, (time.time() - item.get("mtime", 0)) / 86400.0)
    return 1.0 + 0.3 * math.exp(-days / 30.0)

def _depth_penalty(item: dict) -> float:
    # 太深的路徑扣些分（避免奇怪 cache）
    depth = item.get("path","").count(os.sep)
    return 1.0 / (1.0 + max(0, depth - 6) * 0.08)

def _ext_bonus(item: dict, tokens: list[str]) -> float:
    # 若 query 有明確副檔名或類型線索（如 dwg, pdf），給些加成
    ext = (item.get("ext") or "").lstrip(".")
    hints = {"dwg": 1.2, "pdf": 1.1, "xlsx": 1.05}
    for t in tokens:
        if t == ext:
            return hints.get(ext, 1.1)
    return 1.0

class SearchEngine:
    def __init__(self):
        self.mapping = _load_mapping()
        self.items = self.mapping.get("items", [])

    def search(self, query: str, top_k: int = 15) -> List[Tuple[float, Dict[str, Any]]]:
        expanded = expand_query(query)
        query_tokens = tokenize(" ".join(expanded))
        token_bias = get_bias_for_tokens(query_tokens)

        scored: List[Tuple[float, Dict[str, Any]]] = []
        for it in self.items:
            base = _base_score(query_tokens, it)
            if base <= 0:
                continue
            s = base
            s *= _freshness_boost(it)
            s *= _depth_penalty(it)
            s *= _ext_bonus(it, query_tokens)
            s *= get_bias_for_item(it.get("path",""))
            s *= token_bias
            scored.append((s, it))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_k]
