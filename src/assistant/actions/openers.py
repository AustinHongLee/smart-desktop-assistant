import os, sys, subprocess, shlex

def open_path(path: str, timeout: float = 10.0) -> bool:
    """Try to open a file/folder with system default app and return True only on success."""
    if not path:
        return False
    try:
        if sys.platform.startswith("win"):
            # Use start via cmd. /c start returns immediately; we still check errorlevel of cmd itself.
            cmd = f'start "" "{path}"'
            completed = subprocess.run(cmd, shell=True, timeout=timeout)
            return completed.returncode == 0
        elif sys.platform == "darwin":
            completed = subprocess.run(["open", path], timeout=timeout)
            return completed.returncode == 0
        else:
            # Linux/BSD
            # Prefer xdg-open; fallback to gio open if available
            for opener in (["xdg-open", path], ["gio", "open", path]):
                try:
                    completed = subprocess.run(opener, timeout=timeout)
                    if completed.returncode == 0:
                        return True
                except FileNotFoundError:
                    continue
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
    except Exception:
        return False

def run_action(action: str, target: str) -> bool:
    # 保留擴充空間（未來可能有 open_url、open_folder、reveal_in_explorer 等）
    if action in (None, "", "open", "open_file", "open_folder"):
        return open_path(target)
    return False
