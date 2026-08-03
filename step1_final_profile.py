"""Complete profile fix - bio, job title, skills, personal data. Then search & bid projects."""
import sys, time, json
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

def js_set(sel, val):
    return page.evaluate("""(a) => {
        const el = document.querySelector(a.s);
        if(!el) return 'NF'; el.value = a.v;
        el.dispatchEvent(new Event('input',{b:true})); el.dispatchEvent(new Event('change',{b:true}));
        return 'OK';
    }""", {"s": sel, "v": val})

# ===== 1. BIO + JOB TITLE =====
print("[1] Setting bio and job title...")
page.goto('https://nafezly.com/profile/nafezly-settings', timeout=180000)
time.sleep(4)
if 'login' in page.url.lower():
    for _ in range(60):
        time.sleep(1)
        if 'login' not in page.url.lower(): break

new_bio = """أنا علاء فتحي، مهندس أتمتة ذكاء اصطناعي من غزة. متخصص في بناء أنظمة أتمتة متكاملة باستخدام n8n والذكاء الاصطناعي.

أقدم:
- بناء وكلاء ذكاء اصطناعي (AI Agents) باستخدام n8n و OpenAI
- أتمتة سير العمل وربط التطبيقات والخدمات
- تطوير Chatbots ذكية لتليجرام وواتساب وإنستغرام
- ربط APIs وأنظمة السحابة"""

js_set("textarea[name='bio']", new_bio)
js_set("input[name='job_title']", "مهندس أتمتة ذكاء اصطناعي")
time.sleep(1)
page.evaluate("""() => {
    const b = document.querySelector('button');
    const btns = document.querySelectorAll('button');
    for(const b of btns) { if(b.innerText.includes('حفظ')) { b.click(); return; } }
}""")
time.sleep(2)
print("  Bio + job title saved")

# ===== 2. DUMP ALL SKILLS =====
print("[2] Dumping all available skills...")
page.goto('https://nafezly.com/profile/nafezly-settings', timeout=180000)
time.sleep(3)

skills_raw = page.evaluate("""() => {
    const sel = document.querySelector('select[name="tag_id[]"]');
    if(!sel || !sel.selectize) return [];
    const opts = sel.selectize.options;
    return Object.keys(opts).map(k => ({v: k, t: opts[k].text || ''}));
}""")

with open(TEMP / 'nafezly_skills.txt', 'w', encoding='utf-8') as f:
    for s in skills_raw:
        f.write(f"{s['v']}\t{s['t']}\n")
print(f"  Dumped {len(skills_raw)} skills to nafezly_skills.txt")

# ===== 3. READ FILE AND FIND BEST SKILLS =====
# Read the file and let the AI decide
# For now, dump it to stdout for me to analyze
tech_kw = ['ai', 'chat', 'bot', 'python', 'api', 'workflow', 'data', 'cloud',
           'machine', 'neural', 'software', 'database', 'integration', 'analytics',
           'server', 'network', 'script', 'logic', 'system', 'برمج', 'تقن', 'بيان',
           'تطبي', 'تحليل', 'معالجة', 'هندسة', 'تطوير', 'ذكاء', 'اتصال', 'شبكة', 'سحاب',
           'html', 'css', 'javascript', 'node', 'react', 'angular', 'vue', 'django',
           'flask', 'ruby', 'php', 'java', 'c++', 'c#', 'go', 'rust', 'swift',
           'kotlin', 'sql', 'nosql', 'mongo', 'mysql', 'postgres', 'aws', 'azure',
           'docker', 'kubernetes', 'git', 'linux', 'windows', 'agile', 'scrum',
           'devops', 'backend', 'frontend', 'fullstack', 'wordpress', 'shopify',
           'الذكاء', 'البيانات', 'الشبكات', 'البرمج', 'التقنية', 'التطبيقات']

best = []
for s in skills_raw:
    if not s['t']: continue
    t = s['t'].lower()
    for kw in tech_kw:
        if kw in t:
            best.append(s)
            break

print(f"  Found {len(best)} relevant skills")
for s in best[:30]:
    print(f"    {s['v']:5s}: {s['t']}")

# ===== 4. SET BEST SKILLS =====
if best:
    best_ids = [s['v'] for s in best[:15]]
    result = page.evaluate(f"""() => {{
        const sel = document.querySelector('select[name="tag_id[]"]');
        if(!sel || !sel.selectize) return 'no selectize';
        sel.selectize.clear();
        sel.selectize.addItems({json.dumps(best_ids)});
        return 'added ' + sel.selectize.items.length + ' skills';
    }}""")
    print(f"  Skills result: {result}")
    
    page.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for(const b of btns) { if(b.innerText.includes('حفظ')) { b.click(); return; } }
    }""")
    time.sleep(2)
    print("  Skills saved")

# ===== 5. PERSONAL DATA =====
print("[3] Personal data...")
page.goto('https://nafezly.com/profile/personal-data', timeout=180000)
time.sleep(3)
page.evaluate("""() => {
    const btns = document.querySelectorAll('button');
    for(const b of btns) { if(b.innerText.includes('حفظ')) { b.click(); return; } }
}""")
time.sleep(2)
print("  Personal data verified")

# ===== 6. SEARCH PROJECTS =====
print("\n===== STEP 2: SEARCHING PROJECTS =====")
targets = [
    'AI Agents', 'n8n', 'automation', 'chatbot', 
    'وكيل ذكاء', 'أتمتة', 'بوت', 'n8n'
]
projects_found = []

for t in targets:
    print(f"\n[Search] {t}...")
    url = f'https://nafezly.com/projects?key={t.replace(" ", "+")}'
    page.goto(url, timeout=180000)
    time.sleep(4)
    page.screenshot(path=TEMP / f'search_{t[:10].replace(" ","_")}.png')
    
    # Get project cards
    projects = page.eval_on_selector_all("a[href*='/project/'], [class*='project'] a, [class*='Project'] a",
        """els => els.map(e => ({href: e.href, text: e.innerText?.trim().substring(0,100)})).filter(e => e.href && e.href.includes('/project/'))""")
    
    if not projects:
        print(f"  No projects found for '{t}'")
        continue
    
    print(f"  Found {len(projects)} project links")
    for p in projects[:3]:
        projects_found.append(p['href'])
        print(f"    {p['href'][:60]}")

# ===== 7. OPEN PROJECTS AND BID =====
print("\n===== STEP 3: SUBMITTING BIDS =====")
project_urls = list(set(projects_found))[:5]
print(f"Will check {len(project_urls)} unique projects")

for i, p_url in enumerate(project_urls):
    print(f"\n[{i+1}/{len(project_urls)}] {p_url}")
    page.goto(p_url, timeout=180000)
    time.sleep(3)
    
    # Check if there's a bid/offer button
    bid_btns = page.eval_on_selector_all("button, a", """els => els.map(e => ({
        text: e.innerText?.trim().substring(0,30),
        href: e.href || '',
        visible: e.offsetParent !== null
    })).filter(e => e.visible && e.text && (
        e.text.includes('تقديم') || e.text.includes('عرض') || 
        e.text.includes('offer') || e.text.includes('bid') ||
        e.text.includes('أرسل') || e.text.includes('send')
    ))""")
    
    if bid_btns:
        print(f"  Bid button found: {bid_btns[0]['text']}")
    else:
        print(f"  No bid button - checking page content")
    
    page.screenshot(path=TEMP / f'project_{i}.png')

print(f"\n=== ALL DONE! ===")
page.screenshot(path=TEMP / 'final_state.png')
input("Press Enter...")
ctx.close()
pw.stop()
