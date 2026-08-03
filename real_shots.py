"""Visit reference Nafezly service and take real screenshots of n8n/AI interfaces"""
import sys, time, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')
PYTHON = r'C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe'

from playwright.sync_api import sync_playwright

def make_card(img_path, text, sub, price_tag, accent):
    """Add overlay text to a screenshot"""
    img = Image.open(img_path).convert("RGB").resize((800, 500), Image.LANCZOS)
    w, h = 800, 500
    draw = ImageDraw.Draw(img)
    
    # Semi-transparent bottom overlay
    overlay = Image.new('RGBA', (w, h), (0,0,0,0))
    o_draw = ImageDraw.Draw(overlay)
    for y in range(h-160, h):
        alpha = int(200 * (y - (h-160)) / 160)
        o_draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    img.paste(overlay, (0, 0), overlay)
    
    try: f_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 28)
    except: f_title = ImageFont.load_default()
    try: f_sub = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 14)
    except: f_sub = ImageFont.load_default()
    try: f_price = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 18)
    except: f_price = ImageFont.load_default()
    
    draw.text((30, h-130), text, fill='white', font=f_title)
    draw.text((30, h-85), sub, fill='#CBD5E1', font=f_sub)
    
    # Price tag box
    draw.rounded_rectangle([(w-150, h-65), (w-30, h-35)], radius=6, fill=accent)
    draw.text((w-125, h-57), price_tag, fill='white', font=f_price)
    
    # Bottom accent line
    draw.rectangle([(0, h-3), (w, h)], fill=accent)
    
    img.save(img_path, quality=95)

def overlay_status(path, status_text, accent):
    img = Image.open(path).convert("RGB").resize((800, 500), Image.LANCZOS)
    w, h = 800, 500
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, h-40), (w, h)], fill=accent)
    draw.rectangle([(0, 0), (w, 4)], fill=accent)
    try: f = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 16)
    except: f = ImageFont.load_default()
    draw.text((20, h-30), status_text, fill='white', font=f)
    img.save(path, quality=95)

print("Launching browser...")
pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data',
    executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    headless=False, args=['--no-sandbox'], viewport={'width':1280,'height':800})
page = ctx.new_page()
page.set_default_timeout(120000)

results = []

# 1. n8n templates page
print("[1/4] n8n templates...")
try:
    page.goto('https://n8n.io/workflows', timeout=120000)
    time.sleep(4)
    fp = TEMP / 'sb1_n8n.png'
    page.screenshot(path=str(fp))
    status = "n8n Workflow Automation | 400+ integrations | Drag & drop"
    accent = "#E8542D"
    overlay_status(fp, status, accent)
    results.append(('shot_n8n_workflows.jpg', fp))
    print("  OK")
except Exception as e:
    print(f"  FAIL: {e}")

# 2. OpenAI platform
print("[2/4] OpenAI platform...")
try:
    page.goto('https://platform.openai.com', timeout=120000)
    time.sleep(3)
    fp = TEMP / 'sb2_openai.png'
    page.screenshot(path=str(fp))
    status = "AI Agent Development | Powered by OpenAI + n8n"
    accent = "#10A37F"
    overlay_status(fp, status, accent)
    results.append(('shot_ai_agent.jpg', fp))
    print("  OK")
except Exception as e:
    print(f"  FAIL: {e}")

# 3. GitHub n8n
print("[3/4] GitHub n8n...")
try:
    page.goto('https://github.com/n8n-io/n8n', timeout=120000)
    time.sleep(3)
    fp = TEMP / 'sb3_github.png'
    page.screenshot(path=str(fp))
    status = "Workflow Automation | n8n | Automate anything"
    accent = "#0366D6"
    overlay_status(fp, status, accent)
    results.append(('shot_workflow.jpg', fp))
    print("  OK")
except Exception as e:
    print(f"  FAIL: {e}")

# 4. Try to see reference service page images
print("[4/4] Reference service page...")
try:
    page.goto('https://nafezly.com/service/74938', timeout=120000)
    time.sleep(4)
    fp = TEMP / 'sb4_ref.png'
    page.screenshot(path=str(fp))
    results.append(('shot_ref_service.jpg', fp))
    print("  OK")
except Exception as e:
    print(f"  FAIL: {e}")

ctx.close()
pw.stop()

print(f"\n=== {len(results)} screenshots taken ===")
for name, path in results:
    size = os.path.getsize(path)
    print(f"  {name}: {size} bytes")

print("\n\nIMAGES CREATED:")
for name, path in results:
    print(f"  {path} -> {name}")
