"""
Remotive scraper — uses their public REST API (no auth required).
https://remotive.com/api/remote-jobs
"""

import requests
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from config import KEYWORDS, LOOKBACK_MINUTES

API_URL = "https://remotive.com/api/remote-jobs"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobAlertBot/1.0)"}


def get_jobs():
    try:
        resp = requests.get(
            API_URL,
            params={"search": "react native", "limit": 50},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        jobs_raw = resp.json().get("jobs", [])
    except Exception as e:
        print(f"[Remotive] Error: {e}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)
    results = []

    for job in jobs_raw:
        try:
            pub_date = date_parser.parse(job.get("publication_date", ""))
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            if pub_date < cutoff:
                continue

            title = job.get("title", "")
            tags  = " ".join(job.get("tags", []))
            text  = f"{title} {tags}".lower()

            if not any(kw in text for kw in KEYWORDS):
                continue

            results.append({
                "id":          f"remotive_{job.get('id', '')}",
                "title":       title,
                "company":     job.get("company_name", ""),
                "location":    job.get("candidate_required_location", "Worldwide"),
                "url":         job.get("url", ""),
                "salary_text": job.get("salary", ""),
                "description": job.get("description", ""),
                "posted_at":   pub_date.isoformat(),
                "source":      "Remotive",
                "tags":        job.get("tags", []),
            })
        except Exception:
            continue

    print(f"[Remotive] {len(results)} matching jobs found")
    return results
