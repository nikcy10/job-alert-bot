import requests
from bs4 import BeautifulSoup
import schedule
import time
import webbrowser

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

# Telegram config
BOT_TOKEN = '7869812750:AAE1toyimSkNXpWjdwMaWDjCFnLEVu9Pvfw'
CHAT_ID = '933417412'

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram error:", e)

def check_jobs():
    print("🔍 Checking for fresher jobs in Mumbai...")
    headers = {"User-Agent": "Mozilla/5.0"}

    for role in ROLES:
        url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={role}"
            f"&location={LOCATION}"
            f"&f_E=1&f_TP=1&f_WT=2&f_AL=true"
        )

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        job_cards = soup.find_all("a", class_="base-card__full-link")

        for job in job_cards[:10]:
            title = job.text.strip().lower()
            link = job['href'].replace("in.linkedin.com", "www.linkedin.com")

            if any(keyword in title for keyword in KEYWORDS):
                message = f"🚀 New Job Alert!\n\n{title.title()}\n\n🔗 {link}"
                send_telegram_alert(message)
                webbrowser.open(link)
                print(f"✅ Telegram alert sent and browser opened: {title}")
                return  # Stop after first relevant match

schedule.every(1).minutes.do(check_jobs)

print("🤖 Telegram Job Assistant running...")
while True:
    schedule.run_pending()
    time.sleep(5)
