"""Take real screenshots of software interfaces for authentic service images"""
import sys, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')
from playwright.sync_api import sync_playwright

def overlay_text(img_path, text, sub, accent_hex="#00B894"):
    img = Image.open(img_path).convert("RGB").resize((800, 500), Image.LANCZOS)
    w, h = 800, 500
    draw = ImageDraw.Draw(img)
    
    # Bottom gradient
    overlay = Image.new('RGBA', (w, h), (0,0,0,0))
    o_draw = ImageDraw.Draw(overlay)
    for y in range(h-130, h):
        alpha = int(180 * (y - (h-130)) / 130)
        o_draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    img.paste(overlay, (0, 0), overlay)
    
    # Accent bar at bottom
    draw.rectangle([(0, h-3), (w, h)], fill=accent_hex)
    
    # Fonts
    try: f_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 30)
    except: f_title = ImageFont.load_default()
    try: f_sub = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 14)
    except: f_sub = ImageFont.load_default()
    
    # Left-aligned text
    draw.text((30, h-105), text, fill=(255,255,255), font=f_title)
    draw.text((30, h-65), sub, fill=(180,200,220), font=f_sub)
    
    img.save(img_path, quality=92)
    return os.path.getsize(img_path)

print("Launching browser...")
pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data',
    executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    headless=False, args=['--no-sandbox'], viewport={'width':1280,'height':800})
page = ctx.new_page()
page.set_default_timeout(180000)

screenshots = []

# 1: n8n.io - workflow automation platform
print("\n[1/3] Loading n8n.io...")
try:
    page.goto('https://n8n.io', timeout=180000)
    time.sleep(5)
    page.screenshot(path=str(TEMP / '_shot1.png'))
    size = overlay_text(TEMP / '_shot1.png', "Workflow Automation", "n8n | Automate anything | 400+ integrations", "#E8542D")
    os.replace(TEMP / '_shot1.png', TEMP / 'shot_workflow.jpg')
    print(f"  OK: shot_workflow.jpg ({size} bytes)")
    screenshots.append(('Workflow Automation', 'shot_workflow.jpg'))
except Exception as e:
    print(f"  FAILED: {e}")

# 2: Open AI or similar AI chat interface
print("\n[2/3] Loading AI chat interface...")
try:
    page.goto('https://platform.openai.com', timeout=180000)
    time.sleep(5)
    page.screenshot(path=str(TEMP / '_shot2.png'))
    size = overlay_text(TEMP / '_shot2.png', "AI Chatbot Development", "OpenAI | n8n | Smart Conversations", "#10A37F")
    os.replace(TEMP / '_shot2.png', TEMP / 'shot_chatbot.jpg')
    print(f"  OK: shot_chatbot.jpg ({size} bytes)")
    screenshots.append(('AI Chatbot', 'shot_chatbot.jpg'))
except Exception as e:
    print(f"  FAILED: {e}")

# 3: GitHub n8n repository (code/development)
print("\n[3/3] Loading GitHub n8n...")
try:
    page.goto('https://github.com/n8n-io/n8n', timeout=180000)
    time.sleep(5)
    page.screenshot(path=str(TEMP / '_shot3.png'))
    size = overlay_text(TEMP / '_shot3.png', "AI Agent Development", "Custom Agents | n8n | API Integration", "#0366D6")
    os.replace(TEMP / '_shot3.png', TEMP / 'shot_ai_agent.jpg')
    print(f"  OK: shot_ai_agent.jpg ({size} bytes)")
    screenshots.append(('AI Agent', 'shot_ai_agent.jpg'))
except Exception as e:
    print(f"  FAILED: {e}")

print(f"\n=== DONE: {len(screenshots)}/3 screenshots ===")
for name, file in screenshots:
    print(f"  {name} -> {file}")

ctx.close()
pw.stop()
