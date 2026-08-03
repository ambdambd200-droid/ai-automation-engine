"""
sentry.py — Hourly freelance sentry for Mostaql + Nafezly.

Automatically checks both platforms for new projects, scores them
for relevance using AI, generates personalized Arabic bids, and
submits them — text-only.

── WORKFLOW ──────────────────────────────────────────────────────────────
  1. Opens browser with your Brave profile (already logged in)
  2. Every N minutes (default 30):
     a. Scrape Mostaql + Nafezly for new projects
     b. Score each for relevance (AI + keywords)
     c. Generate personalized bid (skills/manager → AI → fallback)
      d. Submit bid, track in state (never re-bid)
     e. Submit bid, track in state (never re-bid)
     f. Respect daily quotas via quota.py

── USAGE ──────────────────────────────────────────────────────────────────
  # Run once (for testing)
  python sentry.py

  # Run forever, check every 30 minutes
  python sentry.py --loop

  # Run once without submitting (preview)
  python sentry.py --dry-run

  # Show state + daily counts
  python sentry.py --status
"""

from __future__ import annotations

import json
import os
import re
import sys
import time as _time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ═══════════════════════════════════════════════════════════════════════════
# PROJECT IMPORTS (with graceful fallback)
# ═══════════════════════════════════════════════════════════════════════════
WORKSPACE = Path(r"C:\Users\A\Desktop\Money")
sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(WORKSPACE / "skills"))

# quota.py — shared daily limits with hunt.py
try:
    from quota import can_send as quota_can_send, record_sent as quota_record_sent
    QUOTA_OK = True
except Exception:
    QUOTA_OK = False

# skills/manager.py — bid templates
try:
    from skills.manager import find_best_skill, apply_skill, learn_from_sent, save_skill
    SKILLS_OK = True
except Exception:
    SKILLS_OK = False

# keyhub_client.py — AI gateway
try:
    import keyhub_client
    AI_OK = True
except Exception:
    AI_OK = False

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
STATE_FILE = WORKSPACE / "sentry_state.json"
LOG_FILE = WORKSPACE / "sentry.log"
TEMP = WORKSPACE / "Temp"
TEMP.mkdir(exist_ok=True)

BRAVE_EXE = Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")
BRAVE_PROFILE = Path(r"C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data")

MOSTAQL_URLS = [
    "https://mostaql.com/projects/ai-machine-learning",
    "https://mostaql.com/projects/development",
]
NAFEZLY_URL = "https://nafezly.com/projects"

# Relevance scoring keywords
RELEVANCE_KEYWORDS = [
    "n8n", "automation", "أتمتة", "ai", "ذكاء اصطناعي",
    "workflow", "chatbot", "api", "integration", "تكامل",
    "python", "flask", "openai", "agent", "وكيل", "ربط",
    "scraping", "webhook", "telegram", "bot", "بوت",
    "برمجة", "development", "مطور", "backend", "تطوير",
    "site", "website", "موقع", "web", "script", "سكريبت",
    "database", "قاعدة بيانات", "server", "خادم",
    "automate", "ربط المواقع", "data", "بيانات",
    "full stack", "fullstack", "line bot", "notification",
]
SCORE_THRESHOLD = 0.15
DEFAULT_INTERVAL = 1800  # 30 minutes

# ═══════════════════════════════════════════════════════════════════════════
# STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "seen_projects": {},
        "bids_submitted": [],
        "last_checked": None,
        "session_started": datetime.now().isoformat(),
    }


def save_state(state: dict):
    """Atomic write: write to .tmp, then rename to prevent corruption on crash."""
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    tmp.replace(STATE_FILE)  # atomic on Windows (same filesystem)


def mark_seen(state: dict, url: str, status: str = "skipped", reason: str = ""):
    normalized = (
        url.rstrip("/").replace("https://www.", "https://")
        .replace("http://www.", "http://")
    )
    state.setdefault("seen_projects", {})[normalized] = {
        "first_seen": datetime.now().isoformat(),
        "status": status,
        "reason": reason,
    }
    save_state(state)


