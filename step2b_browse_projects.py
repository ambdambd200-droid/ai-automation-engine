"""Browse Nafezly projects page and submit bids"""
import sys, time, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
from playwright.sync_api import sync_playwright

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')
sys.path.insert(0, r'C:\Users\A\Desktop\Money')
from keyhub_client import ai_generate

PW = sync_playwright().start()
CTX = PW.chromium.launch_persistent_context(
    user_data_dir=r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data',
    executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    headless=False, args=['--no-sandbox'], viewport={'width':1280,'height':800})
PAGE = CTX.new_page()
PAGE.set_default_timeout(180000)

def wait_login():
    if 'login' in PAGE.url.lower():
        print("  Need login - waiting 60s...")
        for _ in range(60):
            time.sleep(1)
            if 'login' not in PAGE.url.lower(): break

def gen_proposal(project_text):
    prompt = f"""Write a professional proposal in ARABIC (فصحى صحيحة 100%) for a freelance project.

Project details: {project_text[:800]}

Write as "علاء فتحي، مهندس أتمتة ذكاء اصطناعي" (Alaa Fathi, AI Automation Engineer)

Requirements:
- Start: "السلام عليكم ورحمة الله وبركاته"
- Show understanding of the project
- List 3-4 deliverables
- Mention tools: n8n, OpenAI, APIs, Python
- Set price $25-50 (مهم جداً: حدد سعر محدد ضمن هذا النطاق)
- Delivery: mention clear timeline
- End politely
- MAX 120 words
- CORRECT formal Arabic ONLY (no mistakes)"""
    return ai_generate(prompt, caller="bid", temperature=0.2).strip()[:1000]

# Step 1: Browse projects page for AI/automation
print("[1] Opening Nafezly projects...")
PAGE.goto('https://nafezly.com/projects', timeout=180000)
time.sleep(5)
wait_login()

# Search for relevant projects
searches = ['n8n', 'AI Agent', 'automation', 'chatbot', 'ذكاء اصطناعي', 'أتمتة', 'بوت']
all_projects = []

for q in searches:
    print(f"\n[Search] '{q}'...")
    url = f'https://nafezly.com/projects?key={q.replace(" ", "+")}'
    PAGE.goto(url, timeout=180000)
    time.sleep(4)
    
    # Get project cards
    projects = PAGE.eval_on_selector_all("a[href*='/project/']",
        "els => els.map(e => ({href: e.href, text: e.innerText?.trim().substring(0, 120)})).filter(e => e.href && !e.href.includes('/create'))")
    
    print(f"  Found {len(projects)} projects")
    for p in projects[:5]:
        all_projects.append(p)

# Deduplicate
seen = set()
unique = []
for p in all_projects:
    if p['href'] not in seen:
        seen.add(p['href'])
        unique.append(p)
    
print(f"\nTotal unique projects: {len(unique)}")
for p in unique[:10]:
    print(f"  {p['text'][:60]:60s} | {p['href'][:50]}")

# Step 2: Open each project and bid
print(f"\n[2] Opening top {min(5, len(unique))} projects for bidding...")

