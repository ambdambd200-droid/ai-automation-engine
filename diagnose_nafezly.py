"""Diagnose Nafezly page structure - saves FULL HTML"""
import sys, time, json
from pathlib import Path
BRAVE_EXE = Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")
BRAVE_PROFILE = Path(r"C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data")
TEMP = Path(__file__).parent / "Temp"

from playwright.sync_api import sync_playwright
pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=str(BRAVE_PROFILE), executable_path=str(BRAVE_EXE),
    headless=False, args=["--no-sandbox"], viewport={"width":1366,"height":768})
page = ctx.new_page()
page.set_default_timeout(120000)

# Go to nafezly
page.goto("https://nafezly.com", timeout=120000)
time.sleep(3)
print(f"URL: {page.url}")
print(f"Title: {page.title()}")

# Check if logged in
if "login" not in page.url.lower():
    print("✓ Already logged in!")
else:
    print("✗ Need to login - giving 60s...")
    for _ in range(60):
        time.sleep(1)
        if "login" not in page.url.lower():
            print("✓ Logged in!")
            break

# Try various profile URLs and save FULL HTML
urls_to_try = [
    "https://nafezly.com/account",
    "https://nafezly.com/settings",
    "https://nafezly.com/profile",
    "https://nafezly.com",
]

for url in urls_to_try:
    print(f"\n--- {url} ---")
    page.goto(url, timeout=120000)
    time.sleep(3)
    print(f"  URL: {page.url}")
    print(f"  Title: {page.title()}")
    
    # Save full HTML
    name = url.split('/')[-1] if url != "https://nafezly.com" else "home"
    html = page.content()
    (TEMP / f"full_{name}.html").write_text(html, encoding="utf-8")
    print(f"  Saved: full_{name}.html ({len(html)} chars)")
    
    # List all textareas and input fields
    fields = page.eval_on_selector_all("textarea, input:not([type=hidden]):not([type=submit])", 
        "els => els.map(e => ({tag: e.tagName, name: e.name, id: e.id, type: e.type, placeholder: e.placeholder, className: e.className.substring(0,50)}))")
    print(f"  Fields found: {len(fields)}")
    for f in fields[:20]:
        print(f"    [{f['tag']}] name='{f['name']}' id='{f['id']}' type='{f['type']}' placeholder='{f['placeholder']}'")
    
    # Check for buttons
    btns = page.eval_on_selector_all("button, a.btn, a[class*='btn']",
        "els => els.map(e => ({text: e.textContent.trim().substring(0,40), href: e.href || ''})).filter(e => e.text.length > 0)")
    print(f"  Buttons: {len(btns)}")
    for b in btns[:10]:
        print(f"    [{b['text']}] href='{b['href']}'")

print("\n✅ Diagnostic complete. Browser stays open.")
# Keep alive
while True:
    time.sleep(60)
