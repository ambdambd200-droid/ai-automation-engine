"""Read Nafezly projects and submit bids with correct Arabic"""
import sys, time, json, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
from playwright.sync_api import sync_playwright

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')
sys.path.insert(0, r'C:\Users\A\Desktop\Money')
from keyhub_client import ai_generate

PROJECTS = [
    "https://nafezly.com/project/49664-%D9%85%D8%B7%D9%84%D9%88%D8%A8-%D9%85%D9%87%D9%86%D8%AF%D8%B3-%D8%A8%D8%B1%D9%85%D8%AC%D9%8A%D8%A7%D8%AA-%D9%88%D9%85%D8%AA%D8%AE%D8%B5%D8%B5-%D8%A3%D8%AA%D9%85%D8%AA%D8%A9-%D9%84%D8%AA%D9%86%D9%81%D9%8A%D8%B0-%D9%86%D8%B8%D8%A7%D9%85-%D8%A7%D9%84%D8%AD%D8%AC%D9%88%D8%B2%D8%A7%D8%AA-%D8%A8%D8%A7%D8%B3%D8%AA%D8%AE%D8%AF%D8%A7%D9%85-n8n",
    "https://nafezly.com/project/49717-%D8%A8%D9%88%D8%AA-%D8%B0%D9%83%D8%A7%D8%A1-%D8%A7%D8%B5%D8%B7%D9%86%D8%A7%D8%B9%D9%8A-%D9%84%D9%84%D8%A5%D8%AC%D8%A7%D8%A8%D8%A9-%D8%B9%D9%84%D9%89-%D8%A7%D9%84%D8%A3%D8%B3%D8%A6%D9%84%D8%A9-%D9%85%D9%86-%D9%85%D9%84%D9%81-PDF",
    "https://nafezly.com/project/49679-%D9%85%D8%B7%D9%84%D9%88%D8%A8-%D9%85%D9%87%D9%86%D8%AF%D8%B3-%D8%A7%D8%AA%D9%85%D8%AA%D8%A9-%D9%84%D9%83%D8%AA%D8%A8%D8%A9-Bash-Script-%D9%84%D8%A3%D8%AA%D9%85%D8%AA%D8%A9-%D8%A7%D9%84%D9%86%D8%B3%D8%AE-%D8%A7%D9%84%D8%A7%D8%AD%D8%AA%D9%8A%D8%A7%D8%B7%D9%8A",
    "https://nafezly.com/project/48069-%D8%AA%D8%B7%D9%88%D9%8A%D8%B1-%D9%86%D8%B8%D8%A7%D9%85-Agentic-%D9%82%D8%A7%D8%A6%D9%85-%D9%88%D8%A5%D8%B6%D8%A7%D9%81%D8%A9-%D8%AF%D8%B9%D9%85-%D9%84%D8%AA%D9%88%D9%84%D9%8A%D8%AF-%D8%A7%D9%84%D8%B1%D8%B3%D9%88%D9%85-%D8%A7%D9%84%D8%A8%D9%8A%D8%A7%D9%86%D9%8A%D8%A9-Charts",
]

def gen_proposal(title, desc, price_range):
    prompt = f"""Write a professional proposal in ARABIC (فصحى) for a freelance project on Nafezly.

Project: {title}
Description: {desc}

The proposal must:
- Start with "السلام عليكم ورحمة الله وبركاته"
- Introduce myself as "علاء فتحي، مهندس أتمتة ذكاء اصطناعي"
- Show understanding of project requirements
- Outline 3-4 clear deliverables
- Mention tools (n8n, OpenAI, APIs, Python)
- Set a price range: {price_range}
- Set delivery: depends on complexity
- End politely
- Be MAXIMUM 150 words, professional
- Use CORRECT formal Arabic (فصحى)"""

    res = ai_generate(prompt, caller="bid_gen", temperature=0.3)
    return res.strip()

pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data',
    executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    headless=False, args=['--no-sandbox'], viewport={'width':1280,'height':800})
page = ctx.new_page()
page.set_default_timeout(120000)

results = []

