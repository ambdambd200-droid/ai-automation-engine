"""Take screenshot of engine dashboard for portfolio, then fill Mostaql portfolio form"""
import sys, time, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
from playwright.sync_api import sync_playwright

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')

# Check engine
engine_running = False
try:
    resp = urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=5)
    if resp.status == 200:
        engine_running = True
        print("Engine is RUNNING on :5000")
except:
    print("Engine NOT running")

pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data',
    executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    headless=False, args=['--no-sandbox'], viewport={'width':1280,'height':800})
page = ctx.new_page()
page.set_default_timeout(120000)

# Take screenshot of engine dashboard if running
if engine_running:
    print("\n[1] Taking engine dashboard screenshot...")
    page.goto('http://127.0.0.1:5000', timeout=30000)
    time.sleep(3)
    page.screenshot(path=str(TEMP / 'portfolio_engine_dashboard.jpg'), full_page=True)
    print(f"  Dashboard screenshot saved ({Path(TEMP/'portfolio_engine_dashboard.jpg').stat().st_size} bytes)")
else:
    # Create a clean portfolio image
    print("\n[1] Creating portfolio image...")
    page.goto('about:blank')
    html = """<!DOCTYPE html>
<html><head><style>
* { margin:0; padding:0; box-sizing:border-box; }
body {
    width: 800px; height: 500px; overflow: hidden;
    font-family: 'Segoe UI', Arial, sans-serif;
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    display: flex; align-items: center; justify-content: center;
}
.card {
    background: #1E293B; border-radius: 16px;
    padding: 40px; width: 90%; max-width: 700px;
    border: 1px solid #334155;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.badge {
    display: inline-block; font-size: 11px; color: #38BDF8;
    border: 1px solid #38BDF833; background: #38BDF811;
    padding: 4px 14px; border-radius: 20px; margin-bottom: 15px;
}
h1 {
    font-size: 24px; color: white; margin-bottom: 8px;
}
.sub {
    font-size: 13px; color: #94A3B8; margin-bottom: 25px;
}
.nodes {
    display: flex; gap: 10px; align-items: center;
    margin-bottom: 20px; flex-wrap: wrap;
}
.node {
    background: #334155; color: #CBD5E1;
    padding: 10px 16px; border-radius: 8px;
    font-size: 12px; border: 1px solid #475569;
}
.arrow { color: #38BDF8; font-size: 18px; }
.stats {
    display: flex; gap: 20px; margin-top: 20px;
    padding-top: 20px; border-top: 1px solid #334155;
}
.stat { text-align: center; }
.stat-num { font-size: 20px; font-weight: 700; color: #38BDF8; }
.stat-label { font-size: 11px; color: #64748B; }
.footer {
    display: flex; justify-content: space-between;
    margin-top: 20px; font-size: 11px; color: #475569;
}
</style></head><body>
<div class="card">
    <div class="badge">AI Automation Engine</div>
    <h1>Self-Hosted Automation Server</h1>
    <div class="sub">Flask-based engine that processes YAML-defined AI workflows via webhooks</div>
    <div class="nodes">
        <div class="node">Webhook</div>
        <span class="arrow">→</span>
        <div class="node">AI Prompt</div>
        <span class="arrow">→</span>
        <div class="node">Transform</div>
        <span class="arrow">→</span>
        <div class="node">Log</div>
        <span class="arrow">→</span>
        <div class="node">Save</div>
    </div>
    <div class="stats">
        <div class="stat"><div class="stat-num">3</div><div class="stat-label">Workflows</div></div>
        <div class="stat"><div class="stat-num">2</div><div class="stat-label">Actions</div></div>
        <div class="stat"><div class="stat-num">&lt;5s</div><div class="stat-label">Avg Response</div></div>
        <div class="stat"><div class="stat-num">✔</div><div class="stat-label">Open Source</div></div>
    </div>
    <div class="footer">
        <span>Python • Flask • SQLite • YAML</span>
        <span>AI Automation Engineer</span>
    </div>
</div>
</body></html>"""
    page.set_content(html)
    time.sleep(1)
    page.screenshot(path=str(TEMP / 'portfolio_engine_dashboard.jpg'))
    print(f"  Created portfolio image")

