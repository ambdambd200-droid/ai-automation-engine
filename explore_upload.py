"""Find Nafezly service edit/upload interface and upload images"""
import os, time, json
from pathlib import Path
from playwright.sync_api import sync_playwright

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')
BRAVE_EXE = r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'
BRAVE_PROFILE = r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data'

SERVICES = [
    {
        "name": "AI Agent",
        "url": "https://nafezly.com/service/75533-AI-Agent-Development",
        "images": ["pro_ai_agent.jpg", "pro_ai_agent_2.jpg", "pro_ai_agent_3.jpg"]
    },
    {
        "name": "Workflow",
        "url": "https://nafezly.com/service/75535-Workflow-Automation-with-n8n",
        "images": ["pro_workflow.jpg", "pro_workflow_2.jpg", "pro_workflow_3.jpg"]
    },
    {
        "name": "Chatbot",
        "url": "https://nafezly.com/service/75536-AI-Chatbot-Development",
        "images": ["pro_chatbot.jpg", "pro_chatbot_2.jpg", "pro_chatbot_3.jpg"]
    }
]

print("Launching browser...")
pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=BRAVE_PROFILE,
    executable_path=BRAVE_EXE,
    headless=False,
    args=['--no-sandbox'],
    viewport={'width': 1280, 'height': 800})
page = ctx.new_page()
page.set_default_timeout(120000)

# Step 1: Try dashboard/my services page
print("\n[1] Trying dashboard...")
page.goto('https://nafezly.com/dashboard', timeout=180000)
time.sleep(5)
page.screenshot(path=TEMP / 'dash1.png')

# Click any "My Services" or "خدماتي" link
links = page.eval_on_selector_all("a", """els => els.map(e => ({
    text: e.innerText?.trim().substring(0, 40),
    href: e.href,
    visible: e.offsetParent !== null
})).filter(e => e.text)""")

print("Links found on dashboard:")
for l in links:
    if any(w in l['text'].lower() for w in ['خدمات', 'service', 'edit', 'تعديل', 'manage', 'إدارة']):
        print(f"  {l['text']:30s} -> {l['href']}")

# Step 2: Try service edit page
print("\n[2] Trying service edit page...")
page.goto('https://nafezly.com/service/edit/75533', timeout=180000)
time.sleep(3)
page.screenshot(path=TEMP / 'dash2.png')

# Check page content
title = page.title()
print(f"  Page title: {title}")

# Find upload fields
inputs = page.eval_on_selector_all("input, textarea, select, button", """els => els.map(e => ({
    type: e.type || e.tagName,
    name: e.name || '',
    id: e.id || '',
    placeholder: e.placeholder || '',
    text: e.innerText?.trim().substring(0, 30) || '',
    accept: e.accept || '',
    visible: e.offsetParent !== null
})).filter(e => e.visible)""")

file_inputs = [i for i in inputs if i['type'] == 'file' or i['accept']]
if file_inputs:
    print(f"  File uploads found: {len(file_inputs)}")
    for fi in file_inputs:
        print(f"    {fi}")
else:
    print("  No file upload inputs found")

# Try /my-services or /seller/services
print("\n[3] Trying seller services...")
page.goto('https://nafezly.com/seller/services', timeout=180000)
time.sleep(3)
page.screenshot(path=TEMP / 'dash3.png')
title2 = page.title()
print(f"  Title: {title2}")

# Try /user/services  
print("\n[4] Trying user services...")
page.goto('https://nafezly.com/user/services', timeout=180000)
time.sleep(3)
page.screenshot(path=TEMP / 'dash4.png')
title3 = page.title()
print(f"  Title: {title3}")

print("\nDone exploring. Check screenshots in Temp/")
input("Press Enter to close...")
ctx.close()
pw.stop()
