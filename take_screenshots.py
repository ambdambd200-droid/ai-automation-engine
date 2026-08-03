"""Take real screenshots of n8n and AI tools for authentic service images"""
import sys, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')
from playwright.sync_api import sync_playwright

def get_font(size, bold=False):
    for p in [r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf"]:
        if Path(p).exists(): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def add_pro_overlay(img_path, title_lines, subtitle, accent_hex="#00B894"):
    """Add professional text overlay to a screenshot"""
    img = Image.open(img_path).convert("RGB")
    w, h = 800, 500
    img = img.resize((w, h), Image.LANCZOS)
    draw = ImageDraw.Draw(img)
    
    # Dark gradient at bottom
    overlay = Image.new('RGBA', (w, h), (0,0,0,0))
    o_draw = ImageDraw.Draw(overlay)
    for y in range(h-180, h):
        alpha = int(160 * (y - (h-180)) / 180)
        o_draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    img.paste(overlay, (0, 0), overlay)
    
    # Subtle accent line
    line_y = h - 90
    draw.rectangle([(0, line_y), (60, line_y+3)], fill=accent_hex)
    
    # Title - clean, left-aligned
    f_title = get_font(32, bold=True)
    f_sub = get_font(15, bold=False)
    
    for i, line in enumerate(title_lines):
        draw.text((30, line_y - 60 + i*42), line, fill=(255,255,255), font=f_title)
    
    # Subtitle
    draw.text((30, line_y - 60 + len(title_lines)*42 + 5), subtitle, fill=(180, 200, 220), font=f_sub)
    
    img.save(img_path, quality=92)
    print(f"Overlay added: {img_path.name} ({os.path.getsize(img_path)} bytes)")

print("Opening browser to take screenshots...")
pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data',
    executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    headless=False, args=['--no-sandbox'], viewport={'width':1366,'height':768})
page = ctx.new_page()
page.set_default_timeout(120000)

# Screenshot 1: n8n website workflow example
print("1. Taking n8n workflow screenshot...")
page.goto('https://n8n.io/workflows', timeout=120000)
time.sleep(5)
page.screenshot(path=str(TEMP / '_raw_n8n.png'), full_page=False)
add_pro_overlay(TEMP / '_raw_n8n.png', 
    ["Workflow Automation"], "n8n | API Integration | Automate Everything",
    "#00B894")
# Save renamed
img = Image.open(TEMP / '_raw_n8n.png').convert("RGB")
img.save(str(TEMP / "service_workflow.jpg"), quality=92)
print("  -> service_workflow.jpg")

# Screenshot 2: Make.com (formerly Integromat) - another automation tool
print("2. Taking Make.com screenshot...")
page.goto('https://www.make.com/en', timeout=120000)
time.sleep(5)
page.screenshot(path=str(TEMP / '_raw_make.png'), full_page=False)
add_pro_overlay(TEMP / '_raw_make.png',
    ["Workflow Automation"], "Make.com | n8n | Connect Apps",
    "#6C5CE7")
img = Image.open(TEMP / '_raw_make.png').convert("RGB")
img.save(str(TEMP / "service_make.jpg"), quality=92)
print("  -> service_make.jpg")

# Screenshot 3: General AI/tech page
print("3. Taking tech screenshot...")
page.goto('https://openai.com', timeout=120000)
time.sleep(5)
page.screenshot(path=str(TEMP / '_raw_ai.png'), full_page=False)
add_pro_overlay(TEMP / '_raw_ai.png',
    ["AI Agent", "Development"], "Custom AI Agents with n8n & OpenAI",
    "#0984E3")
img = Image.open(TEMP / '_raw_ai.png').convert("RGB")
img.save(str(TEMP / "service_ai_agent.jpg"), quality=92)
print("  -> service_ai_agent.jpg")

print("\nAll 3 screenshots done! Use them for your services.")
ctx.close()
pw.stop()
