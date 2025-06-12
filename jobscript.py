import os
import json
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SEEN_JOBS_FILE = "seen_jobs.json"

def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen_jobs(seen_jobs):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen_jobs), f)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)
    print(f"[INFO] Telegram response: {response.status_code}")

def scrape_linkedin():
    print("[INFO] Scraping LinkedIn...")
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0"}
    url = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"
           "keywords=Software%20Engineer%20OR%20Web%20Developer%20OR%20Frontend%20Developer"
           "&location=Mumbai%2C%20Maharashtra%2C%20India&f_E=1%2C2&f_TPR=r604800")
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print("[WARN] LinkedIn scraping failed.")
        return jobs
    soup = BeautifulSoup(res.text, "html.parser")
    job_cards = soup.find_all("a", class_="base-card__full-link")
    print(f"[INFO] LinkedIn found {len(job_cards)} jobs.")
    for job in job_cards:
        title = job.get_text(strip=True)
        link = job.get("href").split("?")[0]
        jobs.append(f"<b>{title}</b>\n{link}")
    return jobs

def scrape_internshala():
    print("[INFO] Scraping Internshala...")
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0"}
    url = "https://internshala.com/internships/web-development-internship-in-mumbai"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print("[WARN] Internshala scraping failed.")
        return jobs
    soup = BeautifulSoup(res.text, "html.parser")
    job_titles = soup.select(".individual_internship_header .heading_4_5")
    job_links = [a['href'] for a in soup.select(".individual_internship_header a")]
    for title, link in zip(job_titles, job_links):
        if "internshala.com" not in link:
            link = "https://internshala.com" + link
        jobs.append(f"<b>{title.get_text(strip=True)}</b>\n{link}")
    print(f"[INFO] Internshala found {len(jobs)} jobs.")
    return jobs

def run_once():
    seen_jobs = load_seen_jobs()
    new_jobs = []

    all_jobs = scrape_linkedin() + scrape_internshala()
    for job in all_jobs:
        if job not in seen_jobs:
            new_jobs.append(job)
            seen_jobs.add(job)

    if new_jobs:
        message = "\n\n".join(new_jobs)
    else:
        message = "No new jobs found in the last hour."

    send_telegram_message(message)
    save_seen_jobs(seen_jobs)
    print("[END] Script execution complete.")

if __name__ == "__main__":
    run_once()
