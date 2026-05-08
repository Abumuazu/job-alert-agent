"""
Indeed scraper — Playwright + stealth.
Indeed blocks datacenter IPs on their RSS feed and HTTP requests.
Browser rendering with stealth fingerprinting bypasses this reliably.
"""

from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from scrapers.browser import get_page
from config import KEYWORDS, LOOKBACK_MINUTES

# Indeed remote filter attr + sort by date + posted in last day
SEARCH_URL = (
    "https://www.indeed.com/jobs"
    "?q=react+native+developer"
    "&sc=0kf%3Aattr%28DSQF7%29%3B"   # remote attribute
    "&sort=date"
    "&fromage=1"
)


def get_jobs() -> list:
    page    = get_page()
    results = []
    cutoff  = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)

    try:
        page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=35000)
        page.wait_for_selector("#mosaic-jobResults, .jobsearch-ResultsList, .job_seen_beacon", timeout=15000)

        job_cards = (
            page.query_selector_all(".job_seen_beacon")
            or page.query_selector_all("[data-jk]")
            or page.query_selector_all(".resultContent")
        )

        for card in job_cards:
            try:
                title_el   = card.query_selector("h2 a span, h2 span[title], .jobTitle span")
                company_el = card.query_selector("[data-testid='company-name'], .companyName")
                date_el    = card.query_selector("[data-testid='myJobsStateDate'], .date, span[class*='date']")
                link_el    = card.query_selector("h2 a, a[id^='job_']")

                title    = title_el.get_attribute("title") or title_el.inner_text().strip() if title_el else ""
                company  = company_el.inner_text().strip() if company_el else ""
                date_txt = date_el.inner_text().strip()    if date_el    else ""

                href     = link_el.get_attribute("href")  if link_el    else ""
                full_url = f"https://www.indeed.com{href}" if href and href.startswith("/") else href

                jk_attr  = card.get_attribute("data-jk") or ""
                job_id   = jk_attr or abs(hash(title + company))

                if not title or not any(kw in title.lower() for kw in KEYWORDS):
                    card_text = card.inner_text().lower()
                    if not any(kw in card_text for kw in KEYWORDS):
                        continue

                # Indeed shows relative dates like "just posted", "1 day ago"
                posted_at = datetime.now(timezone.utc).isoformat()
                if date_txt:
                    txt = date_txt.lower()
                    now = datetime.now(timezone.utc)
                    if "just" in txt or "today" in txt:
                        posted_at = now.isoformat()
                    elif "hour" in txt:
                        try:
                            hours = int(''.join(filter(str.isdigit, txt)) or "1")
                            posted_at = (now - timedelta(hours=hours)).isoformat()
                        except Exception:
                            pass
                    elif "day" in txt:
                        try:
                            days = int(''.join(filter(str.isdigit, txt)) or "1")
                            if days > 1:
                                continue   # too old
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

    except Exception as e:
        print(f"[Indeed] Error: {e}")
    finally:
        try:
            page.context.close()
        except Exception:
            pass

    print(f"[Indeed] {len(results)} matching jobs found")
    return results
