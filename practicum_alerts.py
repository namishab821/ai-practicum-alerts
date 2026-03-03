import os
import requests
import feedparser
import imaplib
import email
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# -------------------------
# CONFIGURATION
# -------------------------
YOUR_EMAIL = os.environ.get("EMAIL_ADDRESS")       # e.g., your Gmail
YOUR_PASSWORD = os.environ.get("EMAIL_PASSWORD")   # App password
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

REMOTE_KEYWORDS = ["telehealth", "remote", "virtual", "online", "video"]

# Program pages with confirmed internship/practicum listings
PROGRAM_LINKS = {
    "Discovery Counseling Center": "https://www.discoveryctr.net/training-opportunities/",
    "Kaiser Permanente Pre-Master’s Mental Health Internship": "https://mentalhealthtraining-ncal.kaiserpermanente.org/pre-masters-mental-health-internship/",
    "Contra Costa Behavioral Health": "https://www.contracosta.ca.gov/332/Behavioral-Health-Services",
    "Solano County Behavioral Health": "https://www.solanocounty.com/depts/ph/behavioral_health/internships.asp",
    "Alameda County Behavioral Health": "https://www.acgov.org/behavioral-health-services",
    "Health Solutions West": "https://healthsolutionswest.org/careers/internships-practicums/",
    "Earth Circles Counseling Center": "https://www.earthcirclescenter.com/internships/"
}

RSS_FEEDS = [
    f"https://www.indeed.com/rss?q=counseling+practicum+OR+counseling+internship&l={ZIP}&radius={RADIUS_MILES}",
    f"https://www.indeed.com/rss?q=clinical+mental+health+intern+OR+mental+health+intern&l={ZIP}&radius={RADIUS_MILES}"
]

LINKEDIN_SENDER = "jobs-noreply@linkedin.com"

# -------------------------
# FETCH FUNCTIONS
# -------------------------
def fetch_rss():
    listings = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title
            if any(k.lower() in title.lower() for k in KEYWORDS):
                is_remote = any(rk in title.lower() for rk in REMOTE_KEYWORDS)
                listings.append({"title": title.strip(), "link": entry.link.strip(), "remote": is_remote})
    return listings

def fetch_program_links():
    listings = []
    for org, url in PROGRAM_LINKS.items():
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                text = a.get_text().strip()
                if any(k.lower() in text.lower() for k in KEYWORDS + ["internship", "practicum", "apply", "open"]):
                    is_remote = any(rk in text.lower() for rk in REMOTE_KEYWORDS)
                    link = a["href"]
                    # Make relative links absolute
                    if link.startswith("/"):
                        from urllib.parse import urljoin
                        link = urljoin(url, link)
                    listings.append({"title": f"{org}: {text}", "link": link, "remote": is_remote})
        except Exception as e:
            print(f"ERROR fetching {org}: {e}")
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
                            if text and any(k.lower() in text.lower() for k in KEYWORDS):
                                is_remote = any(rk in text.lower() for rk in REMOTE_KEYWORDS)
                                listings.append({"title": text, "link": href, "remote": is_remote})
    except Exception as e:
        print(f"ERROR fetching LinkedIn alerts: {e}")
    return listings

# -------------------------
# EMAIL
# -------------------------
def build_email(listings):
    if not listings:
        return "<html><body><h2>No open practicum listings today 🎉</h2></body></html>"

    remote_listings = [l for l in listings if l["remote"]]
    onsite_listings = [l for l in listings if not l["remote"]]

    body = "<html><body><h2>Open Practicum & Internship Listings (California)</h2>"

    # On-site
    body += "<h3>On-Site Opportunities</h3><ul>"
    for item in onsite_listings:
        body += f'<li><strong>{item["title"]}</strong><br><a href="{item["link"]}" target="_blank">{item["link"]}</a></li>'
    body += "</ul>"

    # Telehealth / Remote
    body += "<h3>Telehealth / Remote Opportunities</h3><ul>"
    for item in remote_listings:
        body += f'<li><strong>{item["title"]}</strong><br><a href="{item["link"]}" target="_blank">{item["link"]}</a></li>'
    body += "</ul></body></html>"

    return body

def send_email(html_body):
    msg = MIMEMultipart("alternative")
    msg["From"] = YOUR_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = "Daily Open Practicum + Internship Listings"
    msg.attach(MIMEText(html_body, "html"))

    # SMTP send via Gmail
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(YOUR_EMAIL, YOUR_PASSWORD)
        server.sendmail(YOUR_EMAIL, TO_EMAIL, msg.as_string())

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    rss_listings = fetch_rss()
    program_listings = fetch_program_links()
    linkedin_listings = fetch_linkedin_alerts()

    all_listings = rss_listings + program_listings + linkedin_listings
    email_content = build_email(all_listings)
    send_email(email_content)
    print(f"Email sent with {len(all_listings)} listings")