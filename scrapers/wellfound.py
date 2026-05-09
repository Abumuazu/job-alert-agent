"""
Wellfound (formerly AngelList Talent) scraper — Playwright + stealth.

Design choices:
- Primary: extract __NEXT_DATA__ JSON embedded by Next.js — this is far more
  reliable than scraping obfuscated React class names that change every deploy.
- Fallback: BS4 DOM parse of whatever rendered, with loose selectors.
- Startup-focused: best source for early-stage React Native roles.
"""

import json
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from bs4 import BeautifulSoup
from scrapers.browser import get_page
from config import KEYWORDS, LOOKBACK_MINUTES

SEARCH_URL = "https://wellfound.com/jobs?q[keywords]=react+native&q[remote]=true"


# ── Primary: __NEXT_DATA__ JSON ──────────────────────────────────────────────

def _extract_next_data(page) -> dict:
    try:
        raw = page.evaluate(
            "() => { const el = document.getElementById('__NEXT_DATA__'); "
            "return el ? el.textContent : null; }"
        )
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


def _jobs_from_next_data(data: dict, cutoff: datetime) -> list:
    results = []
    try:
        props    = data.get("props", {}).get("pageProps", {})
        # Wellfound nests jobs under startupSearchResults.startups[].highlightedJobListings
        startups = (
            props.get("startupSearchResults", {}).get("startups", [])
            or props.get("results", {}).get("startups", [])
            or []
        )

        for startup in startups:
            company   = startup.get("name", "")
            job_lists = (
                startup.get("highlightedJobListings", [])
                or startup.get("jobListings", [])
                or []
            )

            for job in job_lists:
                title    = job.get("title", "") or job.get("role", "")
                job_id   = str(job.get("id", ""))
                slug     = job.get("slug", "")
                salary   = str(job.get("compensation", "") or job.get("salary", "") or "")
                desc     = (job.get("description", "") or "")[:400]
                tags     = [str(t).lower() for t in (job.get("skills", []) or [])]

                if not any(kw in f"{title} {desc}".lower() for kw in KEYWORDS):
                    continue

                posted_raw = job.get("createdAt", "") or job.get("publishedAt", "")
                posted_at  = datetime.now(timezone.utc).isoformat()
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

                url = (
                    f"https://wellfound.com/jobs/{slug}"
                    if slug
                    else f"https://wellfound.com/l/{job_id}"
                    if job_id
                    else SEARCH_URL
                )

                results.append({
                    "id":          f"wellfound_{job_id or abs(hash(title + company))}",
                    "title":       title,
                    "company":     company,
                    "location":    "Remote",
                    "url":         url,
                    "salary_text": salary,
                    "description": desc,
                    "posted_at":   posted_at,
                    "source":      "Wellfound",
                    "tags":        tags or ["startup", "react-native"],
                })
    except Exception:
        pass

    return results


# ── Fallback: BS4 DOM scrape ──────────────────────────────────────────────────

def _jobs_from_dom(html: str, cutoff: datetime) -> list:
    soup = BeautifulSoup(html, "lxml")
    results = []

    cards = (
        soup.select("[data-test='StartupResult']")
        or soup.select("div[class*='JobListing']")
        or soup.select("div[class*='styles_component']")
        or soup.select("div[class*='job']")
    )

    for card in cards:
        try:
            text = card.get_text(" ", strip=True)
            if not any(kw in text.lower() for kw in KEYWORDS):
                continue

            lines   = [l for l in text.splitlines() if l.strip()]
            title   = lines[0] if lines else ""
            company = lines[1] if len(lines) > 1 else ""

            link_el  = card.select_one("a[href*='/jobs/'], a[href*='/l/']")
            href     = link_el.get("href", "") if link_el else ""
            full_url = f"https://wellfound.com{href}" if href.startswith("/") else href

            results.append({
                "id":          f"wellfound_{abs(hash(full_url or title + company))}",
                "title":       title,
                "company":     company,
                "location":    "Remote",
                "url":         full_url or SEARCH_URL,
                "salary_text": "",
                "description": text[:400],
                "posted_at":   datetime.now(timezone.utc).isoformat(),
                "source":      "Wellfound",
                "tags":        ["startup", "react-native"],
            })
        except Exception:
            continue

    return results


# ── Entry point ───────────────────────────────────────────────────────────────

def get_jobs() -> list:
    page    = get_page()
    results = []
    cutoff  = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)

    try:
        page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=40000)

        # Give Next.js time to populate __NEXT_DATA__ and lazy-load cards
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        # Scroll to trigger lazy loading
        for _ in range(3):
            page.keyboard.press("End")
            page.wait_for_timeout(1200)

        # Try structured JSON first
        data = _extract_next_data(page)
        if data:
            results = _jobs_from_next_data(data, cutoff)

        # Fall through to DOM if JSON gave nothing
        if not results:
            results = _jobs_from_dom(page.content(), cutoff)

    except Exception as e:
        print(f"[Wellfound] Error: {e}")
    finally:
        try:
            page.context.close()
        except Exception:
            pass

    print(f"[Wellfound] {len(results)} matching jobs found")
    return results
