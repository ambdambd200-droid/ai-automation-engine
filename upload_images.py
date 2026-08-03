"""Upload images to Nafezly service"""
import sys, time
from pathlib import Path
TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')

from playwright.sync_api import sync_playwright
pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data',
    executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    headless=False, args=['--no-sandbox'], viewport={'width':1366,'height':768})
page = ctx.new_page()
page.set_default_timeout(120000)

# Go to service page
page.goto('https://nafezly.com/service/75533-%D8%A8%D9%86%D8%A7%D8%A1-%D9%88%D9%83%D9%8A%D9%84-%D8%B0%D9%83%D8%A7%D8%A1-%D8%A7%D8%B5%D8%B7%D9%86%D8%A7%D8%B9%D9%8A-AI-Agent-%D8%A8%D8%A7%D8%B3%D8%AA%D8%AE%D8%AF%D8%A7%D9%85-n8n', timeout=120000)
time.sleep(3)
print(f'Service page: {page.url}')

# Look for edit button
for text in ['تعديل', 'تحرير', 'edit', 'إدارة', 'إعدادات']:
    try:
        btn = page.locator(f"a:has-text('{text}'), button:has-text('{text}')").first
        if btn.is_visible():
            href = btn.get_attribute('href')
            print(f'Edit link found: "{text}" -> {href}')
            btn.click()
            time.sleep(3)
            print(f'Edit page: {page.url}')
            break
    except:
        continue
else:
    # Try going to my services page
    print('No edit button, trying my services...')
    page.goto('https://nafezly.com/my/services', timeout=120000)
    time.sleep(3)
    print(f'My services: {page.url}')

html = page.content()
(TEMP / 'edit_service.html').write_text(html, encoding='utf-8')
print(f'Saved edit page ({len(html)} chars)')

input('Press ENTER to close...')
ctx.close()
pw.stop()
