import os, webbrowser, subprocess, sys

def open_path(path: str):
    if not path:
        return False
    try:
        os.startfile(path)  # type: ignore[attr-defined]  # Windows
        return True
    except Exception:
        pass
    try:
        if sys.platform.startswith("darwin"):
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
        return True
    except Exception:
        return False

def open_url(url: str):
    try:
        webbrowser.open(url, new=2)
        return True
    except Exception:
        return False

def run_action(action: str, path: str) -> bool:
    a = (action or "").lower()
    if a in ("open_folder", "open_file", "open_app", "open"):
        return open_path(path)
    if a in ("open_url", "url"):
        return open_url(path)
    if a.startswith("ms-settings"):
        return open_path(path)
    return open_path(path)
