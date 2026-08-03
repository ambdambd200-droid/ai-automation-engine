"""Check if Nafezly has text-based offer submission or only voice"""
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

page.goto('https://nafezly.com/projects?key=n8n', timeout=180000)
time.sleep(4)

link = page.query_selector("a[href*='/project/']:not([href*='create'])")
if link:
    link.click()
    time.sleep(5)

# Check for offer submission section
offer_section = page.evaluate("""() => {
    const body = document.body.innerText;
    const lines = body.split('\\n').filter(l => l.trim());
    const relevant = lines.filter(l => 
        l.includes('تقديم') || l.includes('عرض') || l.includes('offer') || 
        l.includes('سعر') || l.includes('ميزانية') || l.includes('تسجيل')
    );
    return relevant.slice(0, 30);
}""")
print("Relevant page text:")
for l in offer_section:
    print(f"  {l.strip()[:120]}")

# Get the deal/offer section HTML
offer_html = page.evaluate("""() => {
    const sections = document.querySelectorAll('[class*="offer"], [class*="deal"], [class*="proposal"], [class*="عرض"]');
    return Array.from(sections).map(s => ({
        cls: s.className?.substring(0, 50),
        text: s.innerText?.trim().substring(0, 150),
        html: s.innerHTML?.substring(0, 300)
    })).filter(s => s.text);
}""")
print(f"\nOffer sections ({len(offer_html)}):")
for s in offer_html:
    print(f"\n  Class: {s['cls']}")
    print(f"  Text: {s['text'][:200]}")

# Look for the "تقديم عرض" button specifically
all_btns = page.eval_on_selector_all("button, a.btn, a[class*='btn']", """els => els.map(e => ({
    text: e.innerText?.trim().substring(0, 30),
    cls: e.className?.substring(0, 30),
    href: e.href || '',
    onclick: (e.getAttribute('onclick') || '').substring(0, 80)
})).filter(e => e.text)""")
print(f"\nAll buttons ({len(all_btns)}):")
for b in all_btns:
    print(f"  {b['text']:30s} cls={b['cls'] or '-':25s} onclick={b.get('onclick','-')[:40]}")

input("Press Enter to close...")
ctx.close()
pw.stop()
