import os
import time
import requests
import hashlib
from bs4 import BeautifulSoup
import schedule

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

sent_jobs = set()
SENT_FILE = "sent_jobs.txt"
if os.path.exists(SENT_FILE):
    with open(SENT_FILE) as f:
        sent_jobs = set(line.strip() for line in f)

def send_to_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    })
    print(f"[TELE] status={resp.status_code}")

def save_job(hash_id):
    sent_jobs.add(hash_id)
    with open(SENT_FILE, "a") as f:
        f.write(hash_id + "\n")

def job_hash(source, title, company, link):
    return hashlib.md5(f"{source}|{title}|{company}|{link}".encode()).hexdigest()

def fetch_linkedin():
    src="LinkedIn"
    url = ("https://www.linkedin.com/jobs/search/"
           "?keywords=software%20developer%20OR%20engineer&location=Mumbai"
           "&f_E=1&f_TPR=r604800")
    soup = BeautifulSoup(requests.get(url, headers={"User-Agent":"Mozilla/5.0"}).text, "html.parser")
    for card in soup.select(".base-card"):
        t=card.select_one("h3"); c=card.select_one("h4"); a=card.select_one("a.base-card__full-link")
        if not (t and c and a): continue
        title, company, link = t.text.strip(), c.text.strip(), a["href"].split("?")[0]
        h = job_hash(src, title, company, link)
        if h in sent_jobs: continue
        save_job(h)
        yield f"[{src}] <b>{title}</b>\n{company}\n🔗 {link}"

def fetch_indeed():
    src="Indeed"
    for role in ["software+developer","software+engineer","web+developer"]:
        url=f"https://in.indeed.com/jobs?q={role}&l=Mumbai&fromage=7"
        soup=BeautifulSoup(requests.get(url,headers={"User-Agent":"Mozilla/5.0"}).text,"html.parser")
        for a in soup.select("a[data-jk]"):
            link="https://in.indeed.com/viewjob?jk="+a["data-jk"]
            title=a.select_one("span") and a.select_one("span").text.strip() or "N/A"
            company="Indeed Listing"
            h=job_hash(src,title,company,link)
            if h in sent_jobs: continue
            save_job(h)
            yield f"[{src}] <b>{title}</b>\n{company}\n🔗 {link}"

def fetch_internshala():
    src="Internshala"
    for role in ["software-developer","software-engineer","web-developer"]:
        url=f"https://internshala.com/internships/{role}-internship-in-mumbai"
        soup=BeautifulSoup(requests.get(url,headers={"User-Agent":"Mozilla/5.0"}).text,"html.parser")
        for d in soup.select(".individual_internship_header"):
            a=d.select_one("a")
            title=a.text.strip()
            link="https://internshala.com"+a["href"]
            comp=d.find_next_sibling("div").text.split('•')[0].strip()
            h=job_hash(src,title,comp,link)
            if h in sent_jobs: continue
            save_job(h)
            yield f"[{src}] <b>{title}</b>\n{comp}\n🔗 {link}"

def fetch_naukri():
    src="Naukri"
    for role in ["software-developer","software-engineer","web-developer"]:
        url=f"https://www.naukri.com/{role}-jobs-in-mumbai?k={role}&l=mumbai&experience=0"
        soup=BeautifulSoup(requests.get(url,headers={"User-Agent":"Mozilla/5.0"}).text,"html.parser")
        for art in soup.select("article.jobTuple"):
            t=art.select_one("a.title"); c=art.select_one("a.subTitle")
            if not (t and c): continue
            title, comp, link = t.text.strip(), c.text.strip(), t["href"]
            h=job_hash(src,title,comp,link)
            if h in sent_jobs: continue
            save_job(h)
            yield f"[{src}] <b>{title}</b>\n{comp}\n🔗 {link}"

def fetch_foundit():
    src="Foundit"
    for role in ["software-developer","software-engineer","web-developer"]:
        url=f"https://www.foundit.in/search/{role}-jobs-in-mumbai"
        soup=BeautifulSoup(requests.get(url,headers={"User-Agent":"Mozilla/5.0"}).text,"html.parser")
        for card in soup.select(".job-tuple")[:10]:
            t=card.select_one("h3"); c=card.select_one(".company-name"); a=card.select_one("a")
            if not (t and c and a): continue
            title, comp = t.text.strip(), c.text.strip()
            link="https://www.foundit.in"+a["href"]
            h=job_hash(src,title,comp,link)
            if h in sent_jobs: continue
            save_job(h)
            yield f"[{src}] <b>{title}</b>\n{comp}\n🔗 {link}"

def job_runner():
    print("[START] Running job check...")
    msgs = list(fetch_linkedin()) + list(fetch_indeed()) + list(fetch_internshala()) + list(fetch_naukri()) + list(fetch_foundit())
    if msgs:
        payload="🚀 <b>New jobs found:</b>\n\n" + "\n\n".join(msgs)
    else:
        payload="✅ No new jobs found this hour. Bot is alive."
    send_to_telegram(payload)
    print("[TELEGRAM] Message sent.")

schedule.every(1).hours.do(job_runner)

if __name__ == "__main__":
    job_runner()
    while True:
        schedule.run_pending()
        time.sleep(1)
