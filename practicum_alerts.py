import feedparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import json

YOUR_EMAIL = os.environ['EMAIL_ADDRESS']
YOUR_PASSWORD = os.environ['EMAIL_PASSWORD']
TO_EMAIL = YOUR_EMAIL

# Expanded radius for testing
ZIP = "94582"
RADIUS = "30"  # 30 miles for testing

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

SENT_FILE = "sent_listings.json"


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
    print(f"DEBUG: Total listings fetched from RSS feeds (expanded radius): {len(items)}")
    for item in items:
        print(f"DEBUG: {item['title']}")
    return items


def load_sent_listings():
    if not os.path.exists(SENT_FILE):
        return []
    with open(SENT_FILE, "r") as f:
        return json.load(f)


def save_sent_listings(sent_links):
    with open(SENT_FILE, "w") as f:
        json.dump(sent_links, f)


def filter_new_listings(all_listings, sent_links):
    return [item for item in all_listings if item["link"] not in sent_links]


def build_email(listings):
    if not listings:
        return """
        <html>
            <body>
                <h2>No new practicum listings today 🎉</h2>
            </body>
        </html>
        """

    body = """
    <html>
        <body>
            <h2>New Practicum Listings (Expanded Radius)</h2>
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
    msg["Subject"] = "Test: Practicum Listings (Expanded Radius)"

    part = MIMEText(html_body, "html")
    msg.attach(part)

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(YOUR_EMAIL, YOUR_PASSWORD)
    server.sendmail(YOUR_EMAIL, TO_EMAIL, msg.as_string())
    server.quit()


if __name__ == "__main__":
    all_listings = fetch_rss()
    sent_links = load_sent_listings()

    new_listings = filter_new_listings(all_listings, sent_links)

    email_body = build_email(new_listings)
    send_email(email_body)

    # Update sent listings
    updated_links = sent_links + [item["link"] for item in new_listings]
    save_sent_listings(updated_links)

    print(f"Email sent with {len(new_listings)} new listings.")