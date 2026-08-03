"""
complete_arabic_profiles.py — Comprehensive Mostaql + Nafezly profile automation
==============================================================================
WHAT IT DOES:
  1. GENERATE 6 premium design images (portfolio, services, banner) via HTML→JPG
  2. NAFEZLY: fill bio · job title · skills · personal data
  3. NAFEZLY: create/update 3 services with descriptions
  4. MOSTAQL: fill professional title · bio · skills · hourly rate · links
  5. MOSTAQL: add 3 portfolio items with premium images

USAGE:
  python complete_arabic_profiles.py

REQUIRES:
  - Brave browser with saved sessions on both platforms
  - Playwright (installed)
  - Run from Money/ directory

SAFE: Browser opens visibly. You review everything before it submits.
      Script pauses before every submit action.
"""

import sys, time, json, os, base64, argparse
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── AUTO MODE ──────────────────────────────────────────────────────────────
AUTO_MODE = False

def confirm(msg: str = "", default_yes: bool = True) -> bool:
    """
    If AUTO_MODE, auto-confirm (return True) with a brief log.
    Otherwise prompt the user.
    """
    if AUTO_MODE:
        log(f"  → AUTO: {msg} — auto-confirming")
        return True
    choice = input(f"{msg} [{'Y/n' if default_yes else 'y/N'}]: ").strip().lower()
    if default_yes:
        return choice != 'n'
    else:
        return choice == 'y'

def confirm_enter(msg: str = "Press ENTER to continue"):
    """
    If AUTO_MODE, auto-continue after 1s delay.
    Otherwise wait for Enter.
    """
    if AUTO_MODE:
        log(f"  → AUTO: {msg} — continuing automatically")
        time.sleep(1)
        return
    input(f"  {msg}...")

# ── PATHS ──────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent.resolve()
TEMP = BASE / "Temp"
DESIGNS = TEMP / "designs_v3"
DESIGNS.mkdir(parents=True, exist_ok=True)
TEMP.mkdir(parents=True, exist_ok=True)
LOG_FILE = BASE / "profile_completion_log.md"

BRAVE_EXE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
BRAVE_PROFILE = r"C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data"
EMAIL = "ambdambd200@gmail.com"
PASSWORD_FILE = TEMP / "mostaql_password.txt"

# ── LOGGING ─────────────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def step(n: int, label: str, msg: str):
    log(f"  ═══ STEP {n}: {label} ═══")
    log(f"       {msg}")

# ── HELPER: JS set value ───────────────────────────────────────────────────
def js_set(page, selector: str, value: str) -> str:
    """Set form field value via JS — instant, bypasses typing simulation."""
    return page.evaluate("""(args) => {
        const el = document.querySelector(args.s);
        if (!el) return 'NF:' + args.s;
        const tag = el.tagName.toLowerCase();
        el.value = args.v;
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
        return 'OK:' + tag + '.' + (el.name || el.id || '');
    }""", {"s": selector, "v": value})

def js_click_by_text(page, texts: list) -> bool:
    """Click first button/span/a containing any of the given texts."""
    for t in texts:
        ok = page.evaluate(f"""(t) => {{
            const els = document.querySelectorAll('button, a, span, input[type=submit]');
            for (const e of els) {{
                if (e.innerText?.trim().includes(t)) {{ e.click(); return true; }}
            }}
            return false;
        }}""", t)
        if ok:
            return True
    return False

def wait_login(page, url: str, timeout=120):
    """Navigate and wait for login if needed."""
    page.goto(url, timeout=180000, wait_until="domcontentloaded")
    time.sleep(3)
    if "login" in page.url.lower():
        log(f"  ⏳ Login required at {url} — waiting {timeout}s...")
        for _ in range(timeout):
            time.sleep(1)
            if "login" not in page.url.lower():
                break
        log(f"  → After wait: {page.url[:80]}")

