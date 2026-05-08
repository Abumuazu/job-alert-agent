"""
main.py — Job scraper entry point.
Runs every 15 minutes via GitHub Actions.

Sources:
  API-based  (fast, no browser): RemoteOK, Remotive
  Browser-based (Playwright):    LinkedIn, WeWorkRemotely, Wellfound, Indeed
"""

from scrapers.remoteok       import get_jobs as remoteok_jobs
from scrapers.remotive       import get_jobs as remotive_jobs
from scrapers.linkedin       import get_jobs as linkedin_jobs
from scrapers.weworkremotely import get_jobs as wwr_jobs
from scrapers.wellfound      import get_jobs as wellfound_jobs
from scrapers.indeed         import get_jobs as indeed_jobs
from scrapers.browser        import shutdown as browser_shutdown
from scorer       import score_job
from dedup        import load_seen, save_seen, filter_new, mark_seen
from email_sender import send_job_alert
from config       import SCORE_THRESHOLD


def run():
    print("=" * 55)
    print("Job Alert Agent — starting scrape run")
    print("=" * 55)

    all_jobs = []

    # ── Fast API scrapers ───────────────────────────────────
    print("\n[1/6] RemoteOK...")
    all_jobs.extend(remoteok_jobs())

    print("[2/6] Remotive...")
    all_jobs.extend(remotive_jobs())

    # ── Browser scrapers (shared Playwright instance) ────────
    print("[3/6] LinkedIn...")
    all_jobs.extend(linkedin_jobs())

    print("[4/6] WeWorkRemotely...")
    all_jobs.extend(wwr_jobs())

    print("[5/6] Wellfound...")
    all_jobs.extend(wellfound_jobs())

    print("[6/6] Indeed...")
    all_jobs.extend(indeed_jobs())

    # ── Shutdown browser ─────────────────────────────────────
    browser_shutdown()

    print(f"\nTotal raw jobs collected: {len(all_jobs)}")

    # ── Score ─────────────────────────────────────────────────
    for job in all_jobs:
        job["score"] = score_job(job)

    qualified = [j for j in all_jobs if j["score"] >= SCORE_THRESHOLD]
    print(f"Jobs above score threshold ({SCORE_THRESHOLD}): {len(qualified)}")

    # ── Dedup ─────────────────────────────────────────────────
    seen_ids = load_seen()
    new_jobs = filter_new(qualified, seen_ids)
    print(f"New (unseen) jobs: {len(new_jobs)}")

    # ── Alert ─────────────────────────────────────────────────
    if new_jobs:
        new_jobs.sort(key=lambda j: j["score"], reverse=True)
        send_job_alert(new_jobs)
        seen_ids = mark_seen(new_jobs, seen_ids)
        save_seen(seen_ids)
    else:
        print("No new jobs this run — no email sent.")

    print("=" * 55)
    print("Run complete.")


if __name__ == "__main__":
    run()
