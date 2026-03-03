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

def fetch_rss():
    items = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title
            summary = entry.summary
            if any(keyword.lower() in title.lower() or keyword.lower() in summary.lower() for keyword in KEYWORDS):
                items.append({
                    "title": title,
                    "link": entry.link,
                    "published": entry.get("published", "")
                })
    return items


def build_email(listings):
    if not listings:
        return """
        <html>
            <body>
                <h2>No new practicum listings today.</h2>
            </body>
        </html>
        """

    body = """
    <html>
        <body>
            <h2>New Practicum Listings</h2>
            <ul>
    """

    for item in listings:
        body += f"""
            <li style="margin-bottom: 16px;">
                <strong>{item['title']}</strong><br>
                <a href="{item['link']}" target="_blank">{item['link']}</a><br>
                <small>{item['published']}</small>
            </li>
        """

    body += """
            </ul>
        </body>
    </html>
    """

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
    listings = fetch_rss()
    email_body = build_email(listings)
    send_email(email_body)
    print(f"Email sent with {len(listings)} listings.")