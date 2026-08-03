"""
linkedin_agent.py — Autonomous LinkedIn Agent.

Uses linkedin-spider (Selenium) + Playwright helpers for LinkedIn automation:
- Login and session management
- Check incoming connection requests
- Send messages to connections
- Send connection requests (via Playwright)
- Search profiles and opportunities
- Track state and learn from interactions

Usage:
    python linkedin_agent.py                 # Full run
    python linkedin_agent.py --login         # Open browser for login
    python linkedin_agent.py --status        # Show agent state
    python linkedin_agent.py --connect HANDLE --note "Hi!"  # Connect
    python linkedin_agent.py --message HANDLE --text "Hello"  # Message
    python linkedin_agent.py --search "AI engineer"  # Search
"""

import os
import sys
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = Path(__file__).parent
STATE_FILE = WORKSPACE / "linkedin_agent_state.json"
LOG_FILE = WORKSPACE / "linkedin_agent.log"
DECISIONS_FILE = WORKSPACE / "hunt_decisions.md"
COOKIES_FILE = WORKSPACE / "linkedin_cookies.json"

sys.path.insert(0, str(WORKSPACE))
try:
    from keyhub_client import ai_generate, ai_generate_json
    from quota import can_send, record_sent, get_remaining
except ImportError as e:
    print(f"[ERROR] Cannot import workspace modules: {e}")
    sys.exit(1)


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"threads": {}, "connections": [], "last_check": None}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def ls(*args, timeout=120):
    cmd = [str(Path(os.environ.get("PYTHON", "") or sys.executable).parent / "Scripts" / "linkedin-spider-cli.exe")]
    cmd.extend(str(a) for a in args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            err = (r.stderr or r.stdout or "").strip()[:300]
            log(f"  li error: {err}")
            return None
        out = r.stdout.strip()
        if out:
            try:
                return json.loads(out)
            except json.JSONDecodeError:
                return out
        return None
    except FileNotFoundError:
        log("ERROR: linkedin-spider-cli not found")
        return None
    except subprocess.TimeoutExpired:
        log(f"  li timeout: {args[0]}")
        return None
    except Exception as e:
        log(f"  li exception: {e}")
        return None


def prompt_to_ai(prompt, system=None, max_tokens=300):
    system_default = "You are Alaa Fathi, an AI Automation Engineer. Be concise, professional. Never reveal being AI. Sign as Alaa."
    return ai_generate(prompt, system=system or system_default, max_tokens=max_tokens, caller="linkedin_agent")


def cmd_login():
    log("Opening browser for LinkedIn login...")
    result = ls("login", timeout=300)
    if result:
        log("Login completed and cookies saved.")
    else:
        log("Login command sent. Check browser window and complete login.")
    return result


def cmd_profile(handle_or_url):
    result = ls("profile", handle_or_url)
    return result


def cmd_search(keywords, limit=10):
    result = ls("search", keywords, "--results-limit", str(limit))
    return result


def cmd_search_posts(keywords, limit=10):
    result = ls("search-posts", keywords, "--results-limit", str(limit))
    return result


def cmd_incoming_connections():
    result = ls("connections")
    return result


def cmd_send_message(profile_url, text):
    if not can_send("replies"):
        log("Daily reply quota exhausted")
        return {"error": "quota"}
    result = ls("send-message", profile_url, "--text", text, timeout=180)
    if result:
        record_sent("replies", f"linkedin:{profile_url}")
        log(f"Message sent to {profile_url}")
    return result


def ensure_logged_in():
    result = ls("profile", "me", timeout=30)
    return result is not None


def playwright_connect(handle_or_url, note=None):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log("Playwright not available for connect")
        return None

    if not can_send("linkedin_connects"):
        log("Daily connection quota exhausted")
        return None

    url = handle_or_url
    if not url.startswith("http"):
        url = f"https://www.linkedin.com/in/{url}/"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, channel="brave")
            context = browser.new_context(
                storage_state=str(COOKIES_FILE) if COOKIES_FILE.exists() else None,
                viewport={"width": 1366, "height": 768},
            )
            page = context.new_page()
            page.goto(url, timeout=60000, wait_until="domcontentloaded")

            if page.url.startswith("https://www.linkedin.com/login"):
                log("Not logged in. Complete LinkedIn login in Brave first.")
                input("  Press Enter after logging in on LinkedIn...")
                context.storage_state(path=str(COOKIES_FILE))
                page.goto(url, timeout=60000, wait_until="domcontentloaded")

            page.wait_for_timeout(3000)

            more_btn = page.query_selector('button[aria-label*="More"]')
            if more_btn:
                more_btn.click()
                page.wait_for_timeout(1000)
                connect_btn = page.query_selector('div[aria-label*="Connect"]')
                if connect_btn:
                    connect_btn.click()
                    page.wait_for_timeout(2000)

                    if note:
                        note_btn = page.query_selector('button[aria-label*="Add a note"]')
                        if note_btn:
                            note_btn.click()
                            page.wait_for_timeout(1000)
                            textarea = page.query_selector('textarea[name="message"]')
                            if textarea:
                                textarea.fill(note)
                                page.wait_for_timeout(500)

                    send_btn = page.query_selector('button[aria-label*="Send"]')
                    if send_btn:
                        send_btn.click()
                        page.wait_for_timeout(2000)
                        record_sent("linkedin_connects", handle_or_url)
                        log(f"Connection request sent to {handle_or_url}")
                        context.storage_state(path=str(COOKIES_FILE))
                        browser.close()
                        return {"sent": True}
                else:
                    log("Connect button not found")
            else:
                log("More button not found (may already be connected)")

            context.storage_state(path=str(COOKIES_FILE))
            browser.close()
    except Exception as e:
        log(f"Playwright connect error: {e}")

    return None


