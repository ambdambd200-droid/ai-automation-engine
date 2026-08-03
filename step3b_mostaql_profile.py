"""Complete Mostaql onboarding profile"""
import sys, time, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
from playwright.sync_api import sync_playwright

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')
password = (TEMP / 'mostaql_password.txt').read_text(encoding='utf-8').strip()

pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data',
    executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    headless=False, args=['--no-sandbox'], viewport={'width':1280,'height':800})
page = ctx.new_page()
page.set_default_timeout(180000)

def js_set(sel, val):
    return page.evaluate("""(a) => {
        const el = document.querySelector(a.s); if(!el) return 'NF';
        el.value = a.v; el.dispatchEvent(new Event('input',{b:true})); el.dispatchEvent(new Event('change',{b:true}));
        return 'OK';
    }""", {"s": sel, "v": val})

print("[1] Opening onboarding profile...")
page.goto('https://mostaql.com/onboarding/profile', timeout=180000)
time.sleep(5)
print(f"URL: {page.url[:80]}")
page.screenshot(path=TEMP / 'mostaql_onboard.png')

if 'login' in page.url.lower():
    print("Need login - logging in...")
    js_set("input[type='email']", "ambdambd200@gmail.com")
    js_set("input[type='password']", password)
    page.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for(const b of btns) {
            if(b.innerText.toLowerCase().includes('دخول') || b.innerText.toLowerCase().includes('login')) { b.click(); return; }
        }
    }""")
    time.sleep(5)
    print(f"After login: {page.url[:80]}")

# Check what's on the onboarding page
fields = page.eval_on_selector_all("input, textarea, select", """els => els.map(e => ({
    name: e.name || '', id: e.id || '', type: e.type || e.tagName,
    ph: (e.placeholder || '').substring(0, 30),
    visible: e.offsetParent !== null
})).filter(e => e.visible && (e.name || e.id))""")
print(f"\nForm fields: {len(fields)}")
for f in fields:
    print(f"  {f['name'] or f['id']:25s} {f['ph']:30s} ({f['type']})")

# Set title
title_input = page.query_selector("input[placeholder*='title' i], input[placeholder*='مسمى' i], input[name='title']")
if title_input:
    js_set("input[name='title'], input[placeholder*='مسمى']", "مطوّر أتمتة وذكاء اصطناعي | Python | n8n")
    print("Title set")

# Set bio
bio_textarea = page.query_selector("textarea")
if bio_textarea:
    bio = """أنا مطوّر أتمتة وذكاء اصطناعي، أبني أنظمة أتمتة بـ Python و n8n توفر الوقت وتقلل العمل اليدوي.

خدماتي:
• أتمتة سير العمل (n8n, Make.com, Zapier)
• وكلاء ذكاء اصطناعي (OpenAI, Claude)
• تكامل تطبيقات SaaS
• معالجة بيانات بـ Python
• أتمتة البريد الإلكتروني و CRM"""
    js_set("textarea", bio)
    print("Bio set")

# Save/Next
page.evaluate("""() => {
    const btns = document.querySelectorAll('button');
    for(const b of btns) {
        const t = b.innerText.toLowerCase();
        if(t.includes('حفظ') || t.includes('التالي') || t.includes('next') || t.includes('save') || t.includes('تحديث')) { b.click(); return 'clicked'; }
    }
    return 'not found';
}""")
time.sleep(3)
print(f"After save: {page.url[:80]}")
page.screenshot(path=TEMP / 'mostaql_onboard_saved.png')

# Try to add portfolio
print("\n[2] Checking portfolio/skills...")
page.goto('https://mostaql.com/account/portfolio', timeout=180000)
time.sleep(4)
print(f"Portfolio URL: {page.url[:80]}")
page.screenshot(path=TEMP / 'mostaql_portfolio.png')

# Check for skills section
skills_input = page.query_selector("input[placeholder*='skill' i], input[placeholder*='مهارة' i]")
if skills_input:
    skills = ["n8n", "Python", "OpenAI", "Automation", "Flask", "API", "Workflow", "Chatbot"]
    for sk in skills:
        skills_input.fill(sk)
        page.keyboard.press("Enter")
        time.sleep(0.3)
    print(f"Skills added: {skills}")

print(f"\n=== Profile complete! ===")
print(f"Mostaql account: Alaa Fathi")
print(f"Password: {password}")
input("Press Enter...")
ctx.close()
pw.stop()
