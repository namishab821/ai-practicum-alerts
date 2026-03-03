import feedparser
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

YOUR_EMAIL = os.environ['EMAIL_ADDRESS']
YOUR_PASSWORD = os.environ['EMAIL_PASSWORD']
TO_EMAIL = YOUR_EMAIL

ZIP = "94582"
RADIUS = "12"

KEYWORDS = [
    "counseling practicum",
    "counseling internship",
    "mental health intern",
    "school counseling",
    "clinical mental health counseling intern"
]

RSS_FEEDS = [
    f"https://www.indeed.com/rss?q=counseling+practicum+OR+counseling+internship&l={ZIP}&radius={RADIUS}",
    f"https://www.indeed.com/rss?q=clinical+mental+health+intern+OR+mental+health+intern&l={ZIP}&radius={RADIUS}"
]

SCRAPE_URLS = [
    "https://www.discoveryctr.net/training-opportunities/",
    "https://www.healthsolutionswest.org/careers/internships-practicums/",
    "https://www.shinealight.info/for-therapists/internships/",
    "https://www.cccntr.com/employment/internships/",
    "https://www.catalysscounseling.com/internship-opportunities"
]

def fetch_rss():
    items = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title.lower()
            summary = entry.summary.lower()
            if any(keyword.lower() in title or keyword.lower() in summary for keyword in KEYWORDS):
                items.append({"title": entry.title, "link": entry.link, "published": entry.get("published", "")})
    return items

def scrape_search(url):
    items = []
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            text = a_tag.get_text().lower()
            link = a_tag['href']
            if any(k.lower() in text for k in KEYWORDS):
                if link.startswith("/"):
                    base = "/".join(url.split("/")[:3])
                    link = base + link
                items.append({"title": a_tag.get_text().strip(), "link": link, "published": ""})
        if not items:
            for block in soup.find_all(["li", "div"]):
                text = block.get_text().lower()
                if any(k.lower() in text for k in KEYWORDS):
                    a_tag = block.find("a", href=True)
                    if a_tag:
                        link = a_tag['href']
                        if link.startswith("/"):
                            base = "/".join(url.split("/")[:3])
                            link = base + link
                        items.append({"title": a_tag.get_text().strip(), "link": link, "published": ""})
                    else:
                        items.append({"title": block.get_text().strip(), "link": url, "published": ""})
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    return items

def build_email(listings):
    if not listings:
        body = "No new practicum listings today."
    else:
        body = "<h2>New Practicum Listings</h2><ul>"
        for item in listings:
            body += f'<li><a href="{item["link"]}">{item["title"]}</a> ({item["published"]})</li>'
        body += "</ul>"
    return body

def send_email(html_body):
    msg = MIMEMultipart("alternative")
    msg["From"] = YOUR_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = "Daily Practicum Listings"
    part = MIMEText(html_body, "html")
    msg.attach(part)
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(YOUR_EMAIL, YOUR_PASSWORD)
    server.sendmail(YOUR_EMAIL, TO_EMAIL, msg.as_string())
    server.quit()

if __name__ == "__main__":
    all_listings = fetch_rss()
    for url in SCRAPE_URLS:
        all_listings.extend(scrape_search(url))
    unique_links = set()
    filtered_listings = []
    for listing in all_listings:
        if listing['link'] not in unique_links:
            unique_links.add(listing['link'])
            filtered_listings.append(listing)
    email_body = build_email(filtered_listings)
    send_email(email_body)
    print(f"Email sent with {len(filtered_listings)} listings.")