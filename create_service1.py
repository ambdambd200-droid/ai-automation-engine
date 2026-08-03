"""Create Service 1: AI Agent Development ($25) on Nafezly"""
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
        el.value = args.v;
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
        return 'OK';
    }""", {"s": selector, "v": value})

page.goto('https://nafezly.com/service/create', timeout=120000)
time.sleep(3)
print(f'URL: {page.url}')

if 'login' in page.url.lower():
    print('Need login - waiting 60s...')
    for _ in range(60):
        time.sleep(1)
        if 'login' not in page.url.lower():
            break

print(f'Logged in. URL: {page.url}')

# Title
title = 'AI Agent Development - بناء وكيل ذكاء اصطناعي'
r = ev("input[name='service_title']", title)
print(f'Title: {r}')
time.sleep(1)

# Specialization = برمجة (ID 1)
page.select_option("select[name='specialization_id']", "1")
time.sleep(2)
print('Specialization: برمجة')

# Sub-specialization
subs = page.eval_on_selector_all("select[name='sub_specialization_id'] option",
    "opts => opts.map(o => ({v: o.value, t: o.textContent.trim().substring(0,40)})).filter(o => o.v)")
print(f'Sub-specializations: {subs}')
if subs:
    page.select_option("select[name='sub_specialization_id']", subs[0]['v'])
    print(f'Selected sub: {subs[0]}')

# Description
desc = """I will build a custom AI Agent (AI Agent) tailored to your business needs using n8n and OpenAI. This agent automates repetitive tasks, connects your apps, and works 24/7.

What you get:
1. One fully functional AI Agent running on n8n
2. Integration with your chosen services (API)
3. Complete testing and deployment
4. User guide and documentation

Tools: n8n, OpenAI GPT-4o, APIs
Delivery: 3-5 days
Support: 7 days after delivery"""
r = ev("textarea[name='service_description']", desc)
print(f'Description: {r}')

# Period = 5 days
page.select_option("select[name='period']", "5")
print('Period: 5 days')

# Price = $25
page.select_option("select[name='service_price']", "25")
print('Price: $25')

# Instructions
instructions = """Please describe what systems you want to connect and what tasks you want automated. I will contact you within 24 hours of purchase to start."""
r = ev("textarea[name='seller_instructions']", instructions)
print(f'Instructions: {r}')

# Submit
print('Clicking submit...')
btn = page.locator('#submitEvaluation')
if btn.is_visible():
    btn.click()
    time.sleep(5)
    print(f'Submitted! URL: {page.url}')
else:
    print('Submit button not found - trying to find any submit button')
    # Try alternative submit methods
    submit_btn = page.locator('button[type="submit"], input[type="submit"]').first
    if submit_btn.is_visible():
        submit_btn.click()
        time.sleep(5)
        print(f'Clicked! URL: {page.url}')
    else:
        print('No submit button found')

time.sleep(2)
print(f'\nFinal URL: {page.url}')
page.screenshot(path=TEMP / 'service1_created.jpg')

ctx.close()
pw.stop()
