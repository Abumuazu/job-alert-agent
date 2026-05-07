"""
main.py — Job scraper entry point.
Runs every 15 minutes via GitHub Actions.
Checks all sources → scores → deduplicates → sends email if new jobs found.
"""

from scrapers.remoteok       import get_jobs as remoteok_jobs
from scrapers.remotive       import get_jobs as remotive_jobs
from scrapers.weworkremotely import get_jobs as wwr_jobs
from scrapers.linkedin       import get_jobs as linkedin_jobs
from scorer  import score_job
from dedup   import load_seen, save_seen, filter_new, mark_seen
from email_sender import send_job_alert
from config  import SCORE_THRESHOLD


def run():
    print("=" * 50)
    print("Job Alert Agent — starting scrape run")
    print("=" * 50)

    # 1. Collect from all sources
    all_jobs = []
    all_jobs.extend(remoteok_jobs())
    all_jobs.extend(remotive_jobs())
    all_jobs.extend(wwr_jobs())
    all_jobs.extend(linkedin_jobs())
    print(f"\nTotal raw jobs collected: {len(all_jobs)}")

    # 2. Score each job
    for job in all_jobs:
        job["score"] = score_job(job)

    # 3. Filter by minimum score
    qualified = [j for j in all_jobs if j["score"] >= SCORE_THRESHOLD]
    print(f"Jobs above score threshold ({SCORE_THRESHOLD}): {len(qualified)}")

    # 4. Deduplicate against previously seen jobs
    seen_ids = load_seen()
    new_jobs = filter_new(qualified, seen_ids)
    print(f"New (unseen) jobs: {len(new_jobs)}")

    # 5. Alert + persist
    if new_jobs:
        new_jobs.sort(key=lambda j: j["score"], reverse=True)
        send_job_alert(new_jobs)
        seen_ids = mark_seen(new_jobs, seen_ids)
        save_seen(seen_ids)
    else:
        print("No new jobs this run — no email sent.")

    print("=" * 50)
    print("Run complete.")


if __name__ == "__main__":
    run()
