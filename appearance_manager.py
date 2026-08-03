"""
appearance_manager.py — Unified Appearance Manager (P5).

Generates and tracks all profile/service/portfolio/banner images
for freelancing platforms (Nafezly, Mostaql, LinkedIn, Upwork).

Usage:
    python appearance_manager.py --list                        # Show all generated images
    python appearance_manager.py --profile-photo               # Generate profile photo
    python appearance_manager.py --service                     # Generate service image (interactive)
    python appearance_manager.py --service --auto              # Generate all 4 default services
    python appearance_manager.py --portfolio                   # Generate portfolio image (interactive)
    python appearance_manager.py --banner                      # Generate banner image (interactive)
    python appearance_manager.py --all                         # Generate everything
    python appearance_manager.py --platform nafezly            # Show images for Nafezly
    python appearance_manager.py --platform mostaql            # Show images for Mostaql
    python appearance_manager.py --clean                        # Delete all generated images
"""

import os, sys, json, re, time, hashlib
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = Path(__file__).parent
TEMP = WORKSPACE / "Temp"
STATE_FILE = WORKSPACE / "appearance_state.json"
OUT = TEMP / "appearance"
OUT.mkdir(parents=True, exist_ok=True)

FONT_PATHS = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\ARIALBD.TTF",
    r"C:\Windows\Fonts\tahoma.ttf",
    r"C:\Windows\Fonts\TREBUCBD.TTF",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
]

DEFAULT_SIZE = (800, 500)
BANNER_SIZE = (1400, 400)
PROFILE_SIZE = (400, 400)
PORTFOLIO_SIZE = (1400, 788)

COLORS = {
    "emerald": "#00B894",
    "blue": "#0078D4",
    "purple": "#7850C8",
    "orange": "#C86432",
    "teal": "#0EA5E9",
    "rose": "#E11D48",
    "dark": "#0F172A",
    "dark2": "#1E293B",
    "text": "#FFFFFF",
    "subtext": "#B0C4DE",
    "sig": "#7888A8",
}


def _get_font(size, bold=False):
    from PIL import ImageFont
    for p in FONT_PATHS:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _find_ar_font(size):
    from PIL import ImageFont
    ar_paths = [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\tahoma.ttf"]
    for p in ar_paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return _get_font(size)


def _load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"images": [], "platforms": {}, "last_generated": None}


def _save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def _register_image(filename, img_type, title, platform=None, size=None):
    state = _load_state()
    entry = {
        "filename": filename,
        "type": img_type,
        "title": title,
        "created": datetime.now().isoformat(),
        "size": size or list(DEFAULT_SIZE),
        "platforms": [platform] if platform else [],
        "md5": "",
    }
    fp = OUT / filename
    if fp.exists():
        entry["md5"] = hashlib.md5(fp.read_bytes()).hexdigest()[:12]
        entry["size_bytes"] = fp.stat().st_size
    state["images"] = [e for e in state["images"] if e["filename"] != filename]
    state["images"].append(entry)
    state["last_generated"] = datetime.now().isoformat()
    _save_state(state)
    return entry


def _rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# ─── PIL GENERATORS ───────────────────────────────────────────────────────────

def gen_service_image(title, subtitle="", accent="blue", filename=None):
    from PIL import Image, ImageDraw
    if not filename:
        safe = re.sub(r"[^a-zA-Z0-9_\u0600-\u06FF]", "_", title.lower().replace("\n", " ").strip())[:30]
        safe = safe.strip("_")
        filename = f"service_{safe}.jpg"
    accent_rgb = _rgb(COLORS.get(accent, accent))
    w, h = DEFAULT_SIZE
    img = Image.new("RGB", (w, h), (15, 23, 42))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        a = y / h
        r = int(15 * (1-a) + 30 * a)
        g = int(23 * (1-a) + 45 * a)
        b = int(42 * (1-a) + 70 * a)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    draw.rectangle([(0, h-6), (w, h)], fill=accent_rgb)
    draw.ellipse([(w-150, -50), (w-50, 50)], outline=(*accent_rgb, 30), width=2)
    draw.ellipse([(-30, h-120), (50, h-40)], outline=(*accent_rgb, 30), width=2)
    nodes = [(100,80), (200,60), (300,100), (400,70), (500,90), (600,60), (700,100)]
    for i, (x, y) in enumerate(nodes):
        draw.ellipse([(x-4, y-4), (x+4, y+4)], fill=(*accent_rgb, 200))
        if i > 0:
            px, py = nodes[i-1]
            draw.line([(px, py), (x, y)], fill=(*accent_rgb, 60), width=1)
    font_t = _find_ar_font(36)
    font_sub = _find_ar_font(18)
    font_sig = _get_font(14)
    lines = title.split("\n")
    y_start = 160
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_t)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        draw.text((x, y_start + i*50), line, fill=(255, 255, 255), font=font_t)
    if subtitle:
        bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        draw.text((x, y_start + len(lines)*50 + 20), subtitle, fill=_rgb(COLORS["subtext"]), font=font_sub)
    bbox = draw.textbbox((0, 0), "Salim Muhammad", font=font_sig)
    tw = bbox[2] - bbox[0]
    draw.text((w-tw-20, h-45), "Salim Muhammad", fill=_rgb(COLORS["sig"]), font=font_sig)
    fp = OUT / filename
    img.save(str(fp), quality=95)
    _register_image(filename, "service", title)
    print(f"  [SERVICE] {filename} ({fp.stat().st_size} bytes)")
    return fp


