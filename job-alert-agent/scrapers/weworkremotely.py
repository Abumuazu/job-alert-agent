"""
We Work Remotely scraper — uses their public Atom RSS feed (no auth required).
https://weworkremotely.com
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from config import KEYWORDS, LOOKBACK_MINUTES

RSS_URL  = "https://weworkremotely.com/remote-jobs/search.atom"
HEADERS  = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept":     "application/atom+xml,application/xml,text/xml,text/html;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
NS       = {"atom": "http://www.w3.org/2005/Atom"}


def get_jobs():
    try:
        resp = requests.get(
            RSS_URL,
            params={"term": "react native"},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        print(f"[WeWorkRemotely] Error: {e}")
        return []

    cutoff  = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)
    results = []

    for entry in root.findall("atom:entry", NS):
        try:
            pub_el = entry.find("atom:published", NS)
            if pub_el is None:
                continue
            pub_date = date_parser.parse(pub_el.text)
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            if pub_date < cutoff:
                continue

            title_el   = entry.find("atom:title", NS)
            content_el = entry.find("atom:content", NS)
            link_el    = entry.find("atom:link", NS)
            id_el      = entry.find("atom:id", NS)

            raw_title = title_el.text if title_el is not None else ""
            content   = content_el.text if content_el is not None else ""
            url       = link_el.get("href", "") if link_el is not None else ""
            job_id    = id_el.text if id_el is not None else url

            # Keyword check against title + content
            text = f"{raw_title} {content}".lower()
            if not any(kw in text for kw in KEYWORDS):
                continue

            # WWR title format: "Company | Role Title"
            company, title = "", raw_title
            if "|" in raw_title:
                parts   = raw_title.split("|", 1)
                company = parts[0].strip()
                title   = parts[1].strip()

            results.append({
                "id":          f"wwr_{abs(hash(job_id))}",
                "title":       title,
                "company":     company,
                "location":    "Remote – Worldwide",
                "url":         url,
                "salary_text": "",
                "description": content[:500] if content else "",
                "posted_at":   pub_date.isoformat(),
                "source":      "We Work Remotely",
                "tags":        [],
            })
        except Exception:
            continue

    print(f"[WeWorkRemotely] {len(results)} matching jobs found")
    return results
