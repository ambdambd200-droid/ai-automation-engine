"""Upload images to existing Nafezly services"""
import os, time, json
from pathlib import Path
from playwright.sync_api import sync_playwright

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')
BRAVE_EXE = r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'
BRAVE_PROFILE = r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data'

SERVICES = [
    {"file": "pro_ai_agent.jpg", "url": "https://nafezly.com/service/75533-AI-Agent-Development"},
    {"file": "pro_workflow.jpg", "url": "https://nafezly.com/service/75535-Workflow-Automation-with-n8n"},
    {"file": "pro_chatbot.jpg", "url": "https://nafezly.com/service/75536-AI-Chatbot-Development"},
]

print("Starting...")
pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=BRAVE_PROFILE,
    executable_path=BRAVE_EXE,
    headless=False,
    args=['--no-sandbox', '--disable-blink-features=AutomationControlled'],
    viewport={'width': 1280, 'height': 800})
page = ctx.new_page()
page.set_default_timeout(120000)

for svc in SERVICES:
    img_path = TEMP / svc["file"]
    if not img_path.exists():
        print(f"SKIP: {svc['file']} not found")
        continue
    
    print(f"\n=== Opening service: {svc['url']} ===")
    page.goto(svc['url'], timeout=180000)
    time.sleep(4)
    
    # Screenshot to see the page
    page.screenshot(path=TEMP / f"before_{svc['file']}")
    
    # Try clicking edit button or add image
    # Look for image upload area or edit button
    buttons_text = page.eval_on_selector_all("button, a, [role=button]", """els => els.map(e => ({
        text: e.innerText?.trim().substring(0,50),
        visible: e.offsetParent !== null,
        tag: e.tagName,
        href: e.href || ''
    })).filter(e => e.text)""")
    
    print("Found buttons:")
    for b in buttons_text:
        if any(w in (b['text'] or '').lower() for w in ['edit', 'تعديل', 'update', 'تحرير', 'image', 'صور', 'upload', 'رفع', 'setting', 'dashboard']):
            print(f"  MATCH: [{b['tag']}] {b['text']} | href={b['href'][:80]}")

print("\nDone exploring.")
input("Press Enter to close browser...")
ctx.close()
pw.stop()
