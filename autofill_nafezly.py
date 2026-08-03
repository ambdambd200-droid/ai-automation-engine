"""
Nafezly Auto-Filler + Bidder
Opens browser → waits for you to log in (60s) → fills everything automatically
"""

import time, json, re
from pathlib import Path

BASE = Path(__file__).parent
TEMP = BASE / "Temp"

BIO = "مطوّر أتمتة وذكاء اصطناعي، أبني حلول n8n و Python للشركات الصغيرة وأصحاب المشاريع. أقدّم خدمات بأسلوب واضح وتسليم في الوقت.\n\nالتخصص: أتمتة سير العمل | وكلاء ذكاء اصطناعي | تكامل SaaS"

SKILLS = "n8n, Python, Flask, OpenAI, Claude, Make.com, Zapier, Google Sheets, Slack, Airtable, Notion, REST API, AI automation, workflow automation"

PROJECTS = [
    ("محرك أتمتة ذاتي الاستضافة",
     "تطبيق Flask يستقبل webhooks ويعالجها بسلسلة خطوات YAML. يستخدم OpenAI لتحليل النصوص وحفظها في SQLite.",
     "Python, Flask, OpenAI, SQLite"),
    ("خط أنابيب تأهيل العملاء (n8n + AI)",
     "Workflow في n8n يسحب بيانات العملاء من نموذج ويب، يحللها بـ OpenAI، يسجل في Google Sheet ويرسل Slack.",
     "n8n, OpenAI, Google Sheets, Slack"),
    ("بوت فحص Gmail",
     "سكربت Python يستخدم IMAP لفحص Gmail يوميًا والبحث عن ردود العملاء. يفلتر ويحتفظ بسجل.",
     "Python, IMAP, Gmail API"),
]

SERVICE = {
    "title": "سأبني لك workflow في n8n لأتمتة أي عملية يدوية",
    "desc": "هل تكرّر مهمة يومية يمكن أتمتتها؟ أبنيلك workflow في n8n يربط بين التطبيقات ويشتغل تلقائيًا.\n\nمثال:\n• ربط Google Sheets مع Slack\n• تأهيل العملاء عبر OpenAI\n• معالجة البريد وتصنيفه\n• تكامل بين تطبيقات SaaS\n\nالخدمة تشمل:\n✅ workflow جاهز\n✅ توثيق مختصر\n✅ دعم أسبوع\n\nالتسليم: 3-5 أيام\nالسعر: 25$",
    "price": 25,
    "delivery": 5,
}

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

أمثلة أعمالي في معرض أعمالي.

