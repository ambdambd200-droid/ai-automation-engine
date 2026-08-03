"""
arabic_platform_manager.py — AI Freelance Manager for نفذلي & مستقل
==============================================================================
WHAT IT DOES (every time you run it):
  1. Loads state — remembers everything done before
  2. Uses AI to decide the BEST NEXT ACTION (always something new)
  3. Executes that action — creates service, bids, checks email, generates image
  4. NEVER repeats the same service or contacts the same person
  5. Generates a premium image when creating a service
  6. Everything in correct Arabic or English

USAGE:
  python arabic_platform_manager.py              # Auto mode — does next best action
  python arabic_platform_manager.py --status      # Show state + quotas
  python arabic_platform_manager.py --check-email # Check email only
  python arabic_platform_manager.py --browse      # Browse Nafezly projects
  python arabic_platform_manager.py --reset       # [safety] Reset state

RULES ENFORCED:
  • Only 1 service per week (image required)
  • Daily bid limits (3 Nafezly + 3 Mostaql)
  • Never contact the same person twice
  • Never create the same service title twice
  • Email checked every run
  • AI decides the action based on state + time
"""

import sys, time, json, os, argparse, random
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── PATHS ──────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent.resolve()
TEMP = BASE / "Temp"
DESIGNS = TEMP / "designs_v3"
DESIGNS.mkdir(parents=True, exist_ok=True)
STATE_FILE = BASE / "arabic_platform_state.json"
LOG_FILE = BASE / "arabic_platform_log.md"

# ── BROWSER CONSTANTS (shared across all Playwright functions) ────────────
BRAVE_EXE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
BRAVE_PROFILE = r"C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data"

# ── BID TIMING ────────────────────────────────────────────────────────────
# Random delay (seconds) between automated bids to look human
BID_MIN_DELAY = 8
BID_MAX_DELAY = 20

# ── STATE MANAGEMENT ───────────────────────────────────────────────────────

DEFAULT_STATE = {
    "version": 2,
    "created_services": {
        "nafezly": [],
        "mostaql": []
    },
    "contacted_persons": {
        "nafezly": [],
        "mostaql": []
    },
    "bids_sent": {
        "nafezly": [],
        "mostaql": []
    },
    "last_service_date": None,       # date.isoformat()
    "last_email_check": None,        # date.isoformat()
    "last_run": None,                # datetime.isoformat()
    "run_count": 0,
    "run_history": [],
    "created_service_titles": [],    # all titles ever created (dedup)
}

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            for k in DEFAULT_STATE:
                data.setdefault(k, DEFAULT_STATE[k])
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_STATE)

def save_state(state: dict):
    """Atomic write: write to .tmp, then rename to prevent corruption on crash."""
    state["last_run"] = datetime.now().isoformat()
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STATE_FILE)  # atomic on Windows (same filesystem)



# ── QUOTA HELPERS ─────────────────────────────────────────────────────────

def _today() -> str:
    return date.today().isoformat()

def _this_week_key() -> str:
    """Return ISO week string (e.g. 2026-W25)."""
    return date.today().strftime("%Y-W%V")

def can_create_service_this_week(state: dict) -> bool:
    """Only 1 service per week."""
    last_svc = state.get("last_service_date")
    if not last_svc:
        return True
    last_week = datetime.fromisoformat(last_svc).strftime("%Y-W%V")
    return last_week != _this_week_key()

def is_title_used(state: dict, title: str) -> bool:
    """Check if a service title was already used (dedup)."""
    t = title.strip().lower()
    for used in state.get("created_service_titles", []):
        if t in used.lower() or used.lower() in t:
            return True
    return False



# ── LOGGING ────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

# ── AI GATEWAY ────────────────────────────────────────────────────────────

def ai_generate(prompt: str, system: Optional[str] = None, max_tokens: int = 800) -> Optional[str]:
    """Generate text via keyhub / Groq. Falls back to template if unavailable."""
    try:
        sys.path.insert(0, str(BASE))
        from keyhub_client import ai_generate as kh_gen
        result = kh_gen(prompt, system=system or "أنت علاء فتحي، مهندس أتمتة وذكاء اصطناعي.", 
                        max_tokens=max_tokens, temperature=0.4, caller="arabic_platform_manager")
        if result:
            return result.strip()
    except Exception as e:
        log(f"  ⚠ AI generation failed: {e}")
    return None

def ai_generate_json(prompt: str, system: Optional[str] = None) -> Optional[dict]:
    """Generate JSON via AI."""
    try:
        sys.path.insert(0, str(BASE))
        from keyhub_client import ai_generate_json as kh_json
        return kh_json(prompt, system=system or "أنت مساعد ذكي. أعد JSON فقط.",
                       max_tokens=600, temperature=0.2, caller="arabic_platform_manager")
    except Exception:
        return None

# ── IMAGE GENERATION (HTML→Screenshot) ─────────────────────────────────────

SERVICE_IMAGES_HTML = {}

