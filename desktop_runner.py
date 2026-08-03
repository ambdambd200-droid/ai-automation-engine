"""
desktop_runner.py — pyautogui-based desktop automation (fallback option).

When Playwright can't do something (e.g., a desktop app, a non-browser
interface), fall back to pyautogui for mouse/keyboard control.

This is a simple wrapper — give it a series of (action, params) tuples
and it executes them.

Usage:
  python desktop_runner.py

The script reads tasks from desktop_tasks.json (one task per line) and
runs them with confirmation prompts.

Available actions:
  - click X Y          Click at coordinates
  - doubleclick X Y    Double click
  - type "text"        Type text (supports newlines via \\n)
  - press key          Press a key (enter, tab, escape, alt+tab, etc.)
  - hotkey a b         Press a key combination
  - scroll N           Scroll N (positive=down, negative=up)
  - move X Y           Move mouse to X Y
  - wait N             Wait N seconds
  - screenshot PATH    Save screenshot to PATH
  - done               Stop the script

Security: all .zip/.exe/.rar/.scr/.bat/.msi files are blocked.
"""

import json
import sys
import time
import re
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

WORKSPACE = Path(r"C:\Users\A\Desktop\Money")
TASKS_FILE = WORKSPACE / "desktop_tasks.json"
LOG_FILE = WORKSPACE / "desktop_runner.log"
SCREEN_W, SCREEN_H = pyautogui.size()

BLOCKED_EXT = {".zip", ".exe", ".rar", ".scr", ".bat", ".msi", ".cmd", ".com"}


def log_line(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(f"  {msg}")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def check_blocked_path(text: str) -> bool:
    """Return True if text mentions a blocked file extension."""
    lower = text.lower()
    for ext in BLOCKED_EXT:
        if ext in lower:
            return True
    return False


def execute_action(action: dict) -> bool:
    """Execute one action. Returns False if should stop."""
    act = action.get("action", "").lower()

    if act == "click":
        x, y = int(action["x"]), int(action["y"])
        if not (0 <= x <= SCREEN_W and 0 <= y <= SCREEN_H):
            log_line(f"REJECTED: ({x},{y}) out of bounds ({SCREEN_W}x{SCREEN_H})")
            return True
        log_line(f"Click ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.15)
        pyautogui.click()
        time.sleep(0.2)

    elif act == "doubleclick":
        x, y = int(action["x"]), int(action["y"])
        log_line(f"Double-click ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.15)
        pyautogui.doubleClick()
        time.sleep(0.2)

    elif act == "type":
        text = action.get("text", "")
        if check_blocked_path(text):
            log_line(f"BLOCKED: text contains blocked file extension")
            return True
        log_line(f"Type: {text[:50]}{'...' if len(text) > 50 else ''}")
        pyautogui.write(text, interval=0.02)

    elif act == "press":
        key = action.get("key", "")
        log_line(f"Press: {key}")
        pyautogui.press(key)
        time.sleep(0.1)

    elif act == "hotkey":
        keys = action.get("keys", [])
        log_line(f"Hotkey: {'+'.join(keys)}")
        pyautogui.hotkey(*keys)
        time.sleep(0.1)

    elif act == "scroll":
        n = int(action.get("amount", 0))
        log_line(f"Scroll: {n}")
        pyautogui.scroll(n)

    elif act == "move":
        x, y = int(action["x"]), int(action["y"])
        log_line(f"Move to ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.2)

    elif act == "wait":
        n = float(action.get("seconds", 1))
        log_line(f"Wait {n}s")
        time.sleep(n)

    elif act == "screenshot":
        path = action.get("path", "screenshot.png")
        log_line(f"Screenshot → {path}")
        pyautogui.screenshot(path)

    elif act == "done":
        log_line("Done — stopping")
        return False

    else:
        log_line(f"Unknown action: {act}")
        return True

    return True


def main():
    if not TASKS_FILE.exists():
        print(f"❌ Tasks file not found: {TASKS_FILE}")
        print()
        print("Create desktop_tasks.json with this format:")
        print("""[
  {"action": "screenshot", "path": "step1.png"},
  {"action": "wait", "seconds": 1},
  {"action": "click", "x": 100, "y": 200},
  {"action": "type", "text": "hello"},
  {"action": "done"}
]""")
        sys.exit(1)

    tasks = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
    if not isinstance(tasks, list):
        print("❌ desktop_tasks.json must be a JSON array")
        sys.exit(1)

    print("=" * 60)
    print(f"  Desktop Runner — {len(tasks)} tasks")
    print("=" * 60)
    print(f"  Screen: {SCREEN_W}x{SCREEN_H}")
    print()
    print("  ⚠ Move mouse to top-left corner to ABORT (failsafe)")
    print()
    print("  First 3 actions will run automatically. After that,")
    print("  you'll be asked to confirm each one.")
    print()
    input("Press ENTER to start...")

    log_line(f"=== Desktop runner started ({len(tasks)} tasks) ===")

    for i, task in enumerate(tasks, 1):
        if i > 3:
            print(f"\n  Task {i}/{len(tasks)}: {task.get('action', '?')}")
            choice = input("  Press ENTER to execute, or 's' to skip, 'q' to quit: ").strip().lower()
            if choice == "q":
                break
            if choice == "s":
                log_line(f"Task {i}: skipped")
                continue

        if not execute_action(task):
            break

    log_line("=== Desktop runner ended ===")
    print(f"\nLog: {LOG_FILE}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
    except pyautogui.FailSafeException:
        print("\n\nABORTED — mouse moved to corner (failsafe triggered)")
        sys.exit(1)
