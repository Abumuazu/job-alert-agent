"""
Deduplication — tracks job IDs we've already alerted on so we never
send the same job twice. IDs are stored in seen_jobs.json which is
committed back to the repo after every run.
"""

import json
import os

SEEN_FILE = "seen_jobs.json"
MAX_SEEN  = 5000   # cap to keep the file small; oldest entries pruned first


def load_seen() -> set:
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE) as f:
        data = json.load(f)
    return set(data)


def save_seen(seen_ids: set) -> None:
    ids_list = list(seen_ids)
    if len(ids_list) > MAX_SEEN:
        ids_list = ids_list[-MAX_SEEN:]   # keep most recent
    with open(SEEN_FILE, "w") as f:
        json.dump(ids_list, f)


def filter_new(jobs: list, seen_ids: set) -> list:
    return [j for j in jobs if j["id"] not in seen_ids]


def mark_seen(jobs: list, seen_ids: set) -> set:
    for job in jobs:
        seen_ids.add(job["id"])
    return seen_ids
