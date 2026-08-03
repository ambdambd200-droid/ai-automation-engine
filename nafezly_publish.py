"""Nafezly reliable automation - profile + bid via JavaScript injection.
Design: use page.evaluate() for all form filling (instant, no timeout).
Future: modify CONTENT dict at top to change what gets published."""
import sys, time, json
from pathlib import Path

# === CONFIG - edit these for future use ===
CONTENT = {
    "job_title": "مهندس أتمتة ذكاء اصطناعي",
    "bio": "أنا علاء فتحي، مهندس أتمتة ذكاء اصطناعي من غزة. متخصص في بناء أنظمة أتمتة متكاملة باستخدام n8n و Make (Integromat) والذكاء الاصطناعي. أعمل على ربط التطبيقات والخدمات ببعضها البعض لإنشاء سير عمل ذكية توفر الوقت وتزيد الإنتاجية.\n\nأقدم خدماتي في:\n- بناء وكلاء ذكاء اصطناعي (AI Agents)\n- أتمتة سير العمل بـ n8n\n- ربط APIs وتطبيقات السحابة\n- تطوير Chatbots وحلول الذكاء الاصطناعي\n\nأتحدث العربية والإنجليزية وأتواصل باحترافية عالية.",
    "skills": ["n8n", "AI Agents", "Automation", "API Integration", "Chatbot", "Make"],
}

BID = {
    "project_url": "https://nafezly.com/projects?key=AI+Agents",
    "target_project": "AI Agents",
    "proposal": "السلام عليكم،\n\nأنا علاء فتحي، مهندس أتمتة ذكاء اصطناعي من غزة. أرى أن مشروعكم يحتاج إلى:\n\n1. تحليل المتطلبات وتصميم بنية الأتمتة\n2. بناء وكلاء AI باستخدام n8n\n3. ربط التطبيقات والخدمات\n4. اختبار وتشغيل النظام\n\nلدي خبرة في بناء حلول أتمتة متكاملة باستخدام n8n والذكاء الاصطناعي. يمكنني البدء فوراً.\n\nسعر المشروع: 50 دولار (قابل للتفاوض)\nمدة التسليم: 5-7 أيام\n\nأرفق لكم نموذج عمل سابق لعرض أسلوبي في العمل.\n\nوشكراً،\nعلاء فتحي",
    "price": "50",
    "delivery_days": "7"
}

# === PATHS ===
BRAVE_EXE = Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")
BRAVE_PROFILE = Path(r"C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data")
TEMP = Path(__file__).parent / "Temp"
TEMP.mkdir(parents=True, exist_ok=True)

step_num = 0
def step(name, msg):
    global step_num
    step_num += 1
    out = json.dumps({"step": step_num, "state": name, "msg": msg, "time": time.strftime("%H:%M:%S")}, ensure_ascii=False)
    (TEMP / "nafezly_progress.json").write_text(out, encoding="utf-8")
    print(f"[{step_num}] {name}: {msg}")

def js_set_value(page, selector, value):
    """Set form field value via JavaScript - instant, no typing simulation."""
    return page.evaluate("""(args) => {
        const el = document.querySelector(args.selector);
        if (!el) return {ok: false, err: 'not found'};
        const tag = el.tagName.toLowerCase();
        if (tag === 'textarea' || (tag === 'input' && ['text','email','tel','url',''].includes(el.type))) {
            el.value = args.value;
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            return {ok: true, tag, name: el.name};
        }
        return {ok: false, err: 'unsupported element'};
    }""", {"selector": selector, "value": value})

from playwright.sync_api import sync_playwright

def goto_safe(page, url, label, retries=3):
    for attempt in range(1, retries+1):
        try:
            page.goto(url, timeout=120000, wait_until="domcontentloaded")
            time.sleep(3)
            step(label, f"URL: {page.url} (attempt {attempt})")
            return True
        except Exception as e:
            step("retry", f"{label} failed: {e}")
            if attempt < retries:
                time.sleep(5)
    return False

