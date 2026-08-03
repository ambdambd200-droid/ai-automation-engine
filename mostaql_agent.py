"""
mostaql_agent.py — Autonomous Mostaql Agent (منصة مستقل).

Handles the full Mostaql workflow:
- Login/session management via Playwright + Brave profile
- Search projects matching n8n/AI/automation keywords
- Classify and score projects using keywords + AI (Gemini)
- Generate Arabic bids using skills library → AI → fallback
- Submit bids via browser automation
- Check notifications/replies
- Learn from sent bids (save as skills)
- Track state and respect daily quotas

Usage:
    python mostaql_agent.py                    # Auto mode: search + classify + decide
    python mostaql_agent.py --check            # Search projects, write to hunt_decisions.md
    python mostaql_agent.py --bid URL          # Generate + submit bid for a specific project
    python mostaql_agent.py --login            # Open browser for manual login
    python mostaql_agent.py --notifications    # Check Mostaql notifications
    python mostaql_agent.py --status           # Show state + quotas
    python mostaql_agent.py --learn            # Convert sent bids into skills
"""

import os
import sys
import json
import re
import time
import random
from datetime import datetime, date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = Path(__file__).parent
STATE_FILE = WORKSPACE / "mostaql_agent_state.json"
LOG_FILE = WORKSPACE / "mostaql_agent.log"
DECISIONS_FILE = WORKSPACE / "hunt_decisions.md"
LEARNING_DIR = WORKSPACE / "skills" / "learning" / "mostaql_bids"

BRAVE_EXE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
BRAVE_PROFILE = r"C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data"

# Mostaql search URLs - Arabic keywords for automation/n8n/AI
MOSTAQL_SEARCH_URLS = [
    ("n8n automation", "https://mostaql.com/projects?skill=n8n"),
    ("AI automation", "https://mostaql.com/projects?skill=artificial-intelligence"),
    ("Python bot", "https://mostaql.com/projects?skill=python"),
    ("أتمتة", "https://mostaql.com/projects?skill=%D8%A3%D8%AA%D9%85%D8%AA%D8%A9"),
    ("بوت", "https://mostaql.com/projects?skill=%D8%A8%D9%88%D8%AA"),
    ("ذكاء اصطناعي", "https://mostaql.com/projects?skill=%D8%B0%D9%83%D8%A7%D8%A1+%D8%A7%D8%B5%D8%B7%D9%86%D8%A7%D9%8A"),
    ("n8n", "https://mostaql.com/projects?skill=n8n"),
    ("workflow", "https://mostaql.com/projects?skill=workflow"),
]

sys.path.insert(0, str(WORKSPACE))
try:
    from keyhub_client import ai_generate, ai_generate_json
    from quota import can_send, record_sent, get_remaining
    sys.path.insert(0, str(WORKSPACE / "skills"))
    from manager import save_skill
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
    return {"projects_seen": {}, "bids_sent": [], "notifications_checked": None}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def write_decision(item_id, action_type, project, bid_text):
    entry = f"""
## DECISION: {item_id}
ACTION: send
TYPE: {action_type}
PLATFORM: mostaql
TO: {project.get('owner', 'mostaql_client')}
PROJECT: {project.get('title', 'Untitled')[:80]}
URL: {project.get('url', '')}
PRICE: {project.get('price', 'negotiable')}
BODY_AR:
{bid_text}

---
"""
    with open(DECISIONS_FILE, "a", encoding="utf-8") as f:
        f.write(entry)
    log(f"  -> Wrote decision {item_id} to hunt_decisions.md")


def learn_from_bid(project, bid_text, classification):
    LEARNING_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = re.sub(r"[^a-zA-Z0-9_\u0600-\u06FF]", "_", project.get("title", "bid")[:30])
    filename = f"learned_{timestamp}_{safe_title}.json"
    skill = {
        "name": f"learning/mostaql_bids/{filename.replace('.json', '')}",
        "type": "arabic_bid",
        "language": "ar",
        "tags": ["mostaql", "learned", classification, "arabic", "n8n", "automation"],
        "uses": 0,
        "version": 1,
        "created": datetime.now().isoformat(),
        "source": {
            "platform": "mostaql",
            "project_title": project.get("title", "")[:100],
            "project_url": project.get("url", ""),
            "classification": classification,
            "bid_preview": bid_text[:200],
        },
    }
    if save_skill(skill["name"], skill):
        log(f"  -> Learned: saved + indexed as {skill['name']}")
    else:
        log(f"  -> Learned: file write failed for {skill['name']}")


