"""
Job Scanner — FREE, no API costs.

Manually-driven job scanner. User opens Working Nomads / WWR, copies
job links into the list below, this script fetches the HTML and extracts
job details (title, company, salary if listed, description keywords).

Output: appends to Job_Queue.md with auto-extracted info.

Run:
  python job_scanner.py
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json

# Add jobs to scan here (paste from Working Nomads / WWR / LinkedIn)
JOB_URLS = [
    # "https://weworkremotely.com/remote-jobs/...",
    # "https://www.workingnomads.com/job/...",
]


def fetch(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"ERROR fetching {url}: {e}")
        return None


def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def extract_keywords(text, keywords):
    found = [k for k in keywords if k.lower() in text.lower()]
    return found


def score_job(text, my_skills):
    """Score 0-10 based on overlap with my skills."""
    my_skills = [s.lower() for s in my_skills]
    text_lower = text.lower()
    matches = sum(1 for s in my_skills if s in text_lower)
    return min(10, matches)


def scan(url):
    html = fetch(url)
    if not html:
        return None
    text = extract_text(html)

    # Heuristic: find title (first <h1>)
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else "(no title)"

    # Heuristic: look for $XX/hr or $XXX salary
    salary = None
    m = re.search(r"\$\d{1,3}(?:,\d{3})?(?:\s*[-/]\s*\$?\d{1,3}(?:,\d{3})?)?(?:\s*/\s*hr|\s*hourly)?", text)
    if m:
        salary = m.group(0)

    # Heuristic: extract first 5 lines as preview
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 30]
    preview = "\n".join(lines[:8])

    return {
        "url": url,
        "title": title,
        "salary": salary or "(not listed)",
        "preview": preview,
        "text": text,
    }


def main():
    if not JOB_URLS:
        print("=" * 60)
        print("JOB SCANNER")
        print("=" * 60)
        print("No URLs in JOB_URLS list.")
        print("Add job URLs to the JOB_URLS list in this script, then re-run.")
        print()
        print("Sources:")
        print("  - Working Nomads: https://www.workingnomads.com")
        print("  - We Work Remotely: https://weworkremotely.com")
        print("  - LinkedIn Jobs: search 'AI automation' remote")
        return

    print("=" * 60)
    print(f"JOB SCANNER — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"Scanning {len(JOB_URLS)} job URL(s)...\n")

    my_skills = [
        "AI", "automation", "Python", "Zapier", "Make", "n8n", "OpenAI",
        "API", "webhook", "no-code", "workflow", "prompt", "LLM",
        "Flask", "REST", "JSON", "data pipeline",
    ]

    results = []
    for url in JOB_URLS:
        print(f"Scanning: {url}")
        result = scan(url)
        if result:
            score = score_job(result["text"], my_skills)
            keywords = extract_keywords(result["text"], my_skills)
            result["score"] = score
            result["keywords"] = keywords
            results.append(result)
            print(f"  Title: {result['title']}")
            print(f"  Salary: {result['salary']}")
            print(f"  Match score: {score}/10")
            print(f"  Keywords: {', '.join(keywords[:10])}")
            print()

    # Save to JSON for later review
    out_file = f"job_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to: {out_file}")
    print()
    print("Next: pick high-score jobs (>6), add to Job_Queue.md, draft application.")


if __name__ == "__main__":
    main()
