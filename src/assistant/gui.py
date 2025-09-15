from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from assistant.memory.memory_manager import load_memory
from assistant.search.smart_search import SmartSearch
from assistant.actions.openers import run_action


def run_gui():
    items = load_memory()
    if not items:
        messagebox.showinfo("提示", "memory_data.json 是空的或找不到，先放幾個記憶點吧。")
        return

    engine = SmartSearch(items)

    root = tk.Tk()
    root.title("Smart Desktop Assistant")

    frame = ttk.Frame(root, padding=10)
    frame.pack(fill="both", expand=True)

    query_var = tk.StringVar()
    entry = ttk.Entry(frame, textvariable=query_var)
    entry.pack(fill="x")
    entry.focus()

    result_list = tk.Listbox(frame, height=10)
    result_list.pack(fill="both", expand=True, pady=5)

    def search():
        q = query_var.get().strip()
        result_list.delete(0, tk.END)
        if not q:
            return
        results = engine.search(q, top_k=10)
        result_list.results = results
        for score, it in results:
            desc = it.get("description") or "(無描述)"
            result_list.insert(tk.END, f"{score:.3f} {desc}")

    def open_selected(event=None):
        selection = result_list.curselection()
        if not selection:
            return
        idx = selection[0]
        score, chosen = result_list.results[idx]
        ok = run_action(chosen.get("action") or "open_folder", chosen.get("path") or "")
        if ok:
            engine.learn_positive(query_var.get(), chosen)
            messagebox.showinfo("已開啟", "✅ 已開啟，並記錄為正向回饋。")
        else:
            engine.learn_negative(query_var.get(), chosen)
            messagebox.showwarning("開啟失敗", "⚠️ 開啟失敗（或路徑無效），已記錄為負向回饋。")

    btn = ttk.Button(frame, text="搜尋", command=search)
    btn.pack(pady=5)

    result_list.bind("<Double-Button-1>", open_selected)

    root.mainloop()


if __name__ == "__main__":
    run_gui()
