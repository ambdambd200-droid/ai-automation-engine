"""Check Nafezly notifications to see what was accepted"""
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')

pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data',
    executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    headless=False, args=['--no-sandbox'], viewport={'width':1280,'height':800})
page = ctx.new_page()
page.set_default_timeout(120000)

page.goto('https://nafezly.com/notifications/list', timeout=180000)
time.sleep(5)
print(f'URL: {page.url}')

# Get all notification items
notifs = page.eval_on_selector_all("""[class*='notification'], [class*='notif'], li[class*='item'], tr, [class*='alert']""",
    """els => els.map((el, i) => ({
        idx: i,
        text: el.innerText?.trim().substring(0, 300),
        html: el.innerHTML?.substring(0, 200),
        visible: el.offsetParent !== null
    })).filter(e => e.text && e.visible)""")

print(f'\nFound {len(notifs)} notification elements:')
for n in notifs:
    print(f'\n--- [{n["idx"]}] ---')
    print(f'Text: {n["text"]}')

# Try to also get just all text content
body_text = page.eval_on_selector("body", "el => el.innerText")
print(f'\n\n=== FULL PAGE TEXT ===')
print(body_text[:2000])

page.screenshot(path=TEMP / 'nafezly_notifs.png')
print(f'\nScreenshot saved')

input('\nPress Enter to close...')
ctx.close()
pw.stop()
