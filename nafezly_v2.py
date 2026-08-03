"""Nafezly reliable automation v2 - copy of nafezly_publish but with debug"""
import sys, time, json
from pathlib import Path

CONTENT = {"job_title": "مهندس أتمتة ذكاء اصطناعي", "bio": "أنا علاء فتحي"}
BID = {"project_url": "https://nafezly.com/projects?key=AI+Agents", "target_project": "AI Agents", "proposal": "test"}

BRAVE_EXE = Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")
BRAVE_PROFILE = Path(r"C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data")
TEMP = Path(r"C:\Users\A\Desktop\Money\Temp")
TEMP.mkdir(parents=True, exist_ok=True)

print("1: Imports done")
from playwright.sync_api import sync_playwright
print("2: Playwright imported")
pw = sync_playwright().start()
print("3: Playwright started")

ctx = pw.chromium.launch_persistent_context(
    user_data_dir=str(BRAVE_PROFILE), executable_path=str(BRAVE_EXE),
    headless=False, args=["--no-sandbox"], viewport={"width":1366,"height":768})
print("4: Brave launched")

page = ctx.new_page()
page.set_default_timeout(120000)
print("5: Page created")

page.goto("https://nafezly.com", timeout=120000)
print(f"6: On nafezly, URL={page.url}")

if "login" not in page.url.lower():
    print("7: Logged in!")
else:
    print("7: Need login - waiting 30s...")
    for _ in range(30):
        time.sleep(1)
        if "login" not in page.url.lower():
            break
    print(f"   After wait: {page.url}")

# Goto settings
print("8: Going to nafezly-settings...")
page.goto("https://nafezly.com/profile/nafezly-settings", timeout=120000)
time.sleep(2)
print(f"9: Settings URL={page.url}")

# Fill fields
r = page.evaluate("""(args) => {
    const el = document.querySelector(args.s);
    if (!el) return 'not found';
    el.value = args.v;
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
    return 'ok: ' + el.name;
}""", {"s": "input[name='job_title']", "v": CONTENT["job_title"]})
print(f"10: Job title: {r}")

r = page.evaluate("""(args) => {
    const el = document.querySelector(args.s);
    if (!el) return 'not found';
    el.value = args.v;
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
    return 'ok: ' + el.name;
}""", {"s": "textarea[name='bio']", "v": CONTENT["bio"]})
print(f"11: Bio: {r}")

# Save
btn = page.locator("button.btn-primary:has-text('حفظ')")
print(f"12: Save button visible={btn.is_visible()}")
if btn.is_visible():
    btn.click()
    time.sleep(2)
    print("13: Saved!")
else:
    # Try other selectors
    btn2 = page.locator("button:has-text('حفظ')").first
    print(f"   Alternative save: visible={btn2.is_visible()}")

print("14: Done - browser stays open")
while True:
    time.sleep(60)
