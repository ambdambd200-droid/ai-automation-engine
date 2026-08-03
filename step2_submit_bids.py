"""Submit bids on Nafezly projects that match our services"""
import sys, time, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
from playwright.sync_api import sync_playwright

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')

# Projects that match our services
PROJECTS = [
    {"url": "https://nafezly.com/project/49664-%D9%85%D8%B7%D9%84%D9%88%D8%A8-%D9%85%D9%87%D9%86%D8%AF%D8%B3-%D8%A8%D8%B1%D9%85%D8%AC%D9%8A%D8%A7%D8%AA-%D9%88%D9%85%D8%AA%D8%AE%D8%B5%D8%B5-%D8%A3%D8%AA%D9%85%D8%AA%D8%A9-%D9%84%D8%AA%D9%86%D9%81%D9%8A%D8%B0-%D9%86%D8%B8%D8%A7%D9%85-%D8%A7%D9%84%D8%AD%D8%AC%D9%88%D8%B2%D8%A7%D8%AA-%D8%A8%D8%A7%D8%B3%D8%AA%D8%AE%D8%AF%D8%A7%D9%85-n8n",
     "title": "n8n booking system",
     "price": "50",
     "days": "7",
     "proposal": "السلام عليكم،\n\nأنا علاء فتحي، مهندس أتمتة ذكاء اصطناعي متخصص في n8n. لدي خبرة في بناء أنظمة حجوزات متكاملة باستخدام n8n وربطها مع التقويم وقواعد البيانات.\n\nمقترح العمل:\n- تحليل المتطلبات وتصميم نظام الحجوزات\n- بناء سير العمل في n8n (ربط التقويم، إرسال إشعارات، إدارة المواعيد)\n- ربط مع API المطلوبة\n- اختبار وتشغيل النظام\n- تسليم كود مع شرح وافي\n\nالمدة: 5-7 أيام\nالسعر: 50 دولار\n\nمتاح للتواصل لمناقشة التفاصيل.\n\nشكراً،\nعلاء فتحي"},
    {"url": "https://nafezly.com/project/49717-%D8%A8%D9%88%D8%AA-%D8%B0%D9%83%D8%A7%D8%A1-%D8%A7%D8%B5%D8%B7%D9%86%D8%A7%D8%B9%D9%8A-%D9%84%D9%84%D8%A5%D8%AC%D8%A7%D8%A8%D8%A9-%D8%B9%D9%84%D9%89-%D8%A7%D9%84%D8%A3%D8%B3%D8%A6%D9%84%D8%A9-%D9%85%D9%86-%D9%85%D9%84%D9%81-PDF",
     "title": "AI bot from PDF",
     "price": "40",
     "days": "5",
     "proposal": "السلام عليكم،\n\nأنا علاء فتحي، مهندس أتمتة ذكاء اصطناعي. أستطيع بناء بوت ذكاء اصطناعي يقرأ ملف PDF ويجيب على الأسئلة بناءً على محتواه باستخدام n8n و OpenAI.\n\nالمقترح:\n- رفع ملف PDF وتحويله إلى نص\n- بناء بوت ذكي يستخدم RAG للإجابة من المحتوى\n- ربط مع تليجرام أو واتساب\n- اختبار كامل\n\nالمدة: 3-5 أيام\nالسعر: 40 دولار\n\nللتواصل، أنا جاهز.\n\nشكراً،\nعلاء فتحي"},
    {"url": "https://nafezly.com/project/49679-%D9%85%D8%B7%D9%84%D9%88%D8%A8-%D9%85%D9%87%D9%86%D8%AF%D8%B3-%D8%A7%D8%AA%D9%85%D8%AA%D8%A9-%D9%84%D9%83%D8%AA%D8%A7%D8%A8%D8%A9-Bash-Script-%D9%84%D8%A3%D8%AA%D9%85%D8%AA%D8%A9-%D8%A7%D9%84%D9%86%D8%B3%D8%AE-%D8%A7%D9%84%D8%A7%D8%AD%D8%AA%D9%8A%D8%A7%D8%B7%D9%8A",
     "title": "Bash backup automation",
     "price": "30",
     "days": "3",
     "proposal": "السلام عليكم،\n\nأنا علاء فتحي. أستطيع كتابة Bash Script كامل لأتمتة النسخ الاحتياطي مع جدولة وإشعارات.\n\nالمقترح:\n- كتابة Bash Script متكامل\n- إضافة جدولة (Cron)\n- إشعارات البريد الإلكتروني\n- اختبار وتوثيق\n\nالمدة: 2-3 أيام\nالسعر: 30 دولار\n\nشكراً،\nعلاء فتحي"},
    {"url": "https://nafezly.com/project/48069-%D8%AA%D8%B7%D9%88%D9%8A%D8%B1-%D9%86%D8%B8%D8%A7%D9%85-Agentic-%D9%82%D8%A7%D8%A6%D9%85-%D9%88%D8%A5%D8%B6%D8%A7%D9%81%D8%A9-%D8%AF%D8%B9%D9%85-%D9%84%D8%AA%D9%88%D9%84%D9%8A%D8%AF-%D8%A7%D9%84%D8%B1%D8%B3%D9%88%D9%85-%D8%A7%D9%84%D8%A8%D9%8A%D8%A7%D9%86%D9%8A%D8%A9-Charts",
     "title": "Agentic system + charts",
     "price": "60",
     "days": "10",
     "proposal": "السلام عليكم،\n\nأنا علاء فتحي، مهندس أتمتة ذكاء اصطناعي. لدي خبرة في بناء أنظمة Agentic (AI Agents) وربطها مع توليد الرسوم البيانية.\n\nالمقترح:\n- تطوير النظام Agentic الموجود\n- إضافة دعم لتوليد الرسوم البيانية (Charts)\n- ربط مع n8n لسير العمل\n- اختبار وتشغيل\n\nالمدة: 7-10 أيام\nالسعر: 60 دولار\n\nللتواصل للمناقشة.\n\nشكراً،\nعلاء فتحي"},
]

pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data',
    executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    headless=False, args=['--no-sandbox'], viewport={'width':1280,'height':800})
page = ctx.new_page()
page.set_default_timeout(120000)

for i, proj in enumerate(PROJECTS):
    print(f"\n[{i+1}/{len(PROJECTS)}] {proj['title']}")
    print(f"  URL: {proj['url'][:70]}...")
    
    page.goto(proj['url'], timeout=180000)
    time.sleep(4)
    
    # Check if logged in
    if 'login' in page.url.lower():
        print("  Need login - waiting 60s...")
        for _ in range(60):
            time.sleep(1)
            if 'login' not in page.url.lower(): break
    
    # Save screenshot
    page.screenshot(path=TEMP / f'bid_{i}_{proj["title"][:10].replace(" ","_")}.png')
    
    # Check for bid/offer button - try various selectors
    bid_found = False
    bid_selectors = [
        "button:has-text('تقديم')",
        "button:has-text('عرض')", 
        "button:has-text('offer')",
        "button:has-text('send')",
        "button:has-text('أرسل')",
        "button:has-text('تقدم')",
        "a[href*='offer']",
        "a[href*='proposal']",
        "a[href*='send']",
        "[class*='offer'] button",
        "[class*='proposal'] button",
        ".btn-success",
        "a.btn",
    ]
    
    for sel in bid_selectors:
        btn = page.query_selector(sel)
        if btn and btn.is_visible():
            print(f"  Found bid button: {sel} -> text='{btn.inner_text()[:30]}'")
            btn.click()
            time.sleep(3)
            bid_found = True
            break
    
    if not bid_found:
        # Try finding by text content
        btn = page.evaluate("""() => {
            const btns = document.querySelectorAll('button, a');
            for(const b of btns) {
                const t = b.innerText.toLowerCase();
                if(t.includes('تقديم') || t.includes('عرض') || t.includes('offer'))
                    return {text: b.innerText.trim().substring(0,30), tag: b.tagName, html: b.outerHTML.substring(0,200)};
            }
            return null;
        }""")
        if btn:
            print(f"  Found btn via JS: {btn}")
            # Try clicking by text
            page.evaluate("""() => {
                const btns = document.querySelectorAll('button, a');
                for(const b of btns) {
                    const t = b.innerText.toLowerCase();
                    if(t.includes('تقديم') || t.includes('عرض') || t.includes('offer')) {
                        b.click(); return 'clicked';
                    }
                }
                return 'not found';
            }""")
            time.sleep(3)
            bid_found = True
        else:
            print("  NO BID BUTTON FOUND")
            # Show what buttons ARE on the page
            all_btns = page.eval_on_selector_all("button, a.btn", """els => els.map(e => ({
                text: e.innerText?.trim().substring(0,40),
                href: e.href || '',
                cls: e.className?.substring(0,30)
            })).filter(e => e.text)""")
            print(f"  Visible buttons ({len(all_btns)}):")
            for b in all_btns[:10]:
                print(f"    {b['text'][:30]:30s} cls={b['cls']}")
    
    if bid_found:
        print("  Bid form opened!")
        time.sleep(2)
        page.screenshot(path=TEMP / f'bid_form_{i}.png')
        
        # Fill proposal
        proposal_input = page.query_selector("textarea, [contenteditable='true']")
        if proposal_input:
            page.evaluate(f"""() => {{
                const ta = document.querySelector('textarea');
                if(ta) {{ ta.value = {json.dumps(proj['proposal'])}; 
                    ta.dispatchEvent(new Event('input',{{b:true}})); 
                    ta.dispatchEvent(new Event('change',{{b:true}})); }}
            }}""")
            print("  Proposal filled")
        
        # Set price
        price_input = page.query_selector("input[type='number'], input[name*='price'], input[name*='budget']")
        if price_input:
            js_set = f"() => {{ const el = document.querySelector('input[type=number], input[name*=price]'); if(el) {{ el.value = '{proj['price']}'; el.dispatchEvent(new Event('input',{{b:true}})); }} }}"
            page.evaluate(f"() => {{ const el = document.querySelector('input[type=number]'); if(el) {{ el.value = '{proj['price']}'; el.dispatchEvent(new Event('input',{{b:true}})); }} }}")
            print(f"  Price set: ${proj['price']}")
        
        # Set delivery days
        days_select = page.query_selector("select[name*='days'], select[name*='period']")
        if days_select:
            page.select_option(days_select, proj['days'])
            print(f"  Days set: {proj['days']}")
        
        # Submit
        submit_btn = page.query_selector("button[type='submit'], button:has-text('إرسال'), button:has-text('تقديم')")
        if submit_btn:
            submit_btn.click()
            time.sleep(3)
            print(f"  Submitted! URL: {page.url}")
            page.screenshot(path=TEMP / f'bid_submitted_{i}.png')
        else:
            print("  Submit button not found")
    
    time.sleep(2)

print(f"\n=== ALL {len(PROJECTS)} PROJECTS PROCESSED ===")
input("Press Enter...")
ctx.close()
pw.stop()
