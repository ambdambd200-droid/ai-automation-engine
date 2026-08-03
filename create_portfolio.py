"""
create_portfolio.py — Weekly portfolio/service creation on Nafezly + Mostaql.

NOTE: These platforms REQUIRE user-uploaded cover images + work samples.
Full automation isn't possible. This script:
  1. Generates the COPY (title, description, tags) via the engine AI
  2. Opens the platform's create page in browser (session-loaded)
  3. Pre-fills the text fields
  4. PAUSES and asks user to upload images + click Save
  5. Saves the new portfolio/service URL

URLs covered:
  https://nafezly.com/portfolio/create
  https://nafezly.com/service/create
  https://mostaql.com/portfolio/create

Usage:
  python create_portfolio.py portfolio nafezly
  python create_portfolio.py service nafezly
  python create_portfolio.py portfolio mostaql
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import requests
    from session_manager import SessionManager
except ImportError as e:
    print(f"[create_portfolio] Import error: {e}", file=sys.stderr)
    sys.exit(1)

WORKSPACE = Path(__file__).parent.resolve()
ENGINE_URL = os.environ.get("ENGINE_URL", "https://ai-automation-engine.onrender.com")
PROFILE_FILE = WORKSPACE / "salim_profile.json"

PORTFOLIO_URLS = {
    ("portfolio", "nafezly"): "https://nafezly.com/portfolio/create",
    ("service", "nafezly"): "https://nafezly.com/service/create",
    ("portfolio", "mostaql"): "https://mostaql.com/portfolio/create",
}

OUT_DIR = WORKSPACE / "out" / "portfolio"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_profile() -> dict:
    if PROFILE_FILE.exists():
        return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    return {}


def engine_generate_copy(kind: str, platform: str, profile: dict) -> dict | None:
    """Ask engine to generate portfolio/service copy."""
    try:
        r = requests.post(
            f"{ENGINE_URL}/api/bid/generate",  # reuse same AI endpoint
            json={
                "platform": platform,
                "kind": kind,  # "portfolio" or "service"
                "profile": {
                    "full_name": profile.get("identity", {}).get("full_name"),
                    "headline_ar": profile.get("headline_ar"),
                    "bio_ar_short": profile.get("bio_ar_short"),
                    "bio_ar_long": profile.get("bio_ar_long"),
                    "skills_ar": profile.get("skills_ar", [])[:10],
                    "rates": profile.get("rates"),
                },
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log(f"  engine copy gen failed: {e}")
        return None


def open_create_page(page, url: str, copy_data: dict, kind: str, platform: str) -> bool:
    """Open the create page and pre-fill text fields. Best-effort."""
    log(f"\n  Opening: {url}")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
    except Exception as e:
        log(f"  ERROR: {e}")
        return False
    page.screenshot(path=str(WORKSPACE / "screenshots" / f"{platform}_{kind}_create.png"))
    # Try to fill title
    title_sel = "input[name='title'], input[name='name'], input#title, input#name"
    try:
        loc = page.locator(title_sel).first
        if loc.count() > 0 and loc.is_visible():
            loc.fill(copy_data.get("title", ""))
            log(f"  Filled title: {copy_data.get('title', '')[:50]}")
    except Exception as e:
        log(f"  Title fill skipped: {e}")
    # Try description
    desc_sel = "textarea[name='description'], textarea[name='body'], textarea#description"
    try:
        loc = page.locator(desc_sel).first
        if loc.count() > 0 and loc.is_visible():
            loc.fill(copy_data.get("description", ""))
            log(f"  Filled description: {len(copy_data.get('description', ''))} chars")
    except Exception as e:
        log(f"  Description fill skipped: {e}")
    # Try tags
    tag_sel = "input[name='tags'], input[name='skills'], input[placeholder*='مهارات'], input[placeholder*='tags']"
    try:
        loc = page.locator(tag_sel).first
        if loc.count() > 0 and loc.is_visible():
            tags = copy_data.get("tags", [])
            if isinstance(tags, list):
                tags = ",".join(tags)
            loc.fill(tags)
            log(f"  Filled tags")
    except Exception as e:
        log(f"  Tags fill skipped: {e}")
    page.screenshot(path=str(WORKSPACE / "screenshots" / f"{platform}_{kind}_filled.png"))
    log(f"\n  ===============================================")
    log(f"  ACTION NEEDED FROM USER:")
    log(f"  1. Upload the cover image (REQUIRED by the platform)")
    log(f"  2. Upload work samples / screenshots if needed")
    log(f"  3. Review the text fields above")
    log(f"  4. Click Save / Submit")
    log(f"  5. Copy the resulting URL")
    log(f"  6. Come back here and paste the URL")
    log(f"  ===============================================")
    try:
        url_input = input(">>> Paste the new portfolio URL here (or ENTER to skip): ").strip()
    except EOFError:
        url_input = ""
    if url_input:
        # Save to log
        log_file = OUT_DIR / f"{platform}_{kind}_created.json"
        log_file.write_text(
            json.dumps({
                "platform": platform, "kind": kind, "url": url_input,
                "title": copy_data.get("title", ""),
                "created_at": datetime.now().isoformat(),
            }, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        log(f"  Saved to {log_file}")
        return True
    return False


def main():
    ap = argparse.ArgumentParser(description="Create portfolio/service pages")
    ap.add_argument("kind", choices=["portfolio", "service"],
                    help="Type of page to create")
    ap.add_argument("platform", choices=["nafezly", "mostaql"],
                    help="Which platform")
    args = ap.parse_args()

    url = PORTFOLIO_URLS.get((args.kind, args.platform))
    if not url:
        log(f"  No URL mapping for ({args.kind}, {args.platform})")
        sys.exit(1)

    log("=" * 60)
    log(f"  {args.platform.upper()} {args.kind.upper()} creation")
    log(f"  URL: {url}")
    log("=" * 60)

    profile = load_profile()
    copy_data = engine_generate_copy(args.kind, args.platform, profile)
    if not copy_data:
        log("  Using local fallback copy from salim_profile.json")
        copy_data = {
            "title": profile.get("headline_ar", "AI Automation Engineer"),
            "description": profile.get("bio_ar_long", ""),
            "tags": profile.get("skill_tags_for_platforms", {}).get(args.platform, "").split(";"),
        }
    log(f"  Copy ready: {len(copy_data.get('description', ''))} chars")

    with SessionManager(
        platform=args.platform,
        signup_url=url,
        home_url=url.replace("/create", "").replace("/portfolio", ""),
        headless=False,
    ) as sm:
        page = sm.page
        ok = open_create_page(page, url, copy_data, args.kind, args.platform)
        if ok:
            sm.save_session_now()
        log(f"\n  Done. {'Created' if ok else 'Skipped'}: {url}")


if __name__ == "__main__":
    main()
