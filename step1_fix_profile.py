"""Step 1: Fix Nafezly profile - bio, skills, job title"""
import sys, time, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
from playwright.sync_api import sync_playwright

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')
BRAVE_EXE = r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'
BRAVE_PROFILE = r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data'

pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=BRAVE_PROFILE, executable_path=BRAVE_EXE,
    headless=False, args=['--no-sandbox'], viewport={'width':1280,'height':800})
page = ctx.new_page()
page.set_default_timeout(120000)

def js_set(sel, val):
    return page.evaluate("""(a) => {
        const el = document.querySelector(a.s); if(!el) return 'NOTFOUND';
        el.value = a.v;
        el.dispatchEvent(new Event('input',{bubbles:true}));
        el.dispatchEvent(new Event('change',{bubbles:true}));
        return 'OK';
    }""", {"s": sel, "v": val})

# === PROFILE SETTINGS ===
print("[1/3] Opening profile settings...")
page.goto('https://nafezly.com/profile/nafezly-settings', timeout=180000)
time.sleep(4)
print(f"URL: {page.url}")

if 'login' in page.url.lower():
    print("Login required... waiting 60s")
    for _ in range(60):
        time.sleep(1)
        if 'login' not in page.url.lower():
            break
    print(f"Logged in. URL: {page.url}")

# Check current bio field
current_bio = page.eval_on_selector("textarea[name='bio'], textarea#bio, [class*='bio'] textarea",
    "el => el ? el.value?.substring(0, 200) : 'not found'")
sys.stdout.flush()

# New bio
new_bio = """أنا علاء فتحي، مهندس أتمتة ذكاء اصطناعي من غزة. متخصص في بناء أنظمة أتمتة متكاملة باستخدام n8n والذكاء الاصطناعي.

أقدم:
- بناء وكلاء ذكاء اصطناعي (AI Agents) باستخدام n8n و OpenAI
- أتمتة سير العمل وربط التطبيقات والخدمات
- تطوير Chatbots ذكية لتليجرام وواتساب وإنستغرام
- ربط APIs وأنظمة السحابة

لغات: العربية (أم), الإنجليزية (متقدم)"""

# Try different selectors for bio
for sel in ["textarea[name='bio']", "textarea#bio", "textarea", "[contenteditable='true']", "[class*='editor']"]:
    el = page.eval_on_selector(sel, "el => el ? el.tagName + '.' + (el.name||el.id||'') : null")
    if el:
        print(f"  Found editor: {sel} -> {el}")
        # Clear and set
        page.evaluate("""(s) => {
            const el = document.querySelector(s);
            if(!el) return;
            el.value = '';
            el.dispatchEvent(new Event('input',{bubbles:true}));
        }""", sel)
        time.sleep(1)
        r = js_set(sel, new_bio)
        print(f"  Bio set: {r}")
        break

# Job title
print("\nSetting job title...")
for sel in ["input[name='job_title']", "input#job_title", "input[placeholder*='job' i]", "input[placeholder*='مسمى' i]"]:
    el = page.eval_on_selector(sel, "el => el ? (el.tagName + '.' + (el.name||el.id||'')) : null")
    if el:
        print(f"  Found title field: {sel} -> {el}")
        js_set(sel, "مهندس أتمتة ذكاء اصطناعي")
        print(f"  Title set")
        break

# Save button
print("\nLooking for save button...")
save_btns = page.eval_on_selector_all("button, input[type='submit']", """els => els.map(e => ({
    text: e.innerText?.trim().substring(0,40),
    type: e.type || e.tagName,
    visible: e.offsetParent !== null
})).filter(e => e.visible && e.text)""")

for b in save_btns:
    if any(w in b['text'].lower() for w in ['save', 'حفظ', 'update', 'تحديث']):
        print(f"  Save button: {b['text']}")
        page.evaluate(f"""() => {{ 
            const btns = document.querySelectorAll('button');
            for(const b of btns) {{
                if(b.innerText.includes('{b["text"][:5]}')) {{ b.click(); return 'clicked'; }}
            }}
            return 'not found';
        }}""")
        time.sleep(3)
        print("  Saved!")
        break
else:
    print("  No save button found - checking page")

page.screenshot(path=TEMP / 'profile_after_bio.png')

# === SKILLS ===
print("\n[2/3] Checking for skills section...")
# Get all visible text on page to find skills
page_text = page.eval_on_selector("body", "el => el.innerText")
# Find words containing skill-related terms
for line in page_text.split('\n'):
    if any(w in line.lower() for w in ['مهار', 'skill', 'tag', 'chip', 'اختصاص']):
        print(f"  Found: {line.strip()}")

# Try to click on skills or specialization area
skills_click = page.eval_on_selector_all("span, div, label, a",
    """els => els.map(e => ({
        text: e.innerText?.trim().substring(0,30),
        tag: e.tagName,
        cls: e.className?.substring(0,40),
        clickable: e.onclick !== null || e.tagName === 'A'
    })).filter(e => e.text && (e.text.includes('مهار') || e.text.toLowerCase().includes('skill')))""")
print(f"Skill-related elements: {len(skills_click)}")
for s in skills_click:
    print(f"  {s}")

page.screenshot(path=TEMP / 'profile_after_skills.png')

# === PERSONAL DATA ===
print("\n[3/3] Opening personal data...")
page.goto('https://nafezly.com/profile/personal-data', timeout=180000)
time.sleep(3)
print(f"URL: {page.url}")

# Fix name if needed
name_field = page.eval_on_selector("input[name='name'], input#name, input[placeholder*='اسم' i]",
    "el => el ? el.value : null")
if name_field:
    sys.stdout.flush()
    if not name_field or name_field.strip() == '':
        js_set("input[name='name']", "علاء فتحي")
        print("Name set")

page.screenshot(path=TEMP / 'profile_after_personal.png')

print("\n=== PROFILE DONE ===")
input("Press Enter to continue to Step 2 (projects search)...")
ctx.close()
pw.stop()
