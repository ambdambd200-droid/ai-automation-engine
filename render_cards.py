"""Render beautiful HTML/CSS service cards in browser, screenshot them"""
import sys, time, base64
from pathlib import Path
from PIL import Image
import os

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')
from playwright.sync_api import sync_playwright

# HTML templates for service cards
CARDS = [
    {
        "file": "card_ai_agent.png",
        "title": "AI Agent\nDevelopment",
        "sub": "Custom AI Agents with n8n & OpenAI",
        "price": "From $25",
        "accent": "#00B894",
        "bg": "linear-gradient(135deg, #0c0e1a 0%, #1a1f35 50%, #0d1f1a 100%)",
        "deco": "circuit"
    },
    {
        "file": "card_workflow.png",
        "title": "Workflow\nAutomation",
        "sub": "n8n | API | Automate Your Business",
        "price": "From $20",
        "accent": "#0984E3",
        "bg": "linear-gradient(135deg, #0c0e1a 0%, #1a1f35 50%, #0a1628 100%)",
        "deco": "nodes"
    },
    {
        "file": "card_chatbot.png",
        "title": "AI Chatbot\nDevelopment",
        "sub": "Smart 24/7 Customer Support Bot",
        "price": "From $30",
        "accent": "#6C5CE7",
        "bg": "linear-gradient(135deg, #0c0e1a 0%, #1a1f35 50%, #1a0d28 100%)",
        "deco": "chat"
    }
]

HTML_TPL = """<!DOCTYPE html><html><head><style>
* { margin:0; padding:0; box-sizing:border-box; }
body { width:800px; height:500px; overflow:hidden; font-family:'Segoe UI','Tahoma',system-ui,-apple-system,sans-serif; }
.card { width:100%; height:100%; position:relative; background:{bg}; display:flex; flex-direction:column; justify-content:center; padding:60px; }
/* Decorative elements */
.deco {{ position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; overflow:hidden; }}
.deco-circle {{ position:absolute; border-radius:50%; border:1px solid {accent}; opacity:0.08; }}
.deco-line {{ position:absolute; background:{accent}; opacity:0.06; }}
/* Grid dots */
.dots {{ position:absolute; top:0; left:0; width:100%; height:100%; background-image:radial-gradient(circle, {accent}33 0.5px, transparent 0.5px); background-size:24px 24px; opacity:0.3; }}
/* Glow */
.glow {{ position:absolute; width:300px; height:300px; border-radius:50%; background:{accent}; filter:blur(120px); opacity:0.10; top:-50px; right:-50px; }}
.glow2 {{ position:absolute; width:200px; height:200px; border-radius:50%; background:{accent}; filter:blur(100px); opacity:0.08; bottom:-30px; left:-30px; }}
/* Tag */
.tag {{ display:inline-block; background:{accent}; color:white; font-size:10px; font-weight:600; letter-spacing:1.5px; text-transform:uppercase; padding:6px 14px; border-radius:3px; margin-bottom:24px; }}
/* Title */
.title {{ color:white; font-size:44px; font-weight:700; line-height:1.15; letter-spacing:-1px; white-space:pre-line; position:relative; z-index:2; }}
.title span {{ display:block; }}
/* Subtitle */
.sub {{ color:rgba(255,255,255,0.55); font-size:15px; font-weight:400; margin-top:16px; line-height:1.4; position:relative; z-index:2; }}
/* Price */
.price {{ position:absolute; bottom:60px; right:60px; background:{accent}; color:white; font-size:18px; font-weight:700; padding:10px 22px; border-radius:8px; letter-spacing:0.3px; }}
/* Bottom bar */
.bar {{ position:absolute; bottom:0; left:0; width:100%; height:4px; background:{accent}; }}
/* Corner accent */
.corner {{ position:absolute; top:30px; right:30px; width:40px; height:40px; border-top:2px solid {accent}40; border-right:2px solid {accent}40; }}
.corner2 {{ position:absolute; bottom:30px; left:30px; width:40px; height:40px; border-bottom:2px solid {accent}40; border-left:2px solid {accent}40; }}
</style></head><body>
<div class="card">
  <div class="dots"></div>
  <div class="glow"></div>
  <div class="glow2"></div>
  <div class="corner"></div>
  <div class="corner2"></div>
  <div class="tag">SERVICE</div>
  <div class="title">{title}</div>
  <div class="sub">{sub}</div>
  <div class="price">{price}</div>
  <div class="bar"></div>
</div>
</body></html>"""

print("Starting browser...")
pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data',
    executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    headless=True, args=['--no-sandbox'], viewport={'width':800,'height':500})
page = ctx.new_page()

for card in CARDS:
    html = HTML_TPL.replace("{{", "{").replace("}}", "}")
    for k, v in card.items():
        html = html.replace("{" + k + "}", v)
    # Use data URI to load HTML
    data_uri = "data:text/html;base64," + base64.b64encode(html.encode()).decode()
    page.goto(data_uri, timeout=30000)
    time.sleep(1)
    
    path = str(TEMP / card["file"])
    page.screenshot(path=path, full_page=False)
    
    # Convert to JPG for smaller size
    img = Image.open(path).convert("RGB")
    jpg_path = str(TEMP / card["file"].replace(".png", ".jpg"))
    img.save(jpg_path, quality=95)
    print(f"Created: {Path(jpg_path).name} ({os.path.getsize(jpg_path)} bytes)")

ctx.close()
pw.stop()
print("\nDone! All 3 service cards created.")
