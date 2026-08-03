"""Edit Canva template via Playwright."""
from playwright.sync_api import sync_playwright
import time, json, sys

BROWSER_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
TEMPLATES = {
    "project_showcase": "https://www.canva.com/templates/EAFwckKNjDE/",
    "service_proposal": "https://www.canva.com/templates/EAGH8jq6UhE/",
    "service_banner": "https://www.canva.com/design/DAHM0gnZq5E/JGEQJE2gVkYhJiiXzDy30A/edit",
}

def edit_template(url_key: str, page) -> bool:
    url = TEMPLATES.get(url_key)
    if not url:
        print(f"Unknown template: {url_key}")
        return False

    print(f"\n=== Opening {url_key} ===")
    print(f"URL: {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=180000)
    time.sleep(5)

    # Check if logged in
    if "login" in page.url.lower() or "signin" in page.url.lower() or "auth" in page.url.lower():
        print("[LOGIN REQUIRED] Canva needs login. Waiting 60s...")
        try:
            page.wait_for_url(lambda u: "login" not in u.lower() and "auth" not in u.lower(),
                              timeout=60000)
        except:
            pass

    # If it's a template page, click "Use template" or "Customize"
    try:
        use_btn = page.locator("button:has-text('Use template'), button:has-text('Customize'), a:has-text('Use template'), button:has-text('استخدام'), button:has-text('تخصيص')").first
        if use_btn.count() > 0:
            print("[CLICK] Use template button")
            use_btn.click(timeout=10000)
            time.sleep(10)
    except:
        pass

    # Try to edit text elements
    print("[EDIT] Looking for text elements...")
    edited = 0
    for selector in ["[contenteditable='true']", "span[data-text]", "text-area", ".text-input", "[role='textbox']"]:
        try:
            elements = page.locator(selector).all()
            for el in elements:
                try:
                    tag = el.tag_name
                    text = el.inner_text()
                    print(f"  Found text: '{text[:50]}' (tag={tag})")
                except:
                    continue
        except:
            continue

    # Try clicking on text on canvas
    # Click in center of canvas area
    print("[CLICK] Center of canvas...")
    page.mouse.click(683, 350)
    time.sleep(2)

    # Try Ctrl+A to select all, then type new text
    page.keyboard.press("Control+a")
    time.sleep(1)
    page.keyboard.type("AI Automation Engineer — Alaa Fathi", delay=50)
    time.sleep(1)
    page.keyboard.press("Enter")

    # Take screenshot to confirm
    page.screenshot(path=f"C:\\Users\\A\\Desktop\\Money\\Temp\\canva_{url_key}.png")
    print(f"[SCREENSHOT] Saved canva_{url_key}.png")

    # Download via share menu
    try:
        # Click Share/Download
        share = page.locator("button:has-text('Share'), button:has-text('Download'), button:has-text('تحميل'), button:has-text('مشاركة')").first
        if share.count() > 0:
            share.click(timeout=5000)
            time.sleep(3)
            # Click PNG option
            png = page.locator("text=PNG, text=PNG Download, text=صورة").first
            if png.count() > 0:
                png.click(timeout=5000)
                time.sleep(5)
                print("[DOWNLOAD] Initiated PNG download")
    except:
        pass

    return True

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=False,
            executable_path=BROWSER_PATH,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        if target == "project_showcase":
            edit_template("project_showcase", page)
        elif target == "service_proposal":
            edit_template("service_proposal", page)
        elif target == "service_banner":
            edit_template("service_banner", page)
        elif target == "all":
            for key in TEMPLATES:
                edit_template(key, page)
                time.sleep(5)
        else:
            print(f"Unknown target: {target}")

        input("\nPress Enter to close browser...")
        browser.close()

if __name__ == "__main__":
    main()
