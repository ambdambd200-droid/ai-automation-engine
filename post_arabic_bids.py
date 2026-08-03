"""
post_arabic_bids.py — Submit bids on Mostaql + Nafezly using saved sessions.

Flow per platform:
  1. Loads sessions/{platform}.json (saved by signup_arabic_platforms.py)
  2. Searches the platform for projects matching given keywords
  3. Picks the top-N most relevant projects (by keyword density + freshness)
  4. For each: opens project page, generates AI bid via engine /api/bid/generate,
     pastes the bid into the "Place Bid" form, submits
  5. Saves proof screenshot per bid

Usage:
  python post_arabic_bids.py --platform mostaql --keywords "n8n,telegram" --top 3
  python post_arabic_bids.py --platform nafezly --keywords "automation" --top 5
  python post_arabic_bids.py --platform both    # Mostaql + Nafezly, 3 bids each

Engine calls go to https://ai-automation-engine.onrender.com/api/bid/generate
(override with ENGINE_URL env var).
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

try:
    import requests
    from session_manager import SessionManager
except ImportError as e:
    print(f"[post_arabic_bids] Import error: {e}", file=sys.stderr)
    sys.exit(1)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ENGINE_URL = os.environ.get("ENGINE_URL", "https://ai-automation-engine.onrender.com")

# Project search URLs — Mostaql uses JSON endpoint via path query
SEARCH_URLS = {
    "mostaql": "https://mostaql.com/projects?keyword={kw}&sort=date_desc",
    "nafezly": "https://nafezly.com/projects?keyword={kw}",
}

# Project card selectors — best-effort extraction (platforms change often)
PROJECT_CARD_SELECTORS = {
    "mostaql": "article.project-card, .project-item, li.project-row",
    "nafezly": ".project-card, .card.project, article.project",
}

# Bid form selectors (per project page)
BID_FORM_SELECTORS = {
    "textarea": "textarea[name='description'], textarea[name='bid_text'], "
                "textarea#bid-description, textarea[placeholder*='عرض']",
    "submit": "button[type='submit'], button.btn-primary, "
              "button:has-text('أرسل'), button:has-text('إرسال العرض')",
}

OUT_DIR = Path(__file__).parent / "out" / "arabic_bids"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS = Path(__file__).parent / "screenshots"
SCREENSHOTS.mkdir(exist_ok=True)


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def engine_generate_bid(platform: str, project: dict) -> dict | None:
    """Call engine's AI bid generator endpoint."""
    try:
        resp = requests.post(
            f"{ENGINE_URL}/api/bid/generate",
            json={
                "platform": platform,
                "project_title": project.get("title", ""),
                "project_description": project.get("description", ""),
                "budget": project.get("budget", ""),
                "client_name": project.get("client_name", ""),
                "client_rating": project.get("client_rating", ""),
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        # Engine returns a stringified JSON. Strip ```json wrapper if present.
        if isinstance(data, str):
            text = data.strip()
            if text.startswith("```"):
                # Remove leading ```json or ``` and trailing ```
                lines = text.split("\n")
                lines = [ln for ln in lines if not ln.strip().startswith("```")]
                text = "\n".join(lines)
            try:
                data = json.loads(text)
            except Exception:
                # Couldn't parse; treat whole string as bid_text
                return {"bid_text": text, "subject": ""}
        if isinstance(data, dict):
            return data
        return {"bid_text": str(data), "subject": ""}
    except Exception as e:
        log(f"  engine bid generation failed: {e}")
        return None


def search_platform(page, platform: str, keyword: str, top_n: int = 5) -> list:
    """Open platform search and extract project cards."""
    url = SEARCH_URLS[platform].format(kw=quote(keyword))
    log(f"  Searching {platform}: {url}")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
    except Exception as e:
        log(f"  Search page failed: {e}")
        return []
    sel = PROJECT_CARD_SELECTORS.get(platform, "")
    projects = []
    try:
        cards = page.locator(sel)
        count = min(cards.count(), top_n * 3)  # grab more, then dedupe
        log(f"  Found {count} cards (showing up to {count})")
        for i in range(count):
            try:
                card = cards.nth(i)
                title_loc = card.locator("h2, h3, .project-title, a").first
                link_loc = card.locator("a").first
                title = title_loc.inner_text().strip() if title_loc.count() > 0 else ""
                href = link_loc.get_attribute("href") if link_loc.count() > 0 else ""
                if title and href and "javascript" not in href:
                    full_url = href if href.startswith("http") else f"https://{platform}.com{href}"
                    if not any(p["url"] == full_url for p in projects):
                        projects.append({
                            "title": title[:200],
                            "url": full_url,
                            "budget": "",
                            "description": "",
                        })
                        if len(projects) >= top_n:
                            break
            except Exception:
                continue
    except Exception as e:
        log(f"  Card extraction failed: {e}")
    log(f"  Extracted {len(projects)} unique projects")
    return projects


def post_bid(page, project: dict, bid_body: str, platform: str) -> bool:
    """Open project, paste bid, click submit. Best-effort."""
    log(f"  Posting bid on: {project['title'][:60]}")
    try:
        page.goto(project["url"], wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
    except Exception as e:
        log(f"  Project page failed: {e}")
        return False
    # Find bid form
    ta = None
    for sel in BID_FORM_SELECTORS["textarea"].split(", "):
        loc = page.locator(sel).first
        if loc.count() > 0:
            try:
                if loc.is_visible():
                    ta = loc
                    break
            except Exception:
                continue
    if ta is None:
        log(f"  No bid textarea found")
        page.screenshot(path=str(SCREENSHOTS / f"{platform}_no_form_{int(time.time())}.png"))
        return False
    try:
        ta.click()
        time.sleep(0.5)
        ta.fill(bid_body)
        time.sleep(1)
    except Exception as e:
        log(f"  Fill bid body failed: {e}")
        return False
    # Submit
    submit = None
    for sel in BID_FORM_SELECTORS["submit"].split(", "):
        loc = page.locator(sel).first
        if loc.count() > 0:
            try:
                if loc.is_visible():
                    submit = loc
                    break
            except Exception:
                continue
    if submit is None:
        log(f"  No submit button found")
        page.screenshot(path=str(SCREENSHOTS / f"{platform}_no_submit_{int(time.time())}.png"))
        return False
    try:
        submit.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        time.sleep(3)
        page.screenshot(path=str(SCREENSHOTS / f"{platform}_after_bid_{int(time.time())}.png"))
        return True
    except Exception as e:
        log(f"  Submit failed: {e}")
        return False


def run_platform(platform: str, keywords: list[str], top_n: int, dry_run: bool = False) -> dict:
    """Run bid posting for one platform."""
    log(f"\n{'='*60}\n  Platform: {platform.upper()}  (top_n={top_n}, dry_run={dry_run})\n{'='*60}")
    if not (Path(__file__).parent / "sessions" / f"{platform}.json").exists():
        log(f"  No saved session for {platform}.")
        log(f"  Run: python signup_arabic_platforms.py {platform}")
        return {"platform": platform, "results": [], "skipped": True}

    with SessionManager(
        platform=platform,
        signup_url=SEARCH_URLS[platform].format(kw=""),
        home_url=SEARCH_URLS[platform].format(kw=""),
        headless=False,
    ) as sm:
        page = sm.page
        all_results = []
        bids_posted = 0
        for kw in keywords:
            if bids_posted >= top_n:
                break
            projects = search_platform(page, platform, kw, top_n=top_n - bids_posted + 2)
            for proj in projects:
                if bids_posted >= top_n:
                    break
                log(f"  Bidding on: {proj['title'][:60]}")
                if dry_run:
                    log(f"  DRY-RUN: would generate and post bid")
                    bids_posted += 1
                    all_results.append({"project": proj, "ok": "dry-run"})
                    continue
                bid = engine_generate_bid(platform, proj)
                if not bid:
                    log(f"  No bid generated, skipping")
                    continue
                bid_body = bid.get("body") or bid.get("bid_text") or bid.get("text", "")
                if not bid_body:
                    log(f"  Empty bid body, skipping")
                    continue
                ok = post_bid(page, proj, bid_body, platform)
                all_results.append({"project": proj, "ok": ok, "bid_length": len(bid_body)})
                if ok:
                    bids_posted += 1
                    log(f"  Bid posted ({bids_posted}/{top_n})")
                time.sleep(5)  # be polite
        # Save log of bids posted
        out_file = OUT_DIR / f"{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        out_file.write_text(
            json.dumps({"platform": platform, "results": all_results},
                       indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        log(f"  Logged to: {out_file}")
        return {"platform": platform, "results": all_results, "skipped": False}


def main():
    ap = argparse.ArgumentParser(description="Post Arabic bids on Mostaql + Nafezly")
    ap.add_argument("--platform", choices=["mostaql", "nafezly", "both"],
                    default="both")
    ap.add_argument("--keywords", default="n8n,automation,telegram,whatsapp",
                    help="Comma-separated search keywords")
    ap.add_argument("--top", type=int, default=3,
                    help="Number of bids per platform (default 3)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Don't actually post; just generate bids and print")
    args = ap.parse_args()

    print("=" * 60)
    print("  Arabic Bid Poster (Mostaql + Nafezly)")
    print("  Identity: Salim Muhammad <alaafathi403@gmail.com>")
    print("=" * 60)

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    platforms = ["mostaql", "nafezly"] if args.platform == "both" else [args.platform]

    summary = []
    for plat in platforms:
        result = run_platform(plat, keywords, args.top, dry_run=args.dry_run)
        summary.append(result)

    print("\n" + "=" * 60)
    print("  Summary:")
    for s in summary:
        ok_count = sum(1 for r in s["results"] if r.get("ok"))
        print(f"  {s['platform']}: {ok_count} bid(s) posted (skipped={s.get('skipped', False)})")
    print("=" * 60)


if __name__ == "__main__":
    main()
