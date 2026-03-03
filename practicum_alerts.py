import feedparser
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import json

# -----------------------------------
# Configuration
# -----------------------------------
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

SCRAPE_URLS = [
    "https://www.contracosta.ca.gov/332/Behavioral-Health-Services",  # Contra Costa Behavioral Health
    "https://www.solanocounty.com/depts/ph/behavioral_health/internships.asp",  # Solano County BH
    "https://www.acgov.org/behavioral-health-services",  # Alameda County BH (general)
    "https://healthsolutionswest.org/careers/internships-practicums/",
    "https://www.discoveryctr.net/training-opportunities/",
    "https://www.earthcirclescenter.com/internships/",
    "https://mentalhealthtraining-ncal.kaiserpermanente.org/pre-masters-mental-health-internship/"
]

SENT_FILE = "sent_listings.json"

# -----------------------------------
# Fetch RSS Listings
# -----------------------------------
def fetch_rss():
    items = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title
            summary = entry.summary
            if any(k.lower() in title.lower() or k.lower() in summary.lower() for k in KEYWORDS):
                items.append({
                    "title": title,
                    "link": entry.link,
                    "published": entry.get("published", "")
                })
    print(f"DEBUG: RSS found {len(items)} listings")
    return items

# -----------------------------------
# Scrape HTML Pages
# -----------------------------------
def scrape_html(url):
    items = []
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")

        # Look for `<a>` tags
        for a in soup.find_all("a", href=True):
            text = a.get_text().lower().strip()
            link = a["href"]
            if any(keyword.lower() in text for keyword in KEYWORDS):
                # Convert relative to absolute
                if link.startswith("/"):
                    base = "/".join(url.split("/")[:3])
                    link = base + link
                items.append({"title": a.get_text().strip(), "link": link, "published": ""})

        # Also check text blocks if no <a>
        if not items:
            blocks = soup.find_all(["p", "li", "div"])
            for block in blocks:
                text = block.get_text().lower()
                if any(keyword.lower() in text for keyword in KEYWORDS):
                    a = block.find("a", href=True)
                    if a:
                        link = a["href"]
                        if link.startswith("/"):
                            base = "/".join(url.split("/")[:3])
                            link = base + link
                        items.append({"title": a.get_text().strip(), "link": link, "published": ""})
                    else:
                        title = block.get_text().strip()
                        items.append({"title": title[:80] + "...", "link": url, "published": ""})

        print(f"DEBUG: Scraped {len(items)} from {url}")
    except Exception as e:
        print(f"ERROR scraping {url}: {e}")
    return items

# -----------------------------------
# Deduplication Logic
# -----------------------------------
def load_sent_listings():
    if not os.path.exists(SENT_FILE):
        return []
    with open(SENT_FILE, "r") as f:
        return json.load(f)

def save_sent_listings(sent_links):
    with open(SENT_FILE, "w") as f:
        json.dump(sent_links, f)

def filter_new(all_listings, sent_links):
    return [item for item in all_listings if item["link"] not in sent_links]

# -----------------------------------
# Email Builder
# -----------------------------------
def build_email(listings):
    if not listings:
        return """
        <html><body><h2>No new practicum listings today 🎉</h2></body></html>
        """

    body = """
    <html>
      <body>
        <h2>New Practicum & Internship Listings</h2>
        <ul>
    """
    for item in listings:
        body += f"""
            <li style="margin-bottom:12px;">
                <strong>{item['title']}</strong><br>
                <a href="{item['link']}" target="_blank">{item['link']}</a><br>
                <small>{item['published']}</small>
            </li>
        """
    body += "</ul></body></html>"
    return body

def send_email(html_body):
    msg = MIMEMultipart("alternative")
    msg["From"] = YOUR_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = "Daily Practicum + Internship Listings"
    part = MIMEText(html_body, "html")
    msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(YOUR_EMAIL, YOUR_PASSWORD)
        server.sendmail(YOUR_EMAIL, TO_EMAIL, msg.as_string())

# -----------------------------------
# Main
# -----------------------------------
if __name__ == "__main__":

    all_listings = []

    # Indeed RSS
    all_listings += fetch_rss()

    # Scrape HTML sources
    for u in SCRAPE_URLS:
        all_listings += scrape_html(u)

    # Deduplicate across sources
    sent = load_sent_listings()
    new_listings = filter_new(all_listings, sent)

    # Send email
    email_body = build_email(new_listings)
    send_email(email_body)

    # Update store
    updated = sent + [item["link"] for item in new_listings]
    save_sent_listings(updated)

    print(f"Email sent with {len(new_listings)} new listings.")