def check_incoming_connections(state):
    log("Checking incoming connection requests...")
    result = cmd_incoming_connections()
    if not result:
        return
    if isinstance(result, list):
        connections = result
    elif isinstance(result, dict):
        connections = result.get("connections", result.get("result", []))
        if isinstance(connections, dict):
            connections = [connections]
    else:
        connections = []
    for conn in connections:
        profile_url = conn.get("profile_url") or conn.get("url", "")
        name = conn.get("name", conn.get("public_identifier", ""))
        headline = conn.get("headline", "")
        log(f"  Incoming: {name} - {headline[:60]}")
        resp = prompt_to_ai(
            f"Write a brief thank-you message for new LinkedIn connection {name} "
            f"({headline}). Keep it professional, mention AI Automation, "
            f"offer collaboration. 2 paragraphs max. Sign as Alaa.",
            max_tokens=200,
        )
        if resp:
            entry = f"""
## DECISION: li_accept_{datetime.now().strftime('%H%M%S')}
ACTION: send
TYPE: email_followup
TO: {name} ({profile_url})
SUBJECT: Thank you for connecting
CLASSIFICATION: accepted_connection
PLATFORM: linkedin
BODY:
{resp}

---
"""
            with open(DECISIONS_FILE, "a", encoding="utf-8") as f:
                f.write(entry)
            log(f"  Generated thank-you for {name}")


def show_status(state):
    threads = state.get("threads", {})
    connections = state.get("connections", [])

    print(f"\n  LinkedIn Agent State")
    print(f"  {'='*50}")
    print(f"  Last check: {state.get('last_check', 'never')}")
    print(f"  Incoming connections tracked: {len(connections)}")
    print(f"  Threads tracked: {len(threads)}")
    print(f"\n  Remaining quotas:")
    for action in ["replies", "linkedin_connects", "followups"]:
        print(f"    {action}: {get_remaining(action)}")
    print()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="LinkedIn Agent")
    parser.add_argument("--login", action="store_true", help="Open browser for LinkedIn login")
    parser.add_argument("--status", action="store_true", help="Show agent state")
    parser.add_argument("--connect", help="Send connection request (handle or URL)")
    parser.add_argument("--note", default="", help="Note for connection request")
    parser.add_argument("--message", help="Send message to handle/URL")
    parser.add_argument("--text", default="", help="Message text")
    parser.add_argument("--search", help="Search LinkedIn profiles")
    parser.add_argument("--profile", help="Get LinkedIn profile")
    parser.add_argument("--reset-state", action="store_true", help="Clear state")
    parser.add_argument("--incoming", action="store_true", help="Check incoming connections")
    args = parser.parse_args()

    print("=" * 60)
    print(f"  LINKEDIN AGENT — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    state = load_state()

    if args.reset_state:
        state = {"threads": {}, "connections": [], "last_check": None}
        save_state(state)
        log("State reset")
        return

    if args.login:
        cmd_login()
        return

    if args.status:
        show_status(state)
        return

    if args.connect:
        result = playwright_connect(args.connect, args.note)
        log(f"Connect result: {result}")
        return

    if args.message:
        if not args.text:
            log("--text required with --message")
            return
        result = cmd_send_message(args.message, args.text)
        log(f"Message result: {result}")
        return

    if args.search:
        profiles = cmd_search(args.search)
        if profiles:
            results = profiles.get("profiles", profiles.get("result", []))
            if isinstance(results, dict):
                results = [results]
            print(f"\n  Search: '{args.search}'")
            for p in results[:10]:
                name = p.get("name", p.get("public_identifier", "?"))
                headline = p.get("headline", "")[:80]
                print(f"    {name:<30} {headline}")
        return

    if args.profile:
        profile = cmd_profile(args.profile)
        if profile:
            print(json.dumps(profile, indent=2, ensure_ascii=False))
        return

    if args.incoming:
        check_incoming_connections(state)
        save_state(state)
        return

    check_incoming_connections(state)
    save_state(state)

    print()
    show_status(state)
    print()


if __name__ == "__main__":
    main()
