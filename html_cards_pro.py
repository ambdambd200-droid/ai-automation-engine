"""Render professional service cards using HTML+CSS in headless browser"""
import os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')

SERVICES = [
    {
        "title": "AI Agent Development",
        "subtitle": "Custom AI assistants powered by GPT-4o + n8n",
        "price": "$25",
        "features": ["AI Chatbot Development", "n8n Workflow Integration", "Knowledge Base Setup", "Multi-Platform (TG/WA/IG)", "Analytics Dashboard"],
        "accent": "#0891B2",
        "file": "pro_ai_agent.jpg"
    },
    {
        "title": "Workflow Automation",
        "subtitle": "Automate your business with n8n & 400+ integrations",
        "price": "$20",
        "features": ["n8n Pipeline Design", "CRM & Email Sync", "Data Processing", "API Integrations", "Error Handling & Logs"],
        "accent": "#7C3AED",
        "file": "pro_workflow.jpg"
    },
    {
        "title": "AI Chatbot Solutions",
        "subtitle": "Smart bots for Telegram, WhatsApp & Instagram",
        "price": "$30",
        "features": ["Natural Language AI", "Multi-Language Support", "Lead Capture System", "24/7 Auto Response", "Order Management"],
        "accent": "#DC2626",
        "file": "pro_chatbot.jpg"
    }
]

HTML_TPL = """<!DOCTYPE html>
<html><head><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ 
    width: 800px; height: 500px; overflow: hidden;
    font-family: 'Segoe UI', Arial, sans-serif;
    background: {bg};
    position: relative;
}}
.bg-circles {{
    position: absolute; width: 100%; height: 100%; overflow: hidden;
}}
.circle {{
    position: absolute; border-radius: 50%; opacity: 0.08;
}}
.content {{
    position: relative; z-index: 10;
    padding: 45px 50px;
    height: 100%;
    display: flex; flex-direction: column;
}}
.top-line {{
    width: 60px; height: 4px; border-radius: 2px;
    background: {accent}; margin-bottom: 25px;
}}
.title {{
    font-size: 36px; font-weight: 700; color: white;
    margin-bottom: 8px; letter-spacing: -0.5px;
}}
.subtitle {{
    font-size: 15px; color: {gray}; margin-bottom: 30px;
}}
.features {{
    display: flex; flex-direction: column; gap: 10px;
    margin-bottom: auto;
}}
.feature {{
    display: flex; align-items: center; gap: 12px;
}}
.dot {{
    width: 8px; height: 8px; border-radius: 50%;
    background: {accent}; flex-shrink: 0;
}}
.feature-text {{
    font-size: 14px; color: {gray2};
}}
.bottom-bar {{
    display: flex; justify-content: space-between; align-items: center;
    padding-top: 20px; border-top: 1px solid {border};
}}
.price {{
    font-size: 20px; font-weight: 700; color: white;
    background: {accent}; padding: 8px 24px; border-radius: 8px;
}}
.tag {{
    font-size: 12px; color: {gray};
}}
.badge {{
    display: inline-block; font-size: 11px; color: {accent};
    border: 1px solid {accent}33; background: {accent}11;
    padding: 4px 12px; border-radius: 20px;
    margin-bottom: 20px;
}}
</style></head><body>
<div class="bg-circles">
    <div class="circle" style="width:300px;height:300px;background:{accent};top:-80px;right:-60px;"></div>
    <div class="circle" style="width:180px;height:180px;background:{accent};bottom:60px;left:-40px;"></div>
    <div class="circle" style="width:100px;height:100px;background:{accent};bottom:150px;right:80px;"></div>
</div>
<div class="content">
    <div class="top-line"></div>
    <div class="badge">{badge}</div>
    <div class="title">{title}</div>
    <div class="subtitle">{subtitle}</div>
    <div class="features">{features_html}</div>
    <div class="bottom-bar">
        <div class="price">{price}</div>
        <div class="tag">AI Automation Engineer</div>
    </div>
</div>
</body></html>"""

print("Starting Playwright...")
pw = sync_playwright().start()
browser = pw.chromium.launch(headless=True, args=['--no-sandbox'])
page = browser.new_page(viewport={'width': 800, 'height': 500})

for svc in SERVICES:
    feat_html = ""
    for f in svc['features']:
        feat_html += f'<div class="feature"><div class="dot"></div><div class="feature-text">{f}</div></div>'
    
    html = HTML_TPL.format(
        bg='#0F172A',
        accent=svc['accent'],
        gray='#94A3B8',
        gray2='#CBD5E1',
        border='#1E293B',
        badge=svc['title'].split()[0] + ' Development',
        title=svc['title'],
        subtitle=svc['subtitle'],
        price=svc['price'],
        features_html=feat_html
    )
    
    page.set_content(html)
    time.sleep(0.5)
    fp = TEMP / svc['file']
    page.screenshot(path=str(fp))
    sz = os.path.getsize(fp)
    print(f"  {svc['file']}: {sz} bytes")

browser.close()
pw.stop()
print("\nDone! 3 professional service cards created.")
print("\nAssignments:")
print("  pro_ai_agent.jpg  -> Service 1: AI Agent Development ($25)")
print("  pro_workflow.jpg  -> Service 2: Workflow Automation ($20)")
print("  pro_chatbot.jpg   -> Service 3: AI Chatbot Solutions ($30)")