def can_send_quota(action: str) -> bool:
    """Check quota via quota.py. Falls back to a simple True if quota unavailable."""
    if QUOTA_OK:
        return quota_can_send(action)
    return True  # No quota tracking — allow


def record_quota(action: str, marker: str = ""):
    """Record a sent action via quota.py."""
    if QUOTA_OK:
        quota_record_sent(action, marker)


def cleanup_stale_state(state: dict, max_age_days: int = 7) -> int:
    """Remove seen_projects older than max_age_days. Returns count removed."""
    cutoff = datetime.now() - timedelta(days=max_age_days)
    seen = state.get("seen_projects", {})
    to_remove = [
        url for url, info in seen.items()
        if datetime.fromisoformat(info.get("first_seen", "")) < cutoff
    ]
    for url in to_remove:
        del seen[url]
    return len(to_remove)


# ═══════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def banner(text: str):
    bar = "=" * 60
    log(bar)
    log(f"  {text}")
    log(bar)


# ═══════════════════════════════════════════════════════════════════════════
# AI GATEWAY
# ═══════════════════════════════════════════════════════════════════════════

def ai_generate(prompt: str, system: Optional[str] = None,
                max_tokens: int = 1024) -> Optional[str]:
    if not AI_OK:
        return None
    try:
        return keyhub_client.ai_generate(
            prompt, system=system, max_tokens=max_tokens,
            model=os.environ.get("AI_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"),
            caller="sentry.py",
        )
    except Exception as e:
        log(f"  [AI ERROR] {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# RELEVANCE SCORING
# ═══════════════════════════════════════════════════════════════════════════

def score_project(title: str, description: str) -> Tuple[float, str]:
    text = (title + " " + description).lower()

    keyword_matches = sum(1 for kw in RELEVANCE_KEYWORDS if kw.lower() in text)
    keyword_score = min(keyword_matches / 5.0, 1.0)

    budget_match = re.search(r"(\d+)\s*[\$]?", text)
    budget_score = 1.0
    if budget_match:
        try:
            budget = int(budget_match.group(1))
            if budget < 10:
                budget_score = 0.2
            elif budget < 25:
                budget_score = 0.5
        except ValueError:
            pass

    length_bonus = min(len(description) / 500, 0.2)
    score = keyword_score * 0.6 + budget_score * 0.25 + length_bonus * 0.15

    # AI refinement for borderline cases
    if 0.2 < score < 0.6 and AI_OK:
        try:
            ai_result = ai_generate(
                f"Rate this project from 0 to 1 for an n8n/AI Automation Engineer. "
                f"Title: {title[:200]}\nDesc: {description[:500]}\nReturn ONLY a number.",
                max_tokens=10,
            )
            if ai_result:
                ai_score = float(ai_result.strip())
                score = (score + ai_score) / 2
        except Exception:
            pass

    reasons = [kw for kw in RELEVANCE_KEYWORDS[:5] if kw.lower() in text]
    reason = f"kw={keyword_score:.2f}, budget={budget_score:.2f}"
    if reasons:
        reason += f", matched={','.join(reasons[:3])}"
    return min(score, 1.0), reason


# ═══════════════════════════════════════════════════════════════════════════
# BID GENERATION
# ═══════════════════════════════════════════════════════════════════════════

def generate_bid(project_title: str, project_desc: str,
                 platform: str, budget: str = "") -> str:
    # Try skills library first
    if SKILLS_OK:
        try:
            skill = find_best_skill(
                "arabic_bid",
                context_keywords=[platform, "n8n", "automation", "arabic"],
            )
            if skill and skill.get("template"):
                result = apply_skill(skill, {
                    "n_workflows": "15",
                    "duration": "5",
                    "budget": budget or "50",
                    "project_title": project_title[:100],
                }, use_ai_polish=AI_OK)
                if result and len(result) > 50:
                    log(f"  [SKILL] Used '{skill['name']}'")
                    return result
        except Exception as e:
            log(f"  [SKILL ERROR] {e}")

    # AI fallback
    result = ai_generate(
        f"Write a proposal in FORMAL ARABIC (فصحى) for a project on {platform}.\n\n"
        f"Project: {project_title[:200]}\nDesc: {project_desc[:800]}\n"
        f"Budget: {budget or 'negotiable'}\n\n"
        f"Rules:\n"
        f"- Start with 'السلام عليكم'\n"
        f"- Introduce as 'علاء فتحي، مهندس أتمتة ذكاء اصطناعي'\n"
        f"- Show understanding of their specific project\n"
        f"- Mention n8n, Python, OpenAI\n"
        f"- Offer 3-4 deliverables\n"
        f"- Set a fair price\n"
        f"- MAX 200 words\n"
        f"- Output ONLY the proposal",
        max_tokens=900,
    )
    if result:
        return result.strip()

    # Ultimate fallback
    return (
        "السلام عليكم ورحمة الله وبركاته،\n\n"
        "أنا علاء فتحي، مهندس أتمتة ذكاء اصطناعي متخصص في n8n و Python. "
        f"أستطيع تنفيذ مشروع '{project_title[:60]}' بكفاءة عالية.\n\n"
        "خطة العمل:\n"
        "1. تحليل المتطلبات بالتفصيل\n"
        "2. تصميم وبناء الحل المناسب\n"
        "3. اختبار شامل\n"
        "4. تسليم مع توثيق\n\n"
        f"السعر: {budget or 'حسب الاتفاق'} دولار\n"
        "المدة: 3-7 أيام\n\n"
        "للتواصل، أنا جاهز.\n\nوشكراً،\nعلاء فتحي"
    )


# ═══════════════════════════════════════════════════════════════════════════
# LOGIN DETECTION (element-based, robust)
# ═══════════════════════════════════════════════════════════════════════════

def is_logged_in(page: Any) -> bool:
    """Check if user is logged in by looking for known post-login elements."""
    indicators = [
        "a[href*='/account']",
        "a[href*='/profile']",
        "a[href*='/logout']",
        "a[href*='/dashboard']",
        "img[alt*='profile'], img[alt*='avatar']",
        "[class*='avatar'], [class*='user-menu'], [class*='profile-photo']",
        "button:has-text('تسجيل الخروج'), a:has-text('تسجيل الخروج')",
        "button:has-text('Logout'), a:has-text('Logout')",
    ]
    for sel in indicators:
        try:
            if page.locator(sel).count() > 0:
                return True
        except Exception:
            continue
    # URL-based fallback
    url = page.url.lower()
    if "login" not in url and "register" not in url and "sign" not in url:
        return True
    return False


def wait_for_login(page: Any, platform_name: str, timeout_seconds: int = 600) -> bool:
    """Wait for user to log in. Checks every 5 seconds."""
    log(f"  Waiting for login to {platform_name}...")
    for _ in range(timeout_seconds // 5):
        _time.sleep(5)
        if is_logged_in(page):
            log(f"  ✅ Logged in to {platform_name}")
            return True
    log(f"  ⚠ Login timeout for {platform_name}, continuing...")
    return False


# ═══════════════════════════════════════════════════════════════════════════
# MOSTAQL SCRAPER + BIDDER
# ═══════════════════════════════════════════════════════════════════════════

def check_mostaql(page: Any, state: dict, dry_run: bool) -> int:
    banner("MOSTAQL CHECK")
    submitted = 0

    for url in MOSTAQL_URLS:
        if not can_send_quota("mostaql_bids"):
            log("  [QUOTA] Daily mostaql limit reached")
            break
        try:
            log(f"  Loading: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            _time.sleep(3)

            links = page.locator("a[href*='/project/']")
            project_urls = []
            for i in range(min(links.count(), 15)):
                try:
                    href = links.nth(i).get_attribute("href")
                    if href and "/project/" in href:
                        if not href.startswith("http"):
                            href = "https://mostaql.com" + href
                        if href not in project_urls:
                            project_urls.append(href)
                except Exception:
                    continue

            log(f"  Found {len(project_urls)} project(s)")

            for pu in project_urls:
                if not can_send_quota("mostaql_bids"):
                    break
                normalized = pu.rstrip("/").replace("https://www.", "https://")
                if normalized in state.get("seen_projects", {}):
                    continue
                try:
                    submitted += _process_mostaql_project(page, pu, state, dry_run)
                except Exception as e:
                    log(f"  [ERROR] {pu[:60]}: {e}")
                    mark_seen(state, pu, "error", str(e)[:100])
        except Exception as e:
            log(f"  [ERROR] Mostaql page: {e}")

    log(f"  Mostaql: {submitted} bid(s)")
    return submitted


def _process_mostaql_project(page: Any, url: str,
                              state: dict, dry_run: bool) -> int:
    log(f"  Opening: {url[:70]}...")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    _time.sleep(3)

    info = page.evaluate("""() => {
        const title = document.querySelector('h1, h2')?.innerText || '';
        const desc = document.querySelector(
            '[class*="desc"], [class*="detail"], [class*="content"], article, p'
        )?.innerText || '';
        const budget = document.querySelector('[class*="budget"], [class*="price"]')?.innerText || '';
        return { title, desc: desc.substring(0, 1000), budget };
    }""")

    if not info or not info.get("title"):
        log("    No title")
        mark_seen(state, url, "error", "no_title")
        return 0

    title, desc, budget = info["title"].strip(), info["desc"].strip(), info.get("budget", "").strip()
    log(f"    Title: {title[:70]}")

    score, reason = score_project(title, desc)
    log(f"    Score: {score:.2f} ({reason})")

    if score < SCORE_THRESHOLD:
        log(f"    [SKIP] Below threshold")
        mark_seen(state, url, "skipped", f"score={score:.2f}")
        return 0

    bid_text = generate_bid(title, desc, "mostaql", budget)
    log(f"    Bid: {len(bid_text)} chars")

    if dry_run:
        log(f"    [DRY-RUN] Would submit")
        mark_seen(state, url, "dry_run", f"score={score:.2f}")
        return 0

    # Click bid button
    clicked = page.evaluate("""() => {
        for (const el of document.querySelectorAll('button, a')) {
            const t = el.innerText.toLowerCase().trim();
            if (t.includes('تقديم') || t.includes('عرض') || t.includes('offer')) {
                el.click(); return true;
            }
        }
        return false;
    }""")
    if not clicked:
        log("    [SKIP] No bid button")
        mark_seen(state, url, "skipped", "no_bid_button")
        return 0
    _time.sleep(3)

    # Fill bid textarea
    filled = page.evaluate(f"""() => {{
        const ta = document.querySelector('textarea');
        if (!ta) return false;
        ta.value = {json.dumps(bid_text)};
        ta.dispatchEvent(new Event('input', {{bubbles: true}}));
        ta.dispatchEvent(new Event('change', {{bubbles: true}}));
        return true;
    }}""")
    if not filled:
        log("    [SKIP] No textarea")
        mark_seen(state, url, "skipped", "no_textarea")
        return 0
    _time.sleep(1)

    # Set price
    page.evaluate(f"""() => {{
        const pi = document.querySelector('input[type="number"], input[name*="price"], input[name*="budget"]');
        if (pi) {{ pi.value = '35'; pi.dispatchEvent(new Event('input', {{bubbles: true}})); }}
    }}""")

    # Submit
    submitted = page.evaluate("""() => {
        for (const el of document.querySelectorAll('button, input[type="submit"]')) {
            const t = el.innerText.toLowerCase().trim() || el.value?.toLowerCase().trim() || '';
            if (t.includes('إرسال') || t.includes('تقديم') || t.includes('submit')) {
                el.click(); return true;
            }
        }
        return false;
    }""")

    if submitted:
        log(f"    ✅ Bid submitted!")
        state.setdefault("bids_submitted", []).append({
            "url": url, "platform": "mostaql",
            "title": title[:60], "score": round(score, 2),
            "time": datetime.now().isoformat(),
        })
        mark_seen(state, url, "bid_submitted", f"score={score:.2f}")
        record_quota("mostaql_bids", url)
        _auto_learn_bid(bid_text, "mostaql_bid", title)
        _time.sleep(3)
        return 1

    log("    [WARN] Filled but no submit button")
    mark_seen(state, url, "filled_not_submitted", "no_submit_btn")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# NAFEZLY SCRAPER + BIDDER
# ═══════════════════════════════════════════════════════════════════════════

def check_nafezly(page: Any, state: dict, dry_run: bool) -> int:
    banner("NAFEZLY CHECK")
    if not can_send_quota("nafezly_bids"):
        log("  [QUOTA] Daily nafezly limit reached")
        return 0

    try:
        log(f"  Loading: {NAFEZLY_URL}")
        page.goto(NAFEZLY_URL, wait_until="domcontentloaded", timeout=60000)
        _time.sleep(3)

        links = page.locator("a[href*='/project/']")
        project_urls = []
        for i in range(min(links.count(), 15)):
            try:
                href = links.nth(i).get_attribute("href")
                if href and "/project/" in href:
                    if not href.startswith("http"):
                        href = "https://nafezly.com" + href
                    if href not in project_urls:
                        project_urls.append(href)
            except Exception:
                continue

        log(f"  Found {len(project_urls)} project(s)")
        submitted = 0
        for pu in project_urls:
            if not can_send_quota("nafezly_bids"):
                break
            normalized = pu.rstrip("/").replace("https://www.", "https://")
            if normalized in state.get("seen_projects", {}):
                continue
            try:
                submitted += _process_nafezly_project(page, pu, state, dry_run)
            except Exception as e:
                log(f"  [ERROR] {pu[:60]}: {e}")
                mark_seen(state, pu, "error", str(e)[:100])

        log(f"  Nafezly: {submitted} bid(s)")
        return submitted
    except Exception as e:
        log(f"  [ERROR] Nafezly: {e}")
        return 0


def _process_nafezly_project(page: Any, url: str,
                              state: dict, dry_run: bool) -> int:
    log(f"  Opening: {url[:70]}...")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    _time.sleep(3)

    info = page.evaluate("""() => {
        const title = document.querySelector('h1, h2')?.innerText || '';
        const desc = document.querySelector(
            '[class*="desc"], [class*="detail"], [class*="content"], article, p'
        )?.innerText || '';
        return { title, desc: desc.substring(0, 1000) };
    }""")

    if not info or not info.get("title"):
        log("    No title")
        mark_seen(state, url, "error", "no_title")
        return 0

    title, desc = info["title"].strip(), info["desc"].strip()
    log(f"    Title: {title[:70]}")

    score, reason = score_project(title, desc)
    log(f"    Score: {score:.2f} ({reason})")

    if score < SCORE_THRESHOLD:
        log(f"    [SKIP] Below threshold")
        mark_seen(state, url, "skipped", f"score={score:.2f}")
        return 0

    bid_text = generate_bid(title, desc, "nafezly")
    log(f"    Bid: {len(bid_text)} chars")

    if dry_run:
        log(f"    [DRY-RUN] Would submit")
        mark_seen(state, url, "dry_run", f"score={score:.2f}")
        return 0

    # Click bid button
    clicked = page.evaluate("""() => {
        for (const el of document.querySelectorAll('button, a')) {
            const t = el.innerText.toLowerCase().trim();
            if (t.includes('تقديم') || t.includes('عرض') || t.includes('offer')) {
                el.click(); return true;
            }
        }
        return false;
    }""")
    if not clicked:
        log("    [SKIP] No bid button")
        mark_seen(state, url, "skipped", "no_bid_button")
        return 0
    _time.sleep(3)

    # Fill bid textarea
    filled = page.evaluate(f"""() => {{
        const ta = document.querySelector('textarea');
        if (!ta) return false;
        ta.value = {json.dumps(bid_text)};
        ta.dispatchEvent(new Event('input', {{bubbles: true}}));
        ta.dispatchEvent(new Event('change', {{bubbles: true}}));
        return true;
    }}""")
    if not filled:
        log("    [SKIP] No textarea")
        mark_seen(state, url, "skipped", "no_textarea")
        return 0
    _time.sleep(1)

    # Submit
    submitted = page.evaluate("""() => {
        for (const el of document.querySelectorAll('button, input[type="submit"]')) {
            const t = el.innerText.toLowerCase().trim() || el.value?.toLowerCase().trim() || '';
            if (t.includes('إرسال') || t.includes('تقديم') || t.includes('submit')
                || t.includes('send')) {
                el.click(); return true;
            }
        }
        return false;
    }""")

    if submitted:
        log("    ✅ Bid submitted!")
        state.setdefault("bids_submitted", []).append({
            "url": url, "platform": "nafezly",
            "title": title[:60], "score": round(score, 2),
            "time": datetime.now().isoformat(),
        })
        mark_seen(state, url, "bid_submitted",
                  f"score={score:.2f}")
        record_quota("nafezly_bids", url)
        _auto_learn_bid(bid_text, "nafezly_bid", title)
        _time.sleep(3)
        return 1

    log("    [WARN] Filled but no submit button")
    mark_seen(state, url, "filled_not_submitted", "no_submit_btn")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# AUTO-LEARN
# ═══════════════════════════════════════════════════════════════════════════

def _auto_learn_bid(bid_text: str, bid_type: str, project_title: str):
    if not SKILLS_OK:
        return
    try:
        item = {"type": bid_type, "body": bid_text,
                "project_title": project_title, "to": "", "subject": project_title}
        draft = learn_from_sent(item)
        if draft:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            draft["name"] = f"learning/{bid_type}_{ts}"
            draft["source"] = {"platform": bid_type, "project_title": project_title,
                               "learned_at": datetime.now().isoformat(), "auto_sentry": True}
            if save_skill(draft["name"], draft):
                log(f"  [LEARN] Saved: {draft['name']}")
    except Exception as e:
        log(f"  [LEARN ERROR] {e}")


# ═══════════════════════════════════════════════════════════════════════════
# STATUS
# ═══════════════════════════════════════════════════════════════════════════

def show_status():
    state = load_state()
    banner("SENTRY STATUS")
    print(f"  Session started:  {state.get('session_started', 'N/A')}")
    print(f"  Last checked:     {state.get('last_checked', 'never')}")
    print(f"  Seen projects:    {len(state.get('seen_projects', {}))}")
    print(f"  Bids submitted:   {len(state.get('bids_submitted', []))}")
    print()

    # Show quota status via quota.py
    if QUOTA_OK:
        try:
            from quota import show_status as quota_show
            quota_show()
        except Exception:
            pass
    else:
        print("  (quota.py not available)")
    print()

    if state.get("bids_submitted"):
        print("  Recent bids:")
        for b in state["bids_submitted"][-5:]:
            print(f"    [{b.get('time','?')[:16]}] {b['platform']:8s} "
                  f"score={b.get('score','?'):.2f}  {b.get('title','')[:50]}")
    print()


# ═══════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════

def run_once(page: Any, state: dict, dry_run: bool) -> int:
    total = 0
    total += check_mostaql(page, state, dry_run)
    total += check_nafezly(page, state, dry_run)
    state["last_checked"] = datetime.now().isoformat()
    removed = cleanup_stale_state(state)
    save_state(state)
    return total


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="sentry.py — Hourly freelance sentry for Mostaql + Nafezly")
    parser.add_argument("--loop", action="store_true",
                        help="Run in continuous loop")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL,
                        help=f"Check interval in seconds (default {DEFAULT_INTERVAL})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without submitting")
    parser.add_argument("--status", action="store_true",
                        help="Show state and daily counts")
    parser.add_argument("--fresh-profile", action="store_true",
                        help="Use fresh browser profile (default: use Brave profile)")
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    state = load_state()
    dry_run = args.dry_run

    # Log startup info
    banner(f"SENTRY START — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"  Dry-run: {dry_run}")
    log(f"  AI available: {AI_OK}")
    log(f"  Skills available: {SKILLS_OK}")
    log(f"  Quota available: {QUOTA_OK}")

    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()

    # Default: use Brave profile (user is already logged in)
    if not args.fresh_profile:
        log(f"  Using Brave profile (default)")
        context = pw.chromium.launch_persistent_context(
            user_data_dir=str(BRAVE_PROFILE),
            executable_path=str(BRAVE_EXE),
            headless=False,
            args=["--no-sandbox"],
            viewport={"width": 1366, "height": 768},
        )
    else:
        log(f"  Using fresh browser profile")
        context = pw.chromium.launch_persistent_context(
            user_data_dir=str(TEMP / ".sentry_browser_data"),
            headless=False,
            args=["--no-sandbox"],
            viewport={"width": 1366, "height": 768},
        )

    page = context.new_page()
    page.set_default_timeout(120000)

    # Login — quick check (user is already logged in via Brave profile)
    banner("LOGIN")
    log("Opening Mostaql...")
    page.goto("https://mostaql.com", wait_until="domcontentloaded")
    if not is_logged_in(page):
        log("  ⚠ Not detected as logged in. Waiting 30s for manual login...")
        for _ in range(6):
            _time.sleep(5)
            if is_logged_in(page):
                log("  ✅ Logged in!")
                break
    else:
        log("  ✅ Already logged in (Brave profile)")

    log("Opening Nafezly...")
    page2 = context.new_page()
    try:
        page2.goto("https://nafezly.com", wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        log(f"  ⚠ Nafezly load: {e} (continuing)")
    if not is_logged_in(page2):
        log("  ⚠ Not detected as logged in. Waiting 30s for manual login...")
        for _ in range(6):
            _time.sleep(5)
            if is_logged_in(page2):
                log("  ✅ Logged in!")
                break
    else:
        log("  ✅ Already logged in (Brave profile)")
    page2.close()

    log("")
    log("  Ready! Starting checks...")
    log("")

    if args.loop:
        banner(f"LOOP MODE — interval {args.interval}s")
        cycle = 0
        try:
            while True:
                cycle += 1
                banner(f"CYCLE {cycle} — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                try:
                    total = run_once(page, state, dry_run)
                    log(f"  Cycle {cycle}: {total} bid(s)")
                except Exception as e:
                    log(f"  [LOOP ERROR] {e}")
                    import traceback
                    traceback.print_exc()
                log(f"  Sleep {args.interval}s...")
                _time.sleep(args.interval)
        except KeyboardInterrupt:
            log("\nStopped by user.")
    else:
        try:
            total = run_once(page, state, dry_run)
            log(f"  Done: {total} bid(s)")
        except Exception as e:
            log(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()

    # Auto-close after 5 minutes idle to prevent RAM leak
    log("Browser stays open for review (auto-closes in 5 min).")
    try:
        for _ in range(300):
            _time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        log("Closing browser...")
        context.close()
        pw.stop()
        log("Browser closed.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\nAborted (Ctrl+C).")
        sys.exit(1)
