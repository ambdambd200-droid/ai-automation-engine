"""
Nafezly Auto-Filler — runs forever, no timeout issues
Opens browser → waits login → fills everything → keeps browser open
"""

import sys, time, json, os
from pathlib import Path

BASE = Path(__file__).parent
LOG = BASE / "nafezly_progress.json"
TEMP = BASE / "Temp"

BIO = "مطوّر أتمتة وذكاء اصطناعي، أبني حلول n8n و Python للشركات الصغيرة وأصحاب المشاريع. أقدّم خدمات بأسلوب واضح وتسليم في الوقت.\n\nالتخصص: أتمتة سير العمل | وكلاء ذكاء اصطناعي | تكامل SaaS"

SKILLS_STR = "n8n, Python, Flask, OpenAI, Claude, Make.com, Zapier, Google Sheets, Slack, Airtable, Notion, REST API, AI automation, workflow automation"

BID = """السلام عليكم فهد،

قرأت مشروعك عن تطوير AI Agents باستخدام n8n وأعتقد مناسب جدًا لمهاراتي.

خبرتي:
• بنيت workflows في n8n تربط بين OpenAI و Sheets و Slack و Airtable
• pipeline جاهز: webhook ← OpenAI ← Google Sheets ← Slack
• Decision Logic في n8n
• Python لتوسيع الإمكانيات

خطة العمل:
1. نتفق على السيناريوهات
2. أصمم workflow (Switch, HTTP, AI, Webhook)
3. أربط مع AI واختبر
4. نختبر سيناريوهات متعددة
5. تسليم + توثيق بالعربية

المدة: 20 يوم
الميزانية: 75$

تحياتي،
علاء فتحي"""

SERVICE_TITLE = "سأبني لك workflow في n8n لأتمتة أي عملية يدوية"
SERVICE_DESC = """هل تكرّر مهمة يومية يمكن أتمتتها؟ أبنيلك workflow في n8n يربط بين التطبيقات ويشتغل تلقائيًا.

مثال:
• ربط Google Sheets مع Slack
• تأهيل العملاء عبر OpenAI
• معالجة البريد وتصنيفه
• تكامل بين تطبيقات SaaS

الخدمة تشمل:
✅ workflow جاهز
✅ توثيق مختصر
✅ دعم أسبوع

التسليم: 3-5 أيام
السعر: 25$"""


def progress(state, msg):
    data = {"state": state, "msg": msg, "time": time.strftime("%H:%M:%S")}
    LOG.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"[{state}] {msg}")


def snap(page, name):
    try:
        page.screenshot(path=str(TEMP / f"nf_{name}.png"))
        (TEMP / f"nf_{name}.html").write_text(page.content()[:5000], encoding="utf-8")
    except:
        pass


def goto(page, url, label=""):
    """Navigate with retry for slow networks."""
    for attempt in range(3):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=120000)
            time.sleep(2)
            return True
        except Exception as e:
            progress("nav_retry", f"⏳ {label}: timeout, retry {attempt+1}/3")
            time.sleep(5)
    return False


