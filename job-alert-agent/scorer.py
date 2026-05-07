"""
Job scorer — returns a 0-100 match score based on how well a job
fits a React Native engineer seeking fully remote, well-paid work.
"""

from config import EXCLUSION_PHRASES, SALARY_MIN


def score_job(job: dict) -> int:
    score = 50  # neutral baseline

    title        = job.get("title", "").lower()
    description  = job.get("description", "").lower()
    location     = job.get("location", "").lower()
    salary_text  = job.get("salary_text", "").lower()
    tags         = [t.lower() for t in job.get("tags", [])]
    full_text    = f"{title} {description} {' '.join(tags)}"

    # ── Title match quality ──────────────────────────────────────────────────
    if "react native" in title:
        score += 25
    elif "react-native" in title:
        score += 25
    elif "mobile" in title and "react" in full_text:
        score += 15
    elif "mobile engineer" in title or "mobile developer" in title:
        score += 10

    # ── Seniority / leadership ───────────────────────────────────────────────
    if any(w in title for w in ("senior", "lead", "principal", "staff")):
        score += 5

    # ── Remote genuineness ───────────────────────────────────────────────────
    if any(w in location for w in ("worldwide", "anywhere", "global", "remote")):
        score += 8
    if any(w in description for w in ("work from anywhere", "fully remote", "remote-first", "distributed team")):
        score += 6

    # ── Async / flexible culture signals ────────────────────────────────────
    async_signals = ["async", "asynchronous", "flexible hours", "no timezone", "overlap"]
    if any(s in description for s in async_signals):
        score += 5

    # ── Startup / high-growth signals ────────────────────────────────────────
    startup_signals = ["seed", "series a", "series b", "yc", "y combinator", "early stage", "startup"]
    if any(s in full_text for s in startup_signals):
        score += 8

    # ── React Native ecosystem stack match ───────────────────────────────────
    stack = ["expo", "typescript", "redux", "react query", "react navigation",
             "jest", "detox", "reanimated", "zustand", "nativewind"]
    stack_hits = sum(1 for kw in stack if kw in full_text)
    score += min(stack_hits * 3, 12)

    # ── Salary transparency (having it listed = good sign) ───────────────────
    if salary_text:
        score += 5
        # Try to parse and check against minimum
        import re
        nums = re.findall(r"\d[\d,]+", salary_text.replace(",", ""))
        if nums:
            try:
                max_val = max(int(n.replace(",", "")) for n in nums)
                if max_val < 1000:
                    max_val *= 1000   # likely in thousands (e.g. "$80k")
                if max_val >= SALARY_MIN:
                    score += 5
                else:
                    score -= 10
            except Exception:
                pass

    # ── Equity offered ───────────────────────────────────────────────────────
    if any(w in full_text for w in ("equity", "stock options", "esop", "shares")):
        score += 4

    # ── Hard exclusions ──────────────────────────────────────────────────────
    for phrase in EXCLUSION_PHRASES:
        if phrase in full_text or phrase in location:
            score -= 45
            break  # one exclusion is enough

    return max(0, min(100, score))
