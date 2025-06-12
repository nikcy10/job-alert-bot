import requests
from bs4 import BeautifulSoup
import time
import hashlib

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Job Search Config
ROLES = ['software developer', 'software engineer', 'web developer', 'backend developer', 'frontend developer']
LOCATION = 'Mumbai'
FETCH_INTERVAL = 3600  # 1 hour
SENT_JOBS = set()

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=data)

def job_hash(title, company, link):
    return hashlib.md5(f"{title}{company}{link}".encode()).hexdigest()

def fetch_linkedin_jobs():
    jobs = []
    for role in ROLES:
        url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={role}&location={LOCATION}&f_E=1&f_TP=1&f_WT=2&f_AL=true&f_TPR=r604800"
        )
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        listings = soup.find_all('a', {'class': 'base-card__full-link'})

        for link in listings:
            title = link.find_previous('h3')
            company = link.find_previous('h4')
            job_link = link['href'].replace('https://in.linkedin.com', 'https://www.linkedin.com')

            title_text = title.get_text(strip=True) if title else 'N/A'
            company_text = company.get_text(strip=True) if company else 'N/A'
            hash_id = job_hash(title_text, company_text, job_link)

            if hash_id not in SENT_JOBS:
                SENT_JOBS.add(hash_id)
                jobs.append(f"<b>{title_text}</b>\n{company_text}\n🔗 {job_link}")
    return jobs

def fetch_indeed_jobs():
    jobs = []
    for role in ROLES:
        query = role.replace(' ', '+')
        url = f"https://in.indeed.com/jobs?q={query}&l={LOCATION}&fromage=7"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        cards = soup.find_all('a', {'data-jk': True})

        for card in cards:
            job_link = "https://in.indeed.com/viewjob?jk=" + card['data-jk']
            title_tag = card.find('span')
            title_text = title_tag.get_text(strip=True) if title_tag else "N/A"
            company_text = "Indeed Listing"
            hash_id = job_hash(title_text, company_text, job_link)

            if hash_id not in SENT_JOBS:
                SENT_JOBS.add(hash_id)
                jobs.append(f"<b>{title_text}</b>\n{company_text}\n🔗 {job_link}")
    return jobs

def fetch_internshala_jobs():
    jobs = []
    for role in ROLES:
        query = role.replace(' ', '-')
        url = f"https://internshala.com/internships/{query}-internship-in-mumbai"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        listings = soup.find_all('div', class_='individual_internship_header')

        for item in listings:
            title_tag = item.find('a')
            title_text = title_tag.get_text(strip=True) if title_tag else 'N/A'
            job_link = "https://internshala.com" + title_tag['href']
            company_tag = item.find_next_sibling('div')
            company_text = company_tag.get_text(strip=True).split('•')[0] if company_tag else 'Internshala Listing'

            hash_id = job_hash(title_text, company_text, job_link)
            if hash_id not in SENT_JOBS:
                SENT_JOBS.add(hash_id)
                jobs.append(f"<b>{title_text}</b>\n{company_text}\n🔗 {job_link}")
    return jobs

def fetch_naukri_jobs():
    jobs = []
    for role in ROLES:
        query = role.replace(' ', '-')
        url = f"https://www.naukri.com/{query}-jobs-in-mumbai?k={query}&l=mumbai&experience=0"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        cards = soup.find_all('article', class_='jobTuple')

        for card in cards:
            title_tag = card.find('a', class_='title')
            company_tag = card.find('a', class_='subTitle')
            if not title_tag or not company_tag:
                continue
            title_text = title_tag.get_text(strip=True)
            company_text = company_tag.get_text(strip=True)
            job_link = title_tag['href']
            hash_id = job_hash(title_text, company_text, job_link)

            if hash_id not in SENT_JOBS:
                SENT_JOBS.add(hash_id)
                jobs.append(f"<b>{title_text}</b>\n{company_text}\n🔗 {job_link}")
    return jobs

def fetch_foundit_jobs():
    jobs = []
    for role in ROLES:
        query = role.replace(' ', '-')
        url = f"https://www.foundit.in/search/{query}-jobs-in-mumbai"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        cards = soup.find_all('div', class_='job-tuple')[:5]  # Limit to avoid excess

        for card in cards:
            title_tag = card.find('h3')
            company_tag = card.find('span', class_='company-name')
            if not title_tag or not company_tag:
                continue
            title_text = title_tag.get_text(strip=True)
            company_text = company_tag.get_text(strip=True)
            job_link_tag = card.find('a')
            job_link = "https://www.foundit.in" + job_link_tag['href'] if job_link_tag else "#"
            hash_id = job_hash(title_text, company_text, job_link)

            if hash_id not in SENT_JOBS:
                SENT_JOBS.add(hash_id)
                jobs.append(f"<b>{title_text}</b>\n{company_text}\n🔗 {job_link}")
    return jobs

def send_pending_jobs():
    print("[✓] Searching for new jobs...")
    all_jobs = (
        fetch_linkedin_jobs() +
        fetch_indeed_jobs() +
        fetch_internshala_jobs() +
        fetch_naukri_jobs() +
        fetch_foundit_jobs()
    )

    if all_jobs:
        message = "\n\n".join(all_jobs)
        send_telegram_alert(f"🚀 <b>New Jobs Found</b>:\n\n{message}")
        print(f"[✓] Sent {len(all_jobs)} job(s) to Telegram.")
    else:
        send_telegram_alert("✅ Bot is running. No new jobs found this hour.")
        print("[✓] No new jobs found.")

def main():
    send_telegram_alert("🤖 Job Alert Bot is now live and checking every hour.")
    print("⚙️ Job Alert Bot started...")
    while True:
        send_pending_jobs()
        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main()
