"""
signup_arabic_platforms.py — Sign up on Mostaql + Nafezly via Playwright.

v2.0 (2026-07-31) — Refactored to use session_manager.py for state persistence.

Flow per platform:
  1. First run: opens signup URL, user signs up, presses ENTER, session saved.
  2. Subsequent runs: loads saved session, user is already logged in.

Usage:
  python signup_arabic_platforms.py signup    # signup (first time)
  python signup_arabic_platforms.py profile   # fill profile (post email-verify)
  python signup_arabic_platforms.py nafezly   # signup only nafezly
  python signup_arabic_platforms.py mostaql   # signup only mostaql
"""

import argparse
import getpass
import sys
import time
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from session_manager import SessionManager
except ImportError as e:
    print(f"[signup_arabic_platforms] Import error: {e}", file=sys.stderr)
    sys.exit(1)

WORKSPACE = Path(__file__).parent.resolve()
SCREENSHOTS = WORKSPACE / "signup_screenshots"
SCREENSHOTS.mkdir(exist_ok=True)
LOG_FILE = WORKSPACE / "signup_log.md"

EMAIL = "alaafathi403@gmail.com"  # signup email per AGENTS.md
NAME = "Salim Muhammad"


def log_line(line: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {line}\n")


def get_password() -> str:
    import os
    pw = os.environ.get("ACCOUNT_PASSWORD") or os.environ.get("MOSTAQL_PASSWORD") \
         or os.environ.get("NAFEZLY_PASSWORD")
    if pw:
        return pw
    return getpass.getpass("Enter password for the new account (will not be stored): ")


def signup_one(platform: str, signup_url: str, home_url: str, password: str) -> bool:
    """Single signup flow for one platform. Uses SessionManager."""
    print("\n" + "=" * 60)
    print(f"  Signup: {platform.upper()}")
    print(f"  Email: {EMAIL}")
    print(f"  Name: {NAME}")
    print("=" * 60)

    with SessionManager(
        platform=platform,
        signup_url=signup_url,
        home_url=home_url,
        headless=False,
        wait_for_seconds_after_signup=5,
    ) as sm:
        page = sm.page

        if sm.has_session():
            print(f"[signup_arabic_platforms] {platform}: Session already exists. Loading...")
            print(f"[signup_arabic_platforms] If signup is needed, delete the session first:")
            print(f"   python session_manager.py --delete {platform}")
            time.sleep(2)
            return True

        # First-run: pre-fill the signup form (best-effort)
        try:
            page.wait_for_timeout(2000)
            # Try filling name
            for sel in ["input[name='name']", "input[name='fullname']",
                        "input[name='full_name']", "input[placeholder*='اسم']",
                        "input[placeholder*='الاسم']"]:
                loc = page.locator(sel).first
                if loc.count() > 0:
                    try:
                        loc.fill(NAME)
                        print(f"  ✓ Name: {NAME}")
                        break
                    except Exception:
                        pass
            # Email
            for sel in ["input[type='email']", "input[name='email']",
                        "input[placeholder*='بريد']", "input[placeholder*='إيميل']"]:
                loc = page.locator(sel).first
                if loc.count() > 0:
                    try:
                        loc.fill(EMAIL)
                        print(f"  ✓ Email: {EMAIL}")
                        break
                    except Exception:
                        pass
            # Password
            for sel in ["input[type='password']", "input[name='password']"]:
                loc = page.locator(sel).first
                if loc.count() > 0:
                    try:
                        loc.fill(password)
                        print(f"  ✓ Password (hidden)")
                        break
                    except Exception:
                        pass
            page.screenshot(path=str(SCREENSHOTS / f"{platform}_prefilled.png"))
        except Exception as e:
            print(f"  ⚠ Pre-fill error: {e}")

        print("\n  👀 Complete signup in the browser.")
        print("     Verify your email after signup, then press ENTER here to save session.")
        try:
            input("  >>> Press ENTER after signup/login complete: ")
        except EOFError:
            print("[signup_arabic_platforms] No stdin; will wait 5 min...")
            time.sleep(300)

        sm.save_session_now()
        page.screenshot(path=str(SCREENSHOTS / f"{platform}_after_signup.png"))
        return True


def fill_profile(platform: str, home_url: str, profile_path: str,
                 bio_selectors: list[str], skills: str = "",
                 rate: str = "") -> bool:
    """Fill the profile page for a platform. Loads existing session."""
    print("\n" + "=" * 60)
    print(f"  Filling profile: {platform.upper()}")
    print("=" * 60)
    with SessionManager(
        platform=platform,
        signup_url=home_url,
        home_url=home_url,
        headless=False,
    ) as sm:
        page = sm.page
        try:
            page.goto(profile_path, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"  ❌ Could not open profile: {e}")
            return False

        # Bio
        if bio_selectors:
            try:
                for sel in bio_selectors:
                    loc = page.locator(sel).first
                    if loc.count() > 0:
                        # Read bio from profile file
                        setup_file = WORKSPACE / f"{platform.title()}_Setup.md"
                        if not setup_file.exists():
                            setup_file = WORKSPACE / (
                                "Mostaql_Setup.md" if platform == "mostaql"
                                else "Nafezly_Setup.md"
                            )
                        import re
                        bio_text = ""
                        if setup_file.exists():
                            content = setup_file.read_text(encoding="utf-8")
                            m = re.search(r"### .*\(?Bio\)?\s*\n+```\n(.*?)\n```",
                                          content, re.DOTALL)
                            if m:
                                bio_text = m.group(1).strip()
                        if bio_text:
                            loc.fill(bio_text)
                            print(f"  ✓ Bio filled ({len(bio_text)} chars)")
                            break
            except Exception as e:
                print(f"  ⚠ Bio field error: {e}")

        # Skills
        if skills:
            try:
                for sel in ["input[name='skills']", "input[placeholder*='مهارات']"]:
                    loc = page.locator(sel).first
                    if loc.count() > 0:
                        loc.fill(skills)
                        print(f"  ✓ Skills: {skills[:50]}...")
                        break
            except Exception as e:
                print(f"  ⚠ Skills field error: {e}")

        # Rate
        if rate:
            try:
                for sel in ["input[name='hourly_rate']", "input[name='rate']"]:
                    loc = page.locator(sel).first
                    if loc.count() > 0:
                        loc.fill(rate)
                        print(f"  ✓ Rate: ${rate}/hr")
                        break
            except Exception as e:
                print(f"  ⚠ Rate field error: {e}")

        page.screenshot(path=str(SCREENSHOTS / f"{platform}_profile_filled.png"))
        sm.save_session_now()
        print(f"  📸 Screenshot saved. Review and click Save manually.")
        time.sleep(3)
        return True


def main():
    parser = argparse.ArgumentParser(description="Mostaql + Nafezly signup/profile")
    parser.add_argument("mode", choices=["signup", "profile", "mostaql", "nafezly"],
                        help="signup: signup on both; "
                             "profile: fill profile on both; "
                             "mostaql/nafezly: signup on one only")
    args = parser.parse_args()

    print("=" * 60)
    print(f"  Arabic Platforms: {args.mode.upper()} mode")
    print(f"  Identity: {NAME} <{EMAIL}>")
    print("=" * 60)
    log_line(f"=== {args.mode} session started ===")

    if args.mode == "signup":
        password = get_password()
        signup_one("mostaql",
                   signup_url="https://mostaql.com/register",
                   home_url="https://mostaql.com/",
                   password=password)
        log_line("mostaql signup attempted")
        signup_one("nafezly",
                   signup_url="https://nafezly.com/register",
                   home_url="https://nafezly.com/",
                   password=password)
        log_line("nafezly signup attempted")
    elif args.mode == "mostaql":
        password = get_password()
        signup_one("mostaql",
                   signup_url="https://mostaql.com/register",
                   home_url="https://mostaql.com/",
                   password=password)
        log_line("mostaql signup attempted")
    elif args.mode == "nafezly":
        password = get_password()
        signup_one("nafezly",
                   signup_url="https://nafezly.com/register",
                   home_url="https://nafezly.com/",
                   password=password)
        log_line("nafezly signup attempted")
    elif args.mode == "profile":
        fill_profile("mostaql",
                     home_url="https://mostaql.com/",
                     profile_path="https://mostaql.com/account/profile",
                     bio_selectors=["textarea[name='bio']",
                                    "textarea[name='about']",
                                    "textarea[placeholder*='نبذة']"],
                     skills="n8n, Zapier, Make.com, Python, Flask, OpenAI, Groq, "
                            "Google Sheets, Slack, Airtable, Telegram Bots, "
                            "WhatsApp API, AI Agents",
                     rate="15")
        log_line("mostaql profile filled")
        fill_profile("nafezly",
                     home_url="https://nafezly.com/",
                     profile_path="https://nafezly.com/account/profile",
                     bio_selectors=["textarea[name='bio']",
                                    "textarea[name='about']"],
                     skills="n8n, أتمتة, Telegram bots, WhatsApp, AI agents, "
                            "Python, Flask, OpenAI, Groq",
                     rate="10")
        log_line("nafezly profile filled")

    log_line(f"=== {args.mode} session ended ===")
    print(f"\nLog: {LOG_FILE}")


if __name__ == "__main__":
    main()
