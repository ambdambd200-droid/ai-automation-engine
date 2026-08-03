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
print('Go to nafezly...')
page.goto('https://nafezly.com', timeout=120000)
time.sleep(2)
print(f'URL: {page.url}')
if 'login' not in page.url.lower():
    print('Logged in!')
    # Go to service creation
    page.goto('https://nafezly.com/service/create', timeout=120000)
    time.sleep(3)
    print(f'Service page: {page.url}')
    html = page.content()
    (TEMP / 'service_create.html').write_text(html, encoding='utf-8')
    print(f'HTML saved ({len(html)} chars)')
    input('PRESS ENTER to quit')
else:
    print('Need login')
ctx.close()
pw.stop()
