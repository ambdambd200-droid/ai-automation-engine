"""Find Nafezly profile edit form - save FULL HTML"""
import sys, time
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

page.goto("https://nafezly.com/profile/personal-data", timeout=120000)
time.sleep(5)
print(f"URL: {page.url}")
print(f"Title: {page.title()}")
html = page.content()
(TEMP / "full_personal_data.html").write_text(html, encoding="utf-8")
print(f"Saved personal-data ({len(html)} chars)")

# Find ALL editable fields
fields = page.eval_on_selector_all("textarea, input:not([type=hidden]):not([type=submit]):not([type=radio]):not([type=checkbox])",
    "els => els.map(e => ({tag: e.tagName, name: e.name, id: e.id, type: e.type, placeholder: e.placeholder, value: e.value, className: e.className.substring(0,60)}))")
print(f"Fields: {len(fields)}")
for f in fields:
    print(f"  [{f['tag']}] name='{f['name']}' id='{f['id']}' placeholder='{f['placeholder']}' value='{f['value'][:50]}'")

# Find buttons
btns = page.eval_on_selector_all("button, a[class*='btn'], input[type=submit]",
    "els => els.map(e => ({text: e.textContent.trim().substring(0,50), type: e.type || 'a'})).filter(e => e.text.length > 0)")
print(f"Buttons: {len(btns)}")
for b in btns:
    print(f"  '{b['text']}' ({b['type']})")

# Also check nafezly-settings
print("\n--- nafezly-settings ---")
page.goto("https://nafezly.com/profile/nafezly-settings", timeout=120000)
time.sleep(5)
print(f"URL: {page.url}")
html2 = page.content()
(TEMP / "full_nafezly_settings.html").write_text(html2, encoding="utf-8")
print(f"Saved ({len(html2)} chars)")

fields2 = page.eval_on_selector_all("textarea, input:not([type=hidden]):not([type=submit]):not([type=radio]):not([type=checkbox])",
    "els => els.map(e => ({tag: e.tagName, name: e.name, id: e.id, type: e.type, placeholder: e.placeholder, value: e.value, className: e.className.substring(0,60)}))")
print(f"Fields: {len(fields2)}")
for f in fields2:
    txt = f.get('value','')
    print(f"  [{f['tag']}] name='{f['name']}' id='{f['id']}' placeholder='{f['placeholder']}' value='{txt[:50] if txt else ''}'")

btns2 = page.eval_on_selector_all("button, a[class*='btn'], input[type=submit]",
    "els => els.map(e => ({text: e.textContent.trim().substring(0,50), type: e.type || 'a'})).filter(e => e.text.length > 0)")
for b in btns2:
    print(f"  '{b['text']}' ({b['type']})")

print("\n✅ Done. Browser stays open - close manually.")
while True:
    time.sleep(60)
