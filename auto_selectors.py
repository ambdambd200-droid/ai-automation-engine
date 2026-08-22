"""
auto_selectors.py — Smart Selector Discovery for freelance platforms.

Automatically discovers working CSS selectors by analyzing live DOM.
Fallback when hardcoded selectors fail.
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import quote
from collections import Counter

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False

# Add project root to path
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

try:
    from session_manager import SessionManager
    from security_utils import sanitize_url, sanitize_input
except ImportError as e:
    print(f"[auto_selectors] Import warning: {e}")

SEARCH_URLS = {
    "mostaql": "https://mostaql.com/projects?keyword={kw}&sort=date_desc",
    "nafezly": "https://nafezly.com/projects?keyword={kw}",
}

CACHE_DIR = BASE_DIR / "selectors"
CACHE_DIR.mkdir(exist_ok=True)


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}".encode('ascii', 'replace').decode('ascii'), flush=True)


def notify_telegram(message: str) -> bool:
    """Send notification via Telegram if configured."""
    try:
        from telegram_notifier import notify
        return notify(message)
    except Exception:
        return False


def analyze_card_structure(page, platform: str, max_cards: int = 20) -> dict:
    """
    Analyze DOM structure of project cards to find common patterns.
    Returns dict with suggested selectors for: card, title, link, budget, description.
    """
    log(f"[{platform}] Analyzing DOM structure...")
    
    # Get all potential card elements using broad selectors
    broad_selectors = [
        "article", "div.card", "li", ".item", ".project", ".job",
        "[data-testid*='card']", "[data-testid*='project']", "[data-testid*='job']",
        ".project-card", ".job-card", ".project-item", ".job-item",
        "section", ".post", ".listing", ".result"
    ]
    
    all_elements = []
    for sel in broad_selectors:
        try:
            elements = page.locator(sel).all()
            if elements:
                all_elements.extend(elements)
                log(f"  Found {len(elements)} elements with '{sel}'")
        except Exception:
            continue
    
    if not all_elements:
        log("  No elements found with broad selectors")
        return {}
    
    # Analyze each element for project-like characteristics
    card_candidates = []
    for el in all_elements[:max_cards * 3]:
        try:
            # Check if element looks like a project card
            text = el.inner_text() if hasattr(el, 'inner_text') else ""
            if not text or len(text) < 20:
                continue
            
            # Look for project-like keywords
            text_lower = text.lower()
            project_keywords = ['n8n', 'automation', 'api', 'python', 'bot', 'webhook', 
                               'تلقرام', 'واتساب', 'أتمتة', 'بوت', 'مشاريع', 'مشروع']
            if not any(kw in text_lower for kw in project_keywords):
                continue
            
            # Get element info
            tag = el.evaluate("el => el.tagName.toLowerCase()")
            classes = el.get_attribute("class") or ""
            id_attr = el.get_attribute("id") or ""
            testid = el.get_attribute("data-testid") or ""
            
            # Find title element
            title_el = el.locator("h1, h2, h3, h4, .title, .project-title, a").first
            title_text = title_el.inner_text().strip() if title_el.count() > 0 else ""
            
            # Find link
            link_el = el.locator("a[href]").first
            href = link_el.get_attribute("href") if link_el.count() > 0 else ""
            
            # Find budget
            budget_text = ""
            for budget_sel in [".budget", ".price", ".amount", "[class*='budget']", "[class*='price']"]:
                budget_el = el.locator(budget_sel).first
                if budget_el.count() > 0:
                    budget_text = budget_el.inner_text().strip()
                    break
            
            card_candidates.append({
                "tag": tag,
                "classes": classes,
                "id": id_attr,
                "testid": testid,
                "title": title_text[:100],
                "href": href,
                "budget": budget_text[:50],
                "text_preview": text[:200],
            })
        except Exception:
            continue
    
    log(f"  Found {len(card_candidates)} candidate cards")
    
    if not card_candidates:
        return {}
    
    # Analyze patterns to generate selectors
    class_counter = Counter()
    tag_counter = Counter()
    testid_counter = Counter()
    
    for c in card_candidates:
        for cls in c["classes"].split():
            if cls and len(cls) > 2:
                class_counter[cls] += 1
        tag_counter[c["tag"]] += 1
        if c["testid"]:
            testid_counter[c["testid"]] += 1
    
    # Generate selector suggestions
    best_classes = [cls for cls, count in class_counter.most_common(10) if count >= 2]
    best_tags = [tag for tag, count in tag_counter.most_common(5)]
    best_testids = [tid for tid, count in testid_counter.most_common(5) if count >= 2]
    
    # Build selector recommendations
    card_selectors = []
    for cls in best_classes[:5]:
        card_selectors.append(f".{cls}")
    for tag in best_tags[:3]:
        card_selectors.append(tag)
    for tid in best_testids[:3]:
        card_selectors.append(f"[data-testid='{tid}']")
    
    # Title selectors
    title_selectors = ["h1", "h2", "h3", "h4", ".title", ".project-title", ".job-title", "a"]
    
    # Link selectors
    link_selectors = ["a[href]", "h3 a", "h2 a", ".title a", ".project-title a"]
    
    # Budget selectors
    budget_selectors = [".budget", ".price", ".amount", "[class*='budget']", "[class*='price']", "[class*='cost']"]
    
    return {
        "card": list(dict.fromkeys(card_selectors))[:8],
        "title": title_selectors,
        "link": link_selectors,
        "budget": budget_selectors,
        "timestamp": datetime.now().isoformat(),
        "source": "auto_discovery",
        "sample_count": len(card_candidates),
        "top_classes": dict(class_counter.most_common(10)),
    }


def discover_selectors(platform: str, keyword: str = "n8n", headless: bool = False) -> dict:
    """
    Main discovery function. Opens platform search page and analyzes DOM.
    Uses SessionManager to load saved session (cookies/auth).
    """
    if platform not in SEARCH_URLS:
        raise ValueError(f"Unknown platform: {platform}")
    
    url = SEARCH_URLS[platform].format(kw=quote(keyword))
    
    log(f"[{platform}] Starting selector discovery for keyword: {keyword}")
    log(f"[{platform}] URL: {SEARCH_URLS[platform].format(kw=keyword)}")
    
    # Notify Telegram
    notify_telegram(f"Auto-Discovery Started\nPlatform: {platform}\nKeyword: {keyword}")
    
    results = {}
    
    if not PLAYWRIGHT_OK:
        log("ERROR: Playwright not installed")
        return {}
    
    # Use SessionManager to load saved session
    with SessionManager(
        platform=platform,
        signup_url=SEARCH_URLS[platform].format(kw=""),
        home_url=SEARCH_URLS[platform].format(kw=""),
        headless=headless,
    ) as sm:
        page = sm.page
        
        try:
            url_full = SEARCH_URLS[platform].format(kw=quote(keyword))
            log(f"[{platform}] Navigating to: {url_full}")
            page.goto(url_full, wait_until="domcontentloaded", timeout=30000)
            time.sleep(5)  # Wait for dynamic content
            
            # Scroll to load more content
            for _ in range(3):
                page.evaluate("window.scrollBy(0, 1000)")
                time.sleep(1)
            
            # Analyze
            results = analyze_card_structure(page, platform)
            
            if results:
                log(f"[{platform}] Discovery successful!")
                log(f"  Card selectors: {results.get('card', [])}")
                log(f"  Sample count: {results.get('sample_count', 0)}")
            else:
                log(f"[{platform}] No patterns found")
            
        except Exception as e:
            log(f"[{platform}] Discovery error: {e}")
            results = {"error": str(e)}
    
    # Save to cache
    cache_file = CACHE_DIR / f"{platform}.json"
    cache_data = {
        "platform": platform,
        "keyword": keyword,
        "discovered_at": datetime.now().isoformat(),
        "selectors": results,
    }
    cache_file.write_text(json.dumps(cache_data, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"[{platform}] Saved selectors to {cache_file}")
    
    # Notify Telegram
    if results and "error" not in results:
        notify_telegram(
            f"Auto-Discovery Complete\n"
            f"Platform: {platform}\n"
            f"Card selectors found: {len(results.get('card', []))}\n"
            f"Samples analyzed: {results.get('sample_count', 0)}"
        )
    else:
        notify_telegram(f"Auto-Discovery Failed\nPlatform: {platform}\nError: {results.get('error', 'No patterns found')}")
    
    return results


def load_cached_selectors(platform: str) -> dict:
    """Load cached selectors from file."""
    cache_file = CACHE_DIR / f"{platform}.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def get_best_selectors(platform: str, keyword: str = "n8n", force_refresh: bool = False) -> dict:
    """
    Get best selectors for platform. Uses cache if available and not expired.
    """
    cache = load_cached_selectors(platform)
    
    if not force_refresh and cache and "selectors" in cache:
        selectors = cache["selectors"]
        if selectors and "error" not in selectors and selectors.get("card"):
            age = datetime.now() - datetime.fromisoformat(cache["discovered_at"])
            if age.days < 7:  # Cache valid for 7 days
                log(f"[{platform}] Using cached selectors (age: {age.days}d)")
                return selectors
    
    # Cache miss or expired - discover new
    log(f"[{platform}] Cache miss/expired, discovering new selectors...")
    return discover_selectors(platform, keyword)


def main():
    ap = argparse.ArgumentParser(description="Auto-discover CSS selectors for freelance platforms")
    ap.add_argument("--platform", choices=["mostaql", "nafezly", "both"], default="both")
    ap.add_argument("--keyword", default="n8n", help="Search keyword")
    ap.add_argument("--headless", action="store_true", help="Run headless")
    ap.add_argument("--force", action="store_true", help="Force refresh cache")
    args = ap.parse_args()
    
    platforms = ["mostaql", "nafezly"] if args.platform == "both" else [args.platform]
    
    for platform in platforms:
        log(f"\n{'='*60}")
        log(f"Discovering selectors for: {platform}")
        log(f"{'='*60}")
        
        result = get_best_selectors(platform, args.keyword, force_refresh=args.force)
        
        if result and "error" not in result:
            log(f"[OK] {platform}: {len(result.get('card', []))} card selectors found")
            for sel in result.get("card", [])[:5]:
                log(f"  - {sel}")
        else:
            log(f"[FAIL] {platform}: {result.get('error', 'Failed')}")
    
    # Notify completion
    notify_telegram(f"Auto-Discovery Batch Complete\nPlatforms: {', '.join(platforms)}")


if __name__ == "__main__":
    main()