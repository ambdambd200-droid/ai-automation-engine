"""Find best skill matches from Nafezly's predefined list"""
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

# Get ALL options
all_opts = page.evaluate("""() => {
    const select = document.querySelector('select[name="tag_id[]"]');
    if (!select || !select.selectize) return [];
    const opts = select.selectize.options;
    return Object.keys(opts).map(k => ({v: k, t: (opts[k].text || '')}));
}""")

print(f"Total skills: {len(all_opts)}")

# Search for relevant keywords
keywords = ['ai', 'auto', 'chat', 'bot', 'python', 'api', 'workflow', 'n8n', 'openai', 'gpt',
            'ذكاء', 'برمج', 'تقن', 'شبكة', 'بيان', 'تطبي', 'سحاب', 'انترنت', 'اتصال',
            'machine', 'deep', 'neural', 'data', 'analysis', 'integration', 'code',
            'ruby', 'python', 'java', 'script', 'web', 'software', 'developer',
            'back', 'front', 'full', 'database', 'cloud', 'server', 'devops',
            'automation', 'automated', 'api', 'rest', 'micro', 'service',
            'logic', 'program', 'algorithm', 'system', 'analyst', 'engineer']

found = {}
for kw in keywords:
    for o in all_opts:
        if o['t'] and kw.lower() in o['t'].lower():
            found[o['v']] = o['t']

print(f"\nMatching skills ({len(found)}):")
for v, t in sorted(found.items(), key=lambda x: x[1] or ''):
    if v and t:
        print(f"  {v:5s}: {t}")

# Now clear and set the BEST matching skills
best_skills = []
for v, t in found.items():
    if not v or not t: continue
    if any(w in t.lower() for w in ['ai', 'chat', 'auto', 'python', 'api', 'workflow',
                                      'data', 'cloud', 'برمج', 'تقن', 'تطبي', 'سحاب',
                                      'machine', 'neural', 'software', 'database',
                                      'تحليل', 'معالجة', 'شبكة', 'انترنت', 'اتصال',
                                      'development', 'programming', 'logic', 'system']):
        best_skills.append((v, t))

print(f"\nBest skills ({len(best_skills)}):")
for v, t in best_skills[:20]:
    print(f"  {v:5s}: {t}")

# Set top 10
top10 = [s[0] for s in best_skills[:12]]
print(f"\nSetting top {len(top10)} skills...")

result = page.evaluate(f"""() => {{
    const select = document.querySelector('select[name="tag_id[]"]');
    if (!select || !select.selectize) return 'no selectize';
    const sz = select.selectize;
    sz.clear();
    sz.addItems({top10});
    return 'added ' + sz.items.length + ' skills';
}}""")
print(f"Result: {result}")

# Save
btn = page.query_selector("button:has-text('حفظ')")
if btn:
    btn.click()
    time.sleep(2)
    print("Saved!")
else:
    print("No save btn")

page.screenshot(path=TEMP / 'best_skills.png')
print("Done!")
input("Press Enter...")
ctx.close()
pw.stop()
