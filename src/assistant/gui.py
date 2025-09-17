from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox

# === 新增：用我們自己的索引與搜尋 ===
from assistant.indexer import ensure_index
from assistant.search_engine import SearchEngine
from assistant.semantics import tokenize
from assistant.feedback import mark_item, mark_tokens

# 仍然沿用你原本的開啟動作
from assistant.actions.openers import run_action


def run_gui():
    # 1) 確保電腦索引存在（首跑會建 Computer_mapping.json）
    ensure_index(force=False)

    engine = SearchEngine()

    root = tk.Tk()
    root.title("Smart Desktop Assistant")

    frame = ttk.Frame(root, padding=10)
    frame.pack(fill="both", expand=True)

    query_var = tk.StringVar()
    entry = ttk.Entry(frame, textvariable=query_var)
    entry.pack(fill="x")
    entry.focus()

    # 結果清單
    cols = ("score", "name", "path")
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
    for c, w in zip(cols, (80, 240, 520)):
        tree.heading(c, text=c)
        tree.column(c, width=w, anchor="w")
    tree.pack(fill="both", expand=True, pady=6)

    status = tk.StringVar(value="就緒")
    ttk.Label(frame, textvariable=status).pack(anchor="w")

    # 在 tree 上掛結果
    tree.results = []

    def search():
        q = query_var.get().strip()
        for i in tree.get_children():
            tree.delete(i)
        tree.results.clear()
        if not q:
            status.set("請輸入關鍵詞")
            return
        results = engine.search(q, top_k=20)
        if not results:
            status.set(f"找不到與「{q}」相關的項目")
            return
        tree.results = results
        for s, it in results:
            tree.insert("", "end", values=(f"{s:.3f}", it.get("name",""), it.get("path","")))
        status.set(f"🔎 查詢：「{q}」 → 顯示 {len(results)} 筆")

    def open_selected(event=None):
        sel = tree.selection()
        if not sel:
            return
        idx = tree.index(sel[0])
        score, chosen = tree.results[idx]
        ok = run_action(chosen.get("action") or "open_folder", chosen.get("path") or "")
        if ok:
            # 預設開啟算正向一次
            mark_item(chosen.get("path",""), positive=True)
            mark_tokens(tokenize(query_var.get()), positive=True)
            messagebox.showinfo("已開啟", "✅ 已開啟並記錄正向回饋")
            status.set("已開啟（+正向）")
        else:
            mark_item(chosen.get("path",""), positive=False)
            mark_tokens(tokenize(query_var.get()), positive=False)
            messagebox.showwarning("開啟失敗", "⚠️ 已記錄負向回饋")
            status.set("開啟失敗（+負向）")

    def mark_positive():
        sel = tree.selection()
        if not sel: return
        idx = tree.index(sel[0])
        _, chosen = tree.results[idx]
        mark_item(chosen.get("path",""), positive=True)
        mark_tokens(tokenize(query_var.get()), positive=True)
        status.set("標記 O（正向）完成")

    def mark_negative():
        sel = tree.selection()
        if not sel: return
        idx = tree.index(sel[0])
        _, chosen = tree.results[idx]
        mark_item(chosen.get("path",""), positive=False)
        mark_tokens(tokenize(query_var.get()), positive=False)
        status.set("標記 X（負向）完成")

    # 按鈕列
    btns = ttk.Frame(frame)
    btns.pack(fill="x", pady=6)
    ttk.Button(btns, text="搜尋", command=search).pack(side="left")
    ttk.Button(btns, text="開啟（雙擊也可）", command=open_selected).pack(side="left", padx=8)
    ttk.Button(btns, text="O（正向）", command=mark_positive).pack(side="left")
    ttk.Button(btns, text="X（負向）", command=mark_negative).pack(side="left")

    # 快捷鍵
    tree.bind("<Double-Button-1>", open_selected)
    root.bind("<Return>", lambda e: search())
    root.bind("o", lambda e: mark_positive())
    root.bind("x", lambda e: mark_negative())

    root.mainloop()


if __name__ == "__main__":
    run_gui()
