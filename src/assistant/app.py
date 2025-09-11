from __future__ import annotations
import argparse, sys
from assistant.memory.memory_manager import load_memory
from assistant.search.smart_search import SmartSearch
from assistant.actions.openers import run_action

def main():
    parser = argparse.ArgumentParser(description="Smart Desktop Assistant (MVP)")
    parser.add_argument("query", nargs="*", help="你要找什麼？(例如: GL-05 預製圖 308)")
    parser.add_argument("--top", type=int, default=8, help="最多顯示幾筆")
    args = parser.parse_args()

    query = " ".join(args.query).strip()
    if not query:
        print("請輸入關鍵詞，例如：python -m assistant GL-05 預製圖 308")
        sys.exit(0)

    items = load_memory()
    if not items:
        print("memory_data.json 是空的或找不到，先放幾個記憶點吧。")
        sys.exit(1)

    engine = SmartSearch(items)
    results = engine.search(query, top_k=args.top)

    if not results:
        print(f"找不到與「{query}」相關的項目。")
        sys.exit(0)

    print(f"\n🔎 查詢：「{query}」  → 顯示前 {len(results)} 筆")
    for i, (s, it) in enumerate(results, 1):
        desc = it.get("description") or "(無描述)"
        path = it.get("path") or ""
        print(f"{i:>2}. [{s:.3f}] {desc}  →  {path}")

    try:
        choice = input("\n要開哪一個？(輸入編號；直接 Enter 跳過)：").strip()
    except KeyboardInterrupt:
        print()
        sys.exit(0)

    if not choice:
        print("已略過開啟。")
        sys.exit(0)

    try:
        idx = int(choice)
        if not (1 <= idx <= len(results)):
            raise ValueError
    except ValueError:
        print("輸入的編號不合法。")
        sys.exit(1)

    score, chosen = results[idx - 1]
    ok = run_action(chosen.get("action") or "open_folder", chosen.get("path") or "")
    if ok:
        engine.learn_positive(query, chosen)
        print("✅ 已開啟，並記錄為正向回饋。")
    else:
        engine.learn_negative(query, chosen)
        print("⚠️ 開啟失敗（或路徑無效），已記錄為負向回饋。")

if __name__ == "__main__":
    main()