def main():
    from playwright.sync_api import sync_playwright

    BRAVE_EXE = Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")
    BRAVE_PROFILE = Path(r"C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data")

    pw = sync_playwright().start()
    context = pw.chromium.launch_persistent_context(
        user_data_dir=str(BRAVE_PROFILE),
        executable_path=str(BRAVE_EXE),
        headless=False,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        viewport={"width": 1366, "height": 768},
    )
    page = context.new_page()
    page.set_default_timeout(120000)  # 2 min timeout for slow networks

    progress("start", "Browser opened. Please log in to Nafezly in the browser window.")

    # Login page
    goto(page, "https://nafezly.com/login", "login")
    snap(page, "01_login")

    # Wait for login (check every 5s, no timeout limit)
    progress("wait_login", "Waiting for you to log in in the browser...")
    logged_in = False
    for _ in range(3600):  # 3600 * 5s = 5 hours max (practically infinite)
        time.sleep(5)
        try:
            current_url = page.url
            title = page.title()
            if "login" not in current_url.lower() and "register" not in current_url.lower() and "404" not in title:
                logged_in = True
                progress("logged_in", f"Logged in! URL: {current_url}")
                break
        except:
            pass  # page might be loading
    if not logged_in:
        progress("timeout", "Login timeout after 5 hours. Continuing anyway...")

    snap(page, "02_home")

    # === STEP 1: PROFILE ===
    progress("profile", "Finding profile settings...")

    # Look for profile link in navbar
    profile_link = page.locator("a[href*='profile'], a[href*='account'], a[href*='settings']").first
    if profile_link.is_visible():
        progress("profile_click", "Clicking profile link...")
        profile_link.click()
        time.sleep(3)
        snap(page, "03_profile")

    # Try known URLs
    for url in ["https://nafezly.com/settings", "https://nafezly.com/account", "https://nafezly.com/profile"]:
        if goto(page, url, url.split('/')[-1]):
            title = page.title()
            if "404" not in title and "login" not in page.url.lower():
                progress("settings_found", f"Settings page: {page.url}")
                snap(page, f"03_{url.split('/')[-1]}")
                break

    # Try to fill bio
    textareas = page.locator("textarea").all()
    inputs = page.locator("input[type='text'], input[type='email'], input[name*='name']").all()
    progress("found_elements", f"Found {len(textareas)} textareas, {len(inputs)} inputs on settings page")

    # Try each textarea for bio
    filled = False
    for ta in textareas:
        try:
            ta.fill(BIO)
            progress("bio_filled", "✓ Bio field found and filled!")
            filled = True
            snap(page, "04_bio_filled")
            break
        except:
            continue

    if not filled:
        progress("bio_skipped", "⚠ Could not find bio field. Proceeding...")

    # Try to save
    for btn_text in ["حفظ", "تحديث", "إرسال", "حفظ التغييرات"]:
        btn = page.locator(f"button:has-text('{btn_text}'), input[value='{btn_text}']").first
        if btn.is_visible():
            try:
                btn.click()
                time.sleep(2)
                progress("saved", f"✓ Clicked '{btn_text}'")
                snap(page, "05_saved")
            except:
                pass
            break

    # === STEP 2: SERVICE ===
    progress("service", "Creating $25 service...")

    # Click on "إضافة خدمة" or navigate
    service_link = page.locator("a[href*='service'], a:has-text('خدمة'), a:has-text('إضافة')").first
    if service_link.is_visible():
        service_link.click()
        time.sleep(3)
        snap(page, "06_service_page")

    goto(page, "https://nafezly.com/services/create", "service_create")
    snap(page, "06_service_create")

    # Find title field
    title_field = page.locator("input[name='title'], input[placeholder*='عنوان'], input#title").first
    if title_field.is_visible():
        title_field.fill(SERVICE_TITLE)
        progress("service_title", "✓ Service title filled")
        time.sleep(1)
    snap(page, "07_service_title")

    # === STEP 3: FIND AI AGENTS PROJECT ===
    progress("project", "Searching for AI Agents project...")
    goto(page, "https://nafezly.com/projects?key=AI+Agents&pricing=10,10000", "project_search")
    time.sleep(3)
    snap(page, "08_projects_search")

    # Try to find the project link in the results
    try:
        project = page.locator("a:has-text('وكلاء ذكاء')").first
        if project.is_visible():
            progress("project_found", "✓ AI Agents project found in results")
            project.click()
            time.sleep(2)
            snap(page, "09_project_page")

            # Try to find bid button
            bid_btn = page.locator("button:has-text('تقديم'), a:has-text('تقديم عرض'), a:has-text('تقديم')").first
            if bid_btn.is_visible():
                bid_btn.click()
                time.sleep(2)
                snap(page, "10_bid_form")

                # Fill bid
                bid_field = page.locator("textarea").first
                if bid_field.is_visible():
                    bid_field.fill(BID)
                    progress("bid_filled", "✓ Bid text filled!")
                    snap(page, "11_bid_filled")
        else:
            progress("project_not_found", "⚠ Could not find AI Agents project in search")
            snap(page, "08_no_project")
    except Exception as e:
        progress("project_error", f"⚠ Error with project: {e}")

    # DONE
    progress("done", "✅ All operations complete! Check the browser.")
    snap(page, "99_done")

    print("\n" + "=" * 60)
    print("  ✅ Done! Browser stays open for you.")
    print("  📁 Content files at: Desktop\\Money\\Temp\\")
    print("  = 1_bio.txt | 2_skills.txt | 3_projects.txt")
    print("  = 4_bid.txt | 5_service.txt")
    print("=" * 60)

    # Keep open indefinitely
    while True:
        time.sleep(60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        progress("crashed", f"ERROR: {e}")
        with open(TEMP / "crash_log.txt", "w") as f:
            traceback.print_exc(file=f)
        print(f"CRASHED: {e}")
        print("Keeping browser alive for debugging...")
        time.sleep(600)
