"""Direct Canva template editing via pyautogui."""
import pyautogui
import time
import os
import subprocess
import sys

SCREEN_W, SCREEN_H = 1366, 768
BRAVE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

TEMPLATES = {
    "project_showcase": "https://www.canva.com/templates/EAFwckKNjDE/",
    "service_proposal": "https://www.canva.com/templates/EAGH8jq6UhE/",
    "service_banner": "https://www.canva.com/design/DAHM0gnZq5E/JGEQJE2gVkYhJiiXzDy30A/edit",
}

def human_type(text, interval=0.08):
    pyautogui.write(text, interval=interval)

def wait_and_click(x, y, delay=2):
    time.sleep(delay)
    pyautogui.click(x, y)

def open_brave_with_url(url):
    subprocess.Popen([BRAVE, f"--new-window={url}", "--no-sandbox"])
    time.sleep(5)

def edit_template(name, url):
    print(f"\n{'='*60}")
    print(f"Editing: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    open_brave_with_url(url)
    
    # Wait for page load (slow network = 30s)
    print("Waiting 30s for page load...")
    time.sleep(30)
    
    # Take screenshot to see what happened
    ss = pyautogui.screenshot(f"C:\\Users\\A\\Desktop\\Money\\Temp\\canva_step_{name}_1.png")
    print(f"Screenshot 1 saved ({len(ss.tobytes())//1024}KB)")
    
    # Try to click "Use template" button (center-ish of screen, lower half)
    print("Looking for Use template button...")
    # Try clicking at common template button positions
    for y_pos in [500, 550, 600, 450, 400]:
        pyautogui.click(SCREEN_W//2, y_pos)
        time.sleep(1)
    
    # Wait for editor to load
    print("Waiting 20s for editor to load...")
    time.sleep(20)
    
    # Click center of canvas to select text
    print("Clicking canvas center...")
    pyautogui.click(SCREEN_W//2, SCREEN_H//2 - 50)
    time.sleep(2)
    
    # Select all and type
    print("Selecting all text...")
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(1)
    
    # Type new text
    text = "AI Automation Engineer\nAlaa Fathi\nAI Agents · Workflow Automation · Chatbots · n8n Integration"
    print(f"Typing: {text[:50]}...")
    human_type(text)
    time.sleep(2)
    
    # Try to exit edit mode
    pyautogui.press('esc')
    time.sleep(1)
    
    # Take screenshot
    ss = pyautogui.screenshot(f"C:\\Users\\A\\Desktop\\Money\\Temp\\canva_step_{name}_2.png")
    print(f"Screenshot 2 saved")
    
    # Try to download: Ctrl+Shift+S (Save/Download)
    print("Trying to download...")
    pyautogui.hotkey('ctrl', 'shift', 's')
    time.sleep(3)
    pyautogui.press('enter')
    time.sleep(3)
    
    print(f"Done with {name}")

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if target == "all":
        for name, url in TEMPLATES.items():
            edit_template(name, url)
            time.sleep(5)
    elif target in TEMPLATES:
        edit_template(target, TEMPLATES[target])
    else:
        print(f"Unknown: {target}. Options: {list(TEMPLATES.keys()) + ['all']}")

if __name__ == "__main__":
    main()
