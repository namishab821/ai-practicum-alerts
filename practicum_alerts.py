import os
import requests
from bs4 import BeautifulSoup
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
RADIUS = "20"  # miles

# Main keywords
KEYWORDS = [
    "counseling practicum",
    "counseling internship",
    "mental health intern",
    "school counseling",
    "clinical intern",
    "behavioral health intern",
    "trainee"
]

# Remote/Telehealth keywords
TELEHEALTH_KEYWORDS = ["telehealth", "remote", "virtual", "online", "video"]

# Verified program pages
PROGRAM_LINKS = {
    "Discovery Counseling Center": "https://www.discoveryctr.net/training-opportunities/",
    "Kaiser Permanente Pre-Master’s Mental Health Internship": "https://mentalhealthtraining-ncal.kaiserpermanente.org/pre-masters-mental-health-internship/",
    "Contra Costa Behavioral Health": "https://www.contracosta.ca.gov/332/Behavioral-Health-Services",
    "Solano County Behavioral Health": "https://www.solanocounty.com/depts/ph/behavioral_health/internships.asp",
    "Alameda County Behavioral Health": "https://www.acgov.org/behavioral-health-services",
    "Health Solutions West": "https://healthsolutionswest.org/careers/internships-practicums/",
    "Earth Circles Counseling Center": "https://www.earthcirclescenter.com/internships/"
}

# RSS feeds
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
            published = entry.get("published", "")
            if any(k.lower() in title.lower() for k in KEYWORDS + TELEHEALTH_KEYWORDS):
                telehealth_tag = any(tk in title.lower() for tk in TELEHEALTH_KEYWORDS)
                listings.append({"title": title.strip(), "link": entry.link.strip(), "telehealth": telehealth_tag, "source": "RSS", "date": published})
    return listings

def fetch_program_links():
    listings = []
    for org, url in PROGRAM_LINKS.items():
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                text = a.get_text().strip()
                if any(k.lower() in text.lower() for k in KEYWORDS + TELEHEALTH_KEYWORDS + ["apply", "open", "internship", "practicum"]):
                    telehealth_tag = any(tk in text.lower() for tk in TELEHEALTH_KEYWORDS)
                    listings.append({"title": f"{org}: {text}", "link": a["href"], "telehealth": telehealth_tag, "source": "Program Page", "date": ""})
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
                            if text and any(k.lower() in text.lower() for k in KEYWORDS + TELEHEALTH_KEYWORDS):
                                telehealth_tag = any(tk in text.lower() for tk in TELEHEALTH_KEYWORDS)
                                listings.append({"title": text, "link": href, "telehealth": telehealth_tag, "source": "LinkedIn", "date": ""})
    except Exception as e:
        print(f"ERROR fetching LinkedIn alerts: {e}")
    return listings

def fetch_web_search():
    listings = []
    # Bing Search API placeholder - needs API_KEY from Bing free tier
    API_KEY = os.environ.get("BING_SEARCH_API_KEY")
    if not API_KEY:
        print("Bing API key not set; skipping web search")
        return listings

    QUERY = f"{STATE} counseling practicum OR mental health internship"
    url = f"https://api.bing.microsoft.com/v7.0/search?q={QUERY}&count=10"

    headers = {"Ocp-Apim-Subscription-Key": API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        for item in data.get("webPages", {}).get("value", []):
            title = item.get("name", "")
            link = item.get("url", "")
            if any(k.lower() in title.lower() for k in KEYWORDS + TELEHEALTH_KEYWORDS):
                telehealth_tag = any(tk in title.lower() for tk in TELEHEALTH_KEYWORDS)
                listings.append({"title": title, "link": link, "telehealth": telehealth_tag, "source": "Bing Search", "date": ""})
    except Exception as e:
        print(f"ERROR fetching Bing search: {e}")
    return listings

def build_email(listings):
    telehealth_list = [l for l in listings if l["telehealth"]]
    onsite_list = [l for l in listings if not l["telehealth"]]

    if not listings:
        return "<html><body><h2>No open practicum listings today 🎉</h2></body></html>"

    body = "<html><body>"
    body += "<h2>Open Practicum & Internship Listings (California)</h2>"

    if onsite_list:
        body += "<h3>On-Site Opportunities</h3><ul>"
        for item in onsite_list:
            date_info = f"<br><small>{item['date']}</small>" if item['date'] else ""
            link_html = f'<br><a href="{item["link"]}" target="_blank">{item["link"]}</a>' if item["link"] else ""
            body += f'<li><strong>{item["title"]}</strong>{date_info}{link_html}</li>'
        body += "</ul>"

    if telehealth_list:
        body += "<h3>Telehealth / Remote Opportunities</h3><ul>"
        for item in telehealth_list:
            date_info = f"<br><small>{item['date']}</small>" if item['date'] else ""
            link_html = f'<br><a href="{item["link"]}" target="_blank">{item["link"]}</a>' if item["link"] else ""
            body += f'<li><strong>{item["title"]}</strong>{date_info}{link_html}</li>'
        body += "</ul>"

    body += "</body></html>"
    return body

def send_email(html_body):
    msg = MIMEMultipart("alternative")
    msg["From"] = YOUR_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = f"Daily Open Practicum + Internship Listings ({datetime.date.today()})"
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
    web_search_listings = fetch_web_search()

    all_listings = rss_listings + program_listings + linkedin_listings + web_search_listings

    email_body = build_email(all_listings)
    send_email(email_body)

    print(f"Email sent with {len(all_listings)} listings")