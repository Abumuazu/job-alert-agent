"""
Wellfound (formerly AngelList Talent) scraper — Playwright + stealth.
Wellfound is the best source for startup React Native jobs — founders post here
directly, often before jobs appear anywhere else.
"""

from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from scrapers.browser import get_page
from config import KEYWORDS, LOOKBACK_MINUTES

SEARCH_URL = "https://wellfound.com/jobs?q[keywords]=react+native&q[remote]=true"


def get_jobs() -> list:
    page    = get_page()
    results = []
    cutoff  = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)

    try:
        page.goto(SEARCH_URL, wait_until="networkidle", timeout=40000)

        # Wellfound is heavily JS-rendered — wait for job cards to appear
        page.wait_for_selector(
            "[data-test='StartupResult'], .styles_component__Gxwh, [class*='JobListing'], div[class*='job']",
            timeout=20000,
        )

        # Scroll down to trigger lazy loading
        for _ in range(3):
            page.keyboard.press("End")
            page.wait_for_timeout(1500)

        # Try multiple selector strategies
        job_cards = (
            page.query_selector_all("[data-test='StartupResult']")
            or page.query_selector_all("div[class*='JobListing']")
            or page.query_selector_all("div[class*='styles_component']")
        )

        for card in job_cards:
            try:
                card_text = card.inner_text()
                text_lower = card_text.lower()

                if not any(kw in text_lower for kw in KEYWORDS):
                    continue

                # Extract fields from text since class names are obfuscated
                lines = [l.strip() for l in card_text.splitlines() if l.strip()]

                title   = lines[0] if lines else ""
                company = lines[1] if len(lines) > 1 else ""

                link_el  = card.query_selector("a[href*='/jobs/'], a[href*='/l/']")
                href     = link_el.get_attribute("href") if link_el else ""
                full_url = f"https://wellfound.com{href}" if href and href.startswith("/") else href

                # Wellfound doesn't show exact post time in cards — use now as approximation
                posted_at = datetime.now(timezone.utc).isoformat()
                time_el   = card.query_selector("time")
                if time_el:
                    dt = time_el.get_attribute("datetime") or time_el.inner_text()
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
                    "id":          f"wellfound_{abs(hash(full_url or title + company))}",
                    "title":       title,
                    "company":     company,
                    "location":    "Remote",
                    "url":         full_url or SEARCH_URL,
                    "salary_text": "",
                    "description": card_text[:400],
                    "posted_at":   posted_at,
                    "source":      "Wellfound",
                    "tags":        ["startup", "react-native"],
                })
            except Exception:
                continue

    except Exception as e:
        print(f"[Wellfound] Error: {e}")
    finally:
        try:
            page.context.close()
        except Exception:
            pass

    print(f"[Wellfound] {len(results)} matching jobs found")
    return results
