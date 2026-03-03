import requests
from bs4 import BeautifulSoup
import feedparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import json

# -------------------------
# Configuration
# -------------------------
YOUR_EMAIL = os.environ.get("EMAIL_ADDRESS")
YOUR_PASSWORD = os.environ.get("EMAIL_PASSWORD")
TO_EMAIL = YOUR_EMAIL

ZIP = "94582"
RADIUS = "12"  # ~20 min drive

KEYWORDS = [
    "counseling practicum",
    "counseling internship",
    "mental health intern",
    "school counseling",
    "clinical intern",
    "behavioral health intern",
    "trainee"
]

RSS_FEEDS = [
    f"https://www.indeed.com/rss?q=counseling+practicum+OR+counseling+internship&l={ZIP}&radius={RADIUS}",
    f"https://www.indeed.com/rss?q=clinical+mental+health+intern+OR+mental+health+intern&l={ZIP}&radius={RADIUS}"
]

SCRAPE_PAGES = {
    "Discovery Counseling Center – Training Opportunities": "https://www.discoveryctr.net/training-opportunities/",
    "Kaiser Permanente Pre-Master’s Mental Health Internship": "https://mentalhealthtraining-ncal.kaiserpermanente.org/pre-masters-mental-health-internship/",
    "Contra Costa Behavioral Health – Internship Program": "https://www.contracosta.ca.gov/332/Behavioral-Health-Services",
    "Solano County Behavioral Health – Internship Program": "https://www.solanocounty.com/depts/ph/behavioral_health/internships.asp",
    "Alameda County Behavioral Health – Internship Program": "https://www.acgov.org/behavioral-health-services",
    "Health Solutions West – Internships/Practicums": "https://healthsolutionswest.org/careers/internships-practicums/",
    "Earth Circles Counseling Center – Internships": "https://www.earthcirclescenter.com/internships/"
}

SENT_FILE = "sent_listings.json"

# -------------------------
# RSS Functions
# -------------------------
def fetch_rss():
    listings = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title
            summary = entry.summary
            published = entry.get("published", "")
            if any(k.lower() in title.lower() or k.lower() in summary.lower() for k in KEYWORDS):
                listings.append({"title": title.strip(), "link": entry.link.strip(), "date": published})
    print(f"DEBUG: RSS found {len(listings)} listings")
    return listings

# -------------------------
# HTML Scraping Functions
# -------------------------
def scrape_program_pages():
    listings = []
    for program, url in SCRAPE_PAGES.items():
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=12)
            soup = BeautifulSoup(r.text, "html.parser")

            # Look for an "Open" or "Deadline" text nearby
            deadline_text = ""
            text_blocks = soup.find_all(["p", "li", "div"])
            for block in text_blocks:
                txt = block.get_text().lower()
                if "deadline" in txt or "open" in txt:
                    deadline_text = block.get_text().strip()
                    break

            listings.append({"title": program, "link": url, "date": deadline_text})
            print(f"DEBUG: Added {program} ({'with deadline' if deadline_text else 'no deadline'})")
        except Exception as e:
            print(f"ERROR scraping {url}: {e}")
    return listings

# -------------------------
# Deduplication
# -------------------------
def load_sent():
    if not os.path.exists(SENT_FILE):
        return []
    with open(SENT_FILE, "r") as f:
        return json.load(f)

def save_sent(sent_links):
    with open(SENT_FILE, "w") as f:
        json.dump(sent_links, f)

def filter_new(listings, sent_links):
    new = [item for item in listings if item["link"] not in sent_links]
    print(f"DEBUG: {len(new)} new listings after deduplication")
    return new

# -------------------------
# Email Builder
# -------------------------
def build_email(listings):
    if not listings:
        return "<html><body><h2>No new practicum listings today 🎉</h2></body></html>"

    body = "<html><body><h2>New Practicum & Internship Listings</h2><ul>"
    for item in listings:
        date_info = f"<br><small>{item['date']}</small>" if item['date'] else ""
        body += f'<li><strong>{item["title"]}</strong>{date_info}<br><a href="{item["link"]}" target="_blank">{item["link"]}</a></li>'
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
    html_listings = scrape_program_pages()
    all_listings = rss_listings + html_listings

    sent_links = load_sent()
    new_listings = filter_new(all_listings, sent_links)

    email_body = build_email(new_listings)
    send_email(email_body)

    updated_links = sent_links + [item["link"] for item in new_listings]
    save_sent(updated_links)

    print(f"Email sent with {len(new_listings)} new listings")