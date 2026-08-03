"""Open Mostaql + Nafezly in a clean browser (no persistent profile)"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from pathlib import Path
from playwright.sync_api import sync_playwright

BRAVE_EXE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
TEMP_DIR = r"C:\Users\A\Desktop\Money\Temp\_browser_check"

pw = sync_playwright().start()
browser = pw.chromium.launch(
    executable_path=BRAVE_EXE,
    headless=False,
    args=["--no-sandbox"],
    viewport={"width": 1366, "height": 768},
)

print("\n=== Opening Mostaql (مستقل) ===")
page = browser.new_page()
page.goto("https://mostaql.com", timeout=120000)
time.sleep(4)
print("URL:", page.url)
print("Title:", page.title())
if "login" in page.url.lower():
    print("STATUS: NOT LOGGED IN - please log in if you want")
else:
    print("STATUS: Already logged in!")

print("\n=== Opening Nafezly (نفذلي) ===")
page2 = browser.new_page()
page2.goto("https://nafezly.com", timeout=120000)
time.sleep(4)
print("URL:", page2.url)
print("Title:", page2.title())
if "login" in page2.url.lower():
    print("STATUS: NOT LOGGED IN - please log in if you want")
else:
    print("STATUS: Already logged in!")

print("\n--- Browser stays open for you ---")
print("Check both tabs. Close the window when done.")

try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    pass

browser.close()
pw.stop()
