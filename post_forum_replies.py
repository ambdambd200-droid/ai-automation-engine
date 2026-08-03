"""
post_forum_replies.py — Post 3 n8n Community forum replies via Playwright.

Why this script: MCP needs opencode restart to load. Playwright runs as
a standalone Python script — no MCP, no AI, no loading issues.

What it does:
1. Opens Chromium browser
2. Goes to each of the 3 forum threads (mkitplug, easybits, Doru_Gradinaru)
3. For each thread: takes a screenshot, asks user to log in if needed,
   types the draft reply, asks user to review, then clicks Post
4. Saves the post URL + screenshot for each
5. Logs everything to forum_post_log.md

Requirements:
- pip install playwright
- python -m playwright install chromium
- User logged in to community.n8n.io (or logged in during the run)

Run:
  python post_forum_replies.py
"""

import re
import sys
import time
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

WORKSPACE = Path(r"C:\Users\A\Desktop\Money")
SCREENSHOTS = WORKSPACE / "forum_screenshots"
SCREENSHOTS.mkdir(exist_ok=True)
LOG_FILE = WORKSPACE / "forum_post_log.md"

THREADS = [
    {
        "key": "mkitplug",
        "draft_file": "Application_N8N_Community_mkitplug.md",
        "url": "https://community.n8n.io/t/i-built-a-free-figma-plugin-that-sends-design-data-to-n8n-looking-for-agencies-to-build-real-workflows-with/297696",
        "label": "mkitplug (Michael) — Figma → n8n plugin",
    },
    {
        "key": "easybits",
        "draft_file": "Application_N8N_Community_easybits.md",
        "url": "https://community.n8n.io/t/recruiter-friend-was-losing-half-her-day-to-manually-typing-linkedin-profiles-into-a-sheet-built-her-a-workflow-that-ends-the-retyping/297970",
        "label": "easybits — Recruiter LinkedIn workflow",
    },
    {
        "key": "Doru_Gradinaru",
        "draft_file": "Application_N8N_Community_Doru_Gradinaru.md",
        "url": "https://community.n8n.io/t/built-an-importable-guard-workflow-for-costly-ai-tool-calls-looking-for-n8n-feedback/296302",
        "label": "Doru_Gradinaru — Guard workflow for AI tool costs",
    },
]


def extract_reply(md_path: Path) -> str:
    """Extract text between the first pair of ``` fences in the .md file."""
    text = md_path.read_text(encoding="utf-8")
    match = re.search(r"```\n(.*?)\n```", text, re.DOTALL)
    if not match:
        raise ValueError(f"No fenced code block found in {md_path.name}")
    return match.group(1).strip()


