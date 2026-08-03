"""Complete profile setup - fix personal data and skills"""
import sys, time, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
from playwright.sync_api import sync_playwright

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')

pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data',
    executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    headless=False, args=['--no-sandbox'], viewport={'width':1280,'height':800})
page = ctx.new_page()
page.set_default_timeout(120000)

def js_set(sel, val):
    return page.evaluate("""(a) => {
        const el = document.querySelector(a.s); if(!el) return 'NF';
        el.value = a.v;
        el.dispatchEvent(new Event('input',{bubbles:true}));
        el.dispatchEvent(new Event('change',{bubbles:true}));
        return 'OK';
    }""", {"s": sel, "v": val})

# === PERSONAL DATA ===
print("[1] Opening personal data...")
page.goto('https://nafezly.com/profile/personal-data', timeout=180000)
time.sleep(4)
print(f"URL: {page.url}")

if 'login' in page.url.lower():
    print("Need login...")
    for _ in range(60):
        time.sleep(1)
        if 'login' not in page.url.lower(): break

# Get all form fields
fields = page.eval_on_selector_all("input, select, textarea", """els => els.map(e => ({
    name: e.name || '',
    id: e.id || '',
    type: e.type || e.tagName,
    ph: e.placeholder || '',
    val: (e.value || '').substring(0,30),
    visible: e.offsetParent !== null
})).filter(e => e.visible && e.name)""")
print(f"Form fields: {len(fields)}")
for f in fields:
    print(f"  {f['name']:25s} = {str(f['val']):30s} ({f['type']})")

# Try to save
save_btn = page.query_selector("button:has-text('حفظ'), button:has-text('Save'), input[value='حفظ']")
if save_btn:
    save_btn.click()
    time.sleep(2)
    print("Personal data saved")

# === SKILLS (back on settings page) ===
print("\n[2] Going to skills section...")
page.goto('https://nafezly.com/profile/nafezly-settings', timeout=180000)
time.sleep(4)

# Get skills HTML
skills_html = page.eval_on_selector_all("[class*='skill'] div, [class*='tag'] div, [class*='chip'] div, .col-12.mb-3 div",
    """els => els.map(e => ({
        html: e.innerHTML?.substring(0, 200),
        text: e.innerText?.substring(0, 50)
    })).filter(e => e.text)""")
print(f"Skill areas: {len(skills_html)}")
for s in skills_html:
    print(f"  {s}")

# Look for × buttons to remove English skill
remove_btns = page.eval_on_selector_all("button, span, a", """els => els.map(e => ({
    text: e.innerText?.trim(),
    tag: e.tagName,
    cls: e.className?.substring(0,40)
})).filter(e => e.text === '×' || e.text === '✕' || e.text === '✖')""")
print(f"\nRemove buttons: {len(remove_btns)}")
for b in remove_btns:
    print(f"  [{b['tag']}] cls={b['cls']} text='{b['text']}'")

# Click first × if found to remove English
if remove_btns:
    page.evaluate("""() => {
        const spans = document.querySelectorAll('span');
        for(const s of spans) {
            if(s.innerText.trim() === '×') { s.click(); return 'clicked'; }
        }
        return 'not found';
    }""")
    time.sleep(1)
    print("Removed first skill")

# Check if there's an input for adding skills
add_input = page.query_selector("input[placeholder*='إضافة' i], input[placeholder*='اضافة' i], input[type='text']:not([name])")
if add_input:
    print(f"Found skill input: {add_input.get_attribute('placeholder') or 'no placeholder'}")
    skills = ["n8n", "AI Agents", "Automation", "Python", "API", "Chatbot", "OpenAI"]
    for sk in skills:
        add_input.fill(sk)
        time.sleep(0.3)
        page.keyboard.press("Enter")
        time.sleep(0.5)
        print(f"  Added: {sk}")
    # Save
    save_btn = page.query_selector("button:has-text('حفظ'), button:has-text('Save')")
    if save_btn:
        save_btn.click()
        time.sleep(2)
        print("Skills saved!")
else:
    print("No skill input found")

page.screenshot(path=TEMP / 'profile_final.png')
print("\n=== PROFILE COMPLETE ===")
input("Press Enter to close...")
ctx.close()
pw.stop()
