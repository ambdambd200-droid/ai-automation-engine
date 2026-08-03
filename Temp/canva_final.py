"""Canva: open templates, screenshot, edit text."""
from playwright.sync_api import sync_playwright
import time, sys, os, json

BRAVE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
PROFILE = r"C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data"

TEMPLATES = {
    "project_showcase": {
        "url": "https://www.canva.com/templates/EAFwckKNjDE/",
        "texts": ["AI Automation Engineer", "Alaa Fathi", "AI Agents", "Workflow", "Chatbot", "n8n"],
    },
    "service_proposal": {
        "url": "https://www.canva.com/templates/EAGH8jq6UhE/",
        "texts": ["AI Automation Services", "Alaa Fathi", "Automation Engineer", "Workflow Automation"],
    },
    "service_banner": {
        "url": "https://www.canva.com/design/DAHM0gnZq5E/JGEQJE2gVkYhJiiXzDy30A/edit",
        "texts": ["AI Automation", "Alaa Fathi", "n8n", "Chatbot", "Agent"],
    },
}

OUTPUT = r"C:\Users\A\Desktop\Money\Temp"

def process_template(name, info, page, context):
    print(f"\n{'='*60}")
    print(f"Template: {name}")
    print(f"URL: {info['url']}")

    page.goto(info["url"], wait_until="domcontentloaded", timeout=180000)
    time.sleep(10)

    # Check login wall
    if "login" in page.url.lower():
        print("  [LOGIN] Canva login required. Saving screenshot for user...")
        page.screenshot(path=os.path.join(OUTPUT, f"canva_{name}_login.png"))
        return False

    # Click "Use template" and capture popup
    with page.expect_popup() as popup_info:
        for btn_text in ["Use template", "Customize", "استخدام", "تخصيص"]:
            try:
                btn = page.locator(f"button:has-text('{btn_text}'), a:has-text('{btn_text}')").first
                if btn.count() > 0 and btn.is_visible(timeout=3000):
                    print(f"  [CLICK] '{btn_text}'")
                    btn.click(timeout=10000)
                    break
            except:
                continue

        # Try clicking directly (if expect_popup doesn't trigger)
        try:
            btn = page.locator("[class*='button']:has-text('Customize'), [class*='button']:has-text('Use template')").first
            if btn.count() > 0:
                btn.click(timeout=5000)
        except:
            pass

    # Check if popup opened
    try:
        popup = popup_info.value
        page = popup
        print(f"  [POPUP] Editor opened in new tab")
    except:
        print(f"  [SAME TAB] Editor opened in same tab")

    # Wait for editor to fully render
    time.sleep(30)

    # Print current URL
    try:
        print(f"  [URL] {page.url[:100]}")
    except:
        pass

    # Try to edit text on canvas
    try:
        # Click center of canvas area
        page.mouse.click(680, 350)
        time.sleep(3)
        page.keyboard.press("Control+a")
        time.sleep(1)
        page.keyboard.type(f"{info['texts'][0]} — {info['texts'][1]}", delay=15)
        time.sleep(2)
        page.keyboard.press("Escape")
    except Exception as e:
        print(f"  [EDIT1] {e}")

    # Screenshot the result
    ss_path = os.path.join(OUTPUT, f"canva_{name}.png")
    page.screenshot(path=ss_path)
    print(f"  [SS] canva_{name}.png ({os.path.getsize(ss_path)//1024}KB)")

    # Focus on next text area
    try:
        page.mouse.click(680, 400)
        time.sleep(2)
        page.keyboard.press("Control+a")
        time.sleep(1)
        page.keyboard.type(f"{info['texts'][2]} | {info['texts'][3]} | {info['texts'][4]}", delay=10)
        time.sleep(2)
        page.keyboard.press("Escape")
    except Exception as e:
        print(f"  [EDIT2] {e}")

    # Final screenshot
    ss2_path = os.path.join(OUTPUT, f"canva_{name}_edited.png")
    page.screenshot(path=ss2_path)
    print(f"  [SS] canva_{name}_edited.png ({os.path.getsize(ss2_path)//1024}KB)")

    return True

def main():
    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=PROFILE,
            executable_path=BRAVE,
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            viewport={"width": 1366, "height": 768},
        )
        page = context.new_page()
        page.set_default_timeout(120000)

        for name, info in TEMPLATES.items():
            process_template(name, info, page)
            time.sleep(5)

        print("\n✅ All templates processed.")
        print("Browser stays open for review. Press Ctrl+C to close.")

        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            pass
        finally:
            context.close()

if __name__ == "__main__":
    main()
