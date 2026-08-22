"""
telegram_debug.py — Diagnose Telegram bot setup issues.

Run this when sendMessage fails. It will tell you exactly what's wrong.

Usage:
    python telegram_debug.py
"""
import json
import os
import sys
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

API = "https://api.telegram.org"


def call(method: str, params: dict | None = None) -> dict:
    """Call a Telegram Bot API method. Returns the parsed JSON response."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return {"ok": False, "error_code": 0, "description": "TELEGRAM_BOT_TOKEN not set in env"}
    url = f"{API}/bot{token}/{method}"
    if method == "getMe":
        req = urlrequest.Request(url, method="GET")
    else:
        # All other methods are POST with JSON
        body = json.dumps(params or {}).encode("utf-8")
        req = urlrequest.Request(url, data=body, method="POST",
                                  headers={"Content-Type": "application/json"})
    try:
        with urlrequest.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"ok": False, "error_code": e.code,
                    "description": f"HTTP {e.code}"}
    except URLError as e:
        return {"ok": False, "error_code": 0,
                "description": f"Network error: {e.reason}"}
    except Exception as e:
        return {"ok": False, "error_code": 0,
                "description": f"{type(e).__name__}: {e}"}


def hr(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def main():
    hr("1. Token check (getMe)")
    me = call("getMe")
    if me.get("ok"):
        bot = me["result"]
        print(f"  OK — Bot: @{bot.get('username')} ({bot.get('first_name')})")
        print(f"  Bot ID: {bot.get('id')}")
    else:
        print(f"  FAIL — {me.get('error_code')}: {me.get('description')}")
        print("\n  >> The TOKEN is invalid. Get a new one from @BotFather:")
        print("     /mybots -> pick your bot -> API Token")
        sys.exit(1)

    hr("2. Chat ID check (env var)")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not chat_id:
        print("  FAIL — TELEGRAM_CHAT_ID not set in env")
        sys.exit(1)
    print(f"  Set to: '{chat_id}' (len={len(chat_id)}, starts_with_digit={chat_id[0].isdigit() if chat_id else False})")

    hr("3. Updates check (getUpdates)")
    updates = call("getUpdates", {"limit": 5, "timeout": 1})
    if not updates.get("ok"):
        print(f"  FAIL — {updates.get('error_code')}: {updates.get('description')}")
        sys.exit(1)
    result = updates.get("result", [])
    if not result:
        print("  EMPTY — No messages found.")
        print("\n  >> You haven't sent any message to the bot yet:")
        print("     1. Open Telegram")
        print("     2. Search for your bot: @" + bot.get("username", "???"))
        print("     3. Press 'Start' and send any message (e.g. 'hi')")
        print("     4. Run this script again")
        sys.exit(1)
    print(f"  Found {len(result)} update(s)")
    chat_ids_found = set()
    for u in result:
        msg = u.get("message") or u.get("edited_message")
        if not msg:
            continue
        chat = msg.get("chat", {})
        cid = chat.get("id")
        ctype = chat.get("type")
        cname = chat.get("first_name") or chat.get("title", "?")
        print(f"    chat_id={cid} type={ctype} name='{cname}'")
        chat_ids_found.add(cid)
    if not chat_ids_found:
        print("  >> No chat IDs in updates. Send a message first.")
        sys.exit(1)

    hr("4. Match check")
    try:
        wanted_cid = int(chat_id)
    except ValueError:
        print(f"  FAIL — TELEGRAM_CHAT_ID='{chat_id}' is not numeric")
        sys.exit(1)

    if wanted_cid in chat_ids_found:
        print(f"  OK — chat_id {wanted_cid} matches a real conversation")
    else:
        print(f"  FAIL — chat_id {wanted_cid} does NOT match any update")
        print(f"  Real chat_ids from your bot: {sorted(chat_ids_found)}")
        print(f"\n  >> Update TELEGRAM_CHAT_ID to one of: {sorted(chat_ids_found)}")
        sys.exit(1)

    hr("5. Send test message")
    sent = call("sendMessage", {
        "chat_id": wanted_cid,
        "text": "✅ telegram_debug.py — connection test successful.",
        "parse_mode": "HTML",
    })
    if sent.get("ok"):
        print("  OK — Message sent!")
        print(f"  message_id={sent['result'].get('message_id')}")
    else:
        print(f"  FAIL — {sent.get('error_code')}: {sent.get('description')}")

    hr("DONE")
    if sent.get("ok"):
        print("  All checks passed. Telegram is working.")
    else:
        print("  Some checks failed. Fix the issues above and re-run.")


if __name__ == "__main__":
    main()
