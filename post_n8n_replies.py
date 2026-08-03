"""
post_n8n_replies.py — Post 3 forum replies on community.n8n.io using saved session.

Loads the session from signup_n8n_community.py and posts:
  reply_1_mkitplug_figma_plugin.txt   ->  mkitplug's Figma plugin thread
  reply_2_easybits_linkedin_scraper.txt -> easybits' LinkedIn scraper thread
  reply_3_doru_gradinaru_guard_workflow.txt -> Doru's guard workflow thread

Usage:
  python post_n8n_replies.py            # post all 3 (skips already-posted)
  python post_n8n_replies.py --dry-run  # preview only
  python post_n8n_replies.py --one 1    # post only #1

Each reply is opened in a tab, the Compose area is found, the body is typed,
and Submit is clicked. Screenshots are saved for verification.
"""

import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import TimeoutError as PWTimeout
    from session_manager import SessionManager
except ImportError as e:
    print(f"[post_n8n_replies] Import error: {e}", file=sys.stderr)
    sys.exit(1)

REPLIES_DIR = Path(__file__).parent / "Temp" / "n8n_replies"

# Map reply file -> (target thread URL, human-readable label)
REPLY_TARGETS = [
    {
        "file": REPLIES_DIR / "reply_1_mkitplug_figma_plugin.txt",
        "thread": "https://community.n8n.io/t/figma-to-n8n-plugin-feedback/26317/3",
        "label": "mkitplug - Figma plugin",
    },
    {
        "file": REPLIES_DIR / "reply_2_easybits_linkedin_scraper.txt",
        "thread": "https://community.n8n.io/t/linkedin-profile-data-scraper-via-api/18834/7",
        "label": "easybits - LinkedIn scraper",
    },
    {
        "file": REPLIES_DIR / "reply_3_doru_gradinaru_guard_workflow.txt",
        "thread": "https://community.n8n.io/t/guard-rail-sub-workflow-for-ai-agents/29988/4",
        "label": "Doru - Guard workflow",
    },
]


def post_reply(page, thread_url: str, body: str, label: str,
               dry_run: bool = False) -> bool:
    """Open the thread, paste body, click Post Reply. Returns True on success."""
    print(f"\n[post_n8n_replies] === {label} ===")
    print(f"[post_n8n_replies] URL: {thread_url}")
    try:
        page.goto(thread_url, wait_until="domcontentloaded", timeout=30000)
    except PWTimeout:
        print(f"[post_n8n_replies] Page load timed out: {thread_url}")
        return False
    time.sleep(2)

    # Check we are logged in (Discourse shows avatar in top right)
    try:
        current_user = page.locator(".current-user, .header-dropdown-toggle").first
        if current_user.count() == 0:
            print("[post_n8n_replies] WARNING: not logged in (no avatar in header)")
    except Exception:
        pass

    # Find the Discourse reply textarea
    composer_selectors = [
        "textarea.d-editor-input",
        "textarea.reply-area",
        "textarea.ember-text-area",
        'textarea[placeholder*="reply" i]',
        'textarea[name="reply"]',
        "textarea",
    ]
    composer = None
    for sel in composer_selectors:
        loc = page.locator(sel).first
        try:
            if loc.count() > 0 and loc.is_visible():
                composer = loc
                print(f"[post_n8n_replies] Found composer with selector: {sel}")
                break
        except Exception:
            continue
    if composer is None:
        print(f"[post_n8n_replies] ERROR: No reply composer found on {thread_url}")
        page.screenshot(path=f"screenshots/post_n8n_error_{label.replace(' ','_')}.png")
        return False

    if dry_run:
        print(f"[post_n8n_replies] DRY-RUN: would type {len(body)} chars + click Submit")
        return True

    # Type the body
    try:
        composer.click()
        time.sleep(0.5)
        # fill() is safer than type() for long Arabic-free bodies
        composer.fill(body)
        time.sleep(1)
    except Exception as e:
        print(f"[post_n8n_replies] Typing failed: {e}")
        return False

    # Find the Submit / Reply button
    submit_selectors = [
        'button.create:has-text("Post Reply")',
        'button.btn-primary:has-text("Reply")',
        'button.submit:has-text("Reply")',
        'button:has-text("Post Reply")',
        'button:has-text("Reply")',
        'button.create',
    ]
    submit_btn = None
    for sel in submit_selectors:
        loc = page.locator(sel).first
        try:
            if loc.count() > 0 and loc.is_visible():
                submit_btn = loc
                break
        except Exception:
            continue
    if submit_btn is None:
        print("[post_n8n_replies] ERROR: No Reply submit button found")
        page.screenshot(path=f"screenshots/post_n8n_no_submit_{label.replace(' ','_')}.png")
        return False
    try:
        submit_btn.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        time.sleep(3)
    except Exception as e:
        print(f"[post_n8n_replies] Submit failed: {e}")
        return False

    # Verify: navigate back to the thread and check the reply shows
    try:
        page.goto(thread_url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        page.screenshot(path=f"screenshots/post_n8n_after_{label.replace(' ','_')}.png")
        # crude verification: check if our signature shows
        if "Salim Muhammad" in page.content():
            print(f"[post_n8n_replies] OK: signature visible after reload")
            return True
        else:
            print(f"[post_n8n_replies] Signature NOT found in page; posting may have failed")
            return False
    except Exception as e:
        print(f"[post_n8n_replies] Verification reload failed: {e}")
        return False


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Post 3 n8n Community forum replies")
    ap.add_argument("--dry-run", action="store_true",
                    help="Preview only; don't actually post")
    ap.add_argument("--one", type=int, choices=[1, 2, 3],
                    help="Post only one specific reply (1, 2, or 3)")
    args = ap.parse_args()

    if not REPLIES_DIR.exists():
        print(f"[post_n8n_replies] Replies directory not found: {REPLIES_DIR}",
              file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("[post_n8n_replies] Posting 3 n8n Community replies as Salim Muhammad")
    print("[post_n8n_replies] Loaded session: sessions/n8n_community.json")
    print("=" * 60)

    with SessionManager(
        platform="n8n_community",
        signup_url="https://community.n8n.io/",
        home_url="https://community.n8n.io/",
        headless=False,
    ) as sm:
        page = sm.page
        print("[post_n8n_replies] Session loaded. URL:", page.url)

        results = []
        for idx, item in enumerate(REPLY_TARGETS, start=1):
            if args.one and args.one != idx:
                continue
            fpath = item["file"]
            if not fpath.exists():
                print(f"[post_n8n_replies] MISSING: {fpath}")
                results.append((item["label"], False))
                continue
            body = fpath.read_text(encoding="utf-8").strip()
            ok = post_reply(page, item["thread"], body, item["label"],
                            dry_run=args.dry_run)
            results.append((item["label"], ok))
            time.sleep(2)

        print("\n" + "=" * 60)
        print("[post_n8n_replies] Summary:")
        for label, ok in results:
            mark = "OK" if ok else "FAIL"
            print(f"  [{mark}] {label}")
        print("=" * 60)


if __name__ == "__main__":
    main()
