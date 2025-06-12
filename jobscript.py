import os
import time
import requests
import hashlib
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# File to store sent jobs
SENT_JOBS_FILE = "sent_jobs.txt"
SENT_JOBS = set()

# Load sent jobs from file
if os.path.exists(SENT_JOBS_FILE):
    with open(SENT_JOBS_FILE, "r") as f:
        for line in f:
            SENT_JOBS.add(line.strip())

# Utility to send message to Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

# Hash job uniquely
def job_hash(title, company, link):
    return hashlib.md5(f"{title}{company}{link}".encode()).hexdigest()

# Extract jobs from LinkedIn search
def search_linkedin_jobs():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    url = "https://www.linkedin.com/jobs/search/?keywords=software%20engineer%20OR%20web%20developer%20OR%20frontend%20developer%20OR%20backend%20developer&location=Mumbai&f_E=1&f_TPR=r604800"

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.select(".base-card")

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
    return jobs

# Main function to gather jobs and send message
def check_jobs():
    all_new_jobs = search_linkedin_jobs()
    if all_new_jobs:
        message = "📢 <b>New Job Alerts:</b>\n\n"
        for title, company, link in all_new_jobs:
            message += f"<b>{title}</b>\n{company}\n<a href='{link}'>Apply Here</a>\n\n"
        send_telegram_message(message.strip())
    else:
        send_telegram_message("🔍 No new jobs found in the last hour.")

# Run every hour
if __name__ == "__main__":
    while True:
        check_jobs()
        time.sleep(3600)  # 1 hour
