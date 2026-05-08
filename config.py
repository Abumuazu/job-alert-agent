import os

# ── Alert destination ─────────────────────────────────────────────────────────
ALERT_EMAIL = "abumuazu09@gmail.com"

# ── Gmail sender (set as GitHub Secrets) ─────────────────────────────────────
SENDER_EMAIL = os.environ.get("GMAIL_SENDER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

# ── Job search keywords ───────────────────────────────────────────────────────
KEYWORDS = [
    "react native",
    "react-native",
    "react native developer",
    "react native engineer",
    "senior mobile engineer",
    "mobile engineer react",
    "rn developer",
    "rn engineer",
]

# ── Filters ───────────────────────────────────────────────────────────────────
SALARY_MIN = 45000          # USD annual — jobs below this get a lower score
SCORE_THRESHOLD = 40        # Minimum match score (0-100) to include in alert
LOOKBACK_MINUTES = 20       # How far back each run looks (slightly > cron interval)

# ── Phrases that disqualify a job (case-insensitive) ─────────────────────────
EXCLUSION_PHRASES = [
    "us only",
    "us citizens only",
    "must be located in the us",
    "must be in the us",
    "security clearance",
    "us work authorization",
    "requires us citizenship",
    "onsite only",
    "on-site only",
    "not available in africa",
    "no visa sponsorship",       # only exclude if paired with location lock
]