def gen_portfolio_image(title, subtitle="", metrics=None, accent="purple", filename=None):
    from PIL import Image, ImageDraw
    if not filename:
        safe = re.sub(r"[^a-zA-Z0-9_\u0600-\u06FF]", "_", title.lower().replace("\n", " ").strip())[:30]
        safe = safe.strip("_")
        filename = f"portfolio_{safe}.jpg"
    accent_rgb = _rgb(COLORS.get(accent, accent))
    w, h = PORTFOLIO_SIZE
    img = Image.new("RGB", (w, h), (15, 23, 42))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        a = y / h
        r = int(15 * (1-a) + 25 * a)
        g = int(23 * (1-a) + 40 * a)
        b = int(42 * (1-a) + 65 * a)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    draw.rectangle([(0, h-4), (w, h)], fill=accent_rgb)
    draw.ellipse([(-80, -80), (80, 80)], outline=(*accent_rgb, 25), width=2)
    draw.ellipse([(w-200, h-200), (w-40, h-40)], outline=(*accent_rgb, 25), width=2)
    font_t = _find_ar_font(48)
    font_sub = _find_ar_font(22)
    font_m = _get_font(18)
    lines = title.split("\n")
    y0 = 120
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_t)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        draw.text((x, y0 + i*60), line, fill=(255, 255, 255), font=font_t)
    if subtitle:
        bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        draw.text((x, y0 + len(lines)*60 + 15), subtitle, fill=_rgb(COLORS["subtext"]), font=font_sub)
    if metrics:
        mx = 200
        my = h - 100
        for k, v in metrics.items():
            bbox = draw.textbbox((0, 0), f"{v}  {k}", font=font_m)
            tw = bbox[2] - bbox[0]
            draw.text((mx, my), f"{v}  {k}", fill=(*accent_rgb, 220), font=font_m)
            mx += max(tw + 80, 180)
    bbox = draw.textbbox((0, 0), "Salim Muhammad", font=_get_font(16))
    tw = bbox[2] - bbox[0]
    draw.text((w-tw-20, h-40), "Salim Muhammad", fill=_rgb(COLORS["sig"]), font=_get_font(16))
    fp = OUT / filename
    img.save(str(fp), quality=95)
    _register_image(filename, "portfolio", title)
    print(f"  [PORTFOLIO] {filename} ({fp.stat().st_size} bytes)")
    return fp


# ─── PLAYWRIGHT HTML GENERATORS ──────────────────────────────────────────────

def _render_html(html, filename, size, img_type, title):
    from playwright.sync_api import sync_playwright
    w, h = size
    pw = sync_playwright().start()
    try:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": w, "height": h})
        page.set_content(html)
        page.wait_for_timeout(500)
        fp = OUT / filename
        page.screenshot(path=str(fp))
        _register_image(filename, img_type, title, size=list(size))
        print(f"  [{img_type.upper()}] {filename} ({fp.stat().st_size} bytes)")
        page.close()
        browser.close()
        return fp
    finally:
        pw.stop()


def gen_profile_photo(name="Salim Muhammad", initials="SM", accent="blue", filename="profile_photo.jpg"):
    ac = COLORS.get(accent, accent)
    html = f"""<!DOCTYPE html><html><body style="margin:0;width:400px;height:400px;
background:linear-gradient(135deg,{ac},#0F172A);display:flex;align-items:center;justify-content:center;
font-family:system-ui,sans-serif;">
<div style="width:160px;height:160px;border-radius:80px;background:rgba(255,255,255,0.15);
border:3px solid rgba(255,255,255,0.3);display:flex;align-items:center;justify-content:center;
font-size:64px;font-weight:700;color:white;text-shadow:0 2px 10px rgba(0,0,0,0.3);">
{initials}</div>
<div style="position:absolute;bottom:40px;text-align:center;">
<div style="color:white;font-size:20px;font-weight:600;">{name}</div>
<div style="color:rgba(255,255,255,0.6);font-size:12px;">AI Automation Engineer</div>
</div></body></html>"""
    return _render_html(html, filename, PROFILE_SIZE, "profile", f"Profile: {name}")


