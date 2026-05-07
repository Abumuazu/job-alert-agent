"""
Cold targets generator.

Returns:
  - 5 companies to cold-email your portfolio to today
  - 3 recruiters to DM on LinkedIn today

The company list rotates daily (shuffled) from a curated seed list of companies
known to hire React Native engineers remotely, supplemented by any currently
active companies pulled live from Remotive.

The recruiter list is curated and updated manually — these are real people /
platforms that actively place remote React Native engineers globally.
"""

import random
import requests

# ─────────────────────────────────────────────────────────────────────────────
# Curated company seed list
# Add/remove entries here as you learn more about the market.
# ─────────────────────────────────────────────────────────────────────────────
SEED_COMPANIES = [
    {
        "name":   "Expo",
        "reason": "They build the core React Native tooling — literally the perfect fit. Small team, fully remote, async culture.",
        "url":    "https://expo.dev/careers",
    },
    {
        "name":   "Infinite Red",
        "reason": "Leading React Native consultancy. Regularly hires senior RN engineers. Fully distributed, international candidates welcome.",
        "url":    "https://infinite.red/careers",
    },
    {
        "name":   "Software Mansion",
        "reason": "Core RN open-source contributors (Reanimated, Screens). Growing team. Remote-friendly, has hired internationally.",
        "url":    "https://swmansion.com/careers",
    },
    {
        "name":   "Callstack",
        "reason": "Maintainers of React Native Paper and RNEF. Always looking for senior RN talent. Remote-first.",
        "url":    "https://callstack.com/careers",
    },
    {
        "name":   "Shopify",
        "reason": "Heavy React Native user, remote-first since 2020. They hire globally. Check jobs page for mobile roles.",
        "url":    "https://www.shopify.com/careers",
    },
    {
        "name":   "Brex",
        "reason": "Series D fintech that uses React Native for mobile. Has hired international engineers before.",
        "url":    "https://brex.com/careers",
    },
    {
        "name":   "Clerk",
        "reason": "YC W22 auth startup. Small team, React ecosystem, remote-first. Send your portfolio directly.",
        "url":    "https://clerk.com/careers",
    },
    {
        "name":   "Novu",
        "reason": "YC S22 open-source notifications platform. Small remote team. Has a React Native SDK — you'd be a great fit.",
        "url":    "https://novu.co/careers",
    },
    {
        "name":   "Draftbit",
        "reason": "No-code React Native app builder. Small YC team. Deeply embedded in RN ecosystem.",
        "url":    "https://draftbit.com/jobs",
    },
    {
        "name":   "Notifee / Invertase",
        "reason": "Builds Firebase & push notification SDKs for React Native. Small remote UK team, hires globally.",
        "url":    "https://invertase.io/careers",
    },
    {
        "name":   "Buildkite",
        "reason": "CI/CD platform. Remote-first, async culture, international team. Uses React Native for mobile.",
        "url":    "https://buildkite.com/careers",
    },
    {
        "name":   "Juno",
        "reason": "Fintech with a strong mobile product. Remote-first, has hired across Africa and LatAm.",
        "url":    "https://juno.com/careers",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Curated recruiter list
# These are real people / platforms known to place remote RN engineers globally.
# ─────────────────────────────────────────────────────────────────────────────
RECRUITERS = [
    {
        "name":     "Arc.dev Talent Team",
        "title":    "Remote Tech Talent Platform",
        "note":     "Apply to Arc.dev's talent pool — they vet engineers and actively pitch you to remote startups. "
                    "React Native engineers are in demand on their platform. International candidates accepted.",
        "linkedin": "https://arc.dev/talent/join",
    },
    {
        "name":     "Hired.com",
        "title":    "Remote Tech Job Marketplace",
        "note":     "On Hired, companies come to YOU. Set your target role and salary, companies send interview requests. "
                    "Strong for senior mobile engineers. Remote-only filter available.",
        "linkedin": "https://hired.com/signup/candidates",
    },
    {
        "name":     "Toptal Mobile Practice",
        "title":    "Elite Freelance / Full-time Network",
        "note":     "Toptal's mobile practice places React Native engineers at top startups and enterprises. "
                    "Vetting is rigorous but once in, you get high-paying remote offers consistently.",
        "linkedin": "https://www.toptal.com/react-native",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Dynamic company fetch (supplements the seed list with live data)
# ─────────────────────────────────────────────────────────────────────────────

def _get_dynamic_companies() -> list:
    """Pull active React Native hiring companies from Remotive and surface
    ones not already in the seed list."""
    try:
        resp = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"search": "react native", "limit": 30},
            timeout=10,
        )
        jobs = resp.json().get("jobs", [])
        seed_names = {c["name"].lower() for c in SEED_COMPANIES}
        seen, companies = set(), []
        for job in jobs:
            name = job.get("company_name", "").strip()
            if name and name.lower() not in seed_names and name not in seen:
                seen.add(name)
                companies.append({
                    "name":   name,
                    "reason": "Currently posting React Native roles on Remotive — reach out directly with your portfolio before the role fills.",
                    "url":    "",
                })
        return companies[:3]
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def get_cold_targets() -> list:
    """Returns 5 companies shuffled daily so recommendations rotate."""
    dynamic  = _get_dynamic_companies()
    combined = dynamic + SEED_COMPANIES

    # Deduplicate
    seen, unique = set(), []
    for c in combined:
        key = c["name"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)

    random.shuffle(unique)
    return unique[:5]


def get_recruiters() -> list:
    return RECRUITERS