def _launch_browser():
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=BRAVE_PROFILE,
        executable_path=BRAVE_EXE,
        headless=False,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        viewport={"width": 1366, "height": 768},
    )
    page = ctx.new_page()
    page.set_default_timeout(180000)
    return pw, ctx, page


def _wait_login(page, timeout=120):
    if "login" in page.url.lower() or "register" in page.url.lower():
        log(f"  Login required — waiting {timeout}s for manual login...")
        for _ in range(timeout):
            time.sleep(1)
            if "login" not in page.url.lower() and "register" not in page.url.lower():
                log("  Logged in successfully")
                return True
        log("  Login timeout — continuing anyway")
        return False
    return True


def search_projects():
    log("Searching Mostaql for n8n/AI/automation projects...")
    projects = []
    seen_urls = set()

    try:
        pw, ctx, page = _launch_browser()
    except Exception as e:
        log(f"  Browser launch failed: {e}")
        return []

    try:
        for label, url in MOSTAQL_SEARCH_URLS:
            try:
                log(f"  Searching: {label}")
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                time.sleep(3)
                _wait_login(page)

                found = page.evaluate("""() => {
                    const items = [];
                    const cards = document.querySelectorAll(
                        'a[href*="/project/"], [class*="project-card"], ' +
                        '[class*="ProjectCard"], [class*="project-item"], .card, ' +
                        '.project-item a, .job-card a, [data-testid="project-card"] a'
                    );
                    const processed = new Set();
                    for (const el of cards) {
                        const link = el.tagName === 'A' ? el : el.querySelector('a[href*="/project/"]');
                        if (!link) continue;
                        const href = link.href || link.getAttribute('href') || '';
                        if (!href || href.includes('/offer')) continue;
                        const url = href.startsWith('http') ? href : 'https://mostaql.com' + href;
                        if (processed.has(url)) continue;
                        processed.add(url);
                        const title = (link.innerText || link.textContent || '').trim();
                        const priceEl = el.querySelector(
                            '[class*="price"], [class*="budget"], [class*="money"], ' +
                            '[class*="Price"], [class*="Budget"]'
                        );
                        const price = priceEl ? priceEl.innerText.trim() : '';
                        if (title && title.length > 5) {
                            items.push({ title: title.substring(0, 120), url: url, price: price });
                        }
                    }
                    return items;
                }""")

                for p in found:
                    if p["url"] not in seen_urls:
                        seen_urls.add(p["url"])
                        projects.append(p)
                log(f"    -> Found {len(found)} project(s)")
            except Exception as e:
                log(f"  Search '{label}' error: {e}")
                continue
    finally:
        ctx.close()
        pw.stop()

    log(f"Total unique projects found: {len(projects)}")
    return projects


def classify_project(project, state):
    url = project["url"]
    seen = state.get("projects_seen", {}).get(url, {})
    if seen.get("classification") in ("worth_bid", "already_bid"):
        return seen["classification"], seen.get("reason", "")

    title = (project.get("title") or "").lower()
    combined = title + " " + project.get("price", "")

    high_value_kw = ["n8n", "ai", "automation", "chatbot", "bot", "api", "webhook",
                     "workflow", "integrat", "python", "llm", "openai", "agent",
                     "telegram", "slack", "whatsapp", "أتمتة", "بوت", "ذكاء",
                     "api", "تكامل", "تطوير", "برمجة"]
    skip_kw = ["wordpress", "shopify", "woocommerce", "seo", "design", "video",
               "content", "writing", "translation", "mobile app", "flutter",
               "android", "ios", "html", "css", "javascript", "react"]

    score = 0
    for kw in high_value_kw:
        if kw in title:
            score += 2
    for kw in skip_kw:
        if kw in title:
            score -= 3

    if score >= 2:
        return "worth_bid", f"keyword score: {score}"
    if score <= -2:
        return "skip", f"keyword score: {score} (out of scope)"

    prompt = f"""Classify this Arabic freelance project for an AI Automation Engineer:

Title: {project.get('title', '')[:200]}
Price: {project.get('price', 'Not specified')}

Return JSON:
- "classification": "worth_bid" | "skip" | "maybe"
- "confidence": 0.0 to 1.0
- "reason": short explanation
- "suggested_price": estimated bid price in USD

Rules:
- "worth_bid" = AI/automation/n8n/Python project, budget $10+
- "skip" = out of skillset (design, writing, mobile, etc.)
- "maybe" = unclear but might fit"""
    result = ai_generate_json(prompt, temperature=0.2, caller="mostaql_classify")
    if not result:
        return "maybe", "AI unavailable"
    return result.get("classification", "maybe"), result.get("reason", "")


