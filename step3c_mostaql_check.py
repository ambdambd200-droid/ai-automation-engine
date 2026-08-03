"""Check Mostaql account status and complete remaining steps"""
import sys, time
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

def js_set(sel, val):
    return page.evaluate("""(a) => {
        const el = document.querySelector(a.s); if(!el) return 'NF';
        el.value = a.v; el.dispatchEvent(new Event('input',{b:true})); el.dispatchEvent(new Event('change',{b:true}));
        return 'OK';
    }""", {"s": sel, "v": val})

print("[1] Checking Mostaql dashboard...")
page.goto('https://mostaql.com', timeout=180000)
time.sleep(4)
print(f"URL: {page.url[:80]}")
page.screenshot(path=TEMP / 'mostaql_home.png')

# Check if logged in
if 'login' in page.url.lower():
    print("Not logged in - logging in...")
    password = (TEMP / 'mostaql_password.txt').read_text(encoding='utf-8').strip()
    page.goto('https://mostaql.com/login', timeout=180000)
    time.sleep(3)
    js_set("input[type='email']", "ambdambd200@gmail.com")
    js_set("input[type='password']", password)
    page.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for(const b of btns) {
            if(b.innerText.toLowerCase().includes('دخول')) { b.click(); return; }
        }
    }""")
    time.sleep(5)
    print(f"After login: {page.url[:80]}")

# Check onboarding status
page.goto('https://mostaql.com/onboarding/profile', timeout=180000)
time.sleep(4)
print(f"Onboarding URL: {page.url[:80]}")

body_text = page.eval_on_selector("body", "el => el.innerText")
if 'onboarding' in page.url:
    print("Still on onboarding - completing remaining fields...")
    
    # Get all form elements
    fields = page.eval_on_selector_all("input, textarea, select", """els => els.map(e => ({
        name: e.name || '', id: e.id || '', type: e.type || e.tagName,
        ph: (e.placeholder || '').substring(0, 40),
        val: (e.value || '').substring(0, 30),
        visible: e.offsetParent !== null
    })).filter(e => e.visible && (e.name || e.id))""")
    
    for f in fields:
        print(f"  {f['name'] or f['id']:30s} val='{f['val']}' ph='{f['ph']}' ({f['type']})")
    
    # Try setting job title
    if not any(f['val'].strip() for f in fields if f['name'] == 'job_title'):
        js_set("input[name='job_title']", "مطور أتمتة وذكاء اصطناعي")
        print("  Job title set")
    
    # Bio was already set in previous script, but let's verify
    if not any(f['val'].strip() for f in fields if f['type'] == 'textarea'):
        bio = "أنا مطور أتمتة وذكاء اصطناعي، أبني أنظمة أتمتة بـ Python و n8n."
        js_set("textarea", bio)
        print("  Bio set")
    
    # Try to save
    page.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for(const b of btns) {
            const t = b.innerText.toLowerCase();
            if(t.includes('حفظ') || t.includes('التالي') || t.includes('update')) { b.click(); return 'clicked'; }
        }
        return 'not found';
    }""")
    time.sleep(3)
    print(f"  After save: {page.url[:80]}")
    page.screenshot(path=TEMP / 'mostaql_after_save.png')

# Check skills
print("\n[2] Checking skills...")
page.goto('https://mostaql.com/account/profile', timeout=180000)
time.sleep(4)

# Look for skills input
skills_sec = page.eval_on_selector_all("[class*='skill'], [class*='tag']", """els => els.map(e => ({
    text: e.innerText?.trim().substring(0, 80),
    visible: e.offsetParent !== null
})).filter(e => e.text && e.visible)""")
print(f"Skills section: {len(skills_sec)}")
for s in skills_sec[:10]:
    print(f"  {s['text'][:60]}")
    
# Check email verification status
print("\n[3] Checking verification...")
page.goto('https://mostaql.com/account/verification', timeout=180000)
time.sleep(3)
ver_text = page.eval_on_selector("body", "el => el.innerText")
if 'verify' in ver_text.lower() or 'تفعيل' in ver_text:
    print("  Email verification needed")
else:
    print("  Account appears verified")

print(f"\n=== Mostaql Status ===")
print(f"  ✅ Account created: Alaa Fathi")
print(f"  ✅ Password: {(TEMP / 'mostaql_password.txt').read_text(encoding='utf-8').strip()}")
page.screenshot(path=TEMP / 'mostaql_final_state.png')

input("Press Enter...")
ctx.close()
pw.stop()
