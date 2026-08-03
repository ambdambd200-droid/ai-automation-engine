"""Create 4 premium designs at proper Mostaql dimensions"""
import os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r'C:\Users\A\Desktop\Money\Temp\designs_v3')
OUT.mkdir(exist_ok=True)

proposal_html = '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
body{width:800px;height:600px;overflow:hidden;font-family:'Inter',system-ui,-apple-system,sans-serif;background:#f5f5f4;display:flex;align-items:center;justify-content:center;padding:32px}
.card{width:100%;height:100%;background:white;border-radius:4px;padding:48px 56px;display:flex;flex-direction:column;box-shadow:0 0 0 1px rgba(0,0,0,0.02),0 8px 40px rgba(0,0,0,0.04)}
.top-bar{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:40px}
.logo{width:40px;height:40px;background:#0f172a;border-radius:8px;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:16px}
.ref{text-align:right}
.ref-label{font-size:9px;color:#d4d4d4;letter-spacing:2px;text-transform:uppercase}
.ref-num{font-size:11px;color:#a3a3a3;font-weight:500}
.label{font-size:10px;color:#d4d4d4;letter-spacing:3px;text-transform:uppercase;margin-bottom:4px}
.title{font-size:30px;font-weight:700;color:#0f172a;line-height:1.1;margin-bottom:16px;letter-spacing:-0.5px}
.title-em{color:#2563eb}
.divider{width:48px;height:3px;background:#2563eb;border-radius:2px;margin-bottom:20px}
.desc{font-size:13px;color:#737373;line-height:1.6;margin-bottom:28px;max-width:85%}
.specs{display:flex;gap:40px;margin-bottom:auto}
.spec{}
.spec-label{font-size:9px;color:#d4d4d4;letter-spacing:2px;text-transform:uppercase;margin-bottom:2px}
.spec-value{font-size:14px;color:#0f172a;font-weight:600}
.footer{margin-top:auto;padding-top:24px;border-top:1px solid #f0f0f0;display:flex;justify-content:space-between;align-items:center}
.footer-left{}
.fn{font-size:14px;font-weight:600;color:#0f172a}
.fr{font-size:10px;color:#a3a3a3}
.footer-right{text-align:right;font-size:10px;color:#a3a3a3;line-height:1.5}
</style></head><body>
<div class="card">
<div class="top-bar">
<div class="logo">A</div>
<div class="ref"><div class="ref-label">Proposal</div><div class="ref-num">#2026-001</div></div>
</div>
<div class="label">&#8594; Project Proposal</div>
<div class="title">AI Automation <span class="title-em">Engine</span></div>
<div class="divider"></div>
<div class="desc">Custom AI workflow automation system built with Python &amp; Flask.<br>Webhook processing, OpenAI integration, SQLite persistence, live dashboard.</div>
<div class="specs">
<div class="spec"><div class="spec-label">Timeline</div><div class="spec-value">7 days</div></div>
<div class="spec"><div class="spec-label">Support</div><div class="spec-value">30 days</div></div>
<div class="spec"><div class="spec-label">Budget</div><div class="spec-value">$25–50</div></div>
<div class="spec"><div class="spec-label">Revisions</div><div class="spec-value">2 rounds</div></div>
</div>
<div class="footer">
<div class="footer-left"><div class="fn">Alaa Fathi</div><div class="fr">AI Automation Engineer</div></div>
<div class="footer-right">alaafathi@proton.me<br>mostaql.com/u/alaafathi</div>
</div>
</div></body></html>'''

portfolio_html = '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
body{width:1400px;height:788px;overflow:hidden;font-family:'Inter',system-ui,-apple-system,sans-serif;background:#09090b;display:flex;align-items:center;justify-content:center;padding:36px}
.card{width:100%;height:100%;background:linear-gradient(165deg,#0c0c0f 0%,#141418 100%);border-radius:20px;border:1px solid #1c1c22;padding:44px;display:flex;flex-direction:column;position:relative;overflow:hidden}
.glow{position:absolute;top:-30%;right:-10%;width:500px;height:500px;background:radial-gradient(circle,rgba(37,99,235,0.04) 0%,transparent 60%)}
.glow2{position:absolute;bottom:-30%;left:-10%;width:400px;height:400px;background:radial-gradient(circle,rgba(99,102,241,0.03) 0%,transparent 60%)}
.accent-bar{position:absolute;top:0;left:44px;right:44px;height:1px;background:linear-gradient(90deg,transparent,rgba(37,99,235,0.2),transparent)}
.content{position:relative;z-index:1;display:flex;gap:44px;flex:1}
.left{flex:1;display:flex;flex-direction:column;padding-top:12px}
.badge{display:inline-flex;align-items:center;gap:6px;background:rgba(37,99,235,0.08);border:1px solid rgba(37,99,235,0.12);border-radius:20px;padding:4px 12px;font-size:9px;color:#60a5fa;width:fit-content;margin-bottom:20px}
.project-num{font-size:64px;font-weight:800;color:rgba(37,99,235,0.04);line-height:1;margin-bottom:-12px;letter-spacing:-2px}
.title{font-size:28px;font-weight:700;color:#fafafa;line-height:1.1;margin-bottom:8px;letter-spacing:-0.5px}
.title-em{color:#60a5fa}
.subtitle{font-size:12px;color:#52525b;margin-bottom:20px}
.features{display:flex;flex-direction:column;gap:8px}
.feat{display:flex;align-items:center;gap:10px;font-size:12px;color:#a1a1aa}
.feat-dot{width:6px;height:6px;border-radius:50%;background:#2563eb;flex-shrink:0}
.footer-tags{position:relative;z-index:1;margin-top:20px;padding-top:16px;border-top:1px solid #1c1c22;display:flex;gap:8px;flex-wrap:wrap}
.tag{background:#1c1c22;border:1px solid #27272a;border-radius:6px;padding:4px 10px;font-size:9px;color:#71717a}
.right{width:280px;display:flex;flex-direction:column;gap:12px;justify-content:center}
.mock-card{background:#0c0c0f;border:1px solid #1c1c22;border-radius:12px;padding:20px}
.mock-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.mock-title{font-size:11px;font-weight:600;color:#a1a1aa}
.mock-status{font-size:9px;color:#22c55e}
.mock-metrics{display:flex;gap:16px}
.mock-m{text-align:center}
.mock-mn{font-size:18px;font-weight:700;color:#fafafa}
.mock-ml{font-size:8px;color:#52525b;margin-top:1px}
</style></head><body>
<div class="card">
<div class="glow"></div><div class="glow2"></div>
<div class="accent-bar"></div>
<div class="content">
<div class="left">
<div class="badge">&#128640; Latest Project</div>
<div class="project-num">01</div>
<div class="title">AI Automation <span class="title-em">Engine</span></div>
<div class="subtitle">Self-hosted Python/Flask workflow processor</div>
<div class="features">
<div class="feat"><div class="feat-dot"></div>Webhook &#8594; AI &#8594; Log &#8594; Transform pipeline</div>
<div class="feat"><div class="feat-dot"></div>OpenAI lead enrichment &amp; classification</div>
<div class="feat"><div class="feat-dot"></div>Live execution dashboard with real-time stats</div>
<div class="feat"><div class="feat-dot"></div>Deployed on Render — accessible 24/7</div>
</div>
</div>
<div class="right">
<div class="mock-card">
<div class="mock-header"><div class="mock-title">System Status</div><div class="mock-status">&#9679; Running</div></div>
<div class="mock-metrics">
<div class="mock-m"><div class="mock-mn">3</div><div class="mock-ml">Executions</div></div>
<div class="mock-m"><div class="mock-mn">2</div><div class="mock-ml">Workflows</div></div>
<div class="mock-m"><div class="mock-mn">99%</div><div class="mock-ml">Uptime</div></div>
</div>
</div>
<div class="mock-card" style="border-color:#27272a">
<div class="mock-header"><div class="mock-title">Tech Stack</div></div>
<div style="display:flex;flex-wrap:wrap;gap:6px">
<span style="background:#1c1c22;border-radius:4px;padding:3px 8px;font-size:8px;color:#71717a">Python</span>
<span style="background:#1c1c22;border-radius:4px;padding:3px 8px;font-size:8px;color:#71717a">Flask</span>
<span style="background:#1c1c22;border-radius:4px;padding:3px 8px;font-size:8px;color:#71717a">SQLite</span>
<span style="background:#1c1c22;border-radius:4px;padding:3px 8px;font-size:8px;color:#71717a">OpenAI</span>
<span style="background:#1c1c22;border-radius:4px;padding:3px 8px;font-size:8px;color:#71717a">YAML</span>
</div>
</div>
</div>
</div>
<div class="footer-tags">
<span class="tag">Python</span><span class="tag">Flask</span><span class="tag">SQLite</span><span class="tag">OpenAI</span><span class="tag">YAML</span><span class="tag">Webhook</span><span class="tag">Render</span>
</div>
</div></body></html>'''

service_html = '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
body{width:1400px;height:788px;overflow:hidden;font-family:'Inter',system-ui,-apple-system,sans-serif;background:#f0f0ee;display:flex;align-items:center;justify-content:center;padding:40px}
.card{width:100%;height:100%;background:white;border-radius:24px;padding:52px 56px;display:flex;flex-direction:column;box-shadow:0 0 0 1px rgba(0,0,0,0.02),0 20px 60px rgba(0,0,0,0.04);overflow:hidden;position:relative}
.accent-block{position:absolute;top:0;left:0;width:6px;height:100%;background:linear-gradient(180deg,#2563eb,#7c3aed)}
.top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:32px}
.badge{background:#f0f5ff;color:#2563eb;padding:4px 10px;border-radius:6px;font-size:10px;font-weight:600}
.price-tag{text-align:right}
.price-amount{font-size:36px;font-weight:800;color:#0f172a;letter-spacing:-1px}
.price-period{font-size:11px;color:#a3a3a3}
.content{display:flex;gap:44px;flex:1}
.left-col{flex:1;padding-top:8px}
.service-icon{width:56px;height:56px;background:linear-gradient(135deg,#f0f5ff,#eef2ff);border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:24px;margin-bottom:16px}
.title{font-size:30px;font-weight:700;color:#0f172a;margin-bottom:8px;letter-spacing:-0.5px}
.title-em{color:#2563eb}
.desc{font-size:13px;color:#737373;line-height:1.6;margin-bottom:24px;max-width:90%}
.includes{display:flex;flex-direction:column;gap:8px}
.include{display:flex;align-items:center;gap:10px;font-size:12px;color:#52525b}
.check{width:18px;height:18px;background:#2563eb;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-size:10px;flex-shrink:0}
.right-col{width:240px;background:#fafafa;border:1px solid #f0f0f0;border-radius:16px;padding:24px;display:flex;flex-direction:column;justify-content:center}
.right-title{font-size:9px;color:#d4d4d4;letter-spacing:2px;text-transform:uppercase;margin-bottom:16px}
.tech-item{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f0f0f0;font-size:11px;color:#52525b}
.tech-item:last-child{border:none;padding-bottom:0}
.tech-val{color:#0f172a;font-weight:500}
.bottom-bar{margin-top:auto;padding-top:20px;border-top:1px solid #f0f0f0;display:flex;justify-content:space-between;font-size:10px;color:#d4d4d4}
</style></head><body>
<div class="card">
<div class="accent-block"></div>
<div class="top">
<div class="badge">&#9679; Active Service</div>
<div class="price-tag"><div class="price-amount">$25</div><div class="price-period">fixed price</div></div>
</div>
<div class="content">
<div class="left-col">
<div class="service-icon">&#129302;</div>
<div class="title">AI <span class="title-em">Agent</span> Development</div>
<div class="desc">Build custom AI agents for your business — automate workflows,<br>process data, and integrate with your existing tools.</div>
<div class="includes">
<div class="include"><div class="check">&#10003;</div>Custom AI agent built with Python + OpenAI</div>
<div class="include"><div class="check">&#10003;</div>API integration with your existing tools</div>
<div class="include"><div class="check">&#10003;</div>7-day delivery with 30-day support</div>
<div class="include"><div class="check">&#10003;</div>Documentation &amp; handover training</div>
</div>
</div>
<div class="right-col">
<div class="right-title">Includes</div>
<div class="tech-item"><span>OpenAI Integration</span><span class="tech-val">&#10003;</span></div>
<div class="tech-item"><span>Flask API</span><span class="tech-val">&#10003;</span></div>
<div class="tech-item"><span>SQLite Storage</span><span class="tech-val">&#10003;</span></div>
<div class="tech-item"><span>Webhook Support</span><span class="tech-val">&#10003;</span></div>
<div class="tech-item"><span>Dashboard UI</span><span class="tech-val">&#10003;</span></div>
</div>
</div>
<div class="bottom-bar">
<span>Alaa Fathi &mdash; AI Automation Engineer</span>
<span>mostaql.com/u/alaafathi</span>
</div>
</div></body></html>'''

banner_html = '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
body{width:1400px;height:400px;overflow:hidden;font-family:'Inter',system-ui,-apple-system,sans-serif;background:#09090b}
.banner{width:100%;height:100%;background:linear-gradient(135deg,#0c0c0f 0%,#111118 50%,#0c0c0f 100%);position:relative;overflow:hidden;display:flex;align-items:center;padding:0 60px}
.bg-glow{position:absolute;top:-50%;left:20%;width:500px;height:500px;background:radial-gradient(circle,rgba(37,99,235,0.03) 0%,transparent 60%)}
.bg-glow2{position:absolute;bottom:-40%;right:15%;width:400px;height:400px;background:radial-gradient(circle,rgba(99,102,241,0.03) 0%,transparent 60%)}
.accent-line{position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(37,99,235,0.12),transparent)}
.accent-line-b{position:absolute;bottom:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(99,102,241,0.12),transparent)}
.content{position:relative;z-index:1;display:flex;align-items:center;gap:40px;width:100%}
.avatar{width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,#2563eb,#7c3aed);display:flex;align-items:center;justify-content:center;font-size:26px;color:white;font-weight:700;flex-shrink:0}
.text{flex:1}
.name{font-size:24px;font-weight:700;color:#fafafa;margin-bottom:2px;letter-spacing:-0.3px}
.role{font-size:13px;color:#60a5fa;margin-bottom:8px}
.bio-row{font-size:11px;color:#52525b;line-height:1.5;max-width:550px;margin-bottom:12px}
.skills-row{display:flex;gap:6px;flex-wrap:wrap}
.skill{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);border-radius:6px;padding:4px 10px;font-size:9px;color:#71717a}
.stats{display:flex;gap:28px;flex-shrink:0}
.stat{text-align:center}
.stat-num{font-size:20px;font-weight:700;color:#fafafa}
.stat-label{font-size:9px;color:#52525b;margin-top:2px}
.corner-text{position:absolute;bottom:16px;right:40px;font-size:8px;color:#27272a;letter-spacing:3px;text-transform:uppercase}
</style></head><body>
<div class="banner">
<div class="bg-glow"></div><div class="bg-glow2"></div>
<div class="accent-line"></div><div class="accent-line-b"></div>
<div class="content">
<div class="avatar">A</div>
<div class="text">
<div class="name">Alaa Fathi</div>
<div class="role">AI Automation Engineer</div>
<div class="bio-row">Building intelligent automation with Python, n8n &amp; OpenAI — from lead capture pipelines to custom AI agents.</div>
<div class="skills-row">
<span class="skill">Python</span><span class="skill">Flask</span><span class="skill">n8n</span><span class="skill">OpenAI</span><span class="skill">SQLite</span><span class="skill">Automation</span>
</div>
</div>
<div class="stats">
<div class="stat"><div class="stat-num">3</div><div class="stat-label">Projects</div></div>
<div class="stat"><div class="stat-num">New</div><div class="stat-label">On Mostaql</div></div>
<div class="stat"><div class="stat-num">100%</div><div class="stat-label">Delivery</div></div>
</div>
</div>
<div class="corner-text">Available for projects</div>
</div></body></html>'''

print("Generating 4 premium designs...")
pw = sync_playwright().start()
browser = pw.chromium.launch(headless=True, args=['--no-sandbox'])
jobs = [
    ("proposal_premium.jpg", proposal_html, 800, 600),
    ("portfolio_premium.jpg", portfolio_html, 1400, 788),
    ("service_premium.jpg", service_html, 1400, 788),
    ("banner_premium.jpg", banner_html, 1400, 400),
]
for name, html, w, h in jobs:
    page = browser.new_page(viewport={'width': w, 'height': h})
    page.set_content(html)
    time.sleep(0.5)
    fp = OUT / name
    page.screenshot(path=str(fp))
    sz = os.path.getsize(fp)
    print(f"  {name}: {sz} bytes ({w}x{h})")
    page.close()
browser.close()
pw.stop()
print("\n=== RESULTS ===")
for f in sorted(OUT.iterdir()):
    if f.suffix == '.jpg':
        print(f"  {f.name} ({os.path.getsize(f)} bytes)")
