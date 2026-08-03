"""Check Nafezly project page for bid button details"""
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

# Click first project
link = page.query_selector("a[href*='/project/']:not([href*='create'])")
if link:
    link.click()
    time.sleep(5)

# Get ALL clickable elements
all_clickable = page.evaluate("""() => {
    const items = document.querySelectorAll('button, a, [role=button], input[type=submit], .btn');
    return Array.from(items).filter(el => el.offsetParent !== null).map(el => ({
        tag: el.tagName,
        text: el.innerText?.trim().substring(0, 40),
        href: el.href || '',
        cls: el.className?.substring(0, 40),
        onclick: el.getAttribute('onclick')?.substring(0, 60) || '',
        id: el.id || ''
    }));
}""")
print(f"\nClickable elements ({len(all_clickable)}):")
for el in all_clickable:
    print(f"  [{el['tag']}] {el['text']:30s} cls={el['cls'] or '-':20s} {el['href'][:40]}")

# Check for bid/proposal offer
bid_area = page.evaluate("""() => {
    const btns = document.querySelectorAll('button, a');
    for(const b of btns) {
        const t = b.innerText.toLowerCase().trim();
        if(t.includes('تقديم') || t.includes('عرض') || t.includes('offer') || t.includes('bid'))
            return {text: b.innerText.substring(0,50), tag: b.tagName, html: b.outerHTML.substring(0,200)};
    }
    return null;
}""")
print(f"\nBid button search: {bid_area}")

# Get full page text to see all content
page_text = page.eval_on_selector("body", "el => el.innerText")
print(f"\n--- Full page text (sampled): ---")
# Find the 'تقديم' section
for line in page_text.split('\n'):
    if any(w in line.lower() for w in ['تقديم', 'عرض', 'offer', 'bid', 'سعر', 'price']):
        print(f"  {line.strip()[:100]}")

# Check URL params for bid page
print(f"\nURL: {page.url}")

# Try adding /offer or /proposal to URL
page.goto(page.url + '/offer', timeout=180000)
time.sleep(3)
print(f"Offer URL: {page.url}")

page.goto('https://nafezly.com/project/49664/offer', timeout=180000)
time.sleep(3)
print(f"Direct offer URL: {page.url}")

input("Press Enter...")
ctx.close()
pw.stop()
