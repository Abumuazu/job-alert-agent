"""
daily_digest.py — Daily outreach digest entry point.
Runs once at 7am UTC via GitHub Actions.
Sends cold email targets + recruiter DM list to abumuazu09@gmail.com.
"""

from cold_targets import get_cold_targets, get_recruiters
from email_sender import send_daily_digest


def run():
    print("=" * 50)
    print("Job Alert Agent — sending daily digest")
    print("=" * 50)

    cold_targets = get_cold_targets()
    recruiters   = get_recruiters()

    print(f"Cold targets selected: {len(cold_targets)}")
    for t in cold_targets:
        print(f"  · {t['name']}")

    print(f"Recruiters: {len(recruiters)}")
    for r in recruiters:
        print(f"  · {r['name']}")

    send_daily_digest(cold_targets, recruiters)
    print("=" * 50)
    print("Daily digest complete.")


if __name__ == "__main__":
    run()