def generate_bid(project):
    title = project.get("title", "")
    price = project.get("price", "negotiable")

    try:
        from skills.manager import find_best_skill, apply_skill
        skill = find_best_skill("arabic_bid", context_keywords=["mostaql", "n8n", "arabic", title[:30]])
        if skill and skill.get("template"):
            bid = apply_skill(skill, {
                "duration": "5",
                "budget": price or "50",
                "project_title": title[:100],
            }, use_ai_polish=True)
            if bid:
                log(f"  Used skill: {skill.get('name', '?')}")
                return bid
    except Exception as e:
        log(f"  Skills error: {e}")

    log("  Generating bid via AI...")
    bid = ai_generate(
        f"Write a proposal in FORMAL ARABIC (فصحى محترمة) for a project on مستقل.\n\n"
        f"Project title: {title[:200]}\n"
        f"Budget: {price}\n\n"
        f"Rules:\n"
        f"- Start with 'السلام عليكم ورحمة الله وبركاته'\n"
        f"- Introduce yourself as 'سليم محمد، مهندس أتمتة وذكاء اصطناعي'\n"
        f"- Show you understand their specific project\n"
        f"- Mention n8n, Python, OpenAI\n"
        f"- Offer 3-4 specific deliverables\n"
        f"- Set a fair price based on budget ($15-50 range)\n"
        f"- MAX 200 words\n"
        f"- Output ONLY the proposal text",
        max_tokens=900, temperature=0.3, caller="mostaql_bid_gen"
    )
    if bid:
        log(f"  AI bid generated ({len(bid)} chars)")
        return bid

    log("  Using fallback template...")
    return (
        "السلام عليكم ورحمة الله وبركاته،\n\n"
        f"أنا سليم محمد، مهندس أتمتة ذكاء اصطناعي متخصص في n8n و Python. "
        f"أستطيع تنفيذ مشروع '{title[:60]}' بكفاءة واحترافية.\n\n"
        "خطة العمل:\n"
        "1. تحليل المتطلبات بالتفصيل\n"
        "2. تصميم وبناء الحل المناسب باستخدام n8n\n"
        "3. اختبار شامل وضمان الجودة\n"
        "4. تسليم مع توثيق مختصر\n\n"
        f"السعر: {price or 'حسب الاتفاق'} دولار\n"
        "المدة: 3-7 أيام عمل\n\n"
        "للتواصل، أنا جاهز للإجابة على أي استفسار.\n\n"
        "والسلام عليكم ورحمة الله وبركاته،\n"
        "سليم محمد"
    )


