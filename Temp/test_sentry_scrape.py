import sys, json, time, os, re
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
WORKSPACE = Path(r'C:\Users\A\Desktop\Money')

LOG = []
def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = '[%s] %s' % (ts, msg)
    print(line, flush=True)
    LOG.append(line)

def banner(text):
    log('=' * 60)
    log('  ' + text)
    log('=' * 60)

BRAVE_EXE = r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'
BRAVE_PROFILE = r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data'
MOSTAQL_URLS = [
    'https://mostaql.com/projects/ai-machine-learning',
    'https://mostaql.com/projects/development',
]
NAFEZLY_URL = 'https://nafezly.com/projects'
STATE_FILE = WORKSPACE / 'sentry_state.json'

KEYWORDS = [
    'n8n', 'automation', 'automate', 'ai', 'chatbot', 'bot',
    'workflow', 'api', 'integration', 'integrate',
    'python', 'flask', 'openai', 'agent',
    'scraping', 'webhook', 'telegram',
    'database', 'server', 'script', 'backend', 'development',
    'site', 'web', 'website', 'data',
    '\u0623\u062a\u0645\u062a\u0629', '\u0630\u0643\u0627\u0621 \u0627\u0635\u0637\u0646\u0627\u0639\u064a',
    '\u0648\u0643\u064a\u0644', '\u0631\u0628\u0637',
    '\u0628\u0631\u0645\u062c\u0629', '\u0645\u0637\u0648\u0631', '\u062a\u0637\u0648\u064a\u0631',
    '\u0642\u0627\u0639\u062f\u0629 \u0628\u064a\u0627\u0646\u0627\u062a',
]

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding='utf-8'))
        except:
            pass
    return {'seen_projects': {}, 'bids_submitted': []}

def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding='utf-8')

def mark_seen(state, url, status='skipped', reason=''):
    state.setdefault('seen_projects', {})[url] = {
        'first_seen': datetime.now().isoformat(),
        'status': status, 'reason': reason}
    save_state(state)

def score_project(title, desc):
    text = (title + ' ' + desc).lower()
    matches = sum(1 for kw in KEYWORDS if kw.lower() in text)
    kw_score = min(matches / 4.0, 1.0)
    len_bonus = min(len(desc) / 500, 0.2)
    score = kw_score * 0.8 + len_bonus * 0.2
    matched = [kw for kw in KEYWORDS[:5] if kw.lower() in text]
    reason = 'kw=%.2f' % kw_score
    if matched:
        reason += ', matched=' + ','.join(matched[:3])
    return min(score, 1.0), reason

from playwright.sync_api import sync_playwright
pw = sync_playwright().start()
log('Opening Brave...')
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=BRAVE_PROFILE, executable_path=BRAVE_EXE,
    headless=False, args=['--no-sandbox'],
    viewport={'width': 1366, 'height': 768})
page = ctx.new_page()
page.set_default_timeout(60000)
state = load_state()

banner('MOSTAQL DRY-RUN')
for url in MOSTAQL_URLS:
    log('Loading: ' + url)
    try:
        page.goto(url, wait_until='domcontentloaded')
        time.sleep(3)
        links = page.locator("a[href*='/project/']")
        urls = []
        for i in range(min(links.count(), 15)):
            try:
                h = links.nth(i).get_attribute('href')
                if h and '/project/' in h:
                    if not h.startswith('http'):
                        h = 'https://mostaql.com' + h
                    if h not in urls:
                        urls.append(h)
            except:
                pass
        log('  Found %d projects' % len(urls))
        for p_url in urls:
            norm = p_url.rstrip('/')
            if norm in state.get('seen_projects', {}):
                log('  [SEEN] ' + p_url[:60] + '...')
                continue
            log('  Opening: ' + p_url[:60] + '...')
            try:
                page.goto(p_url, wait_until='domcontentloaded')
                time.sleep(2)
                info = page.evaluate("""() => {
                    const t = document.querySelector('h1, h2')?.innerText || '';
                    const d = document.querySelector('[class*=\"desc\"], [class*=\"detail\"], [class*=\"content\"], article, p')?.innerText || '';
                    return {title: t.substring(0,200), desc: d.substring(0,800)};
                }""")
                if info and info.get('title'):
                    score, reason = score_project(info['title'], info['desc'])
                    t = info['title'][:60]
                    log('    Title: ' + t + ' | Score: %.2f (%s)' % (score, reason))
                    if score >= 0.15:
                        log('    >>> MATCH! Would generate bid')
                    else:
                        log('    >>> Below threshold')
                    mark_seen(state, norm, 'scored', 'score=%.2f' % score)
                else:
                    log('    No title found')
                    mark_seen(state, norm, 'error', 'no_title')
            except Exception as e:
                log('    ERROR: ' + str(e))
                mark_seen(state, norm, 'error', str(e)[:100])
    except Exception as e:
        log('  ERROR: ' + str(e))

banner('NAFEZLY DRY-RUN')
log('Loading: ' + NAFEZLY_URL)
try:
    page.goto(NAFEZLY_URL, wait_until='domcontentloaded')
    time.sleep(3)
    links = page.locator("a[href*='/project/']")
    urls = []
    for i in range(min(links.count(), 15)):
        try:
            h = links.nth(i).get_attribute('href')
            if h and '/project/' in h:
                if not h.startswith('http'):
                    h = 'https://nafezly.com' + h
                if h not in urls:
                    urls.append(h)
        except:
            pass
    log('  Found %d projects' % len(urls))
    for p_url in urls:
        norm = p_url.rstrip('/')
        if norm in state.get('seen_projects', {}):
            log('  [SEEN] ' + p_url[:60] + '...')
            continue
        log('  Opening: ' + p_url[:60] + '...')
        try:
            page.goto(p_url, wait_until='domcontentloaded')
            time.sleep(2)
            info = page.evaluate("""() => {
                const t = document.querySelector('h1, h2')?.innerText || '';
                const d = document.querySelector('[class*=\"desc\"], [class*=\"detail\"], [class*=\"content\"], article, p')?.innerText || '';
                return {title: t.substring(0,200), desc: d.substring(0,800)};
            }""")
            if info and info.get('title'):
                score, reason = score_project(info['title'], info['desc'])
                t = info['title'][:60]
                log('    Title: ' + t + ' | Score: %.2f (%s)' % (score, reason))
                if score >= 0.15:
                    log('    >>> MATCH! Would generate bid')
                else:
                    log('    >>> Below threshold')
                mark_seen(state, norm, 'scored', 'score=%.2f' % score)
            else:
                log('    No title found')
                mark_seen(state, norm, 'error', 'no_title')
        except Exception as e:
            log('    ERROR: ' + str(e))
            mark_seen(state, norm, 'error', str(e)[:100])
except Exception as e:
    log('  ERROR: ' + str(e))

log('')
banner('DONE')
log('Seen projects: %d' % len(state.get('seen_projects', {})))
log('Browser stays open.')
ctx.close()
pw.stop()
