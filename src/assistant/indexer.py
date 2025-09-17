from __future__ import annotations
import os, json, time, stat
from typing import Iterator
from .config import MAPPING_PATH, load_user_config

def iter_files() -> Iterator[dict]:
    cfg = load_user_config()
    roots = [p for p in cfg.roots if os.path.isdir(p)]
    exclude_dirs = set(n.lower() for n in cfg.exclude_dir_names)
    exclude_exts = set(e.lower() for e in cfg.exclude_file_exts)

    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            # 過濾資料夾
            dirnames[:] = [d for d in dirnames if d.lower() not in exclude_dirs]
            # 這些目錄通常權限奇怪，跳過
            try:
                if not os.access(dirpath, os.R_OK):
                    continue
            except Exception:
                continue

            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext in exclude_exts:
                    continue
                full = os.path.join(dirpath, fn)
                try:
                    st = os.stat(full)
                    if stat.S_ISDIR(st.st_mode):
                        continue
                except Exception:
                    continue
                yield {
                    "path": full,
                    "name": fn,
                    "ext": ext,
                    "size": st.st_size,
                    "mtime": st.st_mtime,
                    "parent": dirpath,
                }

def build_mapping() -> dict:
    items = list(iter_files())
    # 建簡易倒排索引的基礎：先不做 heavy TF-IDF，之後可擴
    mapping = {
        "version": 1,
        "generated_at": time.time(),
        "count": len(items),
        "items": items
    }
    return mapping

def ensure_index(force: bool = False) -> str:
    from .config import mapping_is_stale
    if force or mapping_is_stale():
        data = build_mapping()
        with open(MAPPING_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    return MAPPING_PATH