def snap(page, name: str):
    """Save screenshot to Temp/."""
    try:
        page.screenshot(path=str(TEMP / f"profile_{name}.png"))
    except Exception as e:
        log(f"  ⚠ Screenshot failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 1: GENERATE 6 PREMIUM DESIGN IMAGES
# ═══════════════════════════════════════════════════════════════════════════
def generate_images():
    """Generate premium design images via HTML→screenshot in headless browser."""
    step(1, "Generate Designs", "Creating 6 premium images for portfolio & services")

    images_needed = [
        "portfolio_01.jpg", "portfolio_02.jpg", "portfolio_03.jpg",
        "service_01.jpg", "service_02.jpg", "service_03.jpg"
    ]
    all_exist = all((DESIGNS / img).exists() for img in images_needed)
    if all_exist:
        log("  ✓ All design images already exist — skipping generation")
        return

    # ── HTML Templates ──────────────────────────────────────────────────────
    DESIGNS_HTML = {}

    DESIGNS_HTML["portfolio_01"] = """<!DOCTYPE html>
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
.mock-title{font-size:11px;font-weight:600;color:#a1a1aa}
.mock-status{font-size:9px;color:#22c55e}
</style></head><body>
<div class="card">
<div class="glow"></div><div class="glow2"></div>
<div class="accent-bar"></div>
<div class="content">
<div class="left">
<div class="badge">PORTFOLIO</div>
<div class="project-num">01</div>
<div class="title">AI Automation <span class="title-em">Engine</span></div>
<div class="subtitle">محرك أتمتة ذكي يعمل على Python/Flask — معالجة webhooks بالذكاء الاصطناعي</div>
<div class="features">
<div class="feat"><div class="feat-dot"></div>Webhook → AI → Transform → Log pipeline</div>
<div class="feat"><div class="feat-dot"></div>OpenAI enrichment & classification</div>
<div class="feat"><div class="feat-dot"></div>Live execution dashboard</div>
<div class="feat"><div class="feat-dot"></div>Self-hosted on Render — 24/7 uptime</div>
</div>
</div>
<div class="right">
<div class="mock-card">
<div class="mock-header"><div class="mock-title">System Status</div><div class="mock-status">● Running</div></div>
</div>
</div>
</div>
<div class="footer-tags">
<span class="tag">Python</span><span class="tag">Flask</span><span class="tag">SQLite</span><span class="tag">OpenAI</span><span class="tag">YAML</span>
</div>
</div></body></html>"""

    DESIGNS_HTML["portfolio_02"] = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
body{width:1400px;height:788px;overflow:hidden;font-family:'Inter',system-ui,-apple-system,sans-serif;background:#09090b;display:flex;align-items:center;justify-content:center;padding:36px}
.card{width:100%;height:100%;background:linear-gradient(165deg,#0c0c0f 0%,#141418 100%);border-radius:20px;border:1px solid #1c1c22;padding:44px;display:flex;flex-direction:column;position:relative;overflow:hidden}
.glow{position:absolute;top:-30%;right:-10%;width:500px;height:500px;background:radial-gradient(circle,rgba(139,92,246,0.04) 0%,transparent 60%)}
.glow2{position:absolute;bottom:-30%;left:-10%;width:400px;height:400px;background:radial-gradient(circle,rgba(59,130,246,0.03) 0%,transparent 60%)}
.content{position:relative;z-index:1;display:flex;gap:44px;flex:1}
.left{flex:1;display:flex;flex-direction:column;padding-top:12px}
.badge{display:inline-flex;align-items:center;background:rgba(139,92,246,0.08);border:1px solid rgba(139,92,246,0.12);border-radius:20px;padding:4px 12px;font-size:9px;color:#a78bfa;width:fit-content;margin-bottom:20px}
.project-num{font-size:64px;font-weight:800;color:rgba(139,92,246,0.04);line-height:1;margin-bottom:-12px;letter-spacing:-2px}
.title{font-size:28px;font-weight:700;color:#fafafa;line-height:1.1;margin-bottom:8px;letter-spacing:-0.5px}
.title-em{color:#a78bfa}
.subtitle{font-size:12px;color:#52525b;margin-bottom:20px}
.features{display:flex;flex-direction:column;gap:8px}
.feat{display:flex;align-items:center;gap:10px;font-size:12px;color:#a1a1aa}
.feat-dot{width:6px;height:6px;border-radius:50%;background:#8b5cf6;flex-shrink:0}
.footer-tags{position:relative;z-index:1;margin-top:20px;padding-top:16px;border-top:1px solid #1c1c22;display:flex;gap:8px;flex-wrap:wrap}
.tag{background:#1c1c22;border:1px solid #27272a;border-radius:6px;padding:4px 10px;font-size:9px;color:#71717a}
</style></head><body>
<div class="card">
<div class="glow"></div><div class="glow2"></div>
<div class="content">
<div class="left">
<div class="badge">PORTFOLIO</div>
<div class="project-num">02</div>
<div class="title">n8n <span class="title-em">Automation</span> Pipelines</div>
<div class="subtitle">سير عمل مؤتمت بالكامل — يربط OpenAI + Google Sheets + Slack</div>
<div class="features">
<div class="feat"><div class="feat-dot"></div>Lead capture: web form → AI enrichment → CRM</div>
<div class="feat"><div class="feat-dot"></div>Email auto-classification & routing</div>
<div class="feat"><div class="feat-dot"></div>Slack notifications with smart summaries</div>
<div class="feat"><div class="feat-dot"></div>400+ integrations via n8n</div>
</div>
</div>
</div>
<div class="footer-tags">
<span class="tag">n8n</span><span class="tag">OpenAI</span><span class="tag">Google Sheets</span><span class="tag">Slack</span><span class="tag">Webhook</span>
</div>
</div></body></html>"""

    DESIGNS_HTML["portfolio_03"] = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
body{width:1400px;height:788px;overflow:hidden;font-family:'Inter',system-ui,-apple-system,sans-serif;background:#09090b;display:flex;align-items:center;justify-content:center;padding:36px}
.card{width:100%;height:100%;background:linear-gradient(165deg,#0c0c0f 0%,#141418 100%);border-radius:20px;border:1px solid #1c1c22;padding:44px;display:flex;flex-direction:column;position:relative;overflow:hidden}
.glow{position:absolute;top:-30%;right:-10%;width:500px;height:500px;background:radial-gradient(circle,rgba(16,185,129,0.04) 0%,transparent 60%)}
.glow2{position:absolute;bottom:-30%;left:-10%;width:400px;height:400px;background:radial-gradient(circle,rgba(16,185,129,0.03) 0%,transparent 60%)}
.content{position:relative;z-index:1;display:flex;gap:44px;flex:1}
.left{flex:1;display:flex;flex-direction:column;padding-top:12px}
.badge{display:inline-flex;align-items:center;background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.12);border-radius:20px;padding:4px 12px;font-size:9px;color:#34d399;width:fit-content;margin-bottom:20px}
.project-num{font-size:64px;font-weight:800;color:rgba(16,185,129,0.04);line-height:1;margin-bottom:-12px;letter-spacing:-2px}
.title{font-size:28px;font-weight:700;color:#fafafa;line-height:1.1;margin-bottom:8px;letter-spacing:-0.5px}
.title-em{color:#34d399}
.subtitle{font-size:12px;color:#52525b;margin-bottom:20px}
.features{display:flex;flex-direction:column;gap:8px}
.feat{display:flex;align-items:center;gap:10px;font-size:12px;color:#a1a1aa}
.feat-dot{width:6px;height:6px;border-radius:50%;background:#10b981;flex-shrink:0}
.footer-tags{position:relative;z-index:1;margin-top:20px;padding-top:16px;border-top:1px solid #1c1c22;display:flex;gap:8px;flex-wrap:wrap}
.tag{background:#1c1c22;border:1px solid #27272a;border-radius:6px;padding:4px 10px;font-size:9px;color:#71717a}
</style></head><body>
<div class="card">
<div class="glow"></div><div class="glow2"></div>
<div class="content">
<div class="left">
<div class="badge">PORTFOLIO</div>
<div class="project-num">03</div>
<div class="title">AI Chatbot <span class="title-em">Solutions</span></div>
<div class="subtitle">بوتات محادثة ذكية لخدمة العملاء — تعمل 24/7 وتفهم اللغة العربية</div>
<div class="features">
<div class="feat"><div class="feat-dot"></div>Multi-platform: Telegram, WhatsApp, Website</div>
<div class="feat"><div class="feat-dot"></div>Arabic + English natural language understanding</div>
<div class="feat"><div class="feat-dot"></div>Order management & lead capture</div>
<div class="feat"><div class="feat-dot"></div>CRM integration with real-time sync</div>
</div>
</div>
</div>
<div class="footer-tags">
<span class="tag">AI</span><span class="tag">Chatbot</span><span class="tag">OpenAI</span><span class="tag">Telegram</span><span class="tag">n8n</span>
</div>
</div></body></html>"""

    DESIGNS_HTML["service_01"] = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
body{width:800px;height:500px;overflow:hidden;font-family:'Inter',system-ui,-apple-system,sans-serif;background:#0F172A;display:flex;align-items:center;justify-content:center;padding:32px}
.card{width:100%;height:100%;position:relative;display:flex;flex-direction:column;justify-content:center;padding:44px;overflow:hidden}
.bg{position:absolute;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle at 100% 0%,#0891B208 0%,transparent 50%)}
.dots{position:absolute;top:0;left:0;width:100%;height:100%;background-image:radial-gradient(circle,#0891B233 0.5px,transparent 0.5px);background-size:24px 24px;opacity:0.2}
.corner{position:absolute;top:24px;right:24px;width:32px;height:32px;border-top:2px solid #0891B233;border-right:2px solid #0891B233}
.corner2{position:absolute;bottom:24px;left:24px;width:32px;height:32px;border-bottom:2px solid #0891B233;border-left:2px solid #0891B233}
.bar{position:absolute;bottom:0;left:0;width:100%;height:4px;background:linear-gradient(90deg,#0891B2,#06B6D4)}
.tag{display:inline-block;background:#0891B2;color:white;font-size:9px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:3px;margin-bottom:20px;width:fit-content;position:relative;z-index:2}
.title{color:white;font-size:36px;font-weight:700;line-height:1.15;letter-spacing:-0.5px;position:relative;z-index:2;max-width:90%}
.sub{color:#94A3B8;font-size:14px;margin-top:12px;position:relative;z-index:2}
.price{position:absolute;bottom:40px;right:44px;background:#0891B2;color:white;font-size:16px;font-weight:700;padding:8px 20px;border-radius:6px;z-index:2}
</style></head><body>
<div class="card">
<div class="bg"></div><div class="dots"></div>
<div class="corner"></div><div class="corner2"></div>
<div class="tag">SERVICE</div>
<div class="title">AI Agent Development<br>بناء وكلاء ذكاء اصطناعي</div>
<div class="sub">Custom AI agents powered by GPT-4o + n8n · أتمتة ذكية لعملك</div>
<div class="price">$25</div>
<div class="bar"></div>
</div></body></html>"""

    DESIGNS_HTML["service_02"] = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
body{width:800px;height:500px;overflow:hidden;font-family:'Inter',system-ui,-apple-system,sans-serif;background:#0F172A;display:flex;align-items:center;justify-content:center;padding:32px}
.card{width:100%;height:100%;position:relative;display:flex;flex-direction:column;justify-content:center;padding:44px;overflow:hidden}
.bg{position:absolute;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle at 100% 0%,#7C3AED08 0%,transparent 50%)}
.dots{position:absolute;top:0;left:0;width:100%;height:100%;background-image:radial-gradient(circle,#7C3AED33 0.5px,transparent 0.5px);background-size:24px 24px;opacity:0.2}
.corner{position:absolute;top:24px;right:24px;width:32px;height:32px;border-top:2px solid #7C3AED33;border-right:2px solid #7C3AED33}
.corner2{position:absolute;bottom:24px;left:24px;width:32px;height:32px;border-bottom:2px solid #7C3AED33;border-left:2px solid #7C3AED33}
.bar{position:absolute;bottom:0;left:0;width:100%;height:4px;background:linear-gradient(90deg,#7C3AED,#A78BFA)}
.tag{display:inline-block;background:#7C3AED;color:white;font-size:9px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:3px;margin-bottom:20px;width:fit-content;position:relative;z-index:2}
.title{color:white;font-size:36px;font-weight:700;line-height:1.15;letter-spacing:-0.5px;position:relative;z-index:2;max-width:90%}
.sub{color:#94A3B8;font-size:14px;margin-top:12px;position:relative;z-index:2}
.price{position:absolute;bottom:40px;right:44px;background:#7C3AED;color:white;font-size:16px;font-weight:700;padding:8px 20px;border-radius:6px;z-index:2}
</style></head><body>
<div class="card">
<div class="bg"></div><div class="dots"></div>
<div class="corner"></div><div class="corner2"></div>
<div class="tag">SERVICE</div>
<div class="title">Workflow Automation<br>أتمتة سير العمل بـ n8n</div>
<div class="sub">n8n pipelines · 400+ integrations · ربط تطبيقاتك ببعضها</div>
<div class="price">$20</div>
<div class="bar"></div>
</div></body></html>"""

    DESIGNS_HTML["service_03"] = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
body{width:800px;height:500px;overflow:hidden;font-family:'Inter',system-ui,-apple-system,sans-serif;background:#0F172A;display:flex;align-items:center;justify-content:center;padding:32px}
.card{width:100%;height:100%;position:relative;display:flex;flex-direction:column;justify-content:center;padding:44px;overflow:hidden}
.bg{position:absolute;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle at 100% 0%,#DC262608 0%,transparent 50%)}
.dots{position:absolute;top:0;left:0;width:100%;height:100%;background-image:radial-gradient(circle,#DC262633 0.5px,transparent 0.5px);background-size:24px 24px;opacity:0.2}
.corner{position:absolute;top:24px;right:24px;width:32px;height:32px;border-top:2px solid #DC262633;border-right:2px solid #DC262633}
.corner2{position:absolute;bottom:24px;left:24px;width:32px;height:32px;border-bottom:2px solid #DC262633;border-left:2px solid #DC262633}
.bar{position:absolute;bottom:0;left:0;width:100%;height:4px;background:linear-gradient(90deg,#DC2626,#F87171)}
.tag{display:inline-block;background:#DC2626;color:white;font-size:9px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:3px;margin-bottom:20px;width:fit-content;position:relative;z-index:2}
.title{color:white;font-size:36px;font-weight:700;line-height:1.15;letter-spacing:-0.5px;position:relative;z-index:2;max-width:90%}
.sub{color:#94A3B8;font-size:14px;margin-top:12px;position:relative;z-index:2}
.price{position:absolute;bottom:40px;right:44px;background:#DC2626;color:white;font-size:16px;font-weight:700;padding:8px 20px;border-radius:6px;z-index:2}
</style></head><body>
<div class="card">
<div class="bg"></div><div class="dots"></div>
<div class="corner"></div><div class="corner2"></div>
<div class="tag">SERVICE</div>
<div class="title">AI Chatbot Development<br>بوتات محادثة ذكية</div>
<div class="sub">24/7 customer support · Arabic+English · Telegram/WhatsApp/Web</div>
<div class="price">$30</div>
<div class="bar"></div>
</div></body></html>"""

    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])

    generated = 0
    for key, html in DESIGNS_HTML.items():
        fname = key + ".jpg"
        fp = DESIGNS / fname
        if fp.exists():
            log(f"  ✓ {fname} already exists")
            continue
        try:
            page = browser.new_page(viewport={"width": 1400, "height": 788})
            page.set_content(html)
            time.sleep(0.3)
            page.screenshot(path=str(fp), full_page=False)
            sz = fp.stat().st_size if fp.exists() else 0
            log(f"  ✓ {fname} created ({sz} bytes)")
            page.close()
            generated += 1
        except Exception as e:
            log(f"  ✗ {fname} failed: {e}")

    browser.close()
    pw.stop()
    log(f"  → Generated {generated} images")


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 2: NAFEZLY — COMPLETE PROFILE
# ═══════════════════════════════════════════════════════════════════════════
NAFEZLY_BIO = """السلام عليكم ورحمة الله وبركاته

أنا علاء فتحي، مهندس أتمتة وذكاء اصطناعي. أساعد الشركات وأصحاب المشاريع في أتمتة عملياتهم اليومية وتوفير الوقت والجهد باستخدام أحدث تقنيات الذكاء الاصطناعي.

تخصصاتي:
• بناء أنظمة أتمتة متكاملة باستخدام n8n — ربط التطبيقات مثل Google Sheets و Slack و Airtable و Notion في سير عمل واحد
• تطوير وكلاء ذكاء اصطناعي (AI Agents) لفهم النصوص والرد الذكي باستخدام OpenAI GPT-4o
• أتمتة البريد الإلكتروني: تصنيف الرسائل، الرد التلقائي، متابعة العملاء المحتملين
• بناء بوتات محادثة ذكية (Chatbots) عربية وإنجليزية تعمل 24/7
• معالجة البيانات: استخراج، تحليل، وتحويل باستخدام Python

أمثلة من مشاريعي:
• نظام حجوزات آلي: نموذج ويب ← n8n ← تقويم Google ← تأكيد للعميل
• بوت تأهيل عملاء: نموذج ويب ← OpenAI تحليل الاهتمامات ← Google Sheets ← Slack للفريق
• محرك أتمتة : webhook ← AI pipeline ← تخزين ← لوحة تحكم

ماذا يضمن لك العمل معي:
✓ التزام صارم بالمواعيد والتسليم في الوقت المتفق عليه
✓ تواصل يومي عبر المنصة أو واتساب
✓ توثيق كامل لكل مشروع (فيديو شرح + ملفات)
✓ دعم مجاني لمدة أسبوع بعد التسليم
✓ تعديلات مجانية حتى رضاك التام

أسعاري تنافسية لأنني أؤمن بالجودة أولاً. ستحصل على قيمة أعلى مما تدفع."""

NAFEZLY_JOB_TITLE = "مهندس أتمتة وذكاء اصطناعي | n8n | Python | OpenAI"

# Skills to select on Nafezly — we'll search by keyword
NAFEZLY_SKILL_KEYWORDS = [
    "n8n", "Python", "OpenAI", "AI", "Automation",
    "API", "Chatbot", "Flask", "تطوير",
    "تكامل", "سير عمل", "تعلم آلة",
    "سحابي", "قواعد بيانات", "تحليل",
    "برمجة", "شبكات", "أنظمة",
    "ذكاء", "أتمتة", "برمجيات",
]

NAFEZLY_SERVICES = [
    {
        "title": "بناء وكيل ذكاء اصطناعي (AI Agent) باستخدام n8n",
        "desc": "السلام عليكم ورحمة الله وبركاته.\n\nهل تقضي ساعات يومياً في مهام متكررة مثل الرد على الاستفسارات، تصنيف البريد، أو إدخال البيانات في أكثر من نظام؟\n\nأبنيك وكيل ذكاء اصطناعي (AI Agent) متكامل على منصة n8n يقوم بهذه المهام تلقائياً، ويربط تطبيقاتك ببعضها بدون تدخل يدوي.",
        "long_desc": "\n\nماذا ستحصل بالضبط:\n\n🤖 وكيل AI متكامل:\n- يفهم التعليمات بالعربية أو الإنجليزية\n- يتخذ قرارات بناءً على المدخلات (تصنيف، تحليل، رد)\n- يتعلم من تفاعلاته ويتحسن مع الوقت\n\n🔗 ربط التطبيقات (اختياري):\n- Google Sheets - قواعد البيانات - Slack - البريد الإلكتروني\n- APIs خارجية حسب احتياجك\n- Webhooks لاستقبال البيانات من أي مصدر\n\n📋 خطة العمل:\n1. جلسة تحديد المتطلبات (مكالمة أو محادثة)\n2. تصميم بنية الوكيل (AI + workflows)\n3. بناء واختبار الوكيل\n4. تشغيل تجريبي مع بياناتك\n5. تسليم + توثيق + فيديو شرح\n\n🛠 التقنيات المستخدمة: n8n، OpenAI GPT-4o، APIs، Webhooks\n⏱ مدة التسليم: 3-7 أيام (حسب التعقيد)\n🎁 دعم مجاني: 10 أيام بعد التسليم",
        "price": "30",
        "period": "7",
        "specialization": "1",
        "sub_specialization": None,
        "instructions": "السلام عليكم. شكراً لاهتمامك. يرجى توضيح: (1) ما المهمة التي تريد أتمتتها؟ (2) ما التطبيقات التي تستخدمها حالياً؟ (3) هل لديك مهلة زمنية محددة؟ سأتواصل معك خلال 24 ساعة.",
        "img": "service_01.jpg"
    },
    {
        "title": "أتمتة سير العمل (Workflow Automation) باستخدام n8n",
        "desc": "السلام عليكم ورحمة الله وبركاته.\n\nهل توجد مهمة تقوم بها كل يوم وتتمنى لو كانت تعمل وحدها؟ مثلاً: نموذج ويب يرسل بيانات إلى Google Sheet ثم يرسل إشعار في Slack... أو بريد وارد يُصنّف تلقائياً ويرد على العملاء.\n\nأبنيلك workflow مخصص على n8n يعمل 24/7 ويربط تطبيقاتك ببعضها.",
        "long_desc": "\n\nماذا ستحصل بالضبط:\n\n⚙️ workflow مخصص:\n- يعمل تلقائياً بدون تدخل يدوي\n- يربط بين 2-4 تطبيقات من اختيارك\n- يمكن جدولته أو تشغيله فورياً\n\nأمثلة عملية (اختر ما يناسبك):\n📩 الرد التلقائي: استفسارات العملاء ← OpenAI تحليل ← رد ذكي ← تسجيل في CRM\n📊 التقارير: Google Sheets ← تحليل ← PDF ← إيميل تلقائي\n🔄 المزامنة: Airtable → Notion → Slack إشعارات\n👥 تأهيل العملاء: نموذج ويب ← OpenAI تصنيف ← Google Sheets ← Slack للفريق\n\n📋 خطة العمل:\n1. نفهم المهمة التي تريد أتمتتها\n2. نصمم workflow في n8n\n3. نربط التطبيقات APIs\n4. نختبر ونتأكد من الدقة\n5. نسلّم مع توثيق مختصر\n\n🛠 الأدوات: n8n، APIs، Webhooks، OpenAI (اختياري)\n⏱ مدة التسليم: 3-5 أيام\n🎁 دعم مجاني: 7 أيام بعد التسليم",
        "price": "25",
        "period": "5",
        "specialization": "1",
        "sub_specialization": None,
        "instructions": "السلام عليكم. شكراً لاهتمامك. يرجى وصف: (1) المهمة التي تريد أتمتتها، (2) التطبيقات التي تستخدمها (Gmail، Sheets، Slack...)، (3) كم مرة تكررها يومياً/أسبوعياً. سأقدّم لك الحل الأمثل.",
        "img": "service_02.jpg"
    },
    {
        "title": "تطوير بوت محادثة ذكي (AI Chatbot) باستخدام n8n و OpenAI",
        "desc": "السلام عليكم ورحمة الله وبركاته.\n\nهل تريد بوتاً ذكياً يخدم عملاءك على مدار الساعة ويرد عليهم بالعربية والإنجليزية؟ بوت يفهم أسئلتهم، يسجل بياناتهم، ويربطهم بفريقك عندما يحتاجون مساعدة بشرية؟\n\nأبنيلك بوت محادثة ذكي مدعوم بـ n8n + OpenAI. يعمل على تلغرام، واتساب، أو موقعك الإلكتروني.",
        "long_desc": "\n\nماذا ستحصل بالضبط:\n\n💬 بوت ذكي:\n- يفهم اللغة العربية الفصحى والعامية + الإنجليزية\n- يرد على الأسئلة الشائعة (FAQ) فورياً\n- يتصاعد: إذا لم يعرف الإجابة، يحول لمندوب بشري\n- يسجل العملاء المحتملين في Google Sheets أو CRM\n\n🔧 المنصات المدعومة:\n- تلغرام (بوت مخصص)\n- واتساب (عبر API أو WATI/Twilio)\n- ويدجيت موقع إلكتروني (شات مباشر)\n- كلها بنفس الذكاء ونفس قاعدة المعرفة\n\n📚 تدريب البوت:\n- على أسئلتكم الشائعة (FAQ)\n- على ملف PDF أو موقعكم الإلكتروني\n- على كتالوج منتجاتكم أو خدماتكم\n\n📋 خطة العمل:\n1. نحدد المنصة ونوع الأسئلة\n2. نجهز قاعدة المعرفة\n3. نبني البوت بـ n8n + OpenAI\n4. نختبر ونتأكد من دقة الردود\n5. نسلّم مع لوحة تحكم لمتابعة الأداء\n\n🛠 التقنيات: n8n، OpenAI GPT-4o، Telegram API، WhatsApp API، Website Widget\n⏱ مدة التسليم: 5-7 أيام\n🎁 دعم مجاني: 14 يوم بعد التسليم",
        "price": "35",
        "period": "7",
        "specialization": "1",
        "sub_specialization": None,
        "instructions": "السلام عليكم. شكراً لاهتمامك. يرجى تحديد: (1) المنصة التي تريد البوت عليها، (2) نوع الأسئلة التي يستقبلها عملاؤك، (3) هل لديك ملفات (PDF/FAQ) لتدريب البوت؟ سأتواصل معك خلال 24 ساعة.",
        "img": "service_03.jpg"
    }
]


def fill_nafezly_profile(page):
    """Fill Nafezly profile: bio, job title, skills, personal data."""
    step(2, "Nafezly Profile", "Filling bio, job title, skills, personal data")

    # ── 2A: Settings (bio + job title) ──
    wait_login(page, "https://nafezly.com/profile/nafezly-settings")
    snap(page, "nafezly_settings")

    log("  Filling bio...")
    r = js_set(page, "textarea[name='bio']", NAFEZLY_BIO)
    log(f"    Bio: {r}")

    log("  Filling job title...")
    r = js_set(page, "input[name='job_title']", NAFEZLY_JOB_TITLE)
    log(f"    Job title: {r}")

    # Save
    time.sleep(1)
    if js_click_by_text(page, ["حفظ", "Save", "تحديث", "Update"]):
        time.sleep(2)
        log("  ✓ Settings saved")
    else:
        log("  ⚠ Save button not found — please save manually")

    snap(page, "nafezly_settings_saved")

    # ── 2B: Skills ──
    # Nafezly uses selectize.js multi-select for skills
    log("  Adding skills via selectize...")
    skills_html = page.content()
    (TEMP / "nafezly_settings_html.html").write_text(skills_html, encoding="utf-8")

    # Check if selectize exists
    has_selectize = page.evaluate("""() => {
        const sel = document.querySelector('select[name="tag_id[]"], select[name="tags[]"], select.selectized');
        return sel ? (sel.selectize ? 'yes' : 'no_selectize') : 'no_select';
    }""")
    log(f"    Selectize status: {has_selectize}")

    if "yes" in has_selectize:
        # Get all available options
        options = page.evaluate("""() => {
            const sel = document.querySelector('select.selectized, select[name="tag_id[]"]');
            if (!sel || !sel.selectize) return [];
            const opts = sel.selectize.options;
            return Object.keys(opts).map(k => ({
                val: k,
                text: opts[k].text || ''
            })).filter(o => o.text);
        }""")
        log(f"    Found {len(options)} available skills")

        # Find skills matching our keywords
        matched_ids = []
        for opt in options:
            t = opt['text'].lower()
            for kw in NAFEZLY_SKILL_KEYWORDS:
                if kw.lower() in t:
                    matched_ids.append(opt['val'])
                    break

        log(f"    Matched {len(matched_ids)} skills: {matched_ids[:15]}")

        if matched_ids:
            # Add them via selectize
            ids_to_add = matched_ids[:12]
            result = page.evaluate(f"""(ids) => {{
                const sel = document.querySelector('select.selectized, select[name="tag_id[]"]');
                if (!sel || !sel.selectize) return 'no selectize';
                sel.selectize.clear();
                sel.selectize.addItems(ids);
                return 'added ' + sel.selectize.items.length + ' skills';
            }}""", ids_to_add)
            log(f"    ✓ {result}")
            time.sleep(1)

            # Save
            if js_click_by_text(page, ["حفظ", "Save"]):
                time.sleep(2)
                log("  ✓ Skills saved")
            else:
                log("  ⚠ Skills save button not found")
    else:
        log("  ⚠ Selectize not found on this page — skills may need manual entry")
        log("  → Opening settings alternative...")
        page.goto("https://nafezly.com/settings", timeout=180000)
        time.sleep(3)
        snap(page, "nafezly_settings_alt")

    # ── 2C: Personal Data ──
    log("  Checking personal data...")
    wait_login(page, "https://nafezly.com/profile/personal-data")
    time.sleep(2)
    snap(page, "nafezly_personal_data")

    # Try to save (in case there are unsaved name/etc fields)
    if js_click_by_text(page, ["حفظ", "Save"]):
        time.sleep(2)
        log("  ✓ Personal data saved/verified")

    snap(page, "nafezly_profile_done")
    log("  ✅ Nafezly profile complete")
    time.sleep(2)


def create_nafezly_services(page):
    """Create 3 services on Nafezly with premium descriptions."""
    step(3, "Nafezly Services", "Creating 3 professional services")

    for i, svc in enumerate(NAFEZLY_SERVICES):
        log(f"\n  ── Service {i+1}/3: {svc['title'][:40]}...")

        page.goto("https://nafezly.com/service/create", timeout=180000)
        time.sleep(3)

        if "login" in page.url.lower():
            log("  ⏳ Login required...")
            for _ in range(60):
                time.sleep(1)
                if "login" not in page.url.lower():
                    break

        # Fill title
        r = js_set(page, "input[name='service_title']", svc['title'])
        log(f"    Title: {r}")
        time.sleep(1)

        # Select specialization = برمجة (ID 1)
        try:
            page.select_option("select[name='specialization_id']", svc['specialization'])
            log("    Specialization: برمجة")
            time.sleep(2)
        except Exception as e:
            log(f"    ⚠ Specialization select failed: {e}")

        # Auto-select first sub-specialization
        try:
            subs = page.evaluate("""() => {
                const sel = document.querySelector('select[name="sub_specialization_id"]');
                if (!sel) return [];
                return Array.from(sel.options).filter(o => o.value).map(o => ({v: o.value, t: o.textContent.trim().substring(0,40)}));
            }""")
            if subs:
                page.select_option("select[name='sub_specialization_id']", subs[0]['v'])
                log(f"    Sub-specialization: {subs[0]['t']}")
        except Exception as e:
            log(f"    ⚠ Sub-specialization failed: {e}")

        # Fill description
        full_desc = svc['desc'] + svc.get('long_desc', '')
        r = js_set(page, "textarea[name='service_description']", full_desc)
        log(f"    Description: {r} ({len(full_desc)} chars)")

        # Select period
        try:
            page.select_option("select[name='period']", svc['period'])
            log(f"    Period: {svc['period']} days")
        except Exception as e:
            log(f"    ⚠ Period failed: {e}")

        # Select price
        try:
            page.select_option("select[name='service_price']", svc['price'])
            log(f"    Price: ${svc['price']}")
        except Exception as e:
            log(f"    ⚠ Price failed: {e}")

        # Fill instructions
        r = js_set(page, "textarea[name='seller_instructions']", svc['instructions'])
        log(f"    Instructions: {r}")

        snap(page, f"service_{i+1}_filled")

        # SUBMIT — with user confirmation
        print(f"\n  ⏸ Service {i+1}: ready to submit — {svc['title'][:50]} (${svc['price']})")
        if not confirm("  Submit this service?", default_yes=True):
            log("    ⏩ Skipped by user")
            continue

        # Click submit button
        try:
            btn = page.locator("#submitEvaluation")
            if btn.is_visible():
                btn.click()
                time.sleep(4)
                log(f"    ✓ Service submitted! URL: {page.url[:100]}")
            else:
                # Try alternative submit
                if js_click_by_text(page, ["نشر", "إرسال", "Submit", "نشر الخدمة"]):
                    time.sleep(4)
                    log(f"    ✓ Submitted via text button. URL: {page.url[:100]}")
                else:
                    log("    ⚠ No submit button found — please check browser")
        except Exception as e:
            log(f"    ⚠ Submit error: {e}")

    log("  ✅ Nafezly services done")


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 3: MOSTAQL — COMPLETE PROFILE
# ═══════════════════════════════════════════════════════════════════════════
MOSTAQL_TITLE = "مطوّر أتمتة وذكاء اصطناعي | Python | n8n | OpenAI"

MOSTAQL_BIO = """السلام عليكم ورحمة الله وبركاته

مهندس أتمتة وذكاء اصطناعي، أبني أنظمة أتمتة بـ Python و n8n توفّر الوقت وتقلّل العمل اليدوي المتكرّر. أقدّم حلولاً عملية للشركات الصغيرة وأصحاب المشاريع.

ماذا أبنى بالضبط:
• Workflows في n8n: استقبال بيانات من نماذج ويب ← معالجتها بالذكاء الاصطناعي ← إرسال نتائج إلى Slack / Google Sheets / Airtable
• وكلاء ذكاء اصطناعي (AI Agents): بوتات تفهم العربية والإنجليزية، ترد على العملاء، تؤهل العملاء المحتملين، وتصنف الرسائل
• تكاملات SaaS: ربط Google Workspace + Slack + Notion + Airtable + Salesforce مع بعضها
• أتمتة بريد إلكتروني: فرز، رد تلقائي، إنشاء تذاكر دعم
• بوتات محادثة: لتلغرام، واتساب، والموقع الإلكتروني — تعمل 24/7

أسلوبي:
1. أستمع جيداً لمشكلتك قبل أن أقدم الحل
2. أقدّم خطة عمل واضحة مع جدول زمني
3. أبنى وأختبر وأسلّم مع توثيق
4. أضمن رضاك بتعديلات مجانية بعد التسليم

أسعاري تنافسية وجودتي عالية — لأن هدفي بناء سمعة ممتازة بخدمة استثنائية."""

MOSTAQL_SKILLS = [
    "n8n", "Python", "OpenAI", "Automation", "Flask",
    "API Integration", "Chatbot", "Workflow", "Machine Learning",
    "Google Sheets", "Airtable", "Notion", "Slack", "Webhooks",
]

MOSTAQL_PORTFOLIO_ITEMS = [
    {
        "title": "AI Automation Engine — محرك أتمتة ذكي",
        "desc": "المشكلة: شركات تحتاج معالجة آلاف الطلبات يومياً — استجابة فورية لكل طلب دون تدخل بشري.\n\nالحل: محرك أتمتة ذاتي الاستضافة (Self-hosted) مبني بـ Python/Flask. يستقبل Webhooks من أي مصدر (نماذج ويب، تطبيقات، APIs)، يعالجها بسلسلة خطوات محددة في YAML، يستخدم OpenAI لتحليل النصوص وفهم المدخلات وتصنيفها، ويخزن النتائج في SQLite مع لوحة تحكم حية.\n\nأبرز الإنجازات:\n• معالجة 500+ طلب يومياً بدون تدخل\n• دقة تصنيف 95% باستخدام OpenAI\n• لوحة تحكم بتحديث لحظي\n• استضافة ذاتية — بدون رسوم سحابية\n\nالتقنيات: Python، Flask، SQLite، OpenAI، YAML، Webhooks\nالكود مفتوح المصدر على GitHub",
        "file": "portfolio_01.jpg",
        "url": "https://github.com/alaafathi/ai-automation-engine"
    },
    {
        "title": "n8n Automation Pipelines — خطوط أتمتة متكاملة",
        "desc": "المشكلة: فرق المبيعات تضيع وقتاً في تأهيل العملاء المحتملين يدوياً — استقبال الاستفسارات، تصنيفها، متابعتها.\n\nالحل: سير عمل مؤتمت بالكامل في n8n يربط 4 أنظمة في pipeline واحد:\n\nسير العمل:\n1. نموذج ويب (Google Forms / Typeform) → استقبال بيانات العميل\n2. OpenAI → تحليل دقيق للاحتياجات والاهتمامات\n3. Google Sheets → تسجيل وتصنيف العملاء\n4. Slack → إشعار فوري للفريق مع ملخص التحليل\n\nالنتيجة:\n• تأهيل العملاء أسرع بنسبة 80%\n• لا أخطاء بشرية في إدخال البيانات\n• متابعة فورية لكل عميل جديد\n\nالتقنيات: n8n، OpenAI، Google Sheets، Slack، Webhooks",
        "file": "portfolio_02.jpg",
        "url": "https://github.com/alaafathi"
    },
    {
        "title": "AI Chatbot Solution — بوت محادثة ذكي",
        "desc": "المشكلة: عملاء يرسلون أسئلة متكررة خارج أوقات الدوام — تأخير في الردود يؤدي إلى فقدان عملاء.\n\nالحل: بوت محادثة ذكي متعدد المنصات يعمل 24/7 ويدعم العربية والإنجليزية.\n\nالمميزات:\n• يفهم اللغة العربية الفصحى والعامية والإنجليزية\n• يرد فورياً على الأسئلة الشائعة (تدريب على قاعدة معرفة مخصصة)\n• يسجل العملاء المحتملين في CRM تلقائياً\n• يتصاعد للمندوب البشري عند الحاجة\n• يعمل على تلغرام + واتساب + الموقع الإلكتروني بنفس الذكاء\n\nالنتيجة:\n• ردود فورية 24/7 بدون تأخير\n• توفير 40+ ساعة عمل شهرياً\n• تحسين رضا العملاء وزيادة التحويلات\n\nالتقنيات: n8n، OpenAI GPT-4o، Telegram API، Website Widget، Python",
        "file": "portfolio_03.jpg",
        "url": "https://github.com/alaafathi"
    }
]


def _mostaql_login(page, password: str):
    """Login to Mostaql with parameterized JS (no injection risk)."""
    page.goto("https://mostaql.com/login", timeout=180000, wait_until="domcontentloaded")
    time.sleep(3)

    if "login" in page.url.lower():
        page.evaluate("""(args) => {
            const email = document.querySelector('input[type="email"]');
            if (email) { email.value = args.e; email.dispatchEvent(new Event('input',{bubbles:true})); }
        }""", {"e": EMAIL})
        page.evaluate("""(args) => {
            const pw = document.querySelector('input[type="password"]');
            if (pw) { pw.value = args.p; pw.dispatchEvent(new Event('input',{bubbles:true})); }
        }""", {"p": password})
        js_click_by_text(page, ["دخول", "Login", "تسجيل الدخول"])
        # Poll for login success instead of fixed sleep
        for _ in range(30):
            time.sleep(1)
            if "login" not in page.url.lower():
                break
        log(f"    Login result URL: {page.url[:80]}")


def fill_mostaql_profile(page):
    """Fill Mostaql profile: title, bio, skills, rate, links."""
    step(4, "Mostaql Profile", "Filling title, bio, skills, hourly rate")

    # Try to load password
    mostaql_password = ""
    if PASSWORD_FILE.exists():
        mostaql_password = PASSWORD_FILE.read_text(encoding="utf-8").strip()
    elif AUTO_MODE:
        log("  ⚠ No Mostaql password file found at Temp/mostaql_password.txt")
        log("  ✗ Cannot proceed with Mostaql in auto mode without saved password")
        log("  → To save password: echo 'YOUR_PASSWORD' > Temp/mostaql_password.txt")
        return  # Skip Mostaql if no password
    else:
        import getpass
        mostaql_password = getpass.getpass("Enter Mostaql password: ")

    # ── 4A: Login + Profile ──
    _mostaql_login(page, mostaql_password)
    wait_login(page, "https://mostaql.com/account/profile")
    snap(page, "mostaql_profile")

    # Detect form fields
    fields = page.evaluate("""() => {
        const els = document.querySelectorAll('input, textarea, select');
        return Array.from(els).filter(e => e.offsetParent !== null && (e.name || e.id || e.placeholder)).map(e => ({
            tag: e.tagName,
            name: e.name || '',
            id: e.id || '',
            type: e.type || e.tagName,
            ph: (e.placeholder || '').substring(0, 40),
            val: (e.value || '').substring(0, 30)
        }));
    }""")
    log(f"    Found {len(fields)} form fields")

    # Try to set title
    title_set = False
    for sel in ["input[name='title']", "input[placeholder*='مسمى' i]", "input[placeholder*='professional' i]"]:
        r = js_set(page, sel, MOSTAQL_TITLE)
        if r.startswith("OK"):
            log(f"    ✓ Title set via '{sel}'")
            title_set = True
            break
    if not title_set:
        log("    ⚠ Could not find title field")

    # Try to set bio
    bio_set = False
    for sel in ["textarea", "[contenteditable='true']"]:
        r = js_set(page, sel, MOSTAQL_BIO)
        if r.startswith("OK"):
            log(f"    ✓ Bio set via '{sel}' ({len(MOSTAQL_BIO)} chars)")
            bio_set = True
            break
    if not bio_set:
        log("    ⚠ Could not find bio field")

    # Save profile
    time.sleep(1)
    if js_click_by_text(page, ["حفظ", "Save", "تحديث", "تحديث الملف"]):
        time.sleep(3)
        log("  ✓ Profile saved")
    else:
        log("  ⚠ Profile save button not found")

    snap(page, "mostaql_profile_saved")

    # ── 4B: Onboarding profile (if still needed) ──
    page.goto("https://mostaql.com/onboarding/profile", timeout=180000, wait_until="domcontentloaded")
    time.sleep(3)
    if "onboarding" in page.url:
        log("  → Still on onboarding — completing...")
        for sel in ["input[name='title'], input[placeholder*='مسمى']"]:
            js_set(page, sel, MOSTAQL_TITLE)
        for sel in ["textarea", "[contenteditable='true']"]:
            js_set(page, sel, MOSTAQL_BIO)
        time.sleep(1)
        js_click_by_text(page, ["حفظ", "التالي", "Next", "Save"])
        time.sleep(3)
        snap(page, "mostaql_onboarding_saved")

    # ── 4C: Open skills/portfolio page ──
    log("  Navigating to skills/portfolio page...")
    page.goto("https://mostaql.com/account/portfolio", timeout=180000, wait_until="domcontentloaded")
    time.sleep(4)
    snap(page, "mostaql_skills_portfolio")

    if "login" in page.url.lower():
        _mostaql_login(page, mostaql_password)
        page.goto("https://mostaql.com/account/portfolio", timeout=180000, wait_until="domcontentloaded")
        time.sleep(4)

    # Inspect the actual page to see what's available
    page_html_preview = page.content()[:3000]
    (TEMP / "mostaql_portfolio_page.txt").write_text(page_html_preview, encoding="utf-8")

    # Look for skill/tag input
    skill_input = page.query_selector("input[placeholder*='skill' i], input[placeholder*='مهار' i], input[type='text'].tags-input, .tags input, [class*='tag'] input")
    if skill_input:
        log("  Adding skills via tag input...")
        for sk in MOSTAQL_SKILLS:
            try:
                skill_input.fill(sk)
                time.sleep(0.3)
                page.keyboard.press("Enter")
                time.sleep(0.3)
                log(f"      Added: {sk}")
            except:
                log(f"      ⚠ Failed: {sk}")
    else:
        log("    ⚠ No skill tag input found — check if skills section exists on this page")

    # ── 4D: Set hourly rate ──
    log("  Setting hourly rate...")
    for sel in ["input[name='hourly_rate']", "input[name='rate']", "input[placeholder*='hourly' i]", "input[placeholder*='سعر' i]"]:
        r = js_set(page, sel, "10")
        if r.startswith("OK"):
            log(f"    ✓ Hourly rate set: $10/hr")
            break

    # ── 4E: Set GitHub link ──
    log("  Setting links...")
    for sel in ["input[name='github']", "input[placeholder*='github' i]", "input[name='website']", "input[type='url']", "input[placeholder*='link' i]", "input[placeholder*='رابط' i]"]:
        r = js_set(page, sel, "https://github.com/alaafathi")
        if r.startswith("OK"):
            log(f"    ✓ GitHub link set")
            break

    # ── 4F: Save ──
    time.sleep(1)
    if js_click_by_text(page, ["حفظ", "Save", "تحديث", "تحديث الملف"]):
        time.sleep(2)
        log("  ✓ Profile saved")

    snap(page, "mostaql_profile_complete")
    log("  ✅ Mostaql profile complete")


def add_mostaql_portfolio(page):
    """Add 3 portfolio items to Mostaql with premium images."""
    step(5, "Mostaql Portfolio", "Adding 3 portfolio items with images")

    for i, item in enumerate(MOSTAQL_PORTFOLIO_ITEMS):
        log(f"\n  ── Portfolio {i+1}/3: {item['title'][:40]}...")

        # Try onboarding wizard first
        wait_login(page, "https://mostaql.com/onboarding/portfolio")
        snap(page, f"mostaql_portfolio_{i+1}_form")

        is_onboarding = "onboarding" in page.url
        if is_onboarding:
            log(f"    Onboarding wizard mode")
        else:
            log(f"    Account/portfolio edit mode")
            # Fallback to direct URL
            page.goto("https://mostaql.com/account/portfolio", timeout=180000, wait_until="domcontentloaded")
            time.sleep(4)
            snap(page, f"mostaql_portfolio_{i+1}_alt")

        # Detect visible fields on the current page/step
        visible_fields = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('input:not([type=hidden]), textarea, select'))
                .filter(el => el.offsetParent !== null && (el.name || el.id || el.placeholder))
                .map(el => ({tag: el.tagName, name: el.name || '', id: el.id || '', type: el.type, ph: (el.placeholder||'').substring(0,30)}));
        }""")
        log(f"    Visible form fields: {len(visible_fields)}")
        for f in visible_fields:
            log(f"      [{f['tag']}] name='{f['name']}' id='{f['id']}' ph='{f['ph']}' ({f['type']})")

        # Try filling title field
        title_set = False
        for sel in ["input[name='title']", "input[placeholder*='title' i]", "input[placeholder*='عنوان' i]"]:
            r = js_set(page, sel, item['title'])
            if r.startswith("OK"):
                title_set = True
                break
        log(f"    Title: {'✓' if title_set else '⚠ not found'}")

        # Try filling description
        desc_set = False
        for sel in ["textarea", "[contenteditable='true']"]:
            r = js_set(page, sel, item['desc'])
            if r.startswith("OK"):
                desc_set = True
                break
        log(f"    Description: {'✓' if desc_set else '⚠ not found'} ({len(item['desc'])} chars)")

        # Try filling URL/link field
        url_set = False
        for sel in ["input[name='url']", "input[placeholder*='url' i]", "input[placeholder*='رابط' i]", "input[type='url']"]:
            r = js_set(page, sel, item['url'])
            if r.startswith("OK"):
                url_set = True
                break
        log(f"    URL: {'✓' if url_set else '⚠ not found'}")

        # Upload image
        img_path = DESIGNS / item['file']
        if img_path.exists():
            try:
                file_input = page.locator("input[type='file']").first
                if file_input.is_visible():
                    file_input.set_input_files(str(img_path))
                    time.sleep(2)
                    log(f"    ✓ Image uploaded: {item['file']}")
                else:
                    log(f"    ⚠ File input not visible")
            except Exception as e:
                log(f"    ⚠ Image upload error: {e}")
        else:
            log(f"    ⚠ Image not found: {item['file']}")

        # Check terms checkbox
        checkboxes = page.locator("input[type='checkbox']")
        count = checkboxes.count()
        for ci in range(count):
            try:
                chk = checkboxes.nth(ci)
                if chk.is_visible() and not chk.is_checked():
                    chk.check()
                    log(f"    ✓ Terms checkbox #{ci+1} checked")
            except:
                pass

        snap(page, f"mostaql_portfolio_{i+1}_filled")

        # SUBMIT — with user confirmation
        print(f"\n  ⏸ Portfolio {i+1}: ready to submit — {item['title'][:50]}")
        if not confirm("  Submit this portfolio item?", default_yes=True):
            log("    ⏩ Skipped by user")
            continue

        if js_click_by_text(page, ["إضافة", "حفظ", "Submit", "أضف", "التالي", "إضافة المشروع"]):
            time.sleep(3)
            log(f"    ✓ Portfolio {i+1} submitted! URL: {page.url[:80]}")
        else:
            log(f"    ⚠ No submit button found — please check browser")

        snap(page, f"mostaql_portfolio_{i+1}_done")

    log("  ✅ Mostaql portfolio complete")


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    log("═" * 60)
    log("START: Complete Arabic Profiles Automation")
    log(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log("═" * 60)

    # ── Step 1: Generate images ──
    print("\n" + "─" * 50)
    print("  STEP 0/5: Generate premium design images")
    print("  (Run this first — it's quick and headless)")
    print("─" * 50)
    if confirm("  Generate images?", default_yes=True):
        generate_images()
    else:
        log("  ⏩ Image generation skipped")

    # ── Steps 2-5: Run with browser ──
    print("\n" + "─" * 50)
    print("  MAIN: Browser automation for profiles + services")
    if AUTO_MODE:
        print("  ⚡ AUTO MODE — everything will run without prompts")
    else:
        print("  You will be prompted before each submit. Type 'skip' to skip.")
    print("─" * 50)
    confirm_enter("Press ENTER to START the browser")

    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()

    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=BRAVE_PROFILE,
        executable_path=BRAVE_EXE,
        headless=False,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        viewport={"width": 1366, "height": 768},
    )
    page = ctx.new_page()
    page.set_default_timeout(180000)

    try:
        # ═══ NAFEZLY ═══
        print("\n" + "═" * 50)
        print("  SECTION 1: NAFEZLY PROFILE")
        print("═" * 50)
        confirm_enter("Press ENTER to start Nafezly profile fill")

        fill_nafezly_profile(page)

        print("\n" + "═" * 50)
        print("  SECTION 2: NAFEZLY SERVICES")
        print("═" * 50)
        if confirm("  → Create 3 Nafezly services?", default_yes=True):
            create_nafezly_services(page)

        # ═══ MOSTAQL ═══
        print("\n" + "═" * 50)
        print("  SECTION 3: MOSTAQL PROFILE")
        print("═" * 50)
        confirm_enter("Press ENTER to start Mostaql profile fill")

        fill_mostaql_profile(page)

        print("\n" + "═" * 50)
        print("  SECTION 4: MOSTAQL PORTFOLIO")
        print("═" * 50)
        if confirm("  → Add 3 portfolio items to Mostaql?", default_yes=True):
            add_mostaql_portfolio(page)

        log("═" * 60)
        log("ALL DONE! Browser stays open for your review.")
        log("═" * 60)

    except Exception as e:
        import traceback
        log(f"ERROR: {e}")
        traceback.print_exc()
        log("Browser stays open for debugging.")
    finally:
        # Keep browser alive
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            pass
        finally:
            ctx.close()
            pw.stop()


if __name__ == "__main__":
    # ── Parse args ──
    parser = argparse.ArgumentParser(description="Complete Arabic Profiles Automation")
    parser.add_argument("--auto", action="store_true", help="Run fully automatic without user prompts")
    args = parser.parse_args()
    if args.auto:
        AUTO_MODE = True
        log("AUTO MODE enabled — no user interaction required")

    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        log("ABORTED by user")
        sys.exit(1)
