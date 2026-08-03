"""Register on Mostaql.com and complete profile"""
import sys, time, json, string, random
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
from playwright.sync_api import sync_playwright

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')

# Generate password
password = 'Alaa@' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
print(f"Password: {password}")
(TEMP / 'mostaql_password.txt').write_text(password, encoding='utf-8')

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

# Step 1: Register
print("[1] Opening mostaql.com/register...")
page.goto('https://mostaql.com/register', timeout=180000)
time.sleep(4)
page.screenshot(path=TEMP / 'mostaql_register.png')

# Fill form
js_set("input[name='name']", "Alaa Fathi")
js_set("input[type='email']", "ambdambd200@gmail.com")
js_set("input[type='password']", password)

# Select freelancer type
page.evaluate("""() => {
    const radios = document.querySelectorAll('input[type="radio"]');
    for(const r of radios) {
        if(r.value === 'freelancer' || r.id.includes('freelancer')) { r.checked = true; r.dispatchEvent(new Event('change',{b:true})); return; }
    }
}""")
time.sleep(1)

# Click register/submit
page.evaluate("""() => {
    const btns = document.querySelectorAll('button');
    for(const b of btns) {
        const t = b.innerText.toLowerCase();
        if(t.includes('تسجيل') || t.includes('register') || t.includes('إنشاء')) { b.click(); return 'clicked'; }
    }
    return 'not found';
}""")
time.sleep(5)
print(f"  Register result URL: {page.url[:80]}")
page.screenshot(path=TEMP / 'mostaql_register_result.png')

# Check if we need email verification
page_text = page.eval_on_selector("body", "el => el.innerText")
if 'verify' in page_text.lower() or 'تفعيل' in page_text:
    print("  Need email verification - opened email")
    # Open Gmail to verify
    page.goto('https://gmail.com', timeout=180000)
    time.sleep(5)
    page.screenshot(path=TEMP / 'gmail_for_verify.png')
    print(f"  Gmail URL: {page.url[:80]}")

print(f"\n=== Mostaql registration info ===")
print(f"  Email: ambdambd200@gmail.com")
print(f"  Password: {password}")
print(f"  Saved to: {TEMP / 'mostaql_password.txt'}")

input("Press Enter to continue to profile setup...")

# Step 2: Complete profile
print("\n[2] Completing profile...")
page.goto('https://mostaql.com/account/profile', timeout=180000)
time.sleep(4)
print(f"  Profile URL: {page.url[:80]}")
page.screenshot(path=TEMP / 'mostaql_profile.png')

# Set professional title
js_set("input[name='title'], input[placeholder*='professional' i], input[placeholder*='مسمى' i]", "مطوّر أتمتة وذكاء اصطناعي | Python | n8n")
time.sleep(1)

# Set bio
bio = """أنا مطوّر أتمتة وذكاء اصطناعي، أبني أنظمة أتمتة بـ Python و n8n توفّر الوقت وتقلّل العمل اليدوي المتكرّر. أعمل بشكل مستقل وأقدّم حلولًا عملية للشركات الصغيرة وأصحاب المشاريع.

خدماتي:
• أتمتة سير العمل عبر n8n و Zapier و Make.com
• بناء وكلاء ذكاء اصطناعي بـ OpenAI و Claude
• تكامل بين تطبيقات SaaS (Google Workspace, Slack, Airtable, Notion)
• خطوط أنابيب لمعالجة البيانات باستخدام Python و Flask
• أتمتة البريد الإلكتروني والـ CRM

أسلوبي:
- تواصل واضح قبل البدء
- تسليم في الوقت المحدد
- توثيق قصير بعد كل تسليم
- مراجعة مجانية صغيرة بعد التسليم

أنا مبتدئ نسبيًا في مستقل، فأسعاري في البداية تنافسية مقابل جودة العمل. أسعى لبناء سجل قوي من خلال عروض احترافية وتسليم موثوق."""

for sel in ["textarea", "[contenteditable='true']"]:
    el = page.query_selector(sel)
    if el and el.is_visible():
        js_set(sel, bio)
        print(f"  Bio filled via {sel}")
        break

# Save
page.evaluate("""() => {
    const btns = document.querySelectorAll('button');
    for(const b of btns) {
        if(b.innerText.includes('حفظ') || b.innerText.includes('Save')) { b.click(); return 'clicked'; }
    }
    return 'not found';
}""")
time.sleep(3)
print(f"  Saved profile")
page.screenshot(path=TEMP / 'mostaql_profile_saved.png')

print(f"\n=== Mostaql Done! ===")
print(f"Check your email ({password}) and verify the account.")
input("Press Enter...")
ctx.close()
pw.stop()
