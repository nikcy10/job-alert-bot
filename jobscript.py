import os
import time
import requests
import schedule
from bs4 import BeautifulSoup

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

sent_jobs = set()

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=data)
    print(f"[INFO] Telegram response: {response.status_code}")

def fetch_linkedin_jobs():
    print("[INFO] Searching LinkedIn for new jobs...")
    url = "https://www.linkedin.com/jobs/search?keywords=Software%20Developer&location=Mumbai%2C%20Maharashtra%2C%20India&f_TPR=r604800&f_E=1&f_E=2"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        job_cards = soup.find_all("a", class_="base-card__full-link")
        print(f"[INFO] Found {len(job_cards)} job cards.")

        new_jobs = 0
        for job in job_cards:
            job_link = job.get("href")
            job_title = job.get("aria-label", "Job")
            company_name = job.find_previous("h4").text.strip() if job.find_previous("h4") else "Unknown"

            if "*" in job_title or "*" in company_name:
                print(f"[SKIPPED] Obfuscated job: {job_title} at {company_name}")
                continue

            if job_link not in sent_jobs:
                message = f"[NEW JOB] {job_title} at {company_name} — {job_link}"
                send_to_telegram(message)
                sent_jobs.add(job_link)
                new_jobs += 1

        if new_jobs == 0:
            send_to_telegram("✅ No new jobs found this hour. Staying vigilant!")

    except Exception as e:
        print(f"[ERROR] Failed to fetch jobs: {e}")
        send_to_telegram("❌ Bot encountered an error while searching jobs.")

def job_runner():
    print("[START] Job bot is running...")
    fetch_linkedin_jobs()
    print("[WAIT] Sleeping for 1 hour...")

schedule.every(1).hours.do(job_runner)

if __name__ == "__main__":
    job_runner()  # run once at start
    while True:
        schedule.run_pending()
        time.sleep(1)
