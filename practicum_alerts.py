def fetch_web_search():
    listings = []
    API_KEY = os.environ.get("WEB_SEARCH_API_KEY")  # Your SerpAPI key
    QUERY = "California telehealth counseling practicum OR mental health internship"

    try:
        params = {
            "engine": "google",
            "q": QUERY,
            "location": "California",
            "api_key": API_KEY
        }
        resp = requests.get("https://serpapi.com/search", params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("organic_results", [])

        for item in results:
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            if any(k.lower() in title.lower() + snippet.lower() for k in KEYWORDS):
                telehealth_tag = any(tk.lower() in title.lower() + snippet.lower() for tk in TELEHEALTH_KEYWORDS)
                listings.append({
                    "title": title,
                    "link": link,
                    "telehealth": telehealth_tag,
                    "source": "Web Search"
                })
    except Exception as e:
        print(f"ERROR fetching Web Search: {e}")

    return listings