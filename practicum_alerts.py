import os
import requests
from bs4 import BeautifulSoup
import feedparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import imaplib
import email
import time
import urllib.parse

# -------------------------
# CONFIGURATION
# -------------------------
YOUR_EMAIL = os.environ.get("EMAIL_ADDRESS")
YOUR_PASSWORD = os.environ.get("EMAIL_PASSWORD")
TO_EMAIL = YOUR_EMAIL

ZIP = "94582"
RADIUS_MILES = 20
STATE = "California"

KEYWORDS = [
    "counseling practicum", "counseling internship",
    "mental health intern", "school counseling",
    "clinical intern", "behavioral health intern",
    "trainee"
]

TELEHEALTH_KEYWORDS = ["telehealth", "remote", "virtual", "online", "video"]

# ------------------------------------------------
# Local on‑site program links (always show)
# ------------------------------------------------
LOCAL_PROGRAMS = [
    {"title": "Discovery Counseling Center – Training Opportunities",
     "link": "https://www.discoveryctr.net/training-opportunities/",
     "telehealth": False},

    {"title": "Kaiser Permanente Pre-Master’s Mental Health Internship",
     "link": "https://mentalhealthtraining-ncal.kaiserpermanente.org/pre-masters-mental-health-internship/",
     "telehealth": False},

    {"title": "Contra Costa Behavioral Health – Internship Program",
     "link": "https://www.contracosta.ca.gov/332/Behavioral-Health-Services",
     "telehealth": False},

    {"title": "Solano County Behavioral Health – Internship Program",
     "link": "https://www.solanocounty.com/depts/ph/behavioral_health/internships.asp",
     "telehealth": False},

    {"title": "Alameda County Behavioral Health – Internship Program",
     "link": "https://www.acgov.org/behavioral-health-services",
     "telehealth": False},

    {"title": "Health Solutions West – Internships/Practicums",
     "link": "https://healthsolutionswest.org/careers/internships-practicums/",
     "telehealth": False},

    {"title": "Earth Circles Counseling Center – Internships",
     "link": "https://www.earthcirclescenter.com/internships/",
     "telehealth": False}
]

# RSS feeds
RSS_FEEDS = [
    f"https://www.indeed.com/rss?q=counseling+practicum+OR+counseling+internship&l={ZIP}&radius={RADIUS_MILES}",
    f"https://www.indeed.com/rss?q=clinical+mental+health+intern+OR+mental+health+intern&l={ZIP}&radius={RADIUS_MILES}"
]

LINKEDIN_SENDER = "jobs-noreply@linkedin.com"

# -------------------------
# FUNCTIONS
# -------------------------

def fetch_rss():
    listings = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title
            if any(k.lower() in title.lower() for k in KEYWORDS):
                telehealth_tag = any(tk in title.lower() for tk in TELEHEALTH_KEYWORDS)
                listings.append({
                    "title": title.strip(),
                    "link": entry.link.strip(),
                    "telehealth": telehealth_tag
                })
    return listings

def fetch_linkedin_alerts():
    listings = []
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(YOUR_EMAIL, YOUR_PASSWORD)
        mail.select("inbox")
        result, data = mail.search(None, f'(UNSEEN FROM "{LINKEDIN_SENDER}")')
        mail_ids = data[0].split()
        for mail_id in mail_ids:
            result, msg_data = mail.fetch(mail_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        html = part.get_payload(decode=True).decode()
                        soup = BeautifulSoup(html, "html.parser")
                        for a in soup.find_all("a", href=True):
                            text = a.get_text().strip()
                            href = a["href"]
                            if any(k.lower() in text.lower() for k in KEYWORDS):
                                telehealth_tag = any(tk in text.lower() for tk in TELEHEALTH_KEYWORDS)
                                listings.append({
                                    "title": text,
                                    "link": href,
                                    "telehealth": telehealth_tag
                                })
    except Exception as e:
        print(f"ERROR fetching LinkedIn alerts: {e}")
    return listings

def fetch_google_search():
    """
    Free Google search scrape for telehealth/remote CA practicum/internship listings.
    This uses basic HTML parsing and may pick up titles & links from Google results.
    """
    listings = []
    query = "telehealth OR remote OR virtual OR online California internship OR practicum"
    headers = {"User-Agent": "Mozilla/5.0"}
    encoded = urllib.parse.quote(query + " California internship practicum")
    url = f"https://www.google.com/search?q={encoded}&num=10"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Google result blocks usually in div with class "yuRUbf"
        for result in soup.find_all("div", class_="yuRUbf"):
            a = result.find("a", href=True)
            title = result.get_text().strip()
            href = a["href"] if a else ""
            if href and any(k in title.lower() for k in KEYWORDS):
                listings.append({
                    "title": title,
                    "link": href,
                    "telehealth": True
                })

        # avoid Google blocking by small pause
        time.sleep(2)

    except Exception as e:
        print(f"ERROR fetching Google search: {e}")
    return listings

def build_email(listings):
    # combine local + dynamic
    all_listings = []

    # always include local
    for p in LOCAL_PROGRAMS:
        all_listings.append(p)

    # dynamic
    all_listings += listings

    # split telehealth vs on‑site
    tele_list = [l for l in all_listings if l["telehealth"]]
    onsite_list = [l for l in all_listings if not l["telehealth"]]

    # build HTML
    body = "<html><body>"

    body += "<h2>On‑Site / Local Practicum & Internship Listings</h2>"
    if onsite_list:
        body += "<ul>"
        for item in onsite_list:
            body += f'<li><strong>{item["title"]}</strong><br><a href="{item["link"]}" target="_blank">{item["link"]}</a></li>'
        body += "</ul>"
    else:
        body += "<p>No on‑site listings found today 🎉</p>"

    body += "<h2>Telehealth / Remote Listings</h2>"
    if tele_list:
        body += "<ul>"
        for item in tele_list:
            body += f'<li><strong>{item["title"]}</strong><br><a href="{item["link"]}" target="_blank">{item["link"]}</a></li>'
        body += "</ul>"
    else:
        body += "<p>No telehealth listings found today 🎉</p>"

    body += "</body></html>"
    return body

def send_email(html_body):
    msg = MIMEMultipart("alternative")
    msg["From"] = YOUR_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = "Daily Practicum + Internship Listings (CA)"
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(YOUR_EMAIL, YOUR_PASSWORD)
        server.sendmail(YOUR_EMAIL, TO_EMAIL, msg.as_string())

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    rss_listings = fetch_rss()
    linkedin_listings = fetch_linkedin_alerts()
    google_listings = fetch_google_search()

    all_dynamic = rss_listings + linkedin_listings + google_listings

    email_body = build_email(all_dynamic)
    send_email(email_body)

    print(f"Email sent with {len(all_dynamic)} dynamic listings")