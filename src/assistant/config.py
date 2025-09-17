from __future__ import annotations
import os, json, time
from dataclasses import dataclass, asdict

APP_DIR = os.path.join(os.path.expanduser("~"), ".smart_desktop_assistant")
os.makedirs(APP_DIR, exist_ok=True)

MAPPING_PATH = os.path.join(APP_DIR, "Computer_mapping.json")
FEEDBACK_PATH = os.path.join(APP_DIR, "feedback.json")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

DEFAULT_ROOTS = [
    os.path.join(os.path.expanduser("~"), "Desktop"),
    os.path.join(os.path.expanduser("~"), "Documents"),
    os.path.join(os.path.expanduser("~"), "Downloads"),
]

EXCLUDE_DIR_NAMES = {
    "Windows", "Program Files", "Program Files (x86)", "ProgramData",
    "AppData", "$Recycle.Bin", "System Volume Information",
    ".git", "__pycache__", ".venv", "venv", "node_modules", ".idea", ".vscode",
    "OneDriveTemp", "Temp", "tmp"
}
EXCLUDE_FILE_EXTS = {".sys", ".dll"}  # 依需求調整

@dataclass
class UserConfig:
    roots: list[str]
    exclude_dir_names: list[str]
    exclude_file_exts: list[str]
    refresh_days: int = 14  # 超過 N 天提示重建索引

def load_user_config() -> UserConfig:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return UserConfig(**{
            "roots": data.get("roots", DEFAULT_ROOTS),
            "exclude_dir_names": data.get("exclude_dir_names", list(EXCLUDE_DIR_NAMES)),
            "exclude_file_exts": data.get("exclude_file_exts", list(EXCLUDE_FILE_EXTS)),
            "refresh_days": data.get("refresh_days", 14),
        })
    cfg = UserConfig(DEFAULT_ROOTS, list(EXCLUDE_DIR_NAMES), list(EXCLUDE_FILE_EXTS))
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(asdict(cfg), f, ensure_ascii=False, indent=2)
    return cfg

def mapping_is_stale() -> bool:
    if not os.path.exists(MAPPING_PATH):
        return True
    cfg = load_user_config()
    mtime = os.path.getmtime(MAPPING_PATH)
    days = (time.time() - mtime) / 86400
    return days > cfg.refresh_days
