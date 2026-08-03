"""Minimal test: open Brave profile, navigate to Nafezly"""
from pathlib import Path
import sys
BRAVE_EXE = Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")
BRAVE_PROFILE = Path(r"C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data")
TEMP = Path(__file__).parent / "Temp"

from playwright.sync_api import sync_playwright
print("[1] Imported playwright")

pw = sync_playwright().start()
print("[2] Playwright started")

ctx = pw.chromium.launch_persistent_context(
    user_data_dir=str(BRAVE_PROFILE), executable_path=str(BRAVE_EXE),
    headless=False, args=["--no-sandbox"], viewport={"width":1366,"height":768})
print("[3] Brave launched")

page = ctx.new_page()
page.set_default_timeout(120000)

print("[4] Navigating to nafezly...")
page.goto("https://nafezly.com", timeout=120000)
print(f"[5] URL: {page.url}")
print(f"[5] Title: {page.title()}")

html = page.content()
(TEMP / "test_nafezly.html").write_text(html, encoding="utf-8")
print(f"[6] Saved HTML ({len(html)} chars)")

# Check if logged in
if "login" not in page.url.lower():
    print("[7] LOGGED IN!")
else:
    print("[7] NOT logged in - waiting 30s...")
    import time
    for _ in range(30):
        time.sleep(1)
        if "login" not in page.url.lower():
            print("[8] Logged in after wait!")
            break

# Navigate to nafezly-settings
page.goto("https://nafezly.com/profile/nafezly-settings", timeout=120000)
time.sleep(3)
print(f"[9] Settings URL: {page.url}")

# Save HTML
html2 = page.content()
(TEMP / "test_settings.html").write_text(html2, encoding="utf-8")
print(f"[10] Saved settings HTML ({len(html2)} chars)")

input("PRESS ENTER to close browser...")
ctx.close()
pw.stop()
print("Done")