def gen_banner(title, subtitle="", accent="blue", filename="banner.jpg"):
    ac = COLORS.get(accent, accent)
    html = f"""<!DOCTYPE html><html><body style="margin:0;width:1400px;height:400px;
background:linear-gradient(135deg,#0F172A 0%,{ac}22 50%,#0F172A 100%);
font-family:system-ui,sans-serif;display:flex;align-items:center;justify-content:center;">
<div style="text-align:center;">
<div style="color:white;font-size:48px;font-weight:700;margin-bottom:12px;">{title}</div>
<div style="color:rgba(255,255,255,0.6);font-size:18px;">{subtitle}</div>
<div style="margin-top:24px;display:flex;justify-content:center;gap:30px;">
<div style="color:{ac};font-size:14px;background:rgba(255,255,255,0.08);padding:8px 20px;border-radius:20px;">AI Agents</div>
<div style="color:{ac};font-size:14px;background:rgba(255,255,255,0.08);padding:8px 20px;border-radius:20px;">Workflow Automation</div>
<div style="color:{ac};font-size:14px;background:rgba(255,255,255,0.08);padding:8px 20px;border-radius:20px;">n8n</div>
</div></div></body></html>"""
    return _render_html(html, filename, BANNER_SIZE, "banner", f"Banner: {title}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def cmd_list():
    state = _load_state()
    imgs = state.get("images", [])
    if not imgs:
        print("No images generated yet. Run `--profile-photo`, `--service`, `--portfolio`, or `--all`")
        return
    print(f"\n{'='*60}")
    print(f"  APPEARANCE MANAGER — {len(imgs)} images")
    print(f"{'='*60}")
    for e in sorted(imgs, key=lambda x: x.get("created", ""), reverse=True):
        fp = OUT / e["filename"]
        exists = fp.exists()
        size = f"({fp.stat().st_size//1024}KB)" if exists else "[MISSING]"
        print(f"  [{e['type']:^10}] {e['filename']:<35} {size}")
        print(f"  {'':>14} {e.get('title',''):<40}")
    platforms = state.get("platforms", {})
    if platforms:
        print(f"\n  Platform deployments:")
        for p, imgs in platforms.items():
            print(f"    {p}: {', '.join(imgs)}")
    print()


def cmd_all():
    print("\n=== Generating ALL appearance assets ===\n")
    gen_profile_photo()
    gen_banner("AI Automation Engineer", "n8n • AI Agents • Workflow Automation", "blue")
    for svc in _DEFAULT_SERVICES:
        gen_service_image(**svc)
    for pf in _DEFAULT_PORTFOLIOS:
        gen_portfolio_image(**pf)
    print("\n=== Done! Run --list to see all generated images ===")


_DEFAULT_SERVICES = [
    {"title": "AI Agent\nDevelopment", "subtitle": "n8n | Python | API Integration | Chatbot", "accent": "emerald"},
    {"title": "Workflow\nAutomation", "subtitle": "n8n | Make.com | Automate Everything", "accent": "blue"},
    {"title": "نظام أتمتة\nمتكامل", "subtitle": "ذكاء اصطناعي | ربط تطبيقات | تقارير", "accent": "purple"},
    {"title": "بوت ذكي\nلخدمة العملاء", "subtitle": "AI-Powered | متعدد المنصات | 24/7", "accent": "teal"},
]

_DEFAULT_PORTFOLIOS = [
    {"title": "Multi-Platform CRM\nIntegration", "subtitle": "Connected 5 platforms into unified data pipeline", "metrics": {"Platforms": "5", "Data/sec": "1.2K", "Uptime": "99.9%"}, "accent": "blue"},
    {"title": "AI Customer Support\nBot", "subtitle": "Automated 80% of support tickets with AI", "metrics": {"Tickets/mo": "12K", "Resolution": "93%", "Cost saved": "70%"}, "accent": "emerald"},
    {"title": "نظام أتمتة\nللتجارة الإلكترونية", "subtitle": "متجر إلكتروني متكامل مع أتمتة الطلبات", "metrics": {"Orders/mo": "3K", "Processing": "Real-time", "Errors": "<1%"}, "accent": "purple"},
]


def cmd_service_auto():
    print("\n=== Generating 4 default service images ===\n")
    for svc in _DEFAULT_SERVICES:
        gen_service_image(**svc)
    print("\nDone.")


def cmd_portfolio_auto():
    print("\n=== Generating 3 default portfolio images ===\n")
    for pf in _DEFAULT_PORTFOLIOS:
        gen_portfolio_image(**pf)
    print("\nDone.")


def cmd_platform(name):
    state = _load_state()
    imgs = state.get("images", [])
    guide = {
        "nafezly": {
            "profile": "profile_photo.jpg - use as profile picture (400x400)",
            "banner": "banner.jpg - upload as profile cover (1400x400)",
            "services": ["service images -> upload to each Nafezly service page (800x500)"],
            "portfolio": ["portfolio images -> add to service descriptions or portfolio section"],
        },
        "mostaql": {
            "profile": "profile_photo.jpg - use as profile picture (400x400)",
            "services": ["service images -> upload to Mostaql portfolio projects (800x500)"],
            "portfolio": ["portfolio images -> upload as project samples (1400x788)"],
        },
        "linkedin": {
            "profile": "profile_photo.jpg - use as LinkedIn profile photo (400x400)",
            "banner": "banner.jpg - use as LinkedIn cover image (1400x400) - will need resizing to 1584x396",
            "portfolio": ["portfolio images -> add to LinkedIn Featured section (1400x788)"],
        },
        "upwork": {
            "profile": "profile_photo.jpg - Upwork profile photo (400x400)",
            "portfolio": ["portfolio images -> add to Upwork Project Catalog"],
            "service": ["service images -> add to Upwork proposals"],
        },
    }
    p = guide.get(name.lower())
    if not p:
        print(f"No guide for '{name}'. Options: nafezly, mostaql, linkedin, upwork")
        return
    print(f"\n{'='*60}")
    print(f"  PLATFORM GUIDE: {name.upper()}")
    print(f"{'='*60}")
    for key, items in p.items():
        print(f"  [{key}]")
        if isinstance(items, list):
            for item in items:
                fname = item.split(" ")[0] if " " in item else ""
                match = [e for e in imgs if e["filename"] == fname]
                status = " [OK]" if match else ""
                print(f"    - {item}{status}")
        else:
            fname = items.split(" ")[0] if " " in items else ""
            match = [e for e in imgs if e["filename"] == fname]
            status = " [OK]" if match else ""
            print(f"    {items}{status}")
    print()


def cmd_clean():
    import shutil
    if OUT.exists():
        shutil.rmtree(OUT)
        OUT.mkdir(parents=True, exist_ok=True)
    state = _load_state()
    state["images"] = []
    _save_state(state)
    print(f"Cleaned {OUT}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Appearance Manager — generate & track profile/service/portfolio images")
    parser.add_argument("--list", action="store_true", help="Show all generated images")
    parser.add_argument("--profile-photo", action="store_true", help="Generate profile photo")
    parser.add_argument("--service", action="store_true", help="Generate service image (interactive or --auto)")
    parser.add_argument("--portfolio", action="store_true", help="Generate portfolio image (interactive or --auto)")
    parser.add_argument("--banner", action="store_true", help="Generate banner image (interactive)")
    parser.add_argument("--auto", action="store_true", help="Auto-generate defaults (use with --service or --portfolio)")
    parser.add_argument("--all", action="store_true", help="Generate all default images")
    parser.add_argument("--platform", type=str, help="Show image guide for a platform (nafezly, mostaql, linkedin, upwork)")
    parser.add_argument("--clean", action="store_true", help="Delete all generated images")
    args = parser.parse_args()

    if args.clean:
        cmd_clean()
    elif args.list:
        cmd_list()
    elif args.platform:
        cmd_platform(args.platform)
    elif args.all:
        cmd_all()
    elif args.service and args.auto:
        cmd_service_auto()
    elif args.portfolio and args.auto:
        cmd_portfolio_auto()
    elif args.service:
        print("Service image generation (interactive):")
        title = input("  Title (use \\n for newlines): ").replace("\\n", "\n")
        subtitle = input("  Subtitle: ")
        accent = input(f"  Accent color {list(COLORS.keys())[:6]}: ") or "blue"
        gen_service_image(title, subtitle, accent)
    elif args.portfolio:
        print("Portfolio image generation (interactive):")
        title = input("  Title (use \\n for newlines): ").replace("\\n", "\n")
        subtitle = input("  Subtitle: ")
        accent = input(f"  Accent color {list(COLORS.keys())[:6]}: ") or "purple"
        gen_portfolio_image(title, subtitle, accent=accent)
    elif args.banner:
        title = input("  Banner title: ") or "AI Automation Engineer"
        subtitle = input("  Subtitle: ") or "n8n | AI Agents | Workflow Automation"
        accent = input(f"  Accent color {list(COLORS.keys())[:6]}: ") or "blue"
        gen_banner(title, subtitle, accent)
    elif args.profile_photo:
        name = input("  Name [Salim Muhammad]: ") or "Salim Muhammad"
        initials = input("  Initials [AF]: ") or "AF"
        accent = input(f"  Accent color {list(COLORS.keys())[:6]}: ") or "blue"
        gen_profile_photo(name, initials, accent)
    else:
        parser.print_help()