for i, url in enumerate(PROJECTS):
    print(f"\n{'='*60}")
    print(f"[{i+1}/{len(PROJECTS)}] Opening project...")
    page.goto(url, timeout=180000)
    time.sleep(4)
    
    if 'login' in page.url.lower():
        for _ in range(60):
            time.sleep(1)
            if 'login' not in page.url.lower(): break
    
    # Get project title and description
    project_info = page.evaluate("""() => {
        const title = document.querySelector('h1, h2, [class*="title"]');
        const desc = document.querySelector('[class*="desc"], [class*="content"], [class*="detail"]');
        const offers = document.querySelectorAll('[class*="offer"], [class*="proposal"], [class*="عرض"]');
        return {
            title: title ? title.innerText.substring(0, 200) : '',
            desc: desc ? desc.innerText.substring(0, 1000) : '',
            offerCount: offers.length
        };
    }""")
    
    print(f"  Title: {project_info['title'][:80]}")
    print(f"  Desc: {project_info['desc'][:150]}")
    
    page.screenshot(path=TEMP / f'proj_{i}_page.png')
    
    # Find bid button
    bid_btn = page.evaluate("""() => {
        const items = document.querySelectorAll('button, a');
        for(const el of items) {
            const t = el.innerText.toLowerCase().trim();
            if(t.includes('تقديم') || t.includes('عرض سعر') || t.includes('تقديم عرض') || t === 'تقديم' || t === 'أرسل')
                return {text: el.innerText.trim().substring(0,30), tag: el.tagName, selector: el.tagName};
            if(t.includes('offer') || t.includes('proposal'))
                return {text: el.innerText.trim().substring(0,30), tag: el.tagName};
        }
        return null;
    }""")
    
    if not bid_btn:
        print(f"  ❌ No bid button found")
        results.append({"url": url, "status": "no_bid_button"})
        continue
    
    print(f"  ✅ Bid button: '{bid_btn['text']}'")
    page.evaluate("""() => {
        const items = document.querySelectorAll('button, a');
        for(const el of items) {
            const t = el.innerText.toLowerCase().trim();
            if(t.includes('تقديم') || t.includes('عرض سعر') || t === 'تقديم') { el.click(); return; }
        }
    }""")
    time.sleep(3)
    
    # Check for popup/modal
    print(f"  URL after click: {page.url[:80]}")
    page.screenshot(path=TEMP / f'proj_{i}_form.png')
    
    # Look for form fields
    form_fields = page.evaluate("""() => {
        const fields = [];
        document.querySelectorAll('textarea, input, select').forEach(el => {
            if(el.offsetParent !== null) {
                fields.push({type: el.type || el.tagName, name: el.name || '', id: el.id || '', placeholder: el.placeholder || ''});
            }
        });
        return fields;
    }""")
    print(f"  Form fields: {len(form_fields)}")
    for f in form_fields:
        print(f"    {f['type']:15s} name={f['name']:20s} placeholder={f['placeholder'][:30]}")
    
    # Find proposal textarea
    ta = None
    for f in form_fields:
        if f['type'] == 'textarea' or f['type'] == 'Textarea':
            ta = f
            break
    
    if not ta:
        print("  ❌ No textarea found for proposal")
        results.append({"url": url, "status": "no_textarea"})
        continue
    
    # Generate proposal with AI
    print("  Generating proposal with AI...")
    try:
        proposal = gen_proposal(
            project_info['title'],
            project_info['desc'],
            "$25-50"
        )
    except Exception as e:
        print(f"  AI gen failed: {e}")
        proposal = f"""السلام عليكم ورحمة الله وبركاته،

أنا علاء فتحي، مهندس أتمتة ذكاء اصطناعي. أستطيع تنفيذ هذا المشروع بكفاءة عالية باستخدام خبرتي في n8n والذكاء الاصطناعي.

مقترح العمل:
1. تحليل المتطلبات وتصميم الحل المناسب
2. بناء وتطوير النظام المطلوب
3. اختبار شامل وضمان الجودة
4. تسليم مع توثيق كامل

السعر: 25-50 دولار (حسب التفاصيل)
المدة: 3-7 أيام

للتواصل، أنا جاهز للمناقشة.

وشكراً،
علاء فتحي"""
    
    print(f"  Proposal ({len(proposal)} chars): {proposal[:100]}...")
    
    # Fill proposal
    page.evaluate(f"""() => {{
        const ta = document.querySelector('textarea');
        if(!ta) return 'not found';
        ta.value = {json.dumps(proposal)};
        ta.dispatchEvent(new Event('input', {{bubbles: true}}));
        ta.dispatchEvent(new Event('change', {{bubbles: true}}));
        return 'filled';
    }}""")
    print("  ✅ Proposal filled")
    
    # Set price
    price_fields = [f for f in form_fields if 'price' in f['name'].lower() or 'budget' in f['name'].lower() or f['type'] == 'number']
    if price_fields:
        pf = price_fields[0]
        page.evaluate(f"""() => {{
            const el = document.querySelector('input[name="{pf['name']}"], input[type=number]');
            if(el) {{ el.value = '35'; el.dispatchEvent(new Event('input',{{b:true}})); el.dispatchEvent(new Event('change',{{b:true}})); }}
        }}""")
        print("  ✅ Price set: $35")
    
    # Submit
    submit_btn = page.evaluate("""() => {
        const items = document.querySelectorAll('button, input[type=submit]');
        for(const el of items) {
            const t = el.innerText.toLowerCase().trim() || el.value?.toLowerCase().trim();
            if(t.includes('إرسال') || t.includes('تقديم') || t.includes('تأكيد') || t.includes('submit') || t.includes('send'))
                { el.click(); return 'clicked: ' + t; }
        }
        return 'not found';
    }""")
    print(f"  Submit: {submit_btn}")
    time.sleep(3)
    
    print(f"  URL after submit: {page.url[:80]}")
    page.screenshot(path=TEMP / f'proj_{i}_done.png')
    
    results.append({"url": url, "status": "bid_submitted", "title": project_info['title'][:60]})

print(f"\n{'='*60}")
print(f"RESULTS: {len(results)} projects processed")
for r in results:
    print(f"  {r.get('status','?'):20s} | {r.get('title','')[:50]}")
print(f"\nDone! Check Temp/ for screenshots.")
input("Press Enter...")
ctx.close()
pw.stop()
