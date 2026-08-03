"""Replace skills on Nafezly profile using selectize API"""
import sys, time, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
from playwright.sync_api import sync_playwright

TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')

pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data',
    executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    headless=False, args=['--no-sandbox'], viewport={'width':1280,'height':800})
page = ctx.new_page()
page.set_default_timeout(120000)

print("Opening profile settings...")
page.goto('https://nafezly.com/profile/nafezly-settings', timeout=180000)
time.sleep(4)

if 'login' in page.url.lower():
    for _ in range(60):
        time.sleep(1)
        if 'login' not in page.url.lower(): break

# Use selectize API to clear all skills and add new ones
result = page.evaluate("""() => {
    const select = document.querySelector('select[name="tag_id[]"]');
    if (!select) return 'select not found';
    
    // Access selectize instance
    const selectize = select.selectize;
    if (!selectize) return 'selectize not initialized';
    
    // Get current items
    const current = selectize.items;
    
    // Clear all
    selectize.clear();
    
    // Try to add new skills
    // First, check what options are available
    const availableOptions = selectize.options;
    
    return {
        cleared: current,
        availableKeys: Object.keys(availableOptions).slice(0, 20),
        availableLabels: Object.values(availableOptions).slice(0, 20).map(o => o.text)
    };
}""")

print(f"Selectize results: {result}")

# Check available options to find AI/automation related ones
all_options = page.evaluate("""() => {
    const select = document.querySelector('select[name="tag_id[]"]');
    if (!select || !select.selectize) return {};
    return Object.values(select.selectize.options).map(o => ({v: o.value, t: o.text}));
}""")
print(f"\nAll available skill options ({len(all_options)}):")
matching = [o for o in all_options if any(w in o['t'].lower() for w in ['ai', 'n8n', 'auto', 'chat', 'bot', 'python', 'api', 'workflow', 'برمج', 'تقن', 'ذكاء', 'شبكة', 'بيان', 'تطبي', 'سحاب'])]
for m in matching:
    print(f"  {m['v']}: {m['t']}")

# Try to add matching skills via selectize
add_result = page.evaluate("""() => {
    const select = document.querySelector('select[name="tag_id[]"]');
    if (!select || !select.selectize) return 'no selectize';
    const sz = select.selectize;
    // Add all matching tech skills
    const toAdd = [];
    for (const [key, opt] of Object.entries(sz.options)) {
        const t = opt.text.toLowerCase();
        if (t.includes('ai') || t.includes('n8n') || t.includes('automation') || 
            t.includes('chatbot') || t.includes('python') || t.includes('api') ||
            t.includes('workflow') || t.includes('ذكاء') || t.includes('برمجة') ||
            t.includes('تقنية') || t.includes('تطبيقات')) {
            toAdd.push(opt);
        }
    }
    // Couldn't find exact matches, add by value
    if (toAdd.length === 0) {
        // Just add a few manually
        return 'no matching skills found in list';
    }
    sz.addItems(toAdd.map(o => o.value));
    return 'added: ' + toAdd.map(o => o.text).join(', ');
}""")
print(f"Add result: {add_result}")

# Save
print("\nSaving...")
btn = page.query_selector("button:has-text('حفظ')")
if btn:
    btn.click()
    time.sleep(2)
    print("Saved!")
else:
    print("No save button found")

page.screenshot(path=TEMP / 'skills_updated.png')
print("\nDone!")
input("Press Enter...")
ctx.close()
pw.stop()
