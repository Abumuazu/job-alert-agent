"""
Indeed scraper — Playwright + stealth + BeautifulSoup.

Design choices:
- Parses page.content() with BS4 — resilient to Indeed's frequent class-name
  changes and A/B test variations.
- wait_for_selector is non-fatal; we proceed with whatever the page loaded.
- Identifies job cards by the stable data-jk attribute (job key) whenever
  possible; falls back to class-based selectors.
"""

from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from bs4 import BeautifulSoup
from scrapers.browser import get_page
from config import KEYWORDS, LOOKBACK_MINUTES

SEARCH_URL = (
    "https://www.indeed.com/jobs"
    "?q=react+native+developer"
    "&sc=0kf%3Aattr%28DSQF7%29%3B"   # remote filter attribute
    "&sort=date"
    "&fromage=1"                       # posted in last 1 day
)


def _parse_html(html: str, cutoff: datetime) -> list:
    soup = BeautifulSoup(html, "lxml")
    results = []

    # Prefer data-jk (stable job key); fall back to class selectors
    cards = (
        soup.select("[data-jk]")
        or soup.select(".job_seen_beacon")
        or soup.select(".resultContent")
    )

    for card in cards:
        try:
            title_el   = (
                card.select_one("h2 a span[title]")
                or card.select_one("h2 span[title]")
                or card.select_one(".jobTitle span")
                or card.select_one("h2 a span")
            )
            company_el = (
                card.select_one("[data-testid='company-name']")
                or card.select_one(".companyName")
                or card.select_one("[class*='companyName']")
            )
            date_el    = (
                card.select_one("[data-testid='myJobsStateDate']")
                or card.select_one(".date")
                or card.select_one("span[class*='date']")
            )
            link_el    = (
                card.select_one("h2 a")
                or card.select_one("a[id^='job_']")
            )

            title    = (
                title_el.get("title") or title_el.get_text(strip=True)
                if title_el else ""
            )
            company  = company_el.get_text(strip=True) if company_el else ""
            date_txt = date_el.get_text(strip=True)    if date_el    else ""
            href     = link_el.get("href", "")         if link_el    else ""
            full_url = (
                f"https://www.indeed.com{href}" if href.startswith("/") else href
            )

            jk     = card.get("data-jk", "")
            job_id = jk or str(abs(hash(title + company)))

            if not title:
                continue

            # Keyword filter
            card_text = card.get_text(" ", strip=True).lower()
            if not any(kw in title.lower() for kw in KEYWORDS):
                if not any(kw in card_text for kw in KEYWORDS):
                    continue

            # Indeed uses relative date strings; parse them into timestamps
            posted_at = datetime.now(timezone.utc).isoformat()
            if date_txt:
                txt = date_txt.lower()
                now = datetime.now(timezone.utc)
                if "just" in txt or "today" in txt:
                    posted_at = now.isoformat()
                elif "hour" in txt:
                    try:
                        hours     = int("".join(filter(str.isdigit, txt)) or "1")
                        posted_at = (now - timedelta(hours=hours)).isoformat()
                    except Exception:
                        pass
                elif "day" in txt:
                    try:
                        days = int("".join(filter(str.isdigit, txt)) or "1")
                        if days > 1:
                            continue   # older than 1 day — skip
                        posted_at = (now - timedelta(days=days)).isoformat()
                    except Exception:
                        pass

            try:
                pub = date_parser.parse(posted_at)
                if pub.tzinfo is None:
                    pub = pub.replace(tzinfo=timezone.utc)
                if pub < cutoff:
                    continue
            except Exception:
                pass

            results.append({
                "id":          f"indeed_{job_id}",
                "title":       title,
                "company":     company,
                "location":    "Remote",
                "url":         full_url,
                "salary_text": "",
                "description": "",
                "posted_at":   posted_at,
                "source":      "Indeed",
                "tags":        [],
            })
        except Exception:
            continue

    return results


def get_jobs() -> list:
    page    = get_page()
    results = []
    cutoff  = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)

    try:
        page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=35000)

        # Non-fatal wait — proceed with whatever the page loaded
        try:
            page.wait_for_selector(
                "#mosaic-jobResults, .jobsearch-ResultsList, .job_seen_beacon, [data-jk]",
                timeout=12000,
            )
        except Exception:
            pass

        results = _parse_html(page.content(), cutoff)

    except Exception as e:
        print(f"[Indeed] Error: {e}")
    finally:
        try:
            page.context.close()
        except Exception:
            pass

    print(f"[Indeed] {len(results)} matching jobs found")
    return results
