"""
Himalayas scraper — pure JSON API, no browser needed.

Himalayas maintains a public jobs API that returns structured JSON with clean,
consistent field names. This is the most reliable source in the pipeline —
no selectors to break, no bot detection, no Playwright overhead.

API reference: https://himalayas.app/jobs/api
"""

import requests
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from config import KEYWORDS, LOOKBACK_MINUTES

API_URL = "https://himalayas.app/jobs/api"

HEADERS = {
    "User-Agent": "JobAlertBot/1.0 (personal job tracker)",
    "Accept":     "application/json",
}


def get_jobs() -> list:
    cutoff  = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)
    results = []

    try:
        resp = requests.get(
            API_URL,
            params={"skills": "React Native", "remote": "true", "limit": 50},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        jobs = data if isinstance(data, list) else data.get("jobs", [])

        for job in jobs:
            title   = job.get("title", "") or job.get("jobTitle", "")
            company = (
                (job.get("company") or {}).get("name", "")
                or job.get("companyName", "")
            )
            url     = (
                job.get("applicationLink", "")
                or job.get("url", "")
                or job.get("applyUrl", "")
            )
            desc    = (job.get("description", "") or "")[:400]
            tags    = [str(t).lower() for t in (job.get("skills", []) or [])]
            job_id  = str(job.get("id", "") or abs(hash(title + company)))

            # Salary: combine currency + min/max when available
            s_min = job.get("salaryMin") or job.get("minSalary") or ""
            s_max = job.get("salaryMax") or job.get("maxSalary") or ""
            s_cur = job.get("salaryCurrency", "USD")
            salary = (
                f"{s_cur} {s_min}–{s_max}".strip(" –")
                if s_min or s_max
                else ""
            )

            text = f"{title} {desc} {' '.join(tags)}".lower()
            if not any(kw in text for kw in KEYWORDS):
                continue

            posted_raw = (
                job.get("createdAt", "")
                or job.get("publishedAt", "")
                or job.get("posted", "")
            )
            posted_at = datetime.now(timezone.utc).isoformat()
            if posted_raw:
                try:
                    pub = date_parser.parse(str(posted_raw))
                    if pub.tzinfo is None:
                        pub = pub.replace(tzinfo=timezone.utc)
                    if pub < cutoff:
                        continue
                    posted_at = pub.isoformat()
                except Exception:
                    pass

            results.append({
                "id":          f"himalayas_{job_id}",
                "title":       title,
                "company":     company,
                "location":    "Remote",
                "url":         url,
                "salary_text": salary,
                "description": desc,
                "posted_at":   posted_at,
                "source":      "Himalayas",
                "tags":        tags,
            })

    except Exception as e:
        print(f"[Himalayas] Error: {e}")

    print(f"[Himalayas] {len(results)} matching jobs found")
    return results