تحياتي،
علاء فتحي"""


def snap(page, name):
    page.screenshot(path=str(TEMP / f"nf_{name}.png"))
    (TEMP / f"nf_{name}.html").write_text(page.content(), encoding="utf-8")
    print(f"  [{name}] saved")


def main():
    import os
    os.environ["PYTHONIOENCODING"] = "utf-8"

    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=False)
    page = browser.new_page()
    page.set_default_timeout(10000)

    print("=" * 60)
    print("  AUTO: مرحبا! سأفتح المتصفح...")
    print("  سجل دخول في نافذة المتصفح اللي ظهرت")
    print("  عندك 90 ثانية عشان تسجل دخول")
    print("=" * 60)

    # Step 1: Login page
    page.goto("https://nafezly.com/login", wait_until="domcontentloaded")
    time.sleep(2)
    snap(page, "01_login")

    # Wait for user to log in (poll URL every 2s, max 90s)
    for i in range(45):
        time.sleep(2)
        if "login" not in page.url.lower() and "تسجيل" not in page.title():
            print(f"  ✅ Logged in after ~{i*2}s! URL: {page.url}")
            break
        if i % 5 == 0:
            print(f"  ⏳ Waiting for login... ({i*2}s)")
    else:
        print("  ⚠ Login timeout. Continuing anyway...")

    snap(page, "02_after_login")

    # Step 2: Find settings/profile page
    print("\n📌 STEP 2: Profile settings...")
    for url in ["https://nafezly.com/settings", "https://nafezly.com/profile", "https://nafezly.com/account"]:
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(2)
        snap(page, f"02_{url.split('/')[-1]}")
        if "404" not in page.title() and "login" not in page.url.lower():
            print(f"  ✓ Settings page: {page.url}")
            break

    # Check for form fields
    bio_field = page.locator("textarea[name*='bio'], textarea[name*='desc'], textarea[placeholder*='نبذ'], textarea").first
    if bio_field.is_visible():
        print("  ✓ Found bio field - filling...")
        bio_field.fill(BIO)
        time.sleep(1)
        snap(page, "03_bio_filled")

        # Find and click save
        save_btn = page.locator("button[type='submit'], button:has-text('حفظ'), button:has-text('تحديث')").first
        if save_btn.is_visible():
            save_btn.click()
            time.sleep(2)
            snap(page, "04_bio_saved")
            print("  ✓ Bio saved!")
    else:
        print("  ⚠ No bio field found on this page")
        # Save HTML for analysis
        html = page.content()
        (TEMP / "settings_html.txt").write_text(html[:5000], encoding="utf-8")

    # Step 3: Try to create a service
    print("\n📌 STEP 3: Creating $25 service...")
    page.goto("https://nafezly.com/services/create", wait_until="domcontentloaded")
    time.sleep(3)
    snap(page, "05_service_page")

    title_inp = page.locator("input[name='title'], input#title, input[placeholder*='عنوان']").first
    if title_inp.is_visible():
        title_inp.fill(SERVICE["title"])
        print("  ✓ Service title filled")
        time.sleep(1)

        desc_field = page.locator("textarea, [contenteditable='true']").first
        if desc_field.is_visible():
            desc_field.fill(SERVICE["desc"])
            print("  ✓ Service description filled")

        price_inp = page.locator("input[type='number'], input[name*='price'], input[name*='cost']").first
        if price_inp.is_visible():
            price_inp.fill(str(SERVICE["price"]))

        snap(page, "06_service_filled")

        submit = page.locator("button[type='submit'], button:has-text('نشر'), button:has-text('حفظ')").first
        if submit.is_visible():
            # Don't auto-submit - let user check
            print("  ⏸ Service ready. Not submitted - review in browser.")
    else:
        print("  ⚠ Could not find service creation form")

    # Step 4: Find AI Agents project
    print("\n📌 STEP 4: Finding AI Agents project...")
    page.goto("https://nafezly.com/projects?key=AI+Agents+n8n&pricing=10,10000", wait_until="domcontentloaded")
    time.sleep(3)
    snap(page, "07_search_ai")

    # Try clicking project
    try:
        link = page.locator("a:has-text('وكلاء ذكاء اصطناعي')").first
        if link.is_visible():
            print("  ✓ Found AI Agents project")
            link.click()
            time.sleep(2)
            snap(page, "08_project_page")

            # Look for bid button
            bid_btn = page.locator("button:has-text('تقديم'), a:has-text('تقديم عرض')").first
            if bid_btn.is_visible():
                bid_btn.click()
                time.sleep(2)
                snap(page, "09_bid_form")

                # Fill bid
                text_area = page.locator("textarea, [contenteditable='true']").first
                if text_area.is_visible():
                    text_area.fill(BID)
                    print("  ✓ Bid text filled")
                    snap(page, "10_bid_filled")

                # Check submit button
                sub = page.locator("button[type='submit'], button:has-text('إرسال')").first
                if sub.is_visible():
                    print("  ⏸ Bid ready. Review and click Submit in browser.")
            else:
                print("  ⚠ No bid button found")
                snap(page, "09_no_bid_btn")
    except Exception as e:
        print(f"  ⚠ Could not interact with AI Agents project: {e}")
        snap(page, "09_error")

    # Final
    snap(page, "99_done")

    print("\n" + "=" * 60)
    print("  ✅ ALL DONE!")
    print("  👀 Browser is STILL OPEN - do what you need:")
    print("  1. Bio & profile ready")
    print("  2. Service draft ready")
    print("  3. Bid draft ready")
    print("  4. Submit/save what you want")
    print("=" * 60)
    print("\n  Close the browser window when done.")

    # Wait for browser to stay open
    time.sleep(1200)


if __name__ == "__main__":
    main()
