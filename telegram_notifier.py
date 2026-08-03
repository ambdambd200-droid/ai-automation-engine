"""
telegram_notifier.py — Free Telegram Bot notifications.

Replaces Resend Web API. No monthly limits, no domain verification.

Setup (one-time):
  1. Open Telegram, talk to @BotFather
  2. /newbot → name it (e.g. "Salim Freelance Bot")
  3. Copy the bot token (looks like: 123456789:ABCDEFGHIJK...)
  4. Start a chat with your bot
  5. Open https://api.telegram.org/bot<TOKEN>/getUpdates
  6. Find your chat_id (the user who messaged the bot)
  7. Save both:
     setx TELEGRAM_BOT_TOKEN "your_token"
     setx TELEGRAM_CHAT_ID "your_chat_id"

Usage:
  from telegram_notifier import notify, notify_error
  notify("Daily routine done. 3 bids posted on Mostaql.")
  notify_error("Engine unreachable: timeout after 30s")
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from urllib import request as urlrequest
from urllib.parse import quote
from urllib.error import URLError, HTTPError

BASE_DIR = Path(__file__).parent.resolve()
LOG_FILE = BASE_DIR / "telegram_log.md"

TELEGRAM_API_BASE = "https://api.telegram.org"


def _log_line(line: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{ts}] {line}\n")
    except Exception:
        pass


def _get_credentials() -> tuple[str, str]:
    """Read bot token + chat_id from env vars."""
    token = (
        os.environ.get("TELEGRAM_BOT_TOKEN")
        or os.environ.get("BOT_TOKEN")
        or ""
    ).strip()
    chat_id = (
        os.environ.get("TELEGRAM_CHAT_ID")
        or os.environ.get("CHAT_ID")
        or ""
    ).strip()
    return token, chat_id


def send_message(text: str, parse_mode: str = "HTML",
                 disable_notification: bool = False) -> bool:
    """Send a message to the configured Telegram chat. Returns True on success."""
    token, chat_id = _get_credentials()
    if not token or not chat_id:
        _log_line(f"[WARN] credentials missing (token={bool(token)}, chat_id={bool(chat_id)})")
        print(f"[telegram] credentials missing — message NOT sent: {text[:80]}")
        return False
    url = f"{TELEGRAM_API_BASE}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text[:4000],  # Telegram limit 4096
        "disable_notification": disable_notification,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(url, data=data,
                              headers={"Content-Type": "application/json"})
    try:
        with urlrequest.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            result = json.loads(body)
            if result.get("ok"):
                _log_line(f"[OK] sent ({len(text)} chars)")
                return True
            _log_line(f"[FAIL] api returned: {body[:200]}")
            return False
    except (URLError, HTTPError, TimeoutError) as e:
        _log_line(f"[ERROR] {e}")
        print(f"[telegram] send failed: {e}")
        return False
    except Exception as e:
        _log_line(f"[ERROR] {type(e).__name__}: {e}")
        return False


def notify(text: str) -> bool:
    """Send a normal notification."""
    return send_message(text)


def notify_error(text: str) -> bool:
    """Send a notification that triggers sound + high priority."""
    body = f"\U0001F6A8 <b>Error</b>\n\n{text}"
    return send_message(body)


def notify_success(text: str) -> bool:
    """Send a success notification."""
    body = f"\u2705 <b>OK</b>\n\n{text}"
    return send_message(body)


def notify_daily_digest(summary: dict) -> bool:
    """Send a structured daily digest."""
    date = summary.get("date", datetime.now().strftime("%Y-%m-%d"))
    lines = [f"\U0001F4CA <b>Daily Digest — {date}</b>", ""]
    if "mostaql_bids" in summary:
        lines.append(f"  Mostaql: {summary['mostaql_bids']} bids posted")
    if "nafezly_bids" in summary:
        lines.append(f"  Nafezly: {summary['nafezly_bids']} bids posted")
    if "n8n_replies" in summary:
        lines.append(f"  n8n Community: {summary['n8n_replies']} replies")
    if "errors" in summary and summary["errors"]:
        lines.append("")
        lines.append(f"\u26A0\uFE0F Errors:")
        for e in summary["errors"][:5]:
            lines.append(f"  - {e}")
    if "next_steps" in summary and summary["next_steps"]:
        lines.append("")
        lines.append(f"\U0001F3AF Next steps:")
        for s in summary["next_steps"][:5]:
            lines.append(f"  - {s}")
    body = "\n".join(lines)
    return send_message(body)


def test_connection() -> bool:
    """Verify bot token + chat_id work. Returns True if message sent."""
    token, chat_id = _get_credentials()
    if not token or not chat_id:
        print("[telegram] credentials missing")
        print("  set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID as env vars")
        return False
    # Verify the token first
    url = f"{TELEGRAM_API_BASE}/bot{token}/getMe"
    try:
        with urlrequest.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                me = data.get("result", {})
                print(f"[telegram] Bot verified: @{me.get('username')} ({me.get('first_name')})")
                return notify_success("Telegram connection test successful.")
            print(f"[telegram] getMe failed: {data}")
            return False
    except Exception as e:
        print(f"[telegram] connection failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Telegram notifier")
    ap.add_argument("--test", action="store_true",
                    help="Test bot connection (sends a message)")
    ap.add_argument("--msg", metavar="TEXT", help="Send a single message")
    ap.add_argument("--error", metavar="TEXT", help="Send an error message")
    args = ap.parse_args()
    if args.test:
        ok = test_connection()
        sys.exit(0 if ok else 1)
    if args.msg:
        ok = notify(args.msg)
        sys.exit(0 if ok else 1)
    if args.error:
        ok = notify_error(args.error)
        sys.exit(0 if ok else 1)
    ap.print_help()
