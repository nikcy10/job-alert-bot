import os
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ROLES = [
    "software+developer",
    "software+engineer",
    "web+developer",
    "frontend+developer",
    "backend+developer"
]

LOCATION = "Mumbai"

KEYWORDS = [
    'fresher', '0-1 year', 'entry level', 'graduate',
    'junior', 'trainee', 'immediate joiner', 'campus',
    'hiring freshers', 'intern to full-time'
]

# --- STATE ---
sent_jobs = set()
pending_jobs = []

# --- UTILITY FUNCTIONS ---

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram error:", e)

def is_valid_link(url):
    try:
        r = requests.head(url, allow_redirects=True, timeout=10)
        return r.status_code == 200
    except:
        return False

def get_job_id(link):
    try:
        return link.split('-')[-1].split('?')[0]
    except:
        return link

# --- SCRAPER FUNCTION ---

def scrape_jobs():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Scraping...")
    headers = {"User-Agent": "Mozilla/5.0"}

    for role in ROLES:
        url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={role}"
            f"&location={LOCATION}"
            f"&f_E=1&f_TP=1&f_WT=2&f_AL=true"
           f"&f_TPR=r604800"  # ✅ Filter: Posted in last 24 hours
        )

        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, "html.parser")
            job_cards = soup.find_all("a", class_="base-card__full-link")

            for job in job_cards:
                title = job.text.strip().lower()
                link = job['href'].replace("in.linkedin.com", "www.linkedin.com")
                job_id = get_job_id(link)

                if job_id in sent_jobs:
                    continue

                if any(keyword in title for keyword in KEYWORDS):
                    if is_valid_link(link):
                        pending_jobs.append((title.title(), link))
                        sent_jobs.add(job_id)

        except Exception as e:
            print("Error scraping:", e)

# --- BATCH SEND FUNCTION ---

def send_pending_jobs():
    if not pending_jobs:
        print("No new jobs found.")
        return

    print(f"Sending {len(pending_jobs)} jobs to Telegram...")

    message = "🚀 *New Fresher Jobs in Mumbai (Last 15 min)* 🚀\n\n"
    for i, (title, link) in enumerate(pending_jobs, 1):
        message += f"{i}. [{title}]({link})\n"

    send_telegram_alert(message)
    pending_jobs.clear()

# --- MAIN LOOP ---

def main():
    print("🤖 Job Alert Bot started (15-min cycle)...")
    start_time = time.time()

    while True:
        scrape_jobs()
        time.sleep(60)  # 1-minute interval

        if time.time() - start_time >= 900:  # 15 minutes
            send_pending_jobs()
            start_time = time.time()

if __name__ == "__main__":
    main()
