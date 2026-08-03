"""
tron.py — One file, full freelance automation.

Run with:
  python tron.py

Or in a new window for interactive prompts:
  Start-Process python -ArgumentList "tron.py" -WorkingDirectory "C:\\Users\\A\\Desktop\\Money" -Wait

Steps (skipped if already done in tron_state.json):
  1. Check Gmail for replies
  2. Post 3 n8n Community forum replies
  3. Sign up on Mostaql (interactive)
  4. Sign up on Nafezly (interactive)
  5. Fill Mostaql profile
  6. Fill Nafezly profile
  7. Find Mostaql projects
  8. Find Nafezly projects
  9. Create Nafezly service ($25 n8n workflow)
  10. Summary

Logs to tron.log, screenshots to tron_screenshots/, state to tron_state.json
"""

import json
import os
import re
import sys
import time
import imaplib
import email
import getpass
from email.header import decode_header
from datetime import datetime, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------- Configuration ----------------
WORKSPACE = Path(r"C:\Users\A\Desktop\Money")
STATE_FILE = WORKSPACE / "tron_state.json"
LOG_FILE = WORKSPACE / "tron.log"
SCREENSHOTS = WORKSPACE / "tron_screenshots"
SCREENSHOTS.mkdir(exist_ok=True)
GMAIL_LOG = WORKSPACE / "gmail_log.md"

EMAIL = "salim.muhammad.work@gmail.com"
NAME = "Salim Muhammad"
GMAIL_RECIPIENTS = [
    "info@zyimmo.de",
    "careers@asiacruit.com",
    "info@s-e.lt",
    "n8nera@gmail.com",
    "wayne@nocodecreative.io",
    "folafoluwaolaneye@gmail.com",
]

THREADS = [
    {
        "key": "mkitplug",
        "draft_file": "Application_N8N_Community_mkitplug.md",
        "url": "https://community.n8n.io/t/i-built-a-free-figma-plugin-that-sends-design-data-to-n8n-looking-for-agencies-to-build-real-workflows-with/297696",
        "label": "mkitplug (Michael) — Figma plugin",
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
        "label": "Doru_Gradinaru — Guard workflow",
    },
]

# ---------------- State Management ----------------
def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"completed": [], "data": {}, "started": datetime.now().isoformat()}


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def is_done(state, key):
    return key in state.get("completed", [])


def mark_done(state, key, data=None):
    if key not in state.get("completed", []):
        state.setdefault("completed", []).append(key)
    if data:
        state.setdefault("data", {})[key] = data
    save_state(state)


# ---------------- Logging ----------------
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def banner(text):
    bar = "=" * 60
    log(bar)
    log(f"  {text}")
    log(bar)


# ---------------- Step 1: Gmail Check (no browser) ----------------
def step_gmail_check(state):
    banner("STEP 1: Gmail reply check")
    if is_done(state, "gmail_check"):
        log("  [SKIP] Already done")
        return True

    pw = os.environ.get("GMAIL_APP_PASSWORD")
    if not pw:
        log("  GMAIL_APP_PASSWORD not in env — skipping (you can source it from registry)")
        return False

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL, pw)
        mail.select("inbox")
        since = (datetime.now() - timedelta(days=14)).strftime("%d-%b-%Y")
        all_ids = set()
        for r in GMAIL_RECIPIENTS:
            status, data = mail.search(None, f'FROM "{r}" SINCE {since}')
            if status == "OK" and data and data[0]:
                all_ids.update(data[0].split())
        log(f"  Found {len(all_ids)} reply candidate(s) in 14-day window")
        with GMAIL_LOG.open("a", encoding="utf-8") as f:
            f.write(f"\n## tron.py check at {datetime.now().isoformat()}\n\n")
            f.write(f"_Replies from {len(GMAIL_RECIPIENTS)} recipients, last 14 days: {len(all_ids)} candidate(s)_\n\n---\n")
        mail.logout()
        mark_done(state, "gmail_check", {"replies_found": len(all_ids)})
        return True
    except Exception as e:
        log(f"  [ERROR] {e}")
        return False


# ---------------- Step 2: Forum Posting ----------------
def extract_reply(md_path):
    text = md_path.read_text(encoding="utf-8")
    match = re.search(r"```\n(.*?)\n```", text, re.DOTALL)
    if not match:
        raise ValueError(f"No code block in {md_path.name}")
    return match.group(1).strip()


