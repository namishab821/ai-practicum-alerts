# AI Practicum Alerts

Automated Python script that fetches daily counseling practicum listings from RSS feeds and local practicum pages, filters by keywords, and emails new listings automatically.

## How it Works

1. Fetches listings from Indeed RSS feeds and local agency webpages.
2. Scrapes public job boards and pages for matching keywords.
3. Filters duplicates and builds an HTML email.
4. Sends email daily via GitHub Actions.

## Setup

1. Upload the repo files to GitHub.
2. Add email credentials as GitHub Secrets: `EMAIL_ADDRESS` & `EMAIL_PASSWORD`.
3. GitHub Actions will run daily and email new practicum listings.

# Trigger GitHub Actions recognition