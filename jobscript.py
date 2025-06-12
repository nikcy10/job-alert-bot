import os
import time
import requests
import hashlib
from bs4 import BeautifulSoup

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# File to store sent jobs
SENT_JOBS_FILE = "sent_jobs.txt"
SENT_JOBS = set()

# Load previously sent jobs
if os.path.exists(SENT_JOBS_FILE):
    with open(SENT_JOBS_FILE, "r") as f:
        for line in f:
            SENT_JOBS.add(line.strip())

print(f"[INFO] Loaded {len(SENT_JOBS)} previously sent jobs.")

# Send message to Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=data)
    print(f"[INFO] Telegram response: {response.status_code}")

# Unique job hash
def job_hash(title, company, link):
    return hashlib.md5(f"{title}{company}{link}".encode()).hexdigest()

# Scrape LinkedIn jobs
def search_linkedin_jobs():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    url = "https://www.linkedin.com/jobs/search/?keywords=software%20engineer%20OR%20web%20developer%20OR%20frontend%20developer%20OR%20backend%20developer&location=Mumbai&f_E=1&f_TPR=r604800"

    print("[INFO] Searching LinkedIn for new jobs...")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.select(".base-card")

    print(f"[INFO] Found {len(results)} job cards.")

    jobs = []
    for card in results:
        title_elem = card.select_one("h3.base-search-card__title")
        company_elem = card.select_one("h4.base-search-card__subtitle")
        link_elem = card.select_one("a.base-card__full-link")

        if title_elem and company_elem and link_elem:
            title = title_elem.text.strip()
            company = company_elem.text.strip()
            link = link_elem["href"].split("?")[0]

            hash_id = job_hash(title, company, link)
            if hash_id not in SENT_JOBS:
                SENT_JOBS.add(hash_id)
                with open(SENT_JOBS_FILE, "a") as f:
                    f.write(f"{hash_id}\n")
                jobs.append((title, company, link))
                print(f"[NEW JOB] {title} at {company} — {link}")
            else:
                print(f"[SKIPPED] Already sent: {title} at {company}")
    return jobs

# Master function
def check_jobs():
    new_jobs = search_linkedin_jobs()
    if new_jobs:
        message = "📢 <b>New Job Alerts:</b>\n\n"
        for title, company, link in new_jobs:
            message += f"<b>{title}</b>\n{company}\n<a href='{link}'>Apply Here</a>\n\n"
        send_telegram_message(message.strip())
    else:
        print("[INFO] No new jobs found.")
        send_telegram_message("🔍 No new jobs found in the last hour.")

# Run every hour
if __name__ == "__main__":
    print("[START] Job bot is running...")
    while True:
        check_jobs()
        print("[WAIT] Sleeping for 1 hour...\n")
        time.sleep(3600)
