"""
Remote OK scraper — uses their public JSON API (no auth required).
https://remoteok.com/api
"""

import requests
from datetime import datetime, timezone
from config import KEYWORDS, LOOKBACK_MINUTES

API_URL = "https://remoteok.com/api"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobAlertBot/1.0; +https://github.com)"}


def get_jobs():
    try:
        resp = requests.get(API_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        jobs_raw = data[1:] if data else []   # first item is metadata
    except Exception as e:
        print(f"[RemoteOK] Error: {e}")
        return []

    cutoff = datetime.now(timezone.utc).timestamp() - (LOOKBACK_MINUTES * 60)
    results = []

    for job in jobs_raw:
        try:
            epoch = int(job.get("epoch", 0))
            if epoch < cutoff:
                continue

            title = job.get("position", "")
            tags  = " ".join(job.get("tags", []))
            text  = f"{title} {tags}".lower()

            if not any(kw in text for kw in KEYWORDS):
                continue

            results.append({
                "id":          f"remoteok_{job.get('id', '')}",
                "title":       title,
                "company":     job.get("company", ""),
                "location":    "Remote – Worldwide",
                "url":         job.get("url", f"https://remoteok.com/l/{job.get('slug', '')}"),
                "salary_text": job.get("salary", ""),
                "description": job.get("description", ""),
                "posted_at":   datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(),
                "source":      "Remote OK",
                "tags":        job.get("tags", []),
            })
        except Exception:
            continue

    print(f"[RemoteOK] {len(results)} matching jobs found")
    return results
