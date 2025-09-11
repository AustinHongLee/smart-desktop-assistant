from __future__ import annotations
import os, json, re
from difflib import SequenceMatcher
from typing import List, Dict, Tuple, Any
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
BIAS_FILE = DATA_DIR / "learn_bias.json"

def _tokenize(s: str) -> List[str]:
    s = (s or "").lower()
    tokens = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", s)
    return [t for t in tokens if t.strip()]

def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def _overlap(q_tokens: List[str], text_tokens: List[str]) -> float:
    if not q_tokens or not text_tokens:
        return 0.0
    qs = set(q_tokens); ts = set(text_tokens)
    return len(qs & ts) / max(1, len(qs))

def _load_bias() -> Dict[str, float]:
    if BIAS_FILE.exists():
        try:
            return json.load(open(BIAS_FILE, "r", encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_bias(bias: Dict[str, float]):
    with open(BIAS_FILE, "w", encoding="utf-8") as f:
        json.dump(bias, f, ensure_ascii=False, indent=2)

class SmartSearch:
    def __init__(self, items: List[Dict[str, Any]]):
        self.items = items
        self.bias = _load_bias()
        self.corpus: List[Tuple[str, List[str]]] = []
        for it in self.items:
            text = " ".join((it.get("description") or "", " ".join(it.get("trigger") or []), it.get("path") or ""))
            self.corpus.append((text, _tokenize(text)))

    def search(self, query: str, top_k: int = 10) -> List[Tuple[float, Dict[str, Any]]]:
        q = query.strip()
        q_tokens = _tokenize(q)
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for it, (full_text, text_tokens) in zip(self.items, self.corpus):
            r1 = _ratio(q, full_text)
            r2 = _overlap(q_tokens, text_tokens)
            key = it.get("path") or it.get("description") or ""
            b  = self.bias.get(key, 0.0)
            score = 0.6 * r1 + 0.35 * r2 + 0.05 * b
            scored.append((score, it))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_k]

    def learn_positive(self, query: str, chosen: Dict[str, Any]):
        key = chosen.get("path") or chosen.get("description") or ""
        self.bias[key] = min(self.bias.get(key, 0.0) + 1.0, 10.0)
        _save_bias(self.bias)

    def learn_negative(self, query: str, wrong: Dict[str, Any]):
        key = wrong.get("path") or wrong.get("description") or ""
        self.bias[key] = max(self.bias.get(key, 0.0) - 0.5, -10.0)
        _save_bias(self.bias)