def submit_bid_via_browser(page, bid_text):
    click_bid = page.evaluate("""() => {
        const buttons = document.querySelectorAll('button, a, span, input[type="submit"]');
        const keywords = ['تقديم', 'عرض', 'offer', 'bid', 'تقدم', 'أرسل عرض', 'تقديم عرض', 'ارسال', 'إرسال'];
        for (const el of buttons) {
            const t = (el.innerText || el.textContent || el.value || '').toLowerCase().trim();
            for (const kw of keywords) {
                if (t.includes(kw.toLowerCase())) { el.click(); return true; }
            }
        }
        return false;
    }""")
    if not click_bid:
        log("  No bid button found")
        return False
    time.sleep(3)

    filled = page.evaluate(f"""() => {{
        const ta = document.querySelector('textarea');
        if (!ta) return false;
        ta.value = {json.dumps(bid_text)};
        ta.dispatchEvent(new Event('input', {{bubbles: true}}));
        ta.dispatchEvent(new Event('change', {{bubbles: true}}));
        return true;
    }}""")
    if not filled:
        log("  No textarea found")
        return False
    time.sleep(1)

    page.evaluate("""() => {
        const pi = document.querySelector('input[type="number"], input[name*="price"]');
        if (pi) {
            pi.value = '25';
            pi.dispatchEvent(new Event('input', {bubbles: true}));
            pi.dispatchEvent(new Event('change', {bubbles: true}));
        }
    }""")
    time.sleep(1)

    submitted = page.evaluate("""() => {
        const buttons = document.querySelectorAll('button, input[type="submit"]');
        const keywords = ['إرسال', 'تقديم', 'submit', 'send', 'تأكيد', 'confirm', 'نشر', 'إرسال العرض'];
        for (const el of buttons) {
            const t = (el.innerText || el.textContent || el.value || '').toLowerCase().trim();
            for (const kw of keywords) {
                if (t.includes(kw.toLowerCase())) { el.click(); return true; }
            }
        }
        return false;
    }""")

    if submitted:
        time.sleep(3)
        log("  Bid submitted!")
        delay = random.uniform(8, 20)
        log(f"  Waiting {delay:.0f}s before next action...")
        time.sleep(delay)
        return True
    log("  Submit button not found")
    return False


