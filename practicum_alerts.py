import feedparser
import requests
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# ==============================
# CONFIG
# ==============================

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
FROM_EMAIL = "your_verified_sender@email.com"
TO_EMAIL = "your_email@email.com"

ZIP_CODE = "94582"
RADIUS = "25"

# ==============================
# HARD-CODED ON-SITE PROGRAMS
# ==============================

ON_SITE_PROGRAMS = [
    {
        "title": "Discovery Counseling Center – Training Opportunities",
        "link": "https://www.discoveryctr.net/training-opportunities/"
    },
    {
        "title": "Kaiser Permanente – Pre-Master’s Mental Health Internship",
        "link": "https://mentalhealthtraining-ncal.kaiserpermanente.org/pre-masters-mental-health-internship/"
    },
    {
        "title": "Contra Costa Behavioral Health – Internship Program",
        "link": "https://www.contracosta.ca.gov/332/Behavioral-Health-Services"
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
        "title": "Health Solutions West – Internships/Practicums",
        "link": "https://healthsolutionswest.org/careers/internships-practicums/"
    },
    {
        "title": "Earth Circles Counseling Center – Internships",
        "link": "https://www.earthcirclescenter.com/internships"
    }
]

# ==============================
# RSS FEEDS
# ==============================

LOCAL_RSS_FEEDS = [
    f"https://www.indeed.com/rss?q=counseling+practicum+OR+counseling+internship&l={ZIP_CODE}&radius={RADIUS}",
    f"https://www.indeed.com/rss?q=mental+health+internship&l={ZIP_CODE}&radius={RADIUS}"
]

REMOTE_RSS_FEEDS = [
    "https://www.indeed.com/rss?q=remote+mental+health+internship",
    "https://www.indeed.com/rss?q=telehealth+mental+health+internship",
    "https://www.indeed.com/rss?q=remote+clinical+counseling+internship",
    "https://www.indeed.com/rss?q=virtual+therapy+internship"
]

TELEHEALTH_KEYWORDS = [
    "telehealth",
    "tele-health",
    "teletherapy",
    "remote",
    "fully remote",
    "work from home",
    "wfh",
    "virtual",
    "online",
    "hybrid"
]

# ==============================
# FETCH LISTINGS
# ==============================

def fetch_listings():
    listings = []

    # Local feeds (on-site by default)
    for feed_url in LOCAL_RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            combined_text = (entry.title + " " + entry.summary).lower()

            is_remote = any(k in combined_text for k in TELEHEALTH_KEYWORDS)

            listings.append({
                "title": entry.title.strip(),
                "link": entry.link.strip(),
                "telehealth": is_remote
            })

    # Remote feeds (explicitly telehealth)
    for feed_url in REMOTE_RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            listings.append({
                "title": entry.title.strip(),
                "link": entry.link.strip(),
                "telehealth": True
            })

    return listings

# ==============================
# BUILD EMAIL
# ==============================

def build_email(listings):
    on_site_list = []
    telehealth_list = []

    for item in listings:
        if item["telehealth"]:
            telehealth_list.append(item)
        else:
            on_site_list.append(item)

    body = "<h2>Open Practicum & Internship Listings (California)</h2>"

    # ------------------------------
    # ON-SITE SECTION
    # ------------------------------

    body += "<h3>On-Site Opportunities</h3><ul>"

    # Hard-coded programs first
    for program in ON_SITE_PROGRAMS:
        body += f'<li><strong>{program["title"]}</strong><br><a href="{program["link"]}" target="_blank">{program["link"]}</a></li>'

    # RSS results
    for item in on_site_list:
        body += f'<li><strong>{item["title"]}</strong><br><a href="{item["link"]}" target="_blank">{item["link"]}</a></li>'

    body += "</ul>"

    # ------------------------------
    # TELEHEALTH SECTION (ALWAYS SHOW)
    # ------------------------------

    body += "<h3>Telehealth / Remote Opportunities</h3><ul>"

    if telehealth_list:
        for item in telehealth_list:
            body += f'<li><strong>{item["title"]}</strong><br><a href="{item["link"]}" target="_blank">{item["link"]}</a></li>'
    else:
        body += "<li><em>No remote or telehealth listings found today.</em></li>"

    body += "</ul>"

    return body

# ==============================
# SEND EMAIL
# ==============================

def send_email(content):
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=TO_EMAIL,
        subject="Daily Practicum & Internship Listings",
        html_content=content
    )

    sg = SendGridAPIClient(SENDGRID_API_KEY)
    sg.send(message)

# ==============================
# MAIN
# ==============================

if __name__ == "__main__":
    listings = fetch_listings()
    email_content = build_email(listings)
    send_email(email_content)