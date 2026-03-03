import feedparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

YOUR_EMAIL = os.environ['EMAIL_ADDRESS']
YOUR_PASSWORD = os.environ['EMAIL_PASSWORD']
TO_EMAIL = YOUR_EMAIL

ZIP = "94582"
RADIUS = "12"

RSS_FEED = f"https://www.indeed.com/rss?q=counseling+internship+OR+mental+health+intern&l={ZIP}&radius={RADIUS}"


def fetch_rss():
    feed = feedparser.parse(RSS_FEED)
    items = []

    for entry in feed.entries:
        items.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.get("published", "")
        })

    return items


def build_email(listings):
    if not listings:
        return """
        <html>
            <body>
                <h2>No listings found at all.</h2>
            </body>
        </html>
        """

    body = """
    <html>
        <body>
            <h2>ALL Practicum Listings Found</h2>
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
    msg["Subject"] = "DEBUG: Practicum Listings"

    part = MIMEText(html_body, "html")
    msg.attach(part)

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(YOUR_EMAIL, YOUR_PASSWORD)
    server.sendmail(YOUR_EMAIL, TO_EMAIL, msg.as_string())
    server.quit()


if __name__ == "__main__":
    listings = fetch_rss()
    print(f"Total listings found: {len(listings)}")
    email_body = build_email(listings)
    send_email(email_body)