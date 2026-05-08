"""
We Work Remotely scraper — Playwright + stealth.
WWR blocks datacenter IPs on their RSS feed. Browser rendering bypasses this.
"""

from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from scrapers.browser import get_page
from config import KEYWORDS, LOOKBACK_MINUTES

SEARCH_URL = "https://weworkremotely.com/remote-jobs/search?term=react+native"


def get_jobs() -> list:
    page    = get_page()
    results = []
    cutoff  = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)

    try:
        page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("section.jobs, ul.jobs-container, article", timeout=12000)

        job_items = page.query_selector_all("li[class*='feature'], section.jobs li")

        for item in job_items:
            try:
                title_el   = item.query_selector(".title, h4, h3")
                company_el = item.query_selector(".company, .region, span[class*='company']")
                link_el    = item.query_selector("a[href]")
                time_el    = item.query_selector("time")

                title    = title_el.inner_text().strip()   if title_el   else ""
                company  = company_el.inner_text().strip() if company_el else ""
                href     = link_el.get_attribute("href")   if link_el    else ""
                full_url = f"https://weworkremotely.com{href}" if href and href.startswith("/") else href

                if not title:
                    continue

                text = title.lower()
                if not any(kw in text for kw in KEYWORDS):
                    # Also check full card text
                    card_text = item.inner_text().lower()
                    if not any(kw in card_text for kw in KEYWORDS):
                        continue

                posted_at = datetime.now(timezone.utc).isoformat()
                if time_el:
                    dt = time_el.get_attribute("datetime")
                    if dt:
                        posted_at = dt

                try:
                    pub = date_parser.parse(posted_at)
                    if pub.tzinfo is None:
                        pub = pub.replace(tzinfo=timezone.utc)
                    if pub < cutoff:
                        continue
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

    except Exception as e:
        print(f"[WeWorkRemotely] Error: {e}")
    finally:
        try:
            page.context.close()
        except Exception:
            pass

    print(f"[WeWorkRemotely] {len(results)} matching jobs found")
    return results
