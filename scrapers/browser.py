"""
Shared Playwright browser — launched once per run, reused across all scrapers.
Each scraper calls get_page() to get a fresh stealth page on the shared browser.
Call shutdown() in main.py after all scraping is done.
"""

from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

_pw      = None
_browser = None

_LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--window-size=1920,1080",
]

_CONTEXT_OPTIONS = {
    "viewport":    {"width": 1920, "height": 1080},
    "locale":      "en-US",
    "timezone_id": "America/New_York",
    "user_agent":  (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}


def get_page():
    """Return a new stealth page on the shared browser instance."""
    global _pw, _browser
    if _pw is None:
        _pw      = sync_playwright().start()
        _browser = _pw.chromium.launch(headless=True, args=_LAUNCH_ARGS)

    context = _browser.new_context(**_CONTEXT_OPTIONS)
    page    = context.new_page()
    stealth_sync(page)

    # Block images, fonts, and media — speeds up page loads significantly
    page.route(
        "**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,mp4,mp3}",
        lambda route: route.abort(),
    )
    return page


def shutdown():
    global _pw, _browser
    try:
        if _browser:
            _browser.close()
        if _pw:
            _pw.stop()
    except Exception:
        pass
    _pw      = None
    _browser = None
