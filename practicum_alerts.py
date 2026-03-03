import os
import requests
from bs4 import BeautifulSoup
import feedparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import imaplib
import email

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

# Verified program pages — always included
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
                    "telehealth": telehealth_tag,
                    "source": "RSS"
                })
    return listings

def fetch_program_links():
    listings = []
    for org, url in PROGRAM_LINKS.items():
        # Always include top-level program page
        listings.append({"title": f"{org}", "link": url, "telehealth": False, "source": "Program Page"})
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            # Include any links that match keywords
            for a in soup.find_all("a", href=True):
                text = a.get_text().strip()
                if any(k.lower() in text.lower() for k in KEYWORDS):
                    telehealth_tag = any(tk in text.lower() for tk in TELEHEALTH_KEYWORDS)
                    listings.append({"title": f"{org}: {text}", "link": a["href"], "telehealth": telehealth_tag, "source": "Program Page"})
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
                            if any(k.lower() in text.lower() for k in KEYWORDS):
                                telehealth_tag = any(tk in text.lower() for tk in TELEHEALTH_KEYWORDS)
                                listings.append({"title": text, "link": href, "telehealth": telehealth_tag, "source": "LinkedIn"})
    except Exception as e:
        print(f"ERROR fetching LinkedIn alerts: {e}")
    return listings

def build_email(listings):
    if not listings:
        return "<html><body><h2>No open practicum listings today 🎉</h2></body></html>"

    # Separate Telehealth vs On-site
    telehealth_list = [l for l in listings if l["telehealth"]]
    onsite_list = [l for l in listings if not l["telehealth"]]

    body = "<html><body><h2>Open Practicum & Internship Listings (California)</h2>"

    if onsite_list:
        body += "<h3>On-Site Programs</h3><ul>"
        for item in onsite_list:
            body += f'<li><strong>{item["title"]}</strong><br><a href="{item["link"]}" target="_blank">{item["link"]}</a></li>'
        body += "</ul>"

    if telehealth_list:
        body += "<h3>Telehealth / Remote Programs</h3><ul>"
        for item in telehealth_list:
            body += f'<li><strong>{item["title"]}</strong><br><a href="{item["link"]}" target="_blank">{item["link"]}</a></li>'
        body += "</ul>"

    body += "</body></html>"
    return body

def send_email(html_body):
    msg = MIMEMultipart("alternative")
    msg["From"] = YOUR_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = "Daily Open Practicum + Internship Listings (CA)"
    msg.attach(MIMEText(html_body, "html"))
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

    email_body = build_email(all_listings)
    send_email(email_body)

    print(f"Email sent with {len(all_listings)} listings")