for idx, proj in enumerate(unique[:5]):
    url = proj['href']
    print(f"\n[{idx+1}] {proj['text'][:60]}")
    print(f"    URL: {url}")
    
    PAGE.goto(url, timeout=180000)
    time.sleep(5)
    wait_login()
    
    # Check if it actually loaded project content
    page_text = PAGE.eval_on_selector("body", "el => el.innerText.substring(0, 500)")
    if 'تسجيل' in page_text[:100] and 'Loading' in page_text[:200]:
        print("    ❌ Page not loaded fully - checking screenshot")
        PAGE.screenshot(path=TEMP / f'bid_{idx}_error.png')
        continue
    
    PAGE.screenshot(path=TEMP / f'bid_{idx}_open.png')
    
    # Get project details
    details = PAGE.evaluate("""() => ({
        title: document.querySelector('h1, h2, [class*="title"]')?.innerText?.substring(0,200) || '',
        desc: document.querySelector('[class*="desc"], [class*="content"], .col-12.mt-2, [class*="detail"], .project-content')?.innerText?.substring(0,1000) || '',
        budget: document.querySelector('[class*="budget"], [class*="price"], [class*="سعر"]')?.innerText?.substring(0,100) || ''
    })""")
    print(f"    Title: {details['title'][:80]}")
    print(f"    Budget: {details['budget'][:60]}")
    
    # Find bid button
    btn = PAGE.evaluate("""() => {
        const items = document.querySelectorAll('button, a');
        for(const el of items) {
            if(!el.offsetParent) continue;
            const t = el.innerText.trim().toLowerCase();
            if(t.includes('تقديم') || t.includes('عرض') || t === 'تقديم' || t.includes('offer'))
                return el.outerHTML.substring(0,100);
        }
        return null;
    }""")
    
    if not btn:
        print("    ❌ No bid button")
        continue
    
    print(f"    ✅ Bid button: {btn[:50]}")
    PAGE.evaluate("""() => {
        const items = document.querySelectorAll('button, a');
        for(const el of items) {
            if(!el.offsetParent) continue;
            const t = el.innerText.trim().toLowerCase();
            if(t.includes('تقديم') || t.includes('عرض') || t === 'تقديم') { el.click(); return; }
        }
    }""")
    time.sleep(3)
    PAGE.screenshot(path=TEMP / f'bid_{idx}_form.png')
    
    # Find textarea
    ta = PAGE.query_selector("textarea")
    if not ta:
        print("    ❌ No textarea found")
        continue
    
    print("    ✅ Textarea found - generating proposal...")
    
    try:
        proposal = gen_proposal(details['title'] + ' | ' + details['desc'])
    except Exception as e:
        print(f"    ⚠ AI failed: {e}")
        proposal = f"""السلام عليكم ورحمة الله وبركاته،

أنا علاء فتحي، مهندس أتمتة ذكاء اصطناعي. يسعدني التقدم لهذا المشروع.

سأقوم بـ:
١. تحليل المتطلبات وفهم الاحتياجات بدقة
٢. تصميم الحل المناسب باستخدام n8n والذكاء الاصطناعي
٣. تنفيذ واختبار النظام
٤. تسليم مع توثيق كامل

السعر: ٣٥ دولاراً
المدة: ٥-٧ أيام

للتواصل، أنا جاهز.

والسلام عليكم،
علاء فتحي"""
    
    print(f"    Proposal ({len(proposal)} chars): {proposal[:100]}...")
    
    PAGE.evaluate(f"""() => {{
        const ta = document.querySelector('textarea');
        if(ta) {{ ta.value = {json.dumps(proposal)}; ta.dispatchEvent(new Event('input',{{b:true}})); ta.dispatchEvent(new Event('change',{{b:true}})); }}
    }}""")
    print("    ✅ Proposal filled")
    
    # Price field
    price_el = PAGE.query_selector("input[type='number']")
    if price_el:
        PAGE.evaluate("() => { const el = document.querySelector('input[type=number]'); if(el) { el.value = '35'; el.dispatchEvent(new Event('input',{b:true})); el.dispatchEvent(new Event('change',{b:true})); } }")
        print("    ✅ Price set")
    
    # Submit
    PAGE.evaluate("""() => {
        const items = document.querySelectorAll('button');
        for(const el of items) {
            const t = el.innerText.trim().toLowerCase();
            if(t.includes('إرسال') || t.includes('تقديم') || t.includes('تأكيد')) { el.click(); return 'clicked'; }
        }
        return 'not found';
    }""")
    time.sleep(3)
    print(f"    Submit result: {PAGE.url[:70]}")
    PAGE.screenshot(path=TEMP / f'bid_{idx}_submitted.png')

print(f"\nDone! {min(5, len(unique))} projects processed")
input("Press Enter...")
CTX.close()
PW.stop()
