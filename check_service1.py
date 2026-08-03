"""Check if Service 1 exists on Nafezly"""
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

# Check service 1
page.goto('https://nafezly.com/service/75533-AI-Agent-Development', timeout=180000)
time.sleep(3)
print(f"Service 1 URL: {page.url}")
print(f"Title: {page.title()}")
status = page.eval_on_selector("body", "el => el.innerText.substring(0, 200)")
print(f"Body: {status[:200]}")

# Also try the exact name
page.goto('https://nafezly.com/service/75533', timeout=180000)
time.sleep(3)
print(f"\nService 1 (by ID): {page.url}")
status2 = page.eval_on_selector("body", "el => el.innerText.substring(0, 200)")
print(f"Body: {status2[:200]}")

input("Press Enter...")
ctx.close()
pw.stop()
