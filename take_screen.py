"""Take screenshot using pyautogui"""
import pyautogui
from pathlib import Path
TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')
img = pyautogui.screenshot()
fp = TEMP / 'user_screen.png'
img.save(fp)
print(f"Screenshot saved: {fp} ({img.size})")
