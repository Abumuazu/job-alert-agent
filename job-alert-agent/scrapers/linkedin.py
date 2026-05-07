"""
Indeed RSS scraper — replaces the LinkedIn guest API which now returns 404.
Indeed's RSS feed is public, reliable, and returns jobs sorted by date.
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from config import KEYWORDS, LOOKBACK_MINUTES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept":     "application/rss+xml,application/xml,text/xml,*/*",
}

# Indeed remote job type ID for "Remote" filter
INDEED_REMOTE_ID = "032b3046-06a3-4876-8dfd-474eb5e7ed11"

SEARCH_TERMS = [
    "react native developer",
    "react native engineer",
]


def _fetch_rss(term: str) -> list:
    url = "https://www.indeed.com/rss"
    params = {
        "q":          term,
        "remotejob":  INDEED_REMOTE_ID,
        "sort":       "date",
        "fromage":    "1",   # posted in last 1 day (we filter more tightly below)
    }
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        print(f"[Indeed] Error for '{term}': {e}")
        return []

    cutoff  = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)
    results = []

    for item in root.findall(".//item"):
        try:
            pub_el    = item.find("pubDate")
            title_el  = item.find("title")
            link_el   = item.find("link")
            guid_el   = item.find("guid")
            desc_el   = item.find("description")

            if pub_el is None:
                continue

            pub_date = date_parser.parse(pub_el.text)
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            if pub_date < cutoff:
                continue

            title = title_el.text if title_el is not None else ""
            url   = link_el.text  if link_el  is not None else ""
            guid  = guid_el.text  if guid_el  is not None else url
            desc  = desc_el.text  if desc_el  is not None else ""

            # Title format on Indeed: "Job Title - Company Name"
            company = ""
            if " - " in title:
                parts   = title.rsplit(" - ", 1)
                title   = parts[0].strip()
                company = parts[1].strip()

            full_text = f"{title} {desc}".lower()
            if not any(kw in full_text for kw in KEYWORDS):
                continue

            results.append({
                "id":          f"indeed_{abs(hash(guid))}",
                "title":       title,
                "company":     company,
                "location":    "Remote",
                "url":         url,
                "salary_text": "",
                "description": desc[:500] if desc else "",
                "posted_at":   pub_date.isoformat(),
                "source":      "Indeed",
                "tags":        [],
            })
        except Exception:
            continue

    return results


def get_jobs() -> list:
    all_results = []
    for term in SEARCH_TERMS:
        all_results.extend(_fetch_rss(term))

    # Deduplicate
    seen, unique = set(), []
    for j in all_results:
        if j["id"] not in seen:
            seen.add(j["id"])
            unique.append(j)

    print(f"[Indeed] {len(unique)} matching jobs found")
    return unique
