"""Generate service images for Nafezly"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')
SIZE = (800, 500)

# Try to find Arabic-supporting font
FONT_PATHS = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\ARIALBD.TTF",
    r"C:\Windows\Fonts\tahoma.ttf",
    r"C:\Windows\Fonts\TREBUCBD.TTF",
    r"C:\Windows\Fonts\segoeuib.ttf",
]
FONT_PATH = None
for fp in FONT_PATHS:
    if Path(fp).exists():
        FONT_PATH = fp
        break

def create_service_image(filename, title, subtitle="", accent_color=(0, 120, 212)):
    img = Image.new('RGB', SIZE, (15, 23, 42))
    draw = ImageDraw.Draw(img)
    
    # Gradient overlay
    for y in range(SIZE[1]):
        alpha = y / SIZE[1]
        r = int(15 * (1-alpha) + 30 * alpha)
        g = int(23 * (1-alpha) + 45 * alpha) 
        b = int(42 * (1-alpha) + 70 * alpha)
        draw.line([(0, y), (SIZE[0], y)], fill=(r, g, b))
    
    # Accent bar at bottom
    bar_h = 6
    draw.rectangle([(0, SIZE[1]-bar_h), (SIZE[0], SIZE[1])], fill=accent_color)
    
    # Decorative circles
    draw.ellipse([(SIZE[0]-150, -50), (SIZE[0]-50, 50)], outline=(*accent_color, 30), width=2)
    draw.ellipse([(-30, SIZE[1]-120), (50, SIZE[1]-40)], outline=(*accent_color, 30), width=2)
    
    # Nodes (connecting dots) - AI network feel
    nodes = [(100,80), (200,60), (300,100), (400,70), (500,90), (600,60), (700,100)]
    for i, (x, y) in enumerate(nodes):
        draw.ellipse([(x-4, y-4), (x+4, y+4)], fill=(*accent_color, 200))
        if i > 0:
            px, py = nodes[i-1]
            draw.line([(px, py), (x, y)], fill=(*accent_color, 60), width=1)
    
    # Text
    title_font_size = 32
    sub_font_size = 18
    
    try:
        font_title = ImageFont.truetype(FONT_PATH, title_font_size) if FONT_PATH else ImageFont.load_default()
        font_sub = ImageFont.truetype(FONT_PATH, sub_font_size) if FONT_PATH else ImageFont.load_default()
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
    
    # Title text (centered)
    text_color = (255, 255, 255)
    
    # For Arabic text, use arial if available
    try:
        font_ar = ImageFont.truetype(r"C:\Windows\Fonts\ARIAL.TTF", 36) if Path(r"C:\Windows\Fonts\ARIAL.TTF").exists() else font_title
        font_sub_ar = ImageFont.truetype(r"C:\Windows\Fonts\ARIAL.TTF", 20) if Path(r"C:\Windows\Fonts\ARIAL.TTF").exists() else font_sub
    except:
        font_ar = font_title
        font_sub_ar = font_sub
    
    # Multi-line title
    lines = title.split('\n')
    y_start = 160
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_ar)
        tw = bbox[2] - bbox[0]
        x = (SIZE[0] - tw) // 2
        draw.text((x, y_start + i*50), line, fill=text_color, font=font_ar)
    
    # Subtitle
    if subtitle:
        bbox = draw.textbbox((0, 0), subtitle, font=font_sub_ar)
        tw = bbox[2] - bbox[0]
        x = (SIZE[0] - tw) // 2
        draw.text((x, y_start + len(lines)*50 + 20), subtitle, fill=(180, 200, 220), font=font_sub_ar)
    
    # Bottom text
    bbox = draw.textbbox((0, 0), "Alaa Fathi", font=font_sub)
    tw = bbox[2] - bbox[0]
    draw.text((SIZE[0]-tw-20, SIZE[1]-45), "Alaa Fathi", fill=(120, 140, 170), font=font_sub)
    
    # Save
    img.save(str(TEMP / filename), quality=95)
    print(f"Saved: {filename} ({os.path.getsize(TEMP/filename)} bytes)")

# Image 1: Main service image - Arabic
create_service_image(
    "service_ai_agent_ar.jpg",
    "بناء وكيل ذكاء\nاصطناعي (AI Agent)",
    "باستخدام n8n | أتمتة ذكية | ربط التطبيقات",
    accent_color=(0, 150, 100)
)

# Image 2: Tech/accent image
create_service_image(
    "service_ai_agent_2.jpg",
    "AI Agents &\nWorkflow Automation",
    "n8n | Make.com | API Integration | Chatbot",
    accent_color=(0, 120, 212)
)

# Image 3: Portfolio showcase image
create_service_image(
    "service_portfolio_1.jpg",
    "نظام أتمتة متكامل\nلخدمة العملاء",
    "AI-Powered | متعدد المنصات | تقارير ذكية",
    accent_color=(120, 80, 200)
)

# Image 4: Another sample
create_service_image(
    "service_portfolio_2.jpg",
    "ربط منصات التواصل\nبقاعدة بيانات ذكية",
    "Social Media | CRM | AI Analytics",
    accent_color=(200, 100, 50)
)

print("\nDone! Images saved to Temp/")
