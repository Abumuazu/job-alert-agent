"""
LinkedIn scraper — uses the public guest job search endpoint LinkedIn's own
website calls. No auth required, but subject to occasional rate-limiting.
Falls back gracefully if blocked.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from config import KEYWORDS, LOOKBACK_MINUTES

SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostingsByCategory"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer":         "https://www.linkedin.com/jobs/search/",
}


def get_jobs():
    lookback_seconds = LOOKBACK_MINUTES * 60
    results = []

    # Run two keyword passes to maximise coverage
    for keyword in ["react native developer", "react native engineer"]:
        params = {
            "keywords": keyword,
            "location": "Worldwide",
            "f_WT":     "2",                      # remote
            "f_TPR":    f"r{lookback_seconds}",   # posted in last N seconds
            "start":    "0",
        }
        try:
            resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for card in soup.find_all("div", class_="base-card"):
                try:
                    title_el   = card.find("h3", class_="base-search-card__title")
                    company_el = card.find("h4", class_="base-search-card__subtitle")
                    link_el    = card.find("a", class_="base-card__full-link")
                    time_el    = card.find("time")

                    title   = title_el.get_text(strip=True)   if title_el   else ""
                    company = company_el.get_text(strip=True) if company_el else ""
                    url     = link_el.get("href", "")         if link_el    else ""

                    if not any(kw in title.lower() for kw in KEYWORDS):
                        continue

                    posted_at = datetime.now(timezone.utc).isoformat()
                    if time_el and time_el.get("datetime"):
                        posted_at = time_el.get("datetime")

                    job_id = url.split("?")[0].rstrip("/").split("/")[-1] if url else abs(hash(title + company))

                    results.append({
                        "id":          f"linkedin_{job_id}",
                        "title":       title,
                        "company":     company,
                        "location":    "Remote",
                        "url":         url.split("?")[0] if url else "",
                        "salary_text": "",
                        "description": "",
                        "posted_at":   posted_at,
                        "source":      "LinkedIn",
                        "tags":        [],
                    })
                except Exception:
                    continue
        except Exception as e:
            print(f"[LinkedIn] Error for '{keyword}': {e}")
            continue

    # Deduplicate within LinkedIn results
    seen = set()
    unique = []
    for j in results:
        if j["id"] not in seen:
            seen.add(j["id"])
            unique.append(j)

    print(f"[LinkedIn] {len(unique)} matching jobs found")
    return unique
