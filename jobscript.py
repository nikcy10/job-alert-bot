import os
import time
import json
import requests
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SEEN_JOBS_FILE = os.getenv("SEEN_JOBS_FILE", "seen_jobs.json")
SCRAPE_INTERVAL_MINUTES = 60

def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        return set(json.load(open(SEEN_JOBS_FILE)))
    return set()

def save_seen_jobs(seen_jobs):
    os.makedirs(os.path.dirname(SEEN_JOBS_FILE) or ".", exist_ok=True)
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen_jobs), f)

def send_to_telegram(new_jobs):
    if new_jobs:
        msg = "🚀 *New Jobs (Last Hour)*\n\n" + "\n\n".join(
            f"{src} • *{title}*\n{link}" for src, title, link in new_jobs
        )
    else:
        msg = "✅ No new jobs found in the last hour."

    resp = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
    )
    print(f"[TELEGRAM] status {resp.status_code}")

def fetch_jobs(url, parser_func):
    try:
        return parser_func(requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text)
    except Exception as e:
        print(f"[ERROR] Scraping failed for {url}: {e}")
        return []

def scrape_linkedin(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for card in soup.select(".base-card"):
        t = card.select_one("h3")
        a = card.select_one("a.base-card__full-link")
        if t and a:
            jobs.append(("LinkedIn", t.get_text(strip=True), a["href"].split("?")[0]))
    return jobs

def scrape_indeed(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for a in soup.select("a[data-jk]"):
        span = a.select_one("span")
        if span:
            jobs.append(("Indeed", span.text.strip(), "https://in.indeed.com/viewjob?jk=" + a["data-jk"]))
    return jobs

def scrape_internshala(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs, titles = [], soup.select(".individual_internship_header .heading_4_5")
    links = soup.select(".individual_internship_header a")
    for t, a in zip(titles, links):
        link = a["href"]
        if not link.startswith("http"):
            link = "https://internshala.com" + link
        jobs.append(("Internshala", t.get_text(strip=True), link))
    return jobs

def scrape_naukri(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for art in soup.select("article.jobTuple"):
        t = art.select_one("a.title")
        if t:
            jobs.append(("Naukri", t.text.strip(), t["href"]))
    return jobs

def scrape_foundit(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for card in soup.select(".job-tuple")[:10]:
        t = card.select_one("h3")
        a = card.select_one("a")
        if t and a:
            jobs.append(("Foundit", t.text.strip(), "https://www.foundit.in" + a["href"]))
    return jobs

SCRAPERS = [
    ("LinkedIn", "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Software%20Engineer%20OR%20Web%20Developer&location=Mumbai&f_E=1%2C2&f_TPR=r604800", scrape_linkedin),
    ("Indeed", "https://in.indeed.com/jobs?q=software+developer&l=Mumbai&fromage=7", scrape_indeed),
    ("Internshala", "https://internshala.com/internships/web-development-internship-in-mumbai", scrape_internshala),
    ("Naukri", "https://www.naukri.com/software-developer-jobs-in-mumbai?experience=0", scrape_naukri),
    ("Foundit", "https://www.foundit.in/search/software-developer-jobs-in-mumbai", scrape_foundit),
]

def main():
    seen = load_seen_jobs()
    print(f"[START] Loaded {len(seen)} seen jobs")

    while True:
        new_jobs = []
        for src, url, parser in SCRAPERS:
            print(f"[INFO] Scraping {src}...")
            html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text
            for job in parser(html):
                key = hashlib.md5(job[2].encode()).hexdigest()
                if key not in seen:
                    seen.add(key)
                    new_jobs.append(job)
        send_to_telegram(new_jobs)
        save_seen_jobs(seen)
        print(f"[END] Cycle complete — sleeping {SCRAPE_INTERVAL_MINUTES} minutes.")
        time.sleep(SCRAPE_INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    main()