def cmd_check():
    log("=" * 60)
    log(f"  MOSTAQL AGENT — CHECK MODE — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)

    state = load_state()
    projects = search_projects()

    if not projects:
        log("No projects found.")
        return

    log(f"\nClassifying {len(projects)} projects...")
    worth_bidding = []
    for p in projects:
        classification, reason = classify_project(p, state)
        state["projects_seen"][p["url"]] = {
            "title": p["title"],
            "price": p.get("price", ""),
            "classification": classification,
            "reason": reason,
            "seen_at": datetime.now().isoformat(),
        }
        log(f"  {classification}: {p['title'][:60]} ({reason[:40]})")
        if classification == "worth_bid":
            worth_bidding.append(p)

    if not worth_bidding:
        log("\nNo projects worth bidding on right now.")
        save_state(state)
        return

    log(f"\nWorth bidding ({len(worth_bidding)}):")
    for p in worth_bidding:
        log(f"  - {p['title'][:70]} | {p.get('price', '?')} | {p['url'][:60]}")

    bids_to_send = []
    for p in worth_bidding:
        if not can_send("mostaql_bids"):
            log("Daily Mostaql bid quota exhausted")
            break
        bid = generate_bid(p)
        if not bid:
            continue
        bids_to_send.append((p, bid))
        state["bids_sent"].append({
            "url": p["url"],
            "title": p["title"][:100],
            "date": datetime.now().isoformat(),
        })
        write_decision(f"mostaql_{datetime.now().strftime('%H%M%S')}_{len(state['bids_sent'])}",
                       "mostaql_bid", p, bid)
        learn_from_bid(p, bid, "worth_bid")
        record_sent("mostaql_bids", p["url"])

    log(f"\nGenerated {len(bids_to_send)} bid(s). Written to hunt_decisions.md.")
    log("Run 'python mostaql_agent.py --execute' to submit them via browser.")
    save_state(state)


def cmd_bid(project_url):
    log(f"Bidding on: {project_url}")
    state = load_state()
    if not can_send("mostaql_bids"):
        log("Daily Mostaql bid quota exhausted.")
        return

    project = {
        "url": project_url,
        "title": project_url.split("/")[-1].replace("-", " ").title(),
        "price": "",
    }

    try:
        pw, ctx, page = _launch_browser()
    except Exception as e:
        log(f"  Browser launch failed: {e}")
        return

    try:
        page.goto(project_url, timeout=60000, wait_until="domcontentloaded")
        time.sleep(3)
        _wait_login(page)

        details = page.evaluate("""() => {
            const title = document.querySelector('h1, h2')?.innerText?.trim() || '';
            const desc = document.querySelector(
                '[class*="desc"], [class*="detail"], article, main p'
            )?.innerText || '';
            const budget = document.querySelector(
                '[class*="budget"], [class*="price"], [class*="money"]'
            )?.innerText?.trim() || '';
            return { title, desc: desc.substring(0, 1500), budget };
        }""")
        if details and details.get("title"):
            project["title"] = details["title"]
            project["price"] = details.get("budget", "")

        log(f"  Project: {project['title'][:70]}")
        log(f"  Budget: {project['price']}")

        bid = generate_bid(project)
        if not bid:
            log("  Could not generate bid.")
            return

        print(f"\n  BID:\n{bid[:500]}...\n")
        log("  Submitting bid...")
        success = submit_bid_via_browser(page, bid)

        if success:
            state["bids_sent"].append({
                "url": project_url,
                "title": project["title"][:100],
                "date": datetime.now().isoformat(),
            })
            learn_from_bid(project, bid, "worth_bid")
            record_sent("mostaql_bids", project_url)
            log(f"  Bid submitted successfully!")
        else:
            log(f"  Browser is open — submit manually if needed.")
    finally:
        ctx.close()
        pw.stop()
    save_state(state)


def cmd_login():
    log("Opening Mostaql login in Brave...")
    try:
        pw, ctx, page = _launch_browser()
        page.goto("https://mostaql.com/login", timeout=60000)
        log("  Waiting up to 120s for manual login...")
        for _ in range(120):
            time.sleep(1)
            if "login" not in page.url.lower():
                log("  Login detected! Session saved.")
                break
        log("  Browser stays open. Close it when done.")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            pass
        ctx.close()
        pw.stop()
    except Exception as e:
        log(f"  Login error: {e}")
    log("Done.")


def cmd_notifications():
    log("Checking Mostaql notifications...")
    try:
        pw, ctx, page = _launch_browser()
        page.goto("https://mostaql.com/notifications", timeout=60000)
        time.sleep(3)
        _wait_login(page)

        notifs = page.evaluate("""() => {
            const items = [];
            const elements = document.querySelectorAll(
                '[class*="notification"], [class*="Notification"], ' +
                '[class*="alert"], [class*="message"], .notification-item'
            );
            for (const el of elements) {
                const text = (el.innerText || el.textContent || '').trim();
                if (text.length > 10) items.push(text.substring(0, 200));
            }
            return items;
        }""")

        if notifs:
            log(f"Found {len(notifs)} notification(s):")
            for n in notifs[:10]:
                log(f"  - {n[:100]}")
        else:
            log("No notifications found.")
    except Exception as e:
        log(f"  Notifications error: {e}")
    finally:
        ctx.close()
        pw.stop()


def cmd_status():
    state = load_state()
    log("=" * 60)
    log("  MOSTAQL AGENT STATUS")
    log("=" * 60)
    log(f"Projects seen: {len(state.get('projects_seen', {}))}")
    log(f"Bids sent: {len(state.get('bids_sent', []))}")
    log(f"Last notifications check: {state.get('notifications_checked', 'never')}")
    log(f"Daily quotas:")
    for q in ["mostaql_bids", "nafezly_bids", "replies", "followups"]:
        rem = get_remaining(q)
        log(f"  {q}: {rem} remaining")


def cmd_learn():
    log("Learning from sent bids...")
    state = load_state()
    for bid in state.get("bids_sent", []):
        project = {"title": bid.get("title", ""), "url": bid.get("url", "")}
        learn_from_bid(project, "", "worth_bid")
    log("Learning complete.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Mostaql Autonomous Agent")
    parser.add_argument("--check", action="store_true", help="Search projects, write to hunt_decisions.md")
    parser.add_argument("--bid", help="Generate + submit bid for specific project URL")
    parser.add_argument("--login", action="store_true", help="Open browser for manual login")
    parser.add_argument("--notifications", action="store_true", help="Check Mostaql notifications")
    parser.add_argument("--status", action="store_true", help="Show state + quotas")
    parser.add_argument("--learn", action="store_true", help="Convert sent bids into skills")
    parser.add_argument("--execute", action="store_true", help="Execute pending bids from hunt_decisions.md")
    args = parser.parse_args()

    if args.check:
        cmd_check()
    elif args.bid:
        cmd_bid(args.bid)
    elif args.login:
        cmd_login()
    elif args.notifications:
        cmd_notifications()
    elif args.status:
        cmd_status()
    elif args.learn:
        cmd_learn()
    elif args.execute:
        log("Execute mode: read hunt_decisions.md and submit bids (not yet implemented)")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()