def post_one_thread(page, thread):
    log(f"  → {thread['label']}")
    page.goto(thread["url"], wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    shot = SCREENSHOTS / f"forum_{thread['key']}_before.png"
    page.screenshot(path=str(shot))

    # Login check
    try:
        sign_in = page.get_by_role("button", name=re.compile("Sign In|Log In", re.I))
        if sign_in.count() > 0:
            log("  ⚠ Not logged in. Log in via the browser window, then press ENTER here.")
            input("  Press ENTER after logging in: ")
            page.reload()
            page.wait_for_load_state("domcontentloaded")
    except Exception:
        pass

    # Click Reply button
    try:
        reply_btn = page.locator("button:has-text('Reply')").first
        reply_btn.scroll_into_view_if_needed()
        reply_btn.click()
        page.wait_for_timeout(1500)
    except Exception as e:
        log(f"  [SKIP] Reply button not found: {e}")
        return None

    # Type reply
    try:
        editor = page.locator("textarea.d-editor-input").first
        editor.wait_for(state="visible", timeout=10000)
        md = WORKSPACE / thread["draft_file"]
        if not md.exists():
            log(f"  [ERROR] Draft not found: {md}")
            return None
        reply = extract_reply(md)
        editor.fill(reply)
        page.wait_for_timeout(500)
        shot2 = SCREENSHOTS / f"forum_{thread['key']}_typed.png"
        page.screenshot(path=str(shot2))
    except Exception as e:
        log(f"  [ERROR] Could not type reply: {e}")
        return None

    log("  👀 Review in browser. Press ENTER to POST, type 'skip' to skip.")
    choice = input("  >>> ").strip().lower()
    if choice == "skip":
        log("  Skipped")
        return None

    try:
        post_btn = page.locator("button:has-text('Reply to Topic'), button:has-text('Post Reply')").first
        post_btn.click()
        page.wait_for_timeout(3000)
        shot3 = SCREENSHOTS / f"forum_{thread['key']}_after.png"
        page.screenshot(path=str(shot3))
    except Exception as e:
        log(f"  [ERROR] Could not post: {e}")
        return None

    return page.url


def step_forum_post(state, browser_context):
    banner("STEP 2: Post 3 n8n Community replies")
    if is_done(state, "forum_posted"):
        log("  [SKIP] Already done")
        return True

    page = browser_context.new_page()
    results = []
    for t in THREADS:
        try:
            url = post_one_thread(page, t)
            results.append({"key": t["key"], "url": url, "status": "Posted" if url else "Skipped"})
        except Exception as e:
            log(f"  [ERROR] {t['key']}: {e}")
            results.append({"key": t["key"], "url": None, "status": f"Error: {e}"})
    page.close()
    mark_done(state, "forum_posted", {"results": results})
    return True


# ---------------- Step 3-4: Signups (interactive) ----------------
def step_mostaql_signup(state, browser_context):
    banner("STEP 3: Sign up on Mostaql")
    if is_done(state, "mostaql_signed_up"):
        log("  [SKIP] Already done")
        return True

    page = browser_context.new_page()
    try:
        page.goto("https://mostaql.com/register", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        # Fill what we can
        for sel, val in [
            ("input[name='name']", NAME),
            ("input[type='email']", EMAIL),
        ]:
            try:
                page.locator(sel).first.fill(val)
            except Exception:
                pass
        page.screenshot(path=str(SCREENSHOTS / "mostaql_signup_filled.png"))
        log("  Form partially filled. Complete signup in browser, then press ENTER.")
        log("  (Need to set password, accept terms, complete CAPTCHA, verify email.)")
        input("  Press ENTER after signup is done: ")
        mark_done(state, "mostaql_signed_up")
    finally:
        page.close()
    return True


def step_nafezly_signup(state, browser_context):
    banner("STEP 4: Sign up on Nafezly")
    if is_done(state, "nafezly_signed_up"):
        log("  [SKIP] Already done")
        return True

    page = browser_context.new_page()
    try:
        page.goto("https://nafezly.com/register", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        for sel, val in [
            ("input[name='name']", NAME),
            ("input[type='email']", EMAIL),
        ]:
            try:
                page.locator(sel).first.fill(val)
            except Exception:
                pass
        page.screenshot(path=str(SCREENSHOTS / "nafezly_signup_filled.png"))
        log("  Form partially filled. Complete signup in browser, then press ENTER.")
        input("  Press ENTER after signup is done: ")
        mark_done(state, "nafezly_signed_up")
    finally:
        page.close()
    return True


# ---------------- Step 5-6: Profile Filling ----------------
MOSTAQL_BIO = """أنا مطوّر أتمتة وذكاء اصطناعي، أبني أنظمة أتمتة بـ Python و n8n توفّر الوقت وتقلّل العمل اليدوي المتكرّر.

خدماتي:
• أتمتة سير العمل عبر n8n و Zapier و Make.com
• بناء وكلاء ذكاء اصطناعي بـ OpenAI و Claude
• تكامل بين تطبيقات SaaS (Google Workspace, Slack, Airtable, Notion)
• خطوط أنابيب لمعالجة البيانات باستخدام Python و Flask

أسلوبي: تواصل واضح، تسليم في الموعد، توثيق قصير بعد كل مشروع."""


def step_mostaql_profile(state, browser_context):
    banner("STEP 5: Fill Mostaql profile")
    if is_done(state, "mostaql_profiled"):
        log("  [SKIP] Already done")
        return True

    page = browser_context.new_page()
    try:
        page.goto("https://mostaql.com/account/profile", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        for sel, val in [
            ("textarea[name='bio']", MOSTAQL_BIO),
            ("input[name='hourly_rate']", "10"),
            ("input[name='skills']", "n8n, Zapier, Make.com, Python, Flask, OpenAI, Claude, Airtable, Slack, Google Sheets"),
        ]:
            try:
                page.locator(sel).first.fill(val)
            except Exception:
                pass
        page.screenshot(path=str(SCREENSHOTS / "mostaql_profile_filled.png"))
        log("  Profile fields filled. Review and SAVE in browser, then press ENTER.")
        input("  Press ENTER after saving: ")
        mark_done(state, "mostaql_profiled")
    finally:
        page.close()
    return True


NAFEZLY_BIO = """مطوّر أتمتة وذكاء اصطناعي، أبني حلول n8n و Python للشركات الصغيرة وأصحاب المشاريع.

التخصص: أتمتة سير العمل، وكلاء ذكاء اصطناعي، تكامل SaaS."""


def step_nafezly_profile(state, browser_context):
    banner("STEP 6: Fill Nafezly profile")
    if is_done(state, "nafezly_profiled"):
        log("  [SKIP] Already done")
        return True

    page = browser_context.new_page()
    try:
        page.goto("https://nafezly.com/account/profile", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        for sel, val in [
            ("textarea[name='bio']", NAFEZLY_BIO),
        ]:
            try:
                page.locator(sel).first.fill(val)
            except Exception:
                pass
        page.screenshot(path=str(SCREENSHOTS / "nafezly_profile_filled.png"))
        log("  Profile fields filled. Review and SAVE in browser, then press ENTER.")
        input("  Press ENTER after saving: ")
        mark_done(state, "nafezly_profiled")
    finally:
        page.close()
    return True


# ---------------- Step 7-8: Find Projects ----------------
def step_mostaql_projects(state, browser_context):
    banner("STEP 7: Find Mostaql projects (AI/ML + Development)")
    if is_done(state, "mostaql_projects_found"):
        log("  [SKIP] Already done")
        return True

    page = browser_context.new_page()
    try:
        page.goto("https://mostaql.com/projects/ai-machine-learning", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        page.screenshot(path=str(SCREENSHOTS / "mostaql_projects.png"))
        # Extract project links
        links = page.locator("a[href*='/project/']").all()
        urls = []
        for a in links[:10]:
            try:
                href = a.get_attribute("href")
                if href and "/project/" in href:
                    if not href.startswith("http"):
                        href = "https://mostaql.com" + href
                    if href not in urls:
                        urls.append(href)
            except Exception:
                pass
        log(f"  Found {len(urls)} project URLs")
        state.setdefault("data", {})["mostaql_projects"] = urls[:5]
        save_state(state)
        log("  Top 5 saved. Review them in browser, then press ENTER.")
        input("  Press ENTER to continue: ")
        mark_done(state, "mostaql_projects_found", {"count": len(urls), "urls": urls[:5]})
    finally:
        page.close()
    return True


def step_nafezly_projects(state, browser_context):
    banner("STEP 8: Find Nafezly projects")
    if is_done(state, "nafezly_projects_found"):
        log("  [SKIP] Already done")
        return True

    page = browser_context.new_page()
    try:
        page.goto("https://nafezly.com/projects", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        page.screenshot(path=str(SCREENSHOTS / "nafezly_projects.png"))
        links = page.locator("a[href*='/project/']").all()
        urls = []
        for a in links[:10]:
            try:
                href = a.get_attribute("href")
                if href and "/project/" in href:
                    if not href.startswith("http"):
                        href = "https://nafezly.com" + href
                    if href not in urls:
                        urls.append(href)
            except Exception:
                pass
        log(f"  Found {len(urls)} project URLs")
        state.setdefault("data", {})["nafezly_projects"] = urls[:5]
        save_state(state)
        log("  Top 5 saved. Review them in browser, then press ENTER.")
        input("  Press ENTER to continue: ")
        mark_done(state, "nafezly_projects_found", {"count": len(urls), "urls": urls[:5]})
    finally:
        page.close()
    return True


# ---------------- Step 9: Nafezly Service ----------------
NAFEZLY_SERVICE = """سأبني لك workflow في n8n لأتمتة أي عملية يدوية

هل تكرّر مهمة يومية يمكن أتمتتها؟ أبنيلك workflow في n8n يربط بين التطبيقات ويشتغل تلقائيًا.

مثال ما أقدر أعمله:
- ربط Google Sheets مع Slack لإشعارات تلقائية
- تأهيل العملاء المحتملين عبر OpenAI
- معالجة البريد الوارد وتصنيفه
- تكامل بين أي تطبيقات SaaS تستخدمها

الخدمة تشمل:
✅ workflow جاهز ومفعّل على n8n
✅ توثيق مختصر بالعربية
✅ دعم لمدة أسبوع بعد التسليم
❌ لا تشمل اشتراك n8n (يحتاج حسابك الخاص)
❌ لا تشمل API مدفوع (OpenAI, etc.) إلا لو متفق

التسليم: خلال 3-5 أيام
"""


def step_nafezly_service(state, browser_context):
    banner("STEP 9: Publish Nafezly service ($25 n8n workflow)")
    if is_done(state, "nafezly_service_created"):
        log("  [SKIP] Already done")
        return True

    page = browser_context.new_page()
    try:
        page.goto("https://nafezly.com/services/create", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        # Try common field selectors
        try:
            page.locator("input[name='title']").first.fill("سأبني لك workflow في n8n لأتمتة أي عملية يدوية")
        except Exception:
            pass
        try:
            page.locator("textarea[name='description']").first.fill(NAFEZLY_SERVICE)
        except Exception:
            pass
        try:
            page.locator("input[name='price']").first.fill("25")
        except Exception:
            pass
        try:
            page.locator("input[name='delivery_days']").first.fill("5")
        except Exception:
            pass
        page.screenshot(path=str(SCREENSHOTS / "nafezly_service_filled.png"))
        log("  Service form filled. Review and SUBMIT in browser, then press ENTER.")
        input("  Press ENTER after submitting: ")
        mark_done(state, "nafezly_service_created")
    finally:
        page.close()
    return True


# ---------------- Main Orchestrator ----------------
def main():
    banner(f"TRON.SCRIPT START — {datetime.now().isoformat()}")
    state = load_state()
    log(f"  Already completed: {state.get('completed', [])}")

    # Step 1: Gmail (no browser needed)
    step_gmail_check(state)

    # Steps 2-9: Need browser
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
            )

            # Forum first (you're already registered)
            step_forum_post(state, context)

            # Then signups + profiles + projects
            step_mostaql_signup(state, context)
            step_nafezly_signup(state, context)
            step_mostaql_profile(state, context)
            step_nafezly_profile(state, context)
            step_mostaql_projects(state, context)
            step_nafezly_projects(state, context)
            step_nafezly_service(state, context)

            browser.close()
    except ImportError:
        log("  [ERROR] playwright not installed. Run: pip install playwright && python -m playwright install chromium")
    except Exception as e:
        log(f"  [FATAL] {e}")
        import traceback
        traceback.print_exc()

    # Summary
    banner("SUMMARY")
    log(f"  Completed steps: {state.get('completed', [])}")
    log(f"  Data saved: {list(state.get('data', {}).keys())}")
    log(f"  State file: {STATE_FILE}")
    log(f"  Log file: {LOG_FILE}")
    log(f"  Screenshots: {SCREENSHOTS}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n\nAborted by user (Ctrl+C).")
        sys.exit(1)
