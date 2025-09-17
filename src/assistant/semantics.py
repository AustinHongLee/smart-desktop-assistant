from __future__ import annotations
import re

# 你可以把常用同義詞放大：專案/行話/中英對照
SYNONYMS = {
    "預製圖": {"預製圖", "預製", "預製配管圖", "shop drawing", "prefab", "pre-fab"},
    "dwg": {"dwg", "autocad"},
    "管線": {"管線", "piping", "line", "line no", "line number"},
}

# 拆詞規則：數字+字母、底線、Dash、斜線、駝峰、中文逐字
SPLIT_RE = re.compile(r"[^\w\u4e00-\u9fff]+")

def split_mixed_token(tok: str) -> list[str]:
    # 駝峰切分 + 數字字母切開
    parts = re.findall(r"[A-Z]?[a-z]+|\d+|[A-Z]+(?=[A-Z][a-z]|$)|[\u4e00-\u9fff]", tok)
    return [p for p in parts if p]

def tokenize(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    raw = [t for t in SPLIT_RE.split(text) if t]
    out = []
    for t in raw:
        out.append(t.lower())
        out.extend(p.lower() for p in split_mixed_token(t))
    # 去重但保留順序
    seen, uniq = set(), []
    for t in out:
        if t not in seen:
            seen.add(t); uniq.append(t)
    return uniq

def expand_query(q: str) -> set[str]:
    toks = tokenize(q)
    expanded = set([q])
    for t in toks:
        if t in SYNONYMS:
            expanded |= SYNONYMS[t]
    # 若 query 本身就是一個同義詞的值，也拉回 key 的全集
    for k, vs in SYNONYMS.items():
        if any(t in vs for t in toks) or q in vs:
            expanded |= vs
            expanded.add(k)
    return {e for e in expanded if e.strip()}
