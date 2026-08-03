"""Check Nafezly project page for bid/voice modal"""
import sys, time, json
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
page.set_default_timeout(180000)

page.goto('https://nafezly.com/projects?key=n8n', timeout=180000)
time.sleep(4)
print(f"Projects page loaded")

# Click on first project link
first_link = page.query_selector("a[href*='/project/']:not([href*='create'])")
if first_link:
    print(f"Clicking first project link...")
    first_link.click()
    time.sleep(5)
    print(f"URL: {page.url}")
else:
    print("No project link found")
    # Try getting full page HTML
    html = page.content()
    (TEMP / 'projects_html.txt').write_text(html[:5000], encoding='utf-8')

# Check what's on the page
html = page.content()
(TEMP / 'project_html.txt').write_text(html, encoding='utf-8')

# Check for modals/overlays
modals = page.eval_on_selector_all("[class*='modal'], [class*='overlay'], [class*='popup']",
    """els => els.map((e,i) => ({
        idx: i,
        visible: e.offsetParent !== null,
        classes: e.className?.substring(0,60),
        text: e.innerText?.trim().substring(0,100)
    })).filter(e => e.visible)""")
print(f"\nModals/overlays found: {len(modals)}")
for m in modals:
    print(f"  [{m['idx']}] {m['classes']}: {m['text'][:80]}")

# Check for voice recording element
voice = page.eval_on_selector_all("[class*='voice'], [class*='audio'], [class*='record'], [class*='تسجيل']",
    """els => els.map(e => ({
        cls: e.className?.substring(0,40),
        text: e.innerText?.trim().substring(0,60),
        visible: e.offsetParent !== null
    })).filter(e => e.visible)""")
print(f"\nVoice/audio elements: {len(voice)}")
for v in voice:
    print(f"  {v['cls']}: {v['text']}")

# Check all buttons
buttons = page.eval_on_selector_all("button", """els => els.map(e => ({
    text: e.innerText?.trim().substring(0,30),
    visible: e.offsetParent !== null,
    type: e.type || ''
})).filter(e => e.visible)""")
print(f"\nButtons: {len(buttons)}")
for b in buttons:
    print(f"  {b['text']:30s} type={b['type']}")

# Try to close any modal
page.evaluate("""() => {
    const closeBtns = document.querySelectorAll('[class*="close"], [class*="إغلاق"], button.close');
    for(const b of closeBtns) {
        if(b.offsetParent !== null) { console.log('closing modal'); b.click(); return 'closed'; }
    }
    return 'no close btn';
}""")
time.sleep(2)

# Check if content loaded
content = page.eval_on_selector("body", "el => el.innerText?.substring(0, 1000)")
print(f"\nPage content after close:\n{content[:500]}")

page.screenshot(path=TEMP / 'project_detail.png')

input("Press Enter...")
ctx.close()
pw.stop()
