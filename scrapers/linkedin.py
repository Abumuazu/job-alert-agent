"""
LinkedIn Jobs scraper — Playwright + stealth.
Scrapes the public LinkedIn jobs search page (no login required).

Design choices:
- f_TPR=r86400 fetches jobs posted in the last 24 h so the 4-hour LOOKBACK
  window always has plenty of candidates to filter down locally.
- Uses BeautifulSoup on page.content() as the primary parser — more resilient
  than Playwright query selectors when LinkedIn reshuffles class names.
- Playwright selector wait is non-fatal: we proceed with whatever loaded.
"""

from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from bs4 import BeautifulSoup
from scrapers.browser import get_page
from config import KEYWORDS, LOOKBACK_MINUTES

SEARCH_URLS = [
    (
        "https://www.linkedin.com/jobs/search/"
        "?keywords=react%20native%20developer"
        "&f_WT=2"          # remote
        "&f_TPR=r86400"    # last 24 hours
        "&sortBy=DD"       # date descending
    ),
    (
        "https://www.linkedin.com/jobs/search/"
        "?keywords=react%20native%20engineer"
        "&f_WT=2"
        "&f_TPR=r86400"
        "&sortBy=DD"
    ),
]


def _parse_html(html: str, cutoff: datetime) -> list:
    soup = BeautifulSoup(html, "lxml")
    results = []

    # LinkedIn public job cards live under .base-card or li[data-occludable-job-id]
    cards = (
        soup.select(".base-card")
        or soup.select("li[data-occludable-job-id]")
        or soup.select("li.jobs-search-results__list-item")
    )

    for card in cards:
        try:
            title_el   = card.select_one("h3, .base-search-card__title")
            company_el = card.select_one("h4, .base-search-card__subtitle")
            link_el    = card.select_one("a.base-card__full-link, a[href*='/jobs/view/']")
            time_el    = card.select_one("time")

            title   = title_el.get_text(strip=True)   if title_el   else ""
            company = company_el.get_text(strip=True) if company_el else ""
            href    = link_el.get("href", "")         if link_el    else ""
            href    = href.split("?")[0]               # strip tracking params

            if not title or not any(kw in title.lower() for kw in KEYWORDS):
                continue

            # Parse post time
            posted_at = datetime.now(timezone.utc).isoformat()
            if time_el:
                dt = time_el.get("datetime", "")
                if dt:
                    try:
                        pub = date_parser.parse(dt)
                        if pub.tzinfo is None:
                            pub = pub.replace(tzinfo=timezone.utc)
                        if pub < cutoff:
                            continue
                        posted_at = pub.isoformat()
                    except Exception:
                        pass

            job_id = href.rstrip("/").split("/")[-1] if href else str(abs(hash(title + company)))

            results.append({
                "id":          f"linkedin_{job_id}",
                "title":       title,
                "company":     company,
                "location":    "Remote",
                "url":         href,
                "salary_text": "",
                "description": "",
                "posted_at":   posted_at,
                "source":      "LinkedIn",
                "tags":        [],
            })
        except Exception:
            continue

    return results


def _scrape_url(url: str, cutoff: datetime) -> list:
    page = get_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Non-fatal wait — proceed even if selector never appears
        try:
            page.wait_for_selector(
                "ul.jobs-search__results-list, .base-card, li[data-occludable-job-id]",
                timeout=12000,
            )
        except Exception:
            pass

        html = page.content()
        return _parse_html(html, cutoff)

    except Exception as e:
        print(f"[LinkedIn] Error on {url}: {e}")
        return []
    finally:
        try:
            page.context.close()
        except Exception:
            pass


def get_jobs() -> list:
    cutoff      = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)
    all_results = []

    for url in SEARCH_URLS:
        all_results.extend(_scrape_url(url, cutoff))

    # Deduplicate by job id
    seen, unique = set(), []
    for j in all_results:
        if j["id"] not in seen:
            seen.add(j["id"])
            unique.append(j)

    print(f"[LinkedIn] {len(unique)} matching jobs found")
    return unique