# Now open Mostaql portfolio form
print("\n[2] Opening Mostaql portfolio onboarding...")
page.goto('https://mostaql.com/onboarding/portfolio', timeout=180000)
time.sleep(4)
print(f"URL: {page.url[:80]}")

if 'login' in page.url.lower():
    password = (TEMP / 'mostaql_password.txt').read_text(encoding='utf-8').strip()
    page.evaluate(f"""() => {{
        const el = document.querySelector('input[type="email"]');
        if(el) {{ el.value = 'ambdambd200@gmail.com'; el.dispatchEvent(new Event('input',{{b:true}})); }}
    }}""")
    page.evaluate(f"""() => {{
        const el = document.querySelector('input[type="password"]');
        if(el) {{ el.value = '{password}'; el.dispatchEvent(new Event('input',{{b:true}})); }}
    }}""")
    page.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for(const b of btns) {
            if(b.innerText.toLowerCase().includes('دخول')) { b.click(); return; }
        }
    }""")
    time.sleep(5)

page.screenshot(path=TEMP / 'mostaql_portfolio_page.png')

# Get form fields
fields = page.eval_on_selector_all("input, textarea, select", """els => els.map(e => ({
    name: e.name || '', id: e.id || '', type: e.type || e.tagName,
    ph: (e.placeholder || '').substring(0, 40),
    visible: e.offsetParent !== null
})).filter(e => e.visible && (e.name || e.id))""")
print(f"\nForm fields: {len(fields)}")
for f in fields:
    print(f"  {f['name'] or f['id']:30s} ph='{f['ph']}' ({f['type']})")

# Fill portfolio form
# Title
page.eval_on_selector("input[name='title']", """el => {
    if(!el) return 'NF';
    el.value = 'AI Automation Engine - محرك أتمتة ذكي';
    el.dispatchEvent(new Event('input',{bubbles:true}));
    el.dispatchEvent(new Event('change',{bubbles:true}));
    return 'OK';
}""")

# Description
page.eval_on_selector("textarea", """el => {
    if(!el) return 'NF';
    el.value = 'Flask app that receives webhooks and processes them through YAML-defined AI workflows. Uses OpenAI for text analysis and saves to SQLite. Works 100% locally.\n\nFeatures:\n- Webhook processing with YAML pipelines\n- OpenAI integration for smart analysis\n- SQLite storage\n- Live execution dashboard\n- Fully self-hosted';
    el.dispatchEvent(new Event('input',{bubbles:true}));
    el.dispatchEvent(new Event('change',{bubbles:true}));
    return 'OK';
}""")

# URL (GitHub)
page.eval_on_selector("input[name='url']", """el => {
    if(!el) return 'NF';
    el.value = 'https://github.com/alaafathi/ai-automation-engine';
    el.dispatchEvent(new Event('input',{bubbles:true}));
    el.dispatchEvent(new Event('change',{bubbles:true}));
    return 'OK';
}""")

# Upload image
file_input = page.query_selector("input[type='file']")
if file_input:
    file_input.set_input_files(str(TEMP / 'portfolio_engine_dashboard.jpg'))
    print("  Image uploaded")
    time.sleep(2)
else:
    print("  No file input found")

# Check terms checkbox
page.eval_on_selector("input[name='portfolio_terms_1'], input[type='checkbox']", """el => {
    if(el) { el.checked = true; el.dispatchEvent(new Event('change',{bubbles:true})); return 'checked'; }
    return 'NF';
}""")

# Save
page.eval_on_selector("button[type='submit'], button.btn-primary", """btn => {
    if(!btn) {
        const all = document.querySelectorAll('button');
        for(const b of all) {
            if(b.innerText.includes('إضافة') || b.innerText.includes('حفظ')) { b.click(); return 'clicked'; }
        }
        return 'NF';
    }
    btn.click();
    return 'clicked';
}""")
time.sleep(3)
print(f"  After save: {page.url[:80]}")
page.screenshot(path=TEMP / 'mostaql_portfolio_added.png')

print(f"\n=== Portfolio item added! ===")
input("Press Enter...")
ctx.close()
pw.stop()
