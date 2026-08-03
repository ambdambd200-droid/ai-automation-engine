"""
signup_n8n_community.py — First-run signup for n8n Community (community.n8n.io).

Flow:
  1. Opens community.n8n.io
  2. Click "Sign Up" -> "Sign in with Google"
  3. User signs in with salim.muhammad.work0@gmail.com (with zero)
  4. Completes email verification (manual)
  5. Fills Discourse profile: name (Salim Muhammad), bio, location
  6. Saves storage_state.json via SessionManager

Subsequent runs skip the signup and just open the forum logged in.

Usage:
  python signup_n8n_community.py           # full signup flow
  python signup_n8n_community.py --profile # update profile only (session must exist)
"""

import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import TimeoutError as PWTimeout
    from session_manager import SessionManager
except ImportError as e:
    print(f"[signup_n8n_community] Import error: {e}", file=sys.stderr)
    sys.exit(1)

SIGNUP_URL = "https://community.n8n.io/"
HOME_URL = "https://community.n8n.io/"

# Salim Muhammad's profile data for Discourse (read by --profile mode)
PROFILE_NAME = "Salim Muhammad"
PROFILE_BIO = (
    "AI Automation Engineer based in Gaza. I build n8n workflows, Telegram/WhatsApp "
    "bots, lead pipelines, and AI-driven automations for solo founders and small teams. "
    "Happy to share what I learn and help others build production-ready workflows. "
    "Get in touch: salim.muhammad.work0@gmail.com"
)
PROFILE_LOCATION = "Gaza, Palestine"
PROFILE_WEBSITE = ""  # leave blank for now


def fill_profile(page) -> bool:
    """
    Fill out the Discourse profile fields after first signup.
    Best-effort: clicks each field if it exists, otherwise skips silently.
    Returns True if at least one field was updated.
    """
    updated = False
    try:
        page.goto("https://community.n8n.io/u/salim-muhammad-work0/preferences/account",
                  wait_until="domcontentloaded", timeout=15000)
        # Name field (Discourse uses input[id="user-name"])
        try:
            name_input = page.locator('input[name="name"], input#user-name').first
            if name_input.count() > 0:
                name_input.fill(PROFILE_NAME)
                print("[signup_n8n_community] Filled name")
                updated = True
        except Exception as e:
            print(f"[signup_n8n_community] name field skipped: {e}")
        # Bio (textarea)
        try:
            bio_ta = page.locator('textarea[name="bio"], textarea#user-bio, '
                                  'textarea[placeholder*="bio" i]').first
            if bio_ta.count() > 0:
                bio_ta.fill(PROFILE_BIO)
                print("[signup_n8n_community] Filled bio")
                updated = True
        except Exception as e:
            print(f"[signup_n8n_community] bio field skipped: {e}")
        # Location
        try:
            loc_input = page.locator('input[name="location"], input#user-location').first
            if loc_input.count() > 0:
                loc_input.fill(PROFILE_LOCATION)
                print("[signup_n8n_community] Filled location")
                updated = True
        except Exception as e:
            print(f"[signup_n8n_community] location field skipped: {e}")
        # Save button
        try:
            save_btn = page.locator('button.save-user-profile, button:has-text("Save")').first
            if save_btn.count() > 0:
                save_btn.click()
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                print("[signup_n8n_community] Clicked Save")
                time.sleep(2)
        except Exception as e:
            print(f"[signup_n8n_community] save skipped: {e}")
        page.screenshot(path=str(Path(__file__).parent / "screenshots" /
                                  "n8n_profile_filled.png"))
    except PWTimeout:
        print("[signup_n8n_community] Profile page timed out (may not exist yet)")
    return updated


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Sign up for n8n Community (Discourse)")
    ap.add_argument("--profile", action="store_true",
                    help="Fill profile only (session must already exist)")
    ap.add_argument("--headless", action="store_true",
                    help="Run browser invisibly (rarely useful for signup)")
    args = ap.parse_args()

    print("=" * 60)
    print("[signup_n8n_community] n8n Community signup")
    print("[signup_n8n_community] Account: salim.muhammad.work0@gmail.com (with zero)")
    print("=" * 60)

    with SessionManager(
        platform="n8n_community",
        signup_url=SIGNUP_URL,
        home_url=HOME_URL,
        headless=args.headless,
        wait_for_seconds_after_signup=8,
    ) as sm:
        page = sm.page
        print("\n[signup_n8n_community] Session ready. Current URL:", page.url)

        if not sm.has_session() or args.profile:
            # We're in first-run or forced profile fill; try to populate profile
            time.sleep(3)
            try:
                filled = fill_profile(page)
                if filled:
                    print("[signup_n8n_community] Profile fields updated")
                else:
                    print("[signup_n8n_community] Profile fields not auto-filled (manual edit later)")
            except Exception as e:
                print(f"[signup_n8n_community] Profile fill error: {e}")
            sm.save_session_now()

        print("\n[signup_n8n_community] Done. Final URL:", page.url)
        sm.screenshot("n8n_final.png")
        print("[signup_n8n_community] Saved final screenshot.")


if __name__ == "__main__":
    main()
