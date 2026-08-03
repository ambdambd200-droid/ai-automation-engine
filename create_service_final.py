"""Create service on Nafezly"""
import sys, time, json
from pathlib import Path
TEMP = Path(r'C:\Users\A\Desktop\Money\Temp')

from playwright.sync_api import sync_playwright
pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data',
    executable_path=r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    headless=False, args=['--no-sandbox'], viewport={'width':1366,'height':768})
page = ctx.new_page()
page.set_default_timeout(120000)

def ev(selector, value):
    return page.evaluate("""(args) => {
        const el = document.querySelector(args.s);
        if (!el) return 'NOT FOUND: ' + args.s;
        const tag = el.tagName.toLowerCase();
        el.value = args.v;
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
        return 'OK ' + tag + '.' + (el.name || el.id);
    }""", {"s": selector, "v": value})

page.goto('https://nafezly.com/service/create', timeout=120000)
time.sleep(3)
print(f'Page: {page.url}')

if 'login' in page.url.lower():
    print('Need login - waiting...')
    for _ in range(60):
        time.sleep(1)
        if 'login' not in page.url.lower():
            break

print(f'Logged in. URL: {page.url}')

# Fill form
title = 'بناء وكيل ذكاء اصطناعي (AI Agent) باستخدام n8n'
r = ev("input[name='service_title']", title)
print(f'Title: {r}')

# Select specialization = برمجة (value=1)
page.select_option("select[name='specialization_id']", "1")
time.sleep(2)
print('Selected specialization = برمجة')
html = page.content()
(TEMP / 'after_specialization.html').write_text(html, encoding='utf-8')
# Check if sub-specialization loaded
subs = page.eval_on_selector_all("select[name='sub_specialization_id'] option", "opts => opts.map(o => ({v: o.value, t: o.textContent.trim().substring(0,40)})).filter(o => o.v)")
print(f'Sub-specializations: {subs}')
# Try to select first real sub
real_subs = [s for s in subs if s['v']]
if real_subs:
    page.select_option("select[name='sub_specialization_id']", real_subs[0]['v'])
    print(f'Selected sub: {real_subs[0]}')

# Description (min 200 chars)
desc = """سأقوم ببناء وكيل ذكاء اصطناعي (AI Agent) متكامل ومخصص لاحتياجات عملك باستخدام منصة n8n. هذا الوكيل سيقوم بأتمتة المهام المتكررة وربط التطبيقات والخدمات التي تستخدمها في شركتك.

ماذا ستحصل:
1. وكيل AI واحد متكامل يعمل على منصة n8n
2. ربط مع الخدمات التي تختارها (API)
3. اختبار وتشغيل كامل للنظام
4. شرح مفصل لكيفية استخدام الوكيل

الأدوات المستخدمة: n8n، APIs، نماذج ذكاء اصطناعي
مدة التسليم: 3-5 أيام"""
r = ev("textarea[name='service_description']", desc)
print(f'Description: {r}')

# Period = 5 ايام
page.select_option("select[name='period']", "5")
print('Period: 5 ايام')

# Price = $25
page.select_option("select[name='service_price']", "25")
print('Price: $25')

# Instructions (min 50 chars)
instructions = """يرجى توضيح الخدمات التي تريد ربطها والنظام الذي تعمل عليه حالياً. سأتواصل معك خلال 24 ساعة من الشراء لبدء العمل."""
r = ev("textarea[name='seller_instructions']", instructions)
print(f'Instructions: {r}')

# Submit
print('Clicking submit...')
btn = page.locator('#submitEvaluation')
if btn.is_visible():
    btn.click()
    time.sleep(5)
    print(f'Submitted! URL: {page.url}')
    html = page.content()
    (TEMP / 'after_submit.html').write_text(html, encoding='utf-8')
else:
    print('Submit button not visible')

input('Press ENTER to quit...')
ctx.close()
pw.stop()
