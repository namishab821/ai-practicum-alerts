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
    "trainee", "training program"
]

TELEHEALTH_KEYWORDS = ["telehealth", "remote", "virtual", "online", "video"]

# Verified program pages
PROGRAM_LINKS = {
    "Discovery Counseling Center": "https://www.discoveryctr.net/training-opportunities/",
    "Kaiser Permanente Pre-Master’s Mental Health Internship": "https://mentalhealthtraining-ncal.kaiserpermanente.org/pre-masters-mental-health-internship/",
    "Contra Costa Behavioral Health": "https://www.contracosta.ca.gov/332/Behavioral-Health-Services",
    "Solano County Behavioral Health": "https://www.solanocounty.com/depts/ph/behavioral_health/internships.asp",
    "Alameda County Behavioral Health": "https://www.acgov.org/behavioral-health-services",
    "Health Solutions West": "https://healthsolutionswest.org/careers/internships-practicums/"
}

# RSS feeds
RSS_FEEDS = [
    f"https://www.indeed.com/rss?q=counseling+practicum+OR+counseling+internship&l={ZIP}&radius={RADIUS_MILES}"
]

LINKEDIN_SENDER = "jobs-noreply@linkedin.com"

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
SEARCH_QUERY = f"California counseling practicum OR mental health internship"

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
                listings.append({"title": title.strip(), "link": entry.link.strip(),
                                 "telehealth": telehealth_tag, "source": "RSS"})
    return listings

def fetch_program_links():
    listings = []
    for org, url in PROGRAM_LINKS.items():
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            # Search all links and text for keywords
            for tag in soup.find_all(["a","p","div"]):
                text = tag.get_text().strip()
                if any(k.lower() in text.lower() for k in KEYWORDS):
                    telehealth_tag = any(tk in text.lower() for tk in TELEHEALTH_KEYWORDS)
                    link = tag.get("href") if tag.has_attr("href") else url
                    listings.append({"title": f"{org}: {text}", "link": link,
                                     "telehealth": telehealth_tag, "source": "Program Page"})
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
                                listings.append({"title": text, "link": href,
                                                 "telehealth": telehealth_tag, "source": "LinkedIn"})
    except Exception as e:
        print(f"ERROR fetching LinkedIn alerts: {e}")
    return listings

def fetch_web_search():
    listings = []
    try:
        params = {
            "engine": "google",
            "q": SEARCH_QUERY,
            "location": STATE,
            "api_key": SERPAPI_KEY
        }
        resp = requests.get("https://serpapi.com/search", params=params)
        results = resp.json().get("organic_results", [])
        for item in results:
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            if any(k.lower() in title.lower() + snippet.lower() for k in KEYWORDS):
                telehealth_tag = any(tk in title.lower() + snippet.lower() for tk in TELEHEALTH_KEYWORDS)
                listings.append({"title": title, "link": link, "telehealth": telehealth_tag, "source": "Web Search"})
    except Exception as e:
        print(f"ERROR fetching Web Search: {e}")
    return listings

def build_email(listings):
    if not listings:
        return "<html><body><h2>No open practicum listings today 🎉</h2></body></html>"
    body = "<html><body><h2>Open Practicum & Internship Listings (CA)</h2><ul>"
    for item in listings:
        tele_tag = " — Telehealth" if item["telehealth"] else ""
        source_tag = f" ({item['source']})"
        body += f'<li><strong>{item["title"]}</strong>{tele_tag}{source_tag}<br><a href="{item["link"]}" target="_blank">{item["link"]}</a></li>'
    body += "</ul></body></html>"
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
    web_search_listings = fetch_web_search()

    all_listings = rss_listings + program_listings + linkedin_listings + web_search_listings

    email_body = build_email(all_listings)
    send_email(email_body)
    print(f"Email sent with {len(all_listings)} listings")