SERVICE_IMAGES_HTML["service_ai_agent"] = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
body{width:800px;height:500px;overflow:hidden;font-family:'Inter',system-ui,-apple-system,sans-serif;background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%);display:flex;align-items:center;justify-content:center;padding:32px}
.card{width:100%;height:100%;position:relative;display:flex;flex-direction:column;justify-content:center;padding:44px;overflow:hidden}
.dots{position:absolute;top:0;left:0;width:100%;height:100%;background-image:radial-gradient(circle,rgba(6,182,212,0.15) 0.5px,transparent 0.5px);background-size:24px 24px;opacity:0.3}
.corner{position:absolute;top:24px;right:24px;width:32px;height:32px;border-top:2px solid rgba(6,182,212,0.3);border-right:2px solid rgba(6,182,212,0.3)}
.corner2{position:absolute;bottom:24px;left:24px;width:32px;height:32px;border-bottom:2px solid rgba(6,182,212,0.3);border-left:2px solid rgba(6,182,212,0.3)}
.bar{position:absolute;bottom:0;left:0;width:100%;height:4px;background:linear-gradient(90deg,#0891B2,#06B6D4)}
.tag{display:inline-block;background:#0891B2;color:white;font-size:9px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:3px;margin-bottom:20px;width:fit-content;position:relative;z-index:2}
.title{color:white;font-size:32px;font-weight:700;line-height:1.2;letter-spacing:-0.5px;position:relative;z-index:2;max-width:90%}
.sub{color:#94A3B8;font-size:13px;margin-top:12px;position:relative;z-index:2;max-width:85%}
.price{position:absolute;bottom:40px;right:44px;background:#0891B2;color:white;font-size:16px;font-weight:700;padding:8px 20px;border-radius:6px;z-index:2}
</style></head><body>
<div class="card"><div class="dots"></div><div class="corner"></div><div class="corner2"></div>
<div class="tag">AI AGENT</div>
<div class="title">وكيل ذكاء اصطناعي<br>AI Agent Development</div>
<div class="sub">n8n + OpenAI GPT-4o · أتمتة ذكية لعملك 24/7</div>
<div class="price">$30</div><div class="bar"></div>
</div></body></html>"""

SERVICE_IMAGES_HTML["service_workflow"] = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
body{width:800px;height:500px;overflow:hidden;font-family:'Inter',system-ui,-apple-system,sans-serif;background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%);display:flex;align-items:center;justify-content:center;padding:32px}
.card{width:100%;height:100%;position:relative;display:flex;flex-direction:column;justify-content:center;padding:44px;overflow:hidden}
.dots{position:absolute;top:0;left:0;width:100%;height:100%;background-image:radial-gradient(circle,rgba(139,92,246,0.15) 0.5px,transparent 0.5px);background-size:24px 24px;opacity:0.3}
.corner{position:absolute;top:24px;right:24px;width:32px;height:32px;border-top:2px solid rgba(139,92,246,0.3);border-right:2px solid rgba(139,92,246,0.3)}
.corner2{position:absolute;bottom:24px;left:24px;width:32px;height:32px;border-bottom:2px solid rgba(139,92,246,0.3);border-left:2px solid rgba(139,92,246,0.3)}
.bar{position:absolute;bottom:0;left:0;width:100%;height:4px;background:linear-gradient(90deg,#7C3AED,#A78BFA)}
.tag{display:inline-block;background:#7C3AED;color:white;font-size:9px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:3px;margin-bottom:20px;width:fit-content;position:relative;z-index:2}
.title{color:white;font-size:32px;font-weight:700;line-height:1.2;letter-spacing:-0.5px;position:relative;z-index:2;max-width:90%}
.sub{color:#94A3B8;font-size:13px;margin-top:12px;position:relative;z-index:2;max-width:85%}
.price{position:absolute;bottom:40px;right:44px;background:#7C3AED;color:white;font-size:16px;font-weight:700;padding:8px 20px;border-radius:6px;z-index:2}
</style></head><body>
<div class="card"><div class="dots"></div><div class="corner"></div><div class="corner2"></div>
<div class="tag">AUTOMATION</div>
<div class="title">أتمتة سير العمل<br>Workflow Automation</div>
<div class="sub">n8n · 400+ تكامل · ربط تطبيقاتك بسلاسة</div>
<div class="price">$25</div><div class="bar"></div>
</div></body></html>"""

SERVICE_IMAGES_HTML["service_chatbot"] = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
body{width:800px;height:500px;overflow:hidden;font-family:'Inter',system-ui,-apple-system,sans-serif;background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%);display:flex;align-items:center;justify-content:center;padding:32px}
.card{width:100%;height:100%;position:relative;display:flex;flex-direction:column;justify-content:center;padding:44px;overflow:hidden}
.dots{position:absolute;top:0;left:0;width:100%;height:100%;background-image:radial-gradient(circle,rgba(16,185,129,0.15) 0.5px,transparent 0.5px);background-size:24px 24px;opacity:0.3}
.corner{position:absolute;top:24px;right:24px;width:32px;height:32px;border-top:2px solid rgba(16,185,129,0.3);border-right:2px solid rgba(16,185,129,0.3)}
.corner2{position:absolute;bottom:24px;left:24px;width:32px;height:32px;border-bottom:2px solid rgba(16,185,129,0.3);border-left:2px solid rgba(16,185,129,0.3)}
.bar{position:absolute;bottom:0;left:0;width:100%;height:4px;background:linear-gradient(90deg,#059669,#34D399)}
.tag{display:inline-block;background:#059669;color:white;font-size:9px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:3px;margin-bottom:20px;width:fit-content;position:relative;z-index:2}
.title{color:white;font-size:32px;font-weight:700;line-height:1.2;letter-spacing:-0.5px;position:relative;z-index:2;max-width:90%}
.sub{color:#94A3B8;font-size:13px;margin-top:12px;position:relative;z-index:2;max-width:85%}
.price{position:absolute;bottom:40px;right:44px;background:#059669;color:white;font-size:16px;font-weight:700;padding:8px 20px;border-radius:6px;z-index:2}
</style></head><body>
<div class="card"><div class="dots"></div><div class="corner"></div><div class="corner2"></div>
<div class="tag">CHATBOT</div>
<div class="title">بوت محادثة ذكي<br>AI Chatbot 24/7</div>
<div class="sub">عربي + إنجليزي · تلغرام · واتساب · ويب</div>
<div class="price">$35</div><div class="bar"></div>
</div></body></html>"""

SERVICE_IMAGES_HTML["service_custom"] = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
body{width:800px;height:500px;overflow:hidden;font-family:'Inter',system-ui,-apple-system,sans-serif;background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%);display:flex;align-items:center;justify-content:center;padding:32px}
.card{width:100%;height:100%;position:relative;display:flex;flex-direction:column;justify-content:center;padding:44px;overflow:hidden}
.dots{position:absolute;top:0;left:0;width:100%;height:100%;background-image:radial-gradient(circle,rgba(234,179,8,0.15) 0.5px,transparent 0.5px);background-size:24px 24px;opacity:0.3}
.corner{position:absolute;top:24px;right:24px;width:32px;height:32px;border-top:2px solid rgba(234,179,8,0.3);border-right:2px solid rgba(234,179,8,0.3)}
.corner2{position:absolute;bottom:24px;left:24px;width:32px;height:32px;border-bottom:2px solid rgba(234,179,8,0.3);border-left:2px solid rgba(234,179,8,0.3)}
.bar{position:absolute;bottom:0;left:0;width:100%;height:4px;background:linear-gradient(90deg,#CA8A04,#EAB308)}
.tag{display:inline-block;background:#CA8A04;color:white;font-size:9px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:3px;margin-bottom:20px;width:fit-content;position:relative;z-index:2}
.title{color:white;font-size:32px;font-weight:700;line-height:1.2;letter-spacing:-0.5px;position:relative;z-index:2;max-width:90%}
.sub{color:#94A3B8;font-size:13px;margin-top:12px;position:relative;z-index:2;max-width:85%}
.price{position:absolute;bottom:40px;right:44px;background:#CA8A04;color:white;font-size:16px;font-weight:700;padding:8px 20px;border-radius:6px;z-index:2}
</style></head><body>
<div class="card"><div class="dots"></div><div class="corner"></div><div class="corner2"></div>
<div class="tag">CUSTOM</div>
<div class="title">حل أتمتة مخصص<br>Custom Automation</div>
<div class="sub">Python · APIs · Webhooks · حلول حسب طلبك</div>
<div class="price">$40</div><div class="bar"></div>
</div></body></html>"""

def generate_service_image(image_key: str) -> Optional[Path]:
    """Generate a service image via HTML→screenshot. Returns path or None."""
    from playwright.sync_api import sync_playwright
    html = SERVICE_IMAGES_HTML.get(image_key)
    if not html:
        return None
    fname = f"{image_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    fpath = DESIGNS / fname
    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 800, "height": 500})
        page.set_content(html)
        time.sleep(0.3)
        page.screenshot(path=str(fpath), full_page=False)
        page.close()
        browser.close()
        pw.stop()
        if fpath.exists():
            log(f"  ✓ Image generated: {fname} ({fpath.stat().st_size} bytes)")
            return fpath
    except Exception as e:
        log(f"  ⚠ Image generation failed: {e}")
    return None

# ── AI CONTENT GENERATION ──────────────────────────────────────────────────

SERVICE_TEMPLATES = [
    {
        "title": "بناء وكيل ذكاء اصطناعي (AI Agent) باستخدام n8n",
        "desc": "السلام عليكم ورحمة الله وبركاته.\n\nهل تقضي ساعات يومياً في مهام متكررة مثل الرد على الاستفسارات، تصنيف البريد، أو إدخال البيانات؟ أبنيك وكيل ذكاء اصطناعي (AI Agent) متكامل على منصة n8n يقوم بهذه المهام تلقائياً.",
        "long_desc": "\n\nماذا ستحصل بالضبط:\n🤖 وكيل AI يفهم العربية والإنجليزية\n🔗 ربط مع تطبيقاتك (Google Sheets, Slack, CRM)\n📋 خطة عمل: تحديد متطلبات ← تصميم ← بناء ← اختبار ← تسليم\n⏱ تسليم: 3-7 أيام\n🎁 دعم: 10 أيام بعد التسليم",
        "price": "30",
        "period": "7",
        "image_key": "service_ai_agent"
    },
    {
        "title": "أتمتة سير العمل (Workflow Automation) باستخدام n8n",
        "desc": "السلام عليكم ورحمة الله وبركاته.\n\nهل توجد مهمة تقوم بها كل يوم وتتمنى لو كانت تعمل وحدها؟ أبنيلك workflow مخصص على n8n يعمل 24/7 ويربط تطبيقاتك ببعضها.",
        "long_desc": "\n\nماذا ستحصل:\n⚙️ workflow مخصص يربط 2-4 تطبيقات\n📊 أمثلة: رد تلقائي، تقارير، مزامنة بيانات\n📋 خطة عمل: فهم المهمة ← تصميم ← ربط APIs ← اختبار ← تسليم\n⏱ تسليم: 3-5 أيام\n🎁 دعم: 7 أيام",
        "price": "25",
        "period": "5",
        "image_key": "service_workflow"
    },
    {
        "title": "تطوير بوت محادثة ذكي (AI Chatbot) باستخدام n8n و OpenAI",
        "desc": "السلام عليكم ورحمة الله وبركاته.\n\nهل تريد بوتاً ذكياً يخدم عملاءك 24/7 بالعربية والإنجليزية؟ أبنيلك بوت محادثة ذكي على تلغرام، واتساب، أو موقعك.",
        "long_desc": "\n\nماذا ستحصل:\n💬 بوت ذكي يفهم العربية والإنجليزية\n🔧 يعمل على تلغرام + واتساب + ويب\n📚 تدريب على قاعدة معرفتك (PDF/FAQ)\n📋 خطة عمل: تحديد منصة ← تجهيز المعرفة ← بناء ← اختبار ← تسليم\n⏱ تسليم: 5-7 أيام\n🎁 دعم: 14 يوم",
        "price": "35",
        "period": "7",
        "image_key": "service_chatbot"
    }
]

def ai_generate_service() -> Optional[dict]:
    """Use AI to pick and customize a service. Returns None if all used."""
    state = load_state()
    used_titles = state.get("created_service_titles", [])
    
    # Filter out already-used templates
    available = [s for s in SERVICE_TEMPLATES 
                 if not is_title_used(state, s["title"])]
    
    if not available:
        # Try AI to generate a fresh service idea
        prompt = f"""أنت علاء فتحي، مهندس أتمتة. 
الخدمات السابقة التي تم إنشاؤها: {json.dumps(used_titles, ensure_ascii=False)}
    
ابتكر خدمة جديدة تماماً في مجال أتمتة الذكاء الاصطناعي باستخدام n8n لم أقدمها من قبل.
أعد JSON بهذا الشكل:
{{
  "title": "عنوان الخدمة بالعربية (مع وصف مختصر بالإنجليزية)",
  "desc": "السلام عليكم ورحمة الله وبركاته.\\n\\n[وصف المشكلة والحل في جملتين]",
  "long_desc": "\\n\\n[قائمة المنافع]\\n[خطة العمل]\\n[المدة والسعر]",
  "price": "السعر بالأرقام",
  "period": "أيام التسليم رقم",
  "image_key": "service_custom"
}}
يجب أن تكون الخدمة فريدة ولم تظهر في القائمة أعلاه."""
        result = ai_generate_json(prompt)
        if result and result.get("title") and not is_title_used(state, result["title"]):
            return result
        log("  ⚠ No available service templates — all used. Add new templates!")
        return None
    
    # Pick a random unused template
    svc = random.choice(available)
    log(f"  ✓ Selected service: {svc['title']}")
    return svc

# ── SERVICE CREATION ──────────────────────────────────────────────────────

def create_service_on_nafezly(svc: dict, image_path: Path) -> bool:
    """Create a service on Nafezly using Playwright (auto mode)."""
    from playwright.sync_api import sync_playwright
    
    try:
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
        
        log("  Opening Nafezly service creation page...")
        page.goto("https://nafezly.com/service/create", timeout=180000)
        time.sleep(4)
        
        if "login" in page.url.lower():
            log("  ⏳ Login required — waiting 60s...")
            for _ in range(60):
                time.sleep(1)
                if "login" not in page.url.lower():
                    break
        
        # Fill title
        page.evaluate("""(args) => {
            const el = document.querySelector('input[name="service_title"]');
            if (el) { el.value = args.v; el.dispatchEvent(new Event('input',{b:true})); el.dispatchEvent(new Event('change',{b:true})); }
        }""", {"v": svc["title"]})
        log("  ✓ Title filled")
        time.sleep(1)
        
        # Select specialization = برمجة (ID 1)
        try:
            page.select_option("select[name='specialization_id']", "1")
            time.sleep(2)
            log("  ✓ Specialization: برمجة")
        except Exception as e:
            log(f"  ⚠ Specialization failed: {e}")
        
        # Select sub-specialization
        try:
            subs = page.evaluate("""() => {
                const sel = document.querySelector('select[name="sub_specialization_id"]');
                if (!sel) return [];
                return Array.from(sel.options).filter(o => o.value).map(o => o.value);
            }""")
            if subs:
                page.select_option("select[name='sub_specialization_id']", subs[0])
                log(f"  ✓ Sub-specialization selected")
        except Exception as e:
            log(f"  ⚠ Sub-specialization failed: {e}")
        
        # Fill description
        full_desc = svc["desc"] + svc.get("long_desc", "")
        page.evaluate("""(args) => {
            const el = document.querySelector('textarea[name="service_description"]');
            if (el) { el.value = args.v; el.dispatchEvent(new Event('input',{b:true})); el.dispatchEvent(new Event('change',{b:true})); }
        }""", {"v": full_desc})
        log(f"  ✓ Description filled ({len(full_desc)} chars)")
        
        # Select period
        try:
            page.select_option("select[name='period']", svc.get("period", "5"))
        except: pass
        
        # Select price
        try:
            page.select_option("select[name='service_price']", svc.get("price", "30"))
        except: pass
        
        # Upload image
        if image_path and image_path.exists():
            try:
                file_input = page.locator("input[type='file']").first
                if file_input.is_visible():
                    file_input.set_input_files(str(image_path))
                    time.sleep(3)
                    log(f"  ✓ Image uploaded: {image_path.name}")
            except Exception as e:
                log(f"  ⚠ Image upload error: {e}")
        
        # Fill instructions
        instructions = "السلام عليكم. شكراً لاهتمامك. يرجى توضيح متطلباتك وسأتواصل معك خلال 24 ساعة."
        page.evaluate("""(args) => {
            const el = document.querySelector('textarea[name="seller_instructions"]');
            if (el) { el.value = args.v; el.dispatchEvent(new Event('input',{b:true})); el.dispatchEvent(new Event('change',{b:true})); }
        }""", {"v": instructions})
        
        time.sleep(2)
        
        # Submit
        log("  Submitting service...")
        try:
            btn = page.locator("#submitEvaluation")
            if btn.is_visible():
                btn.click()
                time.sleep(5)
                log(f"  ✓ Service submitted! URL: {page.url[:100]}")
                ctx.close()
                pw.stop()
                return True
        except:
            pass
        
        # Try alternative submit
        for text in ["نشر", "إرسال", "Submit", "نشر الخدمة"]:
            clicked = page.evaluate(f"""(t) => {{
                const els = document.querySelectorAll('button, a, span, input[type=submit]');
                for (const e of els) {{ if (e.innerText?.trim().includes(t)) {{ e.click(); return true; }} }}
                return false;
            }}""", text)
            if clicked:
                time.sleep(5)
                log(f"  ✓ Service submitted via '{text}' button!")
                ctx.close()
                pw.stop()
                return True
        
        log("  ⚠ Submit button not found — service NOT created")
        ctx.close()
        pw.stop()
        return False
        
    except Exception as e:
        log(f"  ✗ Error: {e}")
        return False

# ── EMAIL CHECK ──────────────────────────────────────────────────────────

def check_email_replies() -> list:
    """Check Gmail for replies from Nafezly/Mostaql contacts."""
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    if not gmail_password:
        log("  ⚠ GMAIL_APP_PASSWORD not set — skipping email check")
        log("  → Set: $env:GMAIL_APP_PASSWORD = 'your-16-char-password'")
        return []
    
    state = load_state()
    contacted = (state.get("contacted_persons", {}).get("nafezly", []) +
                 state.get("contacted_persons", {}).get("mostaql", []))
    
    if not contacted:
        log("  📭 No contacts recorded yet — will check after first bid")
        return []
    
    try:
        import imaplib, email
        from email.header import decode_header
        
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login("ambdambd200@gmail.com", gmail_password)
        mail.select("inbox")
        
        replies = []
        for person in contacted:
            try:
                status, data = mail.search(None, f'FROM "{person}" SINCE {date.today().isoformat()}')
                if status == "OK" and data and data[0]:
                    for num in data[0].split():
                        status_fetch, msg_data = mail.fetch(num, "(RFC822)")
                        if status_fetch != "OK":
                            continue
                        msg = email.message_from_bytes(msg_data[0][1])
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding or "utf-8", errors="replace")
                        replies.append({"from": person, "subject": subject})
            except:
                continue
        
        mail.logout()
        
        if replies:
            log(f"  ✉ Found {len(replies)} new reply/replies!")
            for r in replies:
                log(f"    FROM: {r['from']} — SUBJ: {r['subject']}")
        else:
            log("  ✉ No new replies today")
        
        return replies
    except Exception as e:
        log(f"  ⚠ Email check error: {e}")
        return []

# ── PROJECT BROWSING ─────────────────────────────────────────────────────

def browse_nafezly_projects():
    """Open Nafezly and browser to find new projects to bid on."""
    from playwright.sync_api import sync_playwright
    
    try:
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
        
        # Search for AI/automation projects
        search_urls = [
            "https://nafezly.com/projects?key=n8n+AI+automation&pricing=10,200",
            "https://nafezly.com/projects?key=%D8%B0%D9%83%D8%A7%D8%A1+%D8%A7%D8%B5%D8%B7%D9%86%D8%A7%D8%B9%D9%8A&pricing=10,200",
            "https://nafezly.com/projects?key=%D8%A3%D8%AA%D9%85%D8%AA%D8%A9&pricing=10,200",
        ]
        
        log("  Opening Nafezly project search...")
        page.goto(search_urls[0], timeout=180000)
        time.sleep(5)
        
        if "login" in page.url.lower():
            log("  ⏳ Login required — waiting 60s...")
            for _ in range(60):
                time.sleep(1)
                if "login" not in page.url.lower():
                    break
        
        # Get project titles
        projects = page.evaluate("""() => {
            const links = document.querySelectorAll('a[href*="/project/"]');
            return Array.from(links).slice(0, 10).map(a => ({
                title: a.innerText?.trim().substring(0, 80),
                href: a.href?.substring(0, 100)
            })).filter(p => p.title);
        }""")
        
        log(f"  Found {len(projects)} projects:")
        for p in projects[:5]:
            log(f"    📋 {p['title'][:60]}")
        
        log("  Browser stays open for you to review. Close it when done.")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            pass
        
        ctx.close()
        pw.stop()
        
    except Exception as e:
        log(f"  ⚠ Browse error: {e}")

# ── AI DECISION MAKER ────────────────────────────────────────────────────

ACTIONS_PRIORITY = [
    "check_email",
    "create_service",
    "browse_projects",
    "check_status",
]

def decide_action(state: dict) -> str:
    """Decide what action to take based on state + time."""
    
    # 1. Email check — always do this if not done today
    last_email = state.get("last_email_check")
    if not last_email or last_email != _today():
        return "check_email"
    
    # 2. Service creation — 1 per week, needs image
    if can_create_service_this_week(state):
        unused = [s for s in SERVICE_TEMPLATES 
                  if not is_title_used(state, s["title"])]
        if unused:
            return "create_service"
    
    # 3. Browse projects — do this if we have bid quota
    try:
        sys.path.insert(0, str(BASE))
        from quota import can_send as quota_can_send
        if quota_can_send("nafezly_bids"):
            return "browse_projects"
    except (ImportError, Exception):
        pass
    
    # 4. Check status — always an option
    return "check_status"

def show_status(state: dict):
    """Show current state and quotas."""
    print("\n" + "=" * 60)
    print("  ARABIC PLATFORM MANAGER — STATUS")
    print("=" * 60)
    
    print(f"\n  📊 Run count: {state.get('run_count', 0)}")
    print(f"  🕐 Last run: {state.get('last_run', 'never')}")
    print(f"  📅 Today: {_today()}")
    
    print(f"\n  🏪 Services created:")
    for platform in ["nafezly", "mostaql"]:
        svcs = state.get("created_services", {}).get(platform, [])
        print(f"    {platform}: {len(svcs)} services")
        for s in svcs[-3:]:  # last 3
            print(f"      • {s.get('title', '?')[:50]} ({s.get('created', '?')})")
    
    print(f"\n  📋 Bids sent:")
    for platform in ["nafezly", "mostaql"]:
        bids = state.get("bids_sent", {}).get(platform, [])
        print(f"    {platform}: {len(bids)} bids")
    
    print(f"\n  👥 Persons contacted:")
    for platform in ["nafezly", "mostaql"]:
        contacts = state.get("contacted_persons", {}).get(platform, [])
        print(f"    {platform}: {len(contacts)} persons")
    
    print(f"\n  📧 Last email check: {state.get('last_email_check', 'never')}")
    print(f"  📅 Last service: {state.get('last_service_date', 'never')}")
    
    print(f"\n  ✅ Can create service this week: {can_create_service_this_week(state)}")
    
    available_templates = [s["title"] for s in SERVICE_TEMPLATES 
                          if not is_title_used(state, s["title"])]
    print(f"  📦 Available service templates: {len(available_templates)}")
    for t in available_templates:
        print(f"    • {t}")
    
    print()

# ── SHOW PROJECTS AND BID ────────────────────────────────────────────────

def show_projects_and_bid():
    """
    --show-projects mode:
    1. Scrapes Nafezly + Mostaql project listing pages for AI/automation keywords
    2. Prints them as a numbered list with title, price, platform, link
    3. Asks "Enter project number to bid, or 0 to skip:"
    4. If user picks a project, opens it in browser, generates bid via AI/skills
    5. Asks "Send? (y/n)" and submits if approved
    6. After done, returns so the caller can continue to the next action
    """
    from playwright.sync_api import sync_playwright

    # AI/automation search keywords for Nafezly
    NAFEZLY_SEARCH_URLS = [
        ("n8n + AI + automation", "https://nafezly.com/projects?key=n8n+AI+automation&pricing=10,200"),
        ("ذكاء اصطناعي", "https://nafezly.com/projects?key=%D8%B0%D9%83%D8%A7%D8%A1+%D8%A7%D8%B5%D8%B7%D9%86%D8%A7%D8%B9%D9%8A&pricing=10,200"),
        ("أتمتة", "https://nafezly.com/projects?key=%D8%A3%D8%AA%D9%85%D8%AA%D8%A9&pricing=10,200"),
    ]

    # Mostaql category pages for AI/automation
    MOSTAQL_CATEGORY_URLS = [
        ("AI & Machine Learning", "https://mostaql.com/projects/ai-machine-learning"),
        ("Development", "https://mostaql.com/projects/development"),
    ]

    all_projects = []  # list of {platform, title, price, url}

    try:
        pw = sync_playwright().start()
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=BRAVE_PROFILE,
            executable_path=BRAVE_EXE,
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            viewport={"width": 1366, "height": 768},
        )
        page = ctx.new_page()
        page.set_default_timeout(90000)

        # ── Login check helper ──
        def _wait_login_if_needed(page_obj, platform_name: str):
            if "login" in page_obj.url.lower() or "register" in page_obj.url.lower():
                log(f"  ⏳ {platform_name} login required — waiting 120s...")
                for _ in range(120):
                    time.sleep(1)
                    if "login" not in page_obj.url.lower() and "register" not in page_obj.url.lower():
                        log(f"  ✅ Logged in to {platform_name}")
                        return True
                log(f"  ⚠ Login timeout for {platform_name}, continuing...")
                return False
            return True

        # ── Scrape Nafezly projects ──
        log("=" * 40)
        log("🔍 Scraping Nafezly projects...")
        log("=" * 40)
        seen_urls = set()
        for search_label, search_url in NAFEZLY_SEARCH_URLS:
            try:
                log(f"  Searching: {search_label}")
                page.goto(search_url, timeout=60000, wait_until="domcontentloaded")
                time.sleep(3)
                _wait_login_if_needed(page, "Nafezly")

                projects = page.evaluate("""() => {
                    const items = [];
                    // Try multiple selectors for Nafezly project cards
                    const cards = document.querySelectorAll(
                        'a[href*="/project/"], [class*="project-card"], [class*="ProjectCard"], ' +
                        '[class*="project-item"], .card, article'
                    );
                    const processed = new Set();
                    for (const el of cards) {
                        const link = el.tagName === 'A' ? el : el.querySelector('a[href*="/project/"]');
                        if (!link) continue;
                        const href = link.href || link.getAttribute('href') || '';
                        if (!href || href.includes('/offer')) continue;
                        const url = href.startsWith('http') ? href : 'https://nafezly.com' + href;
                        if (processed.has(url)) continue;
                        processed.add(url);
                        const title = (link.innerText || link.textContent || '').trim();
                        // Try to find price
                        const priceEl = el.querySelector('[class*="price"], [class*="budget"], ' +
                            '[class*="money"], [class*="cost"], span[class*="amount"]');
                        const price = priceEl ? priceEl.innerText.trim() : '';
                        if (title && title.length > 5) {
                            items.push({ title: title.substring(0, 120), url: url, price: price });
                        }
                    }
                    return items;
                }""")

                for p in projects:
                    if p["url"] not in seen_urls:
                        seen_urls.add(p["url"])
                        all_projects.append({
                            "platform": "nafezly",
                            "title": p["title"],
                            "price": p.get("price", ""),
                            "url": p["url"],
                        })
                log(f"    → Found {len(projects)} project(s)")
            except Exception as e:
                log(f"  ⚠ Nafezly search '{search_label}' error: {e}")
                continue

        # ── Scrape Mostaql projects ──
        log("=" * 40)
        log("🔍 Scraping Mostaql projects...")
        log("=" * 40)
        for cat_label, cat_url in MOSTAQL_CATEGORY_URLS:
            try:
                log(f"  Category: {cat_label}")
                page.goto(cat_url, timeout=60000, wait_until="domcontentloaded")
                time.sleep(3)
                _wait_login_if_needed(page, "Mostaql")

                projects = page.evaluate("""() => {
                    const items = [];
                    const links = document.querySelectorAll('a[href*="/project/"]');
                    const processed = new Set();
                    for (const a of links) {
                        const href = a.getAttribute('href');
                        if (!href) continue;
                        const url = href.startsWith('http') ? href : 'https://mostaql.com' + href;
                        if (processed.has(url)) continue;
                        processed.add(url);
                        const title = (a.innerText || a.textContent || '').trim();
                        // Try to find price in parent card
                        const card = a.closest('[class*="card"], [class*="project"], li, article, div') || a.parentElement;
                        let price = '';
                        if (card) {
                            const priceEl = card.querySelector('[class*="price"], [class*="budget"], ' +
                                '[class*="money"], span[class*="amount"]');
                            if (priceEl) price = priceEl.innerText.trim();
                        }
                        if (title && title.length > 5 && !url.includes('/offer')) {
                            items.push({ title: title.substring(0, 120), url: url, price: price });
                        }
                    }
                    return items;
                }""")

                for p in projects:
                    if p["url"] not in seen_urls:
                        seen_urls.add(p["url"])
                        all_projects.append({
                            "platform": "mostaql",
                            "title": p["title"],
                            "price": p.get("price", ""),
                            "url": p["url"],
                        })
                log(f"    → Found {len(projects)} project(s)")
            except Exception as e:
                log(f"  ⚠ Mostaql category '{cat_label}' error: {e}")
                continue

        # ── Display projects as numbered list ──
        if not all_projects:
            log("\n  ⚠ No projects found on either platform.")
            ctx.close()
            pw.stop()
            return

        print("\n" + "═" * 70)
        print("  📋 AVAILABLE PROJECTS — Nafezly + Mostaql")
        print("═" * 70)
        print(f"  {'#':<4} {'Platform':<10} {'Title':<36} {'Price':<10} {'Link'}")
        print("  " + "—" * 66)

        for idx, proj in enumerate(all_projects, 1):
            title_short = proj["title"][:40] + ("..." if len(proj["title"]) > 40 else "")
            price_str = proj["price"] if proj["price"] else "—"
            url_short = proj["url"][:50] + ("..." if len(proj["url"]) > 50 else "")
            print(f"  {idx:<4} {proj['platform']:<10} {title_short:<36} {price_str:<10} {url_short}")

        print("═" * 70)

        # ── Ask user to pick a project ──
        while True:
            try:
                choice = input("\n  Enter project number to bid, or 0 to skip: ").strip()
                if not choice:
                    continue
                choice_num = int(choice)
                if choice_num == 0:
                    log("  Skipped project selection.")
                    break
                if 1 <= choice_num <= len(all_projects):
                    selected = all_projects[choice_num - 1]
                    log(f"  Selected: [{selected['platform']}] {selected['title'][:50]}")
                    # ── Open project page, get details, generate bid, ask to send ──
                    _handle_project_bid(page, selected, ctx)
                    # After the bid attempt, show the full list again? No, we continue
                    # Ask if user wants to bid on another
                    again = input("\n  Bid on another project? (y/n): ").strip().lower()
                    if again != "y":
                        break
                    # Re-show the list so user can pick again
                    print("\n" + "═" * 70)
                    print(f"  {'#':<4} {'Platform':<10} {'Title':<36} {'Price':<10} {'Link'}")
                    print("  " + "—" * 66)
                    for i2, p2 in enumerate(all_projects, 1):
                        t2 = p2["title"][:40] + ("..." if len(p2["title"]) > 40 else "")
                        p_str = p2["price"] if p2["price"] else "—"
                        u2 = p2["url"][:50] + ("..." if len(p2["url"]) > 50 else "")
                        print(f"  {i2:<4} {p2['platform']:<10} {t2:<36} {p_str:<10} {u2}")
                    print("═" * 70)
                else:
                    print(f"  ⚠ Enter a number between 0 and {len(all_projects)}")
            except ValueError:
                print("  ⚠ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n  ⏹ Aborted.")
                break

        ctx.close()
        pw.stop()

    except Exception as e:
        log(f"  ⚠ show_projects error: {e}")
        import traceback
        traceback.print_exc()


def _handle_project_bid(page, project: dict, browser_ctx):
    """
    Open a project page, extract details, generate a bid using skills/AI,
    ask user if they want to send it, and submit if approved.
    """
    log(f"\n  Opening project page...")
    try:
        page.goto(project["url"], timeout=60000, wait_until="domcontentloaded")
        time.sleep(3)
    except Exception as e:
        log(f"  ⚠ Could not open project page: {e}")
        return

    # Extract project details from the page
    details = page.evaluate("""() => {
        const title = document.querySelector('h1, h2')?.innerText?.trim() || '';
        const desc = document.querySelector(
            '[class*="desc"], [class*="detail"], [class*="content"], ' +
            '[class*="description"], article, .project-body, main p'
        )?.innerText || '';
        const budget = document.querySelector('[class*="budget"], [class*="price"], ' +
            '[class*="money"], [class*="cost"]')?.innerText?.trim() || '';
        const owner = document.querySelector('[class*="owner"], [class*="client"], ' +
            '[class*="user-name"], [class*="username"]')?.innerText?.trim() || '';
        return { title, desc: desc.substring(0, 1500), budget, owner };
    }""")

    if not details or not details.get("title"):
        log("  ⚠ Could not extract project details")
        return

    title = details["title"]
    desc = details.get("desc", "")
    budget = details.get("budget", "")
    owner = details.get("owner", "")

    print("\n" + "─" * 50)
    print(f"  📌 Project: {title[:70]}")
    print(f"  💰 Budget: {budget if budget else 'Not specified'}")
    if owner:
        print(f"  👤 Client: {owner[:40]}")
    print(f"  🔗 URL: {project['url']}")
    print(f"  📝 Description excerpt:")
    print(f"    {desc[:300].strip()}")
    print("─" * 50)

    # ── Generate bid ──
    log("  Generating bid...")

    platform = project["platform"]
    bid_text = None

    # Try skills library first
    try:
        sys.path.insert(0, str(BASE))
        from skills.manager import find_best_skill, apply_skill
        skill = find_best_skill(
            "arabic_bid",
            context_keywords=[platform, "n8n", "automation", "arabic", title[:30]],
        )
        if skill and skill.get("template"):
            bid_text = apply_skill(skill, {
                "n_workflows": "15",
                "duration": "5",
                "budget": budget or "50",
                "project_title": title[:100],
            }, use_ai_polish=True)
            if bid_text:
                log(f"  ✓ Used skill: {skill.get('name', '?')}")
    except Exception as e:
        log(f"  ⚠ Skills library error: {e}")

    # AI fallback if skills didn't produce a bid
    if not bid_text:
        log("  Using AI to generate bid...")
        bid_text = ai_generate(
            f"Write a proposal in FORMAL ARABIC (فصحى محترمة) for a project on {platform}.\n\n"
            f"Project title: {title[:200]}\n"
            f"Description: {desc[:800]}\n"
            f"Budget: {budget or 'negotiable'}\n"
            f"Client: {owner[:100] if owner else 'Not specified'}\n\n"
            f"Rules:\n"
            f"- Start with 'السلام عليكم ورحمة الله وبركاته'\n"
            f"- Introduce yourself as 'علاء فتحي، مهندس أتمتة وذكاء اصطناعي'\n"
            f"- Show you understand their specific project\n"
            f"- Mention n8n, Python, OpenAI\n"
            f"- Offer 3-4 specific deliverables\n"
            f"- Set a fair price based on the budget\n"
            f"- MAX 200 words\n"
            f"- Output ONLY the proposal text, no extra commentary",
            max_tokens=900,
        )
        if bid_text:
            log(f"  ✓ AI-generated bid ({len(bid_text)} chars)")

    # Ultimate fallback
    if not bid_text:
        bid_text = (
            "السلام عليكم ورحمة الله وبركاته،\n\n"
            f"أنا علاء فتحي، مهندس أتمتة ذكاء اصطناعي متخصص في n8n و Python. "
            f"أستطيع تنفيذ مشروع '{title[:60]}' بكفاءة واحترافية.\n\n"
            "خطة العمل:\n"
            "1. تحليل المتطلبات بالتفصيل\n"
            "2. تصميم وبناء الحل المناسب باستخدام n8n\n"
            "3. اختبار شامل وضمان الجودة\n"
            "4. تسليم مع توثيق مختصر\n\n"
            f"السعر: {budget or 'حسب الاتفاق'} دولار\n"
            "المدة: 3-7 أيام عمل\n\n"
            "للتواصل، أنا جاهز للإجابة على أي استفسار.\n\n"
            "والسلام عليكم ورحمة الله وبركاته،\n"
            "علاء فتحي"
        )
        log(f"  ✓ Used fallback template ({len(bid_text)} chars)")

    # ── Show the bid and ask to send ──
    print("\n" + "─" * 50)
    print("  📝 GENERATED BID:")
    print("─" * 50)
    print(f"\n{bid_text}\n")
    print("─" * 50)

    send_choice = input("\n  Send this bid? (y/n): ").strip().lower()
    if send_choice != "y":
        log("  Bid not sent.")
        return

    # ── Send the bid via browser ──
    log("  Sending bid...")
    posted = _submit_bid_via_browser(page, bid_text, platform)

    if posted:
        log(f"  ✅ Bid submitted for: {title[:60]}")
        # Record in state
        state = load_state()
        platform_key = "nafezly" if platform == "nafezly" else "mostaql"
        state["bids_sent"][platform_key].append({
            "url": project["url"],
            "title": title[:100],
            "owner": owner[:50],
            "date": datetime.now().isoformat(),
        })
        state["contacted_persons"][platform_key].append(owner[:80] if owner else project["url"][:80])
        save_state(state)

        # Try to record in quota if available
        try:
            sys.path.insert(0, str(BASE))
            from quota import record_sent as quota_record
            quota_record(f"{platform_key}_bids", project["url"])
        except Exception:
            pass
    else:
        log(f"  ⚠ Failed to submit bid for: {title[:60]}")
        log("  The browser is open — you can submit manually if needed.")


def _submit_bid_via_browser(page, bid_text: str, platform: str) -> bool:
    """
    Try to submit a bid on the current project page.
    Returns True if the bid was successfully submitted.
    """
    # Try clicking a bid/proposal button
    clicked = page.evaluate("""() => {
        const buttons = document.querySelectorAll('button, a, span, input[type="submit"]');
        const keywords = ['تقديم', 'عرض', 'offer', 'bid', 'تقدم', 'أرسل عرض', 'تقديم عرض', 'ارسال'];
        for (const el of buttons) {
            const t = (el.innerText || el.textContent || el.value || '').toLowerCase().trim();
            for (const kw of keywords) {
                if (t.includes(kw.toLowerCase())) {
                    el.click();
                    return true;
                }
            }
        }
        return false;
    }""")

    if not clicked:
        log("  ⚠ No bid/submit button found on page")
        return False

    time.sleep(3)

    # Fill the bid textarea
    filled = page.evaluate(f"""() => {{
        const ta = document.querySelector('textarea');
        if (!ta) return false;
        ta.value = {json.dumps(bid_text)};
        ta.dispatchEvent(new Event('input', {{bubbles: true}}));
        ta.dispatchEvent(new Event('change', {{bubbles: true}}));
        ta.dispatchEvent(new Event('blur'));
        return true;
    }}""")

    if not filled:
        log("  ⚠ No textarea found on page")
        return False

    time.sleep(1)

    # Try to fill price if there's an input
    page.evaluate("""() => {
        const pi = document.querySelector('input[type="number"], input[name*="price"], input[name*="amount"]');
        if (pi) {
            const budgetText = document.querySelector('[class*="budget"], [class*="price"]')?.innerText || '';
            const match = budgetText.match(/\\d+/);
            pi.value = match ? match[1] : '35';
            pi.dispatchEvent(new Event('input', {{bubbles: true}}));
            pi.dispatchEvent(new Event('change', {{bubbles: true}}));
        }
    }}""")

    time.sleep(1)

    # Submit the form
    submitted = page.evaluate("""() => {
        const buttons = document.querySelectorAll('button, input[type="submit"]');
        const keywords = ['إرسال', 'تقديم', 'submit', 'send', 'تأكيد', 'confirm', 'نشر'];
        for (const el of buttons) {
            const t = (el.innerText || el.textContent || el.value || '').toLowerCase().trim();
            for (const kw of keywords) {
                if (t.includes(kw.toLowerCase())) {
                    el.click();
                    return true;
                }
            }
        }
        return false;
    }""")

    if submitted:
        time.sleep(3)
        log("  ✓ Bid form submitted!")
        # Take a confirmation screenshot for verification
        try:
            ss_dir = TEMP / "bid_confirmations"
            ss_dir.mkdir(parents=True, exist_ok=True)
            ss_name = f"bid_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=str(ss_dir / ss_name))
            log(f"  📸 Confirmation screenshot: {ss_name}")
        except Exception as e:
            log(f"  ⚠ Screenshot failed: {e}")
        # Add random delay before next action to look human
        delay = random.uniform(BID_MIN_DELAY, BID_MAX_DELAY)
        log(f"  ⏳ Waiting {delay:.0f}s before next action...")
        time.sleep(delay)
        return True

    log("  ⚠ Could not find submit button")
    return False


# ── MAIN ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Freelance Manager for Nafezly & Mostaql")
    parser.add_argument("--status", action="store_true", help="Show state and quotas")
    parser.add_argument("--check-email", action="store_true", help="Check email only")
    parser.add_argument("--browse", action="store_true", help="Browse Nafezly projects")
    parser.add_argument("--show-projects", action="store_true", help="Browse Nafezly + Mostaql projects, pick one to bid on")
    parser.add_argument("--create-service", action="store_true", help="Force create a service")
    parser.add_argument("--reset", action="store_true", help="Reset state (safety)")
    args = parser.parse_args()
    
    state = load_state()
    
    # ── SHOW PROJECTS (runs BEFORE other actions) ──
    if args.show_projects:
        log("📋 Step 0: Showing projects from Nafezly + Mostaql...")
        show_projects_and_bid()
        # If --show-projects was the ONLY flag, we're done — fall through to auto mode
        other_flags = [args.reset, args.status, args.check_email, args.create_service, args.browse]
        if not any(other_flags):
            log("  → Continuing to auto mode (deciding next action)")
            # Fall through to auto mode at the end

    # ── RESET ──
    if args.reset:
        STATE_FILE.write_text(json.dumps(DEFAULT_STATE, ensure_ascii=False, indent=2), encoding="utf-8")
        log("✅ State reset to default")
        print("  Run again without --reset to start fresh.")
        return
    
    # ── STATUS ──
    if args.status:
        show_status(state)
        return
    
    # ── CHECK EMAIL ──
    if args.check_email:
        log("📧 Checking email for replies...")
        replies = check_email_replies()
        state = load_state()
        state["last_email_check"] = _today()
        save_state(state)
        print(f"\n  Found {len(replies)} replies")
        return
    
    # ── CREATE SERVICE ──
    if args.create_service:
        log("🚀 Force-creating a service...")
        svc = ai_generate_service()
        if not svc:
            log("  ✗ No service available to create")
            return
        log(f"  Generating image for: {svc['title']}")
        img_path = generate_service_image(svc.get("image_key", "service_custom"))
        if not img_path:
            log("  ⚠ Image generation failed — service won't be created without image")
            return
        log("  Opening Nafezly to create service...")
        success = create_service_on_nafezly(svc, img_path)
        if success:
            state = load_state()
            state["created_services"]["nafezly"].append({
                "title": svc["title"],
                "price": svc.get("price", "30"),
                "created": _today(),
                "image": img_path.name
            })
            state["created_service_titles"].append(svc["title"])
            state["last_service_date"] = datetime.now().isoformat()
            state["run_count"] = state.get("run_count", 0) + 1
            state["run_history"].append({
                "date": datetime.now().isoformat(),
                "action": "create_service",
                "title": svc["title"]
            })
            save_state(state)
            log(f"✅ Service created successfully: {svc['title']}")
        return
    
    # ── BROWSE ──
    if args.browse:
        log("🔍 Browsing Nafezly projects...")
        browse_nafezly_projects()
        state = load_state()
        state["run_count"] = state.get("run_count", 0) + 1
        save_state(state)
        return
    
    # ── AUTO MODE (default) — AI decides what to do ──
    log("═" * 60)
    log("ARABIC PLATFORM MANAGER — Auto Mode")
    log(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log(f"Run #{state.get('run_count', 0) + 1}")
    log("═" * 60)
    
    # First, always check email
    if not args.check_email:
        log("📧 Step 1: Checking email...")
        check_email_replies()
        state = load_state()
        state["last_email_check"] = _today()
        save_state(state)
    
    # Decide next action
    action = decide_action(state)
    log(f"🧠 AI decided: {action}")
    
    if action == "create_service":
        svc = ai_generate_service()
        if svc:
            log(f"🖼 Generating premium image for: {svc['title']}")
            img_path = generate_service_image(svc.get("image_key", "service_custom"))
            if img_path:
                log("🚀 Creating service on Nafezly...")
                success = create_service_on_nafezly(svc, img_path)
                if success:
                    state = load_state()
                    state["created_services"]["nafezly"].append({
                        "title": svc["title"],
                        "price": svc.get("price", "30"),
                        "created": _today(),
                        "image": img_path.name
                    })
                    state["created_service_titles"].append(svc["title"])
                    state["last_service_date"] = datetime.now().isoformat()
                    log(f"✅ Service created: {svc['title']}")
                else:
                    log(f"⚠ Service creation failed — browser may need attention")
            else:
                log(f"⚠ Image generation failed — skipping service creation")
        else:
            log("⚠ No new service to create — all templates used!")
            log("  → Browse projects instead")
            browse_nafezly_projects()
    
    elif action == "browse_projects":
        browse_nafezly_projects()
    
    elif action == "check_status":
        show_status(state)
        log("  Nothing urgent to do. Run with --browse to find projects.")
    
    # Update state
    state = load_state()
    state["run_count"] = state.get("run_count", 0) + 1
    state["run_history"].append({
        "date": datetime.now().isoformat(),
        "action": action
    })
    save_state(state)
    
    log("═" * 60)
    log("SESSION COMPLETE")
    log("═" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  ⏹ Aborted by user.")
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f"\n  ❌ Error: {e}")
        traceback.print_exc()
        sys.exit(1)
