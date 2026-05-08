"""
LinkedIn Jobs scraper — Playwright + stealth.
Scrapes the public LinkedIn jobs search page (no login required).
Stealth plugin bypasses LinkedIn's bot detection from server IPs.
"""

from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from scrapers.browser import get_page
from config import KEYWORDS, LOOKBACK_MINUTES

SEARCH_URLS = [
    "https://www.linkedin.com/jobs/search/?keywords=react%20native%20developer&f_WT=2&f_TPR=r1800&sortBy=DD",
    "https://www.linkedin.com/jobs/search/?keywords=react%20native%20engineer&f_WT=2&f_TPR=r1800&sortBy=DD",
]


def _parse_linkedin_time(page, card) -> str:
    """Extract and return ISO timestamp from a LinkedIn job card."""
    try:
        time_el = card.query_selector("time")
        if time_el:
            dt = time_el.get_attribute("datetime")
            if dt:
                return dt
    except Exception:
        pass
    return datetime.now(timezone.utc).isoformat()


def _scrape_url(url: str) -> list:
    page = get_page()
    results = []
    cutoff  = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("ul.jobs-search__results-list, .base-card", timeout=15000)

        cards = page.query_selector_all(".base-card")
        for card in cards:
            try:
                title_el   = card.query_selector("h3")
                company_el = card.query_selector("h4")
                link_el    = card.query_selector("a.base-card__full-link")

                title   = title_el.inner_text().strip()   if title_el   else ""
                company = company_el.inner_text().strip() if company_el else ""
                url_href = link_el.get_attribute("href")  if link_el    else ""
                url_href = url_href.split("?")[0]         if url_href   else ""

                if not title or not any(kw in title.lower() for kw in KEYWORDS):
                    continue

                posted_at = _parse_linkedin_time(page, card)
                try:
                    pub = date_parser.parse(posted_at)
                    if pub.tzinfo is None:
                        pub = pub.replace(tzinfo=timezone.utc)
                    if pub < cutoff:
                        continue
                except Exception:
                    pass  # keep if we can't parse the date

                job_id = url_href.rstrip("/").split("/")[-1] if url_href else abs(hash(title + company))

                results.append({
                    "id":          f"linkedin_{job_id}",
                    "title":       title,
                    "company":     company,
                    "location":    "Remote",
                    "url":         url_href,
                    "salary_text": "",
                    "description": "",
                    "posted_at":   posted_at,
                    "source":      "LinkedIn",
                    "tags":        [],
                })
            except Exception:
                continue
    except Exception as e:
        print(f"[LinkedIn] Error on {url}: {e}")
    finally:
        try:
            page.context.close()
        except Exception:
            pass

    return results


def get_jobs() -> list:
    all_results = []
    for url in SEARCH_URLS:
        all_results.extend(_scrape_url(url))

    seen, unique = set(), []
    for j in all_results:
        if j["id"] not in seen:
            seen.add(j["id"])
            unique.append(j)

    print(f"[LinkedIn] {len(unique)} matching jobs found")
    return unique