def log_line(line: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {line}\n")


def wait_for_user_login(page, label: str) -> bool:
    """If user is not logged in, prompt them to log in then continue."""
    print(f"\n  → {label}")
    print(f"    URL: {page.url[:80]}...")
    # Heuristic: look for 'Sign In' or 'Log In' button
    needs_login = False
    try:
        sign_in = page.get_by_role("button", name=re.compile("Sign In|Log In", re.I))
        if sign_in.count() > 0:
            needs_login = True
    except Exception:
        pass

    if needs_login:
        print("\n  ⚠ You appear to NOT be logged in to community.n8n.io.")
        print("    Please log in now in the browser window.")
        print("    After you log in, press ENTER here to continue.")
        input("  Press ENTER after logging in: ")
        page.reload()
        page.wait_for_load_state("domcontentloaded")
        return True
    else:
        print("    (Logged in detected — proceeding)")
        return True


def post_reply(page, url: str, label: str, reply_text: str) -> str | None:
    """Navigate to thread, click Reply, type text, click Post. Returns post URL."""
    print(f"\n{'=' * 60}")
    print(f"  Posting: {label}")
    print(f"{'=' * 60}")

    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    # Screenshot before
    screenshot_before = SCREENSHOTS / f"{label.split(' ')[0]}_before.png"
    page.screenshot(path=str(screenshot_before))
    print(f"  📸 Screenshot: {screenshot_before.name}")

    # Check login
    if not wait_for_user_login(page, label):
        return None

    # Find the reply button — Discourse has a footer Reply button
    print("  Looking for Reply button...")
    try:
        # Discourse: button at the bottom of the topic with text "Reply"
        reply_btn = page.locator("button:has-text('Reply')").first
        if reply_btn.count() == 0:
            print("  ❌ No Reply button found. Page may have changed.")
            return None
        reply_btn.scroll_into_view_if_needed()
        reply_btn.click()
        page.wait_for_timeout(1500)
    except PWTimeout:
        print("  ❌ Reply button timeout.")
        return None

    # Type the reply into the editor
    print("  Typing reply...")
    try:
        # Discourse composer textarea
        editor = page.locator("textarea.d-editor-input").first
        editor.wait_for(state="visible", timeout=10000)
        editor.fill(reply_text)
        page.wait_for_timeout(500)
    except PWTimeout:
        # Fallback: any textarea in the composer
        try:
            editor = page.locator("div.d-editor textarea, .d-editor-input").first
            editor.fill(reply_text)
        except Exception as e:
            print(f"  ❌ Could not find editor: {e}")
            return None

    # Screenshot after typing
    screenshot_typed = SCREENSHOTS / f"{label.split(' ')[0]}_typed.png"
    page.screenshot(path=str(screenshot_typed))
    print(f"  📸 Screenshot: {screenshot_typed.name}")

    # Ask user to review
    print("\n  👀 Review the reply in the browser window.")
    print("     Make sure the text is correct, then press ENTER here to POST.")
    print("     Or type 'skip' + ENTER to skip this thread.")
    choice = input("  >>> ").strip().lower()
    if choice == "skip":
        print("  ⏭ Skipped.")
        return None

    # Click the final Post button (Discourse has "Reply to Topic" or just "Reply")
    print("  Clicking Post button...")
    try:
        post_btn = page.locator("button:has-text('Reply to Topic'), button:has-text('Post Reply')").first
        post_btn.click()
        page.wait_for_timeout(3000)
    except PWTimeout:
        print("  ❌ Post button timeout. Reply may not have been posted.")
        return None

    # Screenshot after post
    screenshot_after = SCREENSHOTS / f"{label.split(' ')[0]}_after.png"
    page.screenshot(path=str(screenshot_after))

    # Get the post URL (Discourse appends /N to the thread URL)
    post_url = page.url
    print(f"  ✅ Posted. URL: {post_url[:100]}")
    return post_url


def main():
    print("=" * 60)
    print("  POST FORUM REPLIES — Playwright-based")
    print("=" * 60)
    print()
    print("This script will:")
    print("  1. Open Chromium browser")
    print("  2. Navigate to each of 3 n8n Community threads")
    print("  3. Type your draft reply")
    print("  4. Wait for you to review and confirm before posting")
    print()
    print("⚠ You MUST be logged in to community.n8n.io for this to work.")
    print("  If not logged in, the script will pause and ask you to log in.")
    print()
    input("Press ENTER to start (Ctrl+C to abort)...")

    log_line("=== Forum post session started ===")

    # Load all 3 replies
    replies = {}
    for t in THREADS:
        md = WORKSPACE / t["draft_file"]
        if not md.exists():
            print(f"  ❌ Missing: {md}")
            sys.exit(1)
        replies[t["key"]] = extract_reply(md)
        print(f"  ✓ Loaded reply for {t['key']} ({len(replies[t['key']])} chars)")

    results = []

    with sync_playwright() as p:
        # Headless=False so user can see + log in
        browser = p.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        for t in THREADS:
            try:
                post_url = post_reply(
                    page,
                    t["url"],
                    t["label"],
                    replies[t["key"]],
                )
                results.append({
                    "key": t["key"],
                    "label": t["label"],
                    "url": post_url,
                    "status": "Posted" if post_url else "Skipped",
                })
                log_line(f"{t['key']}: {'Posted' if post_url else 'Skipped'} - {post_url or 'N/A'}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
                results.append({
                    "key": t["key"],
                    "label": t["label"],
                    "url": None,
                    "status": f"Error: {e}",
                })
                log_line(f"{t['key']}: Error - {e}")

        browser.close()

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    for r in results:
        status_icon = "✅" if r["status"] == "Posted" else "⏭" if r["status"] == "Skipped" else "❌"
        url = r["url"] or "—"
        print(f"  {status_icon} {r['label']}: {r['status']}")
        print(f"     URL: {url[:80]}")

    print()
    print(f"Log saved to: {LOG_FILE}")
    print(f"Screenshots in: {SCREENSHOTS}")
    print()
    print("Next step: copy the post URLs into Application_Pipeline.md")

    log_line("=== Forum post session ended ===")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
