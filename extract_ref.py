"""Extract images from a Nafezly service page and recreate similar style"""
import sys, os, json, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import requests

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')
PYTHON = r'C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe'

# Load reference page to see images
from playwright.sync_api import sync_playwright

pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data',
    executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    headless=False, args=['--no-sandbox'], viewport={'width':1280,'height':800})
page = ctx.new_page()
page.set_default_timeout(120000)

print("Loading reference service page...")
page.goto('https://nafezly.com/service/74938', timeout=120000)
time.sleep(3)

# Extract image sources
images = page.eval_on_selector_all('img', 'els => els.map(el => ({src: el.src, alt: el.alt, cls: el.className, w: el.naturalWidth, h: el.naturalHeight}))')
print(f"\nFound {len(images)} images:")
for img in images:
    if img['src'] and not img['src'].startswith('data:'):
        print(f"  [{img['w']}x{img['h']}] {img['src'][:100]}")

# Take full-page screenshot of the reference service area
page.screenshot(path=str(TEMP / 'ref_full.jpg'), full_page=True)
print(f"\nFull page screenshot saved ({os.path.getsize(TEMP/'ref_full.jpg')} bytes)")

# Also check the service content HTML structure
content_area = page.eval_on_selector('.service-content || .description || .content', """
(el) => {
    if (!el) return null;
    const imgs = el.querySelectorAll('img');
    return Array.from(imgs).map(i => ({
        src: i.src,
        alt: i.alt,
        w: i.naturalWidth,
        h: i.naturalHeight,
        parent: i.parentElement ? i.parentElement.tagName : null
    }));
}
""")
print(f"\nContent images: {json.dumps(content_area, indent=2)}")

ctx.close()
pw.stop()
print("\nDone. Check ref_full.jpg to see the reference service layout.")
