"""
We Work Remotely scraper — Playwright + stealth + BeautifulSoup.

Design choices:
- Parses page.content() with BS4 instead of relying on specific Playwright
  selectors that break when WWR reshuffles their CSS classes.
- Falls back to the Programming category page if the search page returns zero.
- wait_for_selector is non-fatal; we always proceed with whatever loaded.
"""

from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from bs4 import BeautifulSoup
from scrapers.browser import get_page
from config import KEYWORDS, LOOKBACK_MINUTES

SEARCH_URL   = "https://weworkremotely.com/remote-jobs/search?term=react+native"
CATEGORY_URL = "https://weworkremotely.com/categories/remote-programming-jobs"


def _parse_html(html: str, cutoff: datetime) -> list:
    soup = BeautifulSoup(html, "lxml")
    results = []

    # WWR HTML: <section class="jobs"><ul><li class="feature">...</li></ul></section>
    # Try both the feature-list items and any generic article/li approach
    items = (
        soup.select("section.jobs li")
        or soup.select("li.feature")
        or soup.select("article")
        or soup.select("li[class*='job']")
    )

    for item in items:
        try:
            # Skip view-all / section headers
            if item.select_one("header") or item.get("class", [""])[0] == "view-all":
                continue

            title_el   = item.select_one(".title, h4, h3, [class*='title']")
            company_el = item.select_one(".company, .region, [class*='company']")
            link_el    = item.select_one("a[href]")
            time_el    = item.select_one("time")

            title   = title_el.get_text(strip=True)   if title_el   else ""
            company = company_el.get_text(strip=True) if company_el else ""
            href    = link_el.get("href", "")         if link_el    else ""

            if not title:
                continue

            card_text = item.get_text(" ", strip=True).lower()
            if not any(kw in card_text for kw in KEYWORDS):
                continue

            full_url = (
                f"https://weworkremotely.com{href}" if href.startswith("/") else href
            )

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

            results.append({
                "id":          f"wwr_{abs(hash(full_url or title + company))}",
                "title":       title,
                "company":     company,
                "location":    "Remote – Worldwide",
                "url":         full_url,
                "salary_text": "",
                "description": "",
                "posted_at":   posted_at,
                "source":      "We Work Remotely",
                "tags":        [],
            })
        except Exception:
            continue

    return results


def _fetch(url: str, cutoff: datetime) -> list:
    page = get_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass   # proceed with whatever loaded

        return _parse_html(page.content(), cutoff)

    except Exception as e:
        print(f"[WeWorkRemotely] Error fetching {url}: {e}")
        return []
    finally:
        try:
            page.context.close()
        except Exception:
            pass


def get_jobs() -> list:
    cutoff  = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)
    results = _fetch(SEARCH_URL, cutoff)

    # If the search page returned nothing try the category page
    if not results:
        results = _fetch(CATEGORY_URL, cutoff)

    print(f"[WeWorkRemotely] {len(results)} matching jobs found")
    return results
