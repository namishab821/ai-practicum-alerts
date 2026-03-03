import os
import requests
import feedparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import imaplib
import email
import datetime

# -------------------------
# CONFIGURATION
# -------------------------
YOUR_EMAIL = os.environ.get("EMAIL_ADDRESS")
YOUR_PASSWORD = os.environ.get("EMAIL_PASSWORD")
TO_EMAIL = YOUR_EMAIL

ZIP = "94582"
RADIUS = "20"

KEYWORDS = [
    "counseling practicum",
    "counseling internship",
    "mental health intern",
    "clinical intern",
    "behavioral health intern",
    "trainee"
]

TELEHEALTH_KEYWORDS = [
    "telehealth",
    "remote",
    "virtual",
    "online",
    "video"
]

# -------------------------
# HARD-CODED ON-SITE PROGRAMS (ALWAYS SHOW)
# -------------------------
ON_SITE_PROGRAMS = [
    {
        "title": "Discovery Counseling Center – Training Opportunities",
        "link": "https://www.discoveryctr.net/training-opportunities/"
    },
    {
        "title": "Kaiser Permanente Pre-Master’s Mental Health Internship",
        "link": "https://mentalhealthtraining-ncal.kaiserpermanente.org/pre-masters-mental-health-internship/"
    },
    {
        "title": "Contra Costa Behavioral Health – Job Openings",
        "link": "https://www.contracosta.ca.gov/cccpublicworkscareers"
    },
    {
        "title": "Solano County Behavioral Health – Internship Program",
        "link": "https://www.solanocounty.com/depts/ph/behavioral_health/internships.asp"
    },
    {
        "title": "Alameda County Behavioral Health – Internship Program",
        "link": "https://www.acgov.org/behavioral-health-services"
    },
    {
        "title": "Health Solutions West – All Open Positions",
        "link": "https://healthsolutionswest.org/careers/open-positions/"
    },
    {
        "title": "Health Solutions West – Internships & Practicums",
        "link": "https://healthsolutionswest.org/careers/internships-practicums/"
    },
    {
        "title": "Earth Circles Counseling Center – Internships",
        "link": "https://www.earthcirclescenter.com/internships"
    }
]

RSS_FEEDS = [
    f"https://www.indeed.com/rss?q=counseling+practicum+OR+counseling+internship&l={ZIP}&radius={RADIUS}",
    f"https://www.indeed.com/rss?q=clinical+mental+health+intern+OR+mental+health+intern&l={ZIP}&radius={RADIUS}"
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
            if any(k.lower() in title.lower() for k in KEYWORDS + TELEHEALTH_KEYWORDS):
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
                        if any(k.lower() in html.lower() for k in KEYWORDS + TELEHEALTH_KEYWORDS):
                            telehealth_tag = any(tk in html.lower() for tk in TELEHEALTH_KEYWORDS)
                            listings.append({
                                "title": "LinkedIn Job Alert",
                                "link": "Check LinkedIn email",
                                "telehealth": telehealth_tag
                            })
    except Exception as e:
        print(f"LinkedIn error: {e}")

    return listings


def fetch_bing_search():
    listings = []
    API_KEY = os.environ.get("BING_SEARCH_API_KEY")

    if not API_KEY:
        return listings

    query = "California counseling practicum OR mental health internship remote OR telehealth"
    url = f"https://api.bing.microsoft.com/v7.0/search?q={query}&count=10"
    headers = {"Ocp-Apim-Subscription-Key": API_KEY}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()

        for item in data.get("webPages", {}).get("value", []):
            title = item.get("name", "")
            link = item.get("url", "")
            if any(k.lower() in title.lower() for k in KEYWORDS + TELEHEALTH_KEYWORDS):
                telehealth_tag = any(tk in title.lower() for tk in TELEHEALTH_KEYWORDS)
                listings.append({
                    "title": title,
                    "link": link,
                    "telehealth": telehealth_tag
                })
    except Exception as e:
        print(f"Bing error: {e}")

    return listings


def build_email(onsite_programs, dynamic_listings):

    telehealth_list = [l for l in dynamic_listings if l["telehealth"]]
    onsite_dynamic = [l for l in dynamic_listings if not l["telehealth"]]

    body = "<html><body>"
    body += f"<h2>Open Practicum & Internship Listings (California)</h2>"
    body += f"<p><small>{datetime.date.today()}</small></p>"

    # Always show hard-coded on-site programs
    body += "<h3>On-Site Opportunities</h3><ul>"
    for item in onsite_programs:
        body += f'<li><strong>{item["title"]}</strong><br><a href="{item["link"]}" target="_blank">{item["link"]}</a></li>'

    # Add dynamic on-site results
    for item in onsite_dynamic:
        body += f'<li><strong>{item["title"]}</strong><br><a href="{item["link"]}" target="_blank">{item["link"]}</a></li>'

    body += "</ul>"

    # Telehealth Section
    if telehealth_list:
        body += "<h3>Telehealth / Remote Opportunities</h3><ul>"
        for item in telehealth_list:
            body += f'<li><strong>{item["title"]}</strong><br><a href="{item["link"]}" target="_blank">{item["link"]}</a></li>'
        body += "</ul>"

    body += "</body></html>"
    return body


def send_email(html_body):
    msg = MIMEMultipart("alternative")
    msg["From"] = YOUR_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = f"Daily Practicum & Internship Listings – {datetime.date.today()}"
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(YOUR_EMAIL, YOUR_PASSWORD)
        server.sendmail(YOUR_EMAIL, TO_EMAIL, msg.as_string())


# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    rss = fetch_rss()
    linkedin = fetch_linkedin_alerts()
    bing = fetch_bing_search()

    dynamic = rss + linkedin + bing

    email_body = build_email(ON_SITE_PROGRAMS, dynamic)
    send_email(email_body)

    print(f"Email sent with {len(dynamic)} dynamic listings")