def main():
    global step_num
    step_num = 0
    
    step("start", "Opening Brave with profile...")
    pw = sync_playwright().start()
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=str(BRAVE_PROFILE), executable_path=str(BRAVE_EXE),
        headless=False, args=["--no-sandbox"], viewport={"width":1366,"height":768})
    page = ctx.new_page()
    page.set_default_timeout(120000)

    # STEP 1: Verify logged in
    step("login_check", "Checking login status...")
    page.goto("https://nafezly.com", timeout=120000)
    time.sleep(3)
    if "login" in page.url.lower():
        step("wait_login", "Need login - waiting 120s for user...")
        for _ in range(120):
            time.sleep(1)
            if "login" not in page.url.lower():
                break
    step("logged_in", f"Logged in. URL: {page.url}")

    # STEP 2: Fill profile/nafezly-settings (bio + job title)
    step("profile", "Opening nafezly-settings...")
    if not goto_safe(page, "https://nafezly.com/profile/nafezly-settings", "settings_page"):
        step("error", "Could not load settings page")
        return

    step("fill_job_title", f"Setting job title to '{CONTENT['job_title']}'...")
    r = js_set_value(page, "input[name='job_title']", CONTENT["job_title"])
    step("job_title_result", f"Job title: {r}")
    time.sleep(1)

    step("fill_bio", "Filling bio...")
    r = js_set_value(page, "textarea[name='bio']", CONTENT["bio"])
    step("bio_result", f"Bio: {r}")
    time.sleep(1)

    step("save", "Clicking save button...")
    try:
        btn = page.locator("button.btn-primary:has-text('حفظ')")
        if btn.is_visible():
            btn.click()
            time.sleep(3)
            step("saved", "Settings saved successfully")
        else:
            step("save_btn_missing", "Save button not visible")
    except Exception as e:
        step("save_error", f"Could not click save: {e}")

    # STEP 3: Find and bid on AI Agents project
    step("project_search", f"Searching for {BID['target_project']}...")
    if not goto_safe(page, BID["project_url"], "project_search"):
        step("error", "Could not load project search")

    time.sleep(3)
    step("projects_loaded", f"URL: {page.url}")

    # Save search page HTML to understand structure
    html = page.content()
    (TEMP / "projects_search.html").write_text(html, encoding="utf-8")
    step("html_saved", f"Saved search HTML ({len(html)} chars)")
    
    # Try to find the project link - try multiple keywords
    project_link = None
    for kw in [BID['target_project'], "AI", "n8n", "Agent", "ذكاء", "وكلاء", "أتمتة"]:
        try:
            link = page.locator(f"a:has-text('{kw}')").first
            if link.is_visible():
                href = link.get_attribute("href")
                if href and "/project/" in href.lower():
                    project_link = link
                    step("project_found", f"Found project with keyword '{kw}': {href}")
                    break
        except:
            continue
    
    if not project_link:
        # Try to find ANY project link
        try:
            links = page.locator("a[href*='/project/']")
            count = links.count()
            if count > 0:
                project_link = links.first
                step("project_found", f"Found project #{count} - clicking first")
        except:
            pass
    
    if project_link:
        project_link.click()
        time.sleep(3)
        step("project_page", f"On project page: {page.url}")
        
        # Look for "تقديم عرض" button
        bid_btn = page.locator("button:has-text('تقديم'), a:has-text('تقديم'), button:has-text('ارسال')").first
        if bid_btn.is_visible():
            bid_btn.click()
            time.sleep(3)
            step("bid_form", "Opened bid form")
            
            # Fill proposal textarea - try JavaScript first, fallback to fill()
            ta = page.locator("textarea").first
            if ta.is_visible():
                result = js_set_value(page, "textarea", BID["proposal"])
                step("proposal_filled", f"Proposal: {result}")
                
                # Try to fill price
                try:
                    price_input = page.locator("input[type='number'], input[name*='price'], input[name*='budget']").first
                    if price_input.is_visible():
                        price_name = price_input.get_attribute("name")
                        js_set_value(page, f"input[name='{price_name}']", BID["price"])
                        step("price_filled", f"Price: ${BID['price']}")
                except:
                    pass
                
                # Submit
                submit_btn = page.locator("button[type='submit'], button:has-text('إرسال'), button:has-text('تقديم')").first
                if submit_btn.is_visible():
                    step("ready_to_submit", "Ready! Waiting 10s for you to verify...")
                    time.sleep(10)
                    submit_btn.click()
                    time.sleep(3)
                    step("submitted", "Bid submitted!")
                else:
                    step("submit_btn_missing", "Could not find submit button - filling done, please submit manually")
            else:
                step("proposal_ta_missing", "No textarea found in bid form")
        else:
            step("bid_btn_missing", "No تقديم عرض button")
            step("need_manual", "Please navigate to bid form manually - browser stays open")
    else:
        step("project_not_found", "Could not find any project link")
        step("need_manual", "Please navigate to the project manually - browser stays open")
    
    step("done", "All done! Browser stays open for review.")
    
    # Keep browser alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
