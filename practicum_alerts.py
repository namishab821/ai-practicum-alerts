import feedparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import imaplib
import email
from bs4 import BeautifulSoup

# -------------------------
# Configuration
# -------------------------
YOUR_EMAIL = os.environ.get("EMAIL_ADDRESS")
YOUR_PASSWORD = os.environ.get("EMAIL_PASSWORD")
TO_EMAIL = YOUR_EMAIL

ZIP = "94582"
RADIUS = "12"  # ~20 min drive

# Keywords to filter all sources
KEYWORDS = [
    "counseling practicum",
    "counseling internship",
    "mental health intern",
    "school counseling",
    "clinical intern",
    "behavioral health intern",
    "trainee"
]

# Verified program links
PROGRAM_LINKS = {
    "Discovery Counseling Center – Training Opportunities": "https://www.discoveryctr.net/training-opportunities/",
    "Kaiser Permanente Pre-Master’s Mental Health Internship": "https://mentalhealthtraining-ncal.kaiserpermanente.org/pre-masters-mental-health-internship/",
    "Contra Costa Behavioral Health – Internship Program": "https://www.contracosta.ca.gov/332/Behavioral-Health-Services",
    "Solano County Behavioral Health – Internship Program": "https://www.solanocounty.com/depts/ph/behavioral_health/internships.asp",
    "Alameda County Behavioral Health – Internship Program": "https://www.acgov.org/behavioral-health-services",
    "Health Solutions West – Internships/Practicums": "https://healthsolutionswest.org/careers/internships-practicums/",
    "Earth Circles Counseling Center – Internships": "https://www.earthcirclescenter.com/internships/"
}

RSS_FEEDS = [
    f"https://www.indeed.com/rss?q=counseling+practicum+OR+counseling+internship&l={ZIP}&radius={RADIUS}",
    f"https://www.indeed.com/rss?q=clinical+mental+health+intern+OR+mental+health+intern&l={ZIP}&radius={RADIUS}"
]

LINKEDIN_SENDER = "jobs-noreply@linkedin.com"

# -------------------------
# RSS Functions
# -------------------------
def fetch_rss():
    listings = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title
            published = entry.get("published", "")
            if any(k.lower() in title.lower() for k in KEYWORDS):
                listings.append({"title": title.strip(), "link": entry.link.strip(), "date": published})
    return listings

# -------------------------
# Program Links
# -------------------------
def fetch_program_links():
    return [{"title": title, "link": url, "date": ""} for title, url in PROGRAM_LINKS.items()]

# -------------------------
# LinkedIn Email Alerts
# -------------------------
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

            # Extract HTML content
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        html = part.get_payload(decode=True).decode()
                        soup = BeautifulSoup(html, "html.parser")
                        for a in soup.find_all("a", href=True):
                            href = a["href"]
                            text = a.get_text().strip()
                            if text and any(k.lower() in text.lower() for k in KEYWORDS):
                                listings.append({"title": text, "link": href, "date": ""})
            else:
                text = msg.get_payload(decode=True).decode()
                for line in text.splitlines():
                    if any(k.lower() in line.lower() for k in KEYWORDS):
                        listings.append({"title": line.strip(), "link": "", "date": ""})

        mail.logout()
    except Exception as e:
        print(f"ERROR fetching LinkedIn alerts: {e}")

    print(f"DEBUG: Found {len(listings)} LinkedIn listings matching keywords")
    return listings

# -------------------------
# Email Builder
# -------------------------
def build_email(listings):
    if not listings:
        return "<html><body><h2>No practicum listings today 🎉</h2></body></html>"

    body = "<html><body><h2>Practicum & Internship Listings</h2><ul>"
    for item in listings:
        date_info = f"<br><small>{item['date']}</small>" if item['date'] else ""
        link_html = f'<br><a href="{item["link"]}" target="_blank">{item["link"]}</a>' if item["link"] else ""
        body += f'<li><strong>{item["title"]}</strong>{date_info}{link_html}</li>'
    body += "</ul></body></html>"
    return body

# -------------------------
# Email Sender
# -------------------------
def send_email(html_body):
    msg = MIMEMultipart("alternative")
    msg["From"] = YOUR_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = "Daily Practicum + Internship Listings"
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(YOUR_EMAIL, YOUR_PASSWORD)
        server.sendmail(YOUR_EMAIL, TO_EMAIL, msg.as_string())

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    rss_listings = fetch_rss()
    program_listings = fetch_program_links()
    linkedin_listings = fetch_linkedin_alerts()

    all_listings = rss_listings + program_listings + linkedin_listings

    email_body = build_email(all_listings)
    send_email(email_body)

    print(f"Email sent with {len(all_listings)} listings")