"""Create 2 more Nafezly services"""
import sys, time
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
        if (!el) return 'NOT FOUND';
        el.value = args.v;
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
        return 'OK';
    }""", {"s": selector, "v": value})

def create_service(title, desc, price, period, instructions, label):
    print(f"\n=== Creating: {title} ===")
    page.goto('https://nafezly.com/service/create', timeout=120000)
    time.sleep(3)
    if 'login' in page.url.lower():
        for _ in range(60):
            time.sleep(1)
            if 'login' not in page.url.lower(): break
    print(f'Page: {page.url}')
    
    ev("input[name='service_title']", title)
    page.select_option("select[name='specialization_id']", "1")
    time.sleep(2)
    # Select sub-specialization
    subs = page.eval_on_selector_all("select[name='sub_specialization_id'] option", 
        "opts => opts.map(o => ({v: o.value, t: o.textContent})).filter(o => o.v)")
    if subs:
        page.select_option("select[name='sub_specialization_id']", subs[0]['v'])
        print(f'Sub: {subs[0]}')
    
    ev("textarea[name='service_description']", desc)
    page.select_option("select[name='period']", str(period))
    page.select_option("select[name='service_price']", str(price))
    ev("textarea[name='seller_instructions']", instructions)
    
    print('Submitting...')
    btn = page.locator('#submitEvaluation')
    if btn.is_visible():
        btn.click()
        time.sleep(4)
        print(f'Submitted! URL: {page.url}')
        html = page.content()
        (TEMP / f'created_{label}.html').write_text(html, encoding='utf-8')
        return page.url
    else:
        print('Submit button not found')
        return None

# Service 2: Workflow Automation - $20
url2 = create_service(
    title="Workflow Automation with n8n",
    desc="""I will set up a complete workflow automation system for your business using n8n. Automate repetitive tasks, connect your apps, and save hours of manual work every day.

What you get:
1. Custom workflow automation built on n8n
2. Integration with 2-3 apps/services of your choice
3. Testing and deployment
4. Documentation on how it works

Use cases:
- Auto-respond to customer inquiries
- Sync data between CRM, email, and Slack
- Schedule and automate social media posts
- Generate reports automatically

Tools: n8n, APIs, Webhooks
Delivery: 3-5 days
Support: 7 days after delivery""",
    price=20,
    period=5,
    instructions="Please describe the task you want automated and which apps/services you use. I will contact you within 24 hours.",
    label="service2"
)

# Service 3: AI Chatbot - $30
url3 = create_service(
    title="AI Chatbot Development (n8n + OpenAI)",
    desc="""I will build a smart AI chatbot for your business that handles customer inquiries 24/7. Powered by n8n and OpenAI, your chatbot will understand natural language and provide instant responses.

What you get:
1. AI chatbot integrated with your website or Telegram
2. Custom knowledge base training
3. FAQ automation with smart replies
4. CRM / database integration
5. Analytics dashboard

Features:
- Natural language understanding
- Multi-language support (Arabic + English)
- 24/7 automated responses
- Easy to update and maintain

Tools: n8n, OpenAI GPT, Telegram API, Website Widget
Delivery: 5-7 days
Support: 14 days after delivery""",
    price=30,
    period=7,
    instructions="Please specify which platform you need the chatbot for (website, Telegram, WhatsApp) and what kind of questions your customers typically ask.",
    label="service3"
)

print(f"\n\n=== RESULTS ===")
print(f"Service 1 (AI Agent): already exists")
print(f"Service 2 (Workflow): {url2}")
print(f"Service 3 (Chatbot): {url3}")
input('Press ENTER to close...')
ctx.close()
pw.stop()
