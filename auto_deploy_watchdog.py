"""Auto-deploy watchdog — triggers Render deploy after git push.

Run this as a background process or include in git hooks to auto-deploy
after every commit to main.

Usage:
    python auto_deploy_watchdog.py --once      # trigger immediately
    python auto_deploy_watchdog.py --watch 60  # check every 60 seconds
"""
import os
import sys
import time
import subprocess
import requests
from datetime import datetime

HOOK_URL = os.environ.get("RENDER_DEPLOY_HOOK", "").strip()
ENGINE_DIR = os.environ.get("ENGINE_DIR", "C:/Users/A/Desktop/Money/ai-automation-engine")


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def get_last_commit():
    """Get current HEAD commit hash."""
    try:
        result = subprocess.run(
            ["git", "-C", ENGINE_DIR, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return None


def trigger_deploy():
    if not HOOK_URL:
        log("ERROR: RENDER_DEPLOY_HOOK not set")
        return False
    try:
        resp = requests.post(HOOK_URL, timeout=30)
        log(f"Deploy triggered: {resp.status_code}")
        return resp.status_code in (200, 201, 202)
    except Exception as e:
        log(f"Deploy failed: {e}")
        return False


def watch(interval=60):
    log(f"Watching {ENGINE_DIR} every {interval}s")
    last_commit = get_last_commit()
    log(f"Current commit: {last_commit[:8] if last_commit else 'unknown'}")

    try:
        while True:
            time.sleep(interval)
            current = get_last_commit()
            if current and current != last_commit:
                log(f"New commit detected: {current[:8]}")
                last_commit = current
                trigger_deploy()
    except KeyboardInterrupt:
        log("Stopped")


def main():
    if "--once" in sys.argv:
        trigger_deploy()
    elif "--watch" in sys.argv:
        idx = sys.argv.index("--watch")
        interval = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 60
        watch(interval)
    else:
        log("Usage: python auto_deploy_watchdog.py --once | --watch 60")


if __name__ == "__main__":
    main()
