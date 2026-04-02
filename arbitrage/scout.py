"""
ADRION 369 - Scout Agent
Discovers freelance jobs from Fiverr/Upwork.
Modes: apify (real) | mock (no API key needed)
"""
import hashlib
import random
from datetime import datetime

from .config import APIFY_TOKEN, SCOUT_KEYWORDS, SCOUT_MAX_BUDGET, SCOUT_MIN_BUDGET
from .database import upsert_job

try:
    from apify_client import ApifyClient
    APIFY_AVAILABLE = True
except ImportError:
    APIFY_AVAILABLE = False


# ── Mock data for demo/testing ─────────────────────────────────────────────

MOCK_JOBS = [
    {"title": "Write 5 SEO blog posts for SaaS company", "budget_min": 150, "budget_max": 250, "platform": "upwork", "client": "TechStartupCo"},
    {"title": "Product descriptions for 20 e-commerce items", "budget_min": 80, "budget_max": 120, "platform": "fiverr", "client": "ShopOwner99"},
    {"title": "Monthly content writing retainer - 8 articles", "budget_min": 300, "budget_max": 400, "platform": "upwork", "client": "MarketingAgency"},
    {"title": "Ghostwrite 3000-word thought leadership article", "budget_min": 200, "budget_max": 350, "platform": "upwork", "client": "CEO_Branding"},
    {"title": "Website copywriting - Home + About + Services pages", "budget_min": 180, "budget_max": 300, "platform": "fiverr", "client": "SmallBizOwner"},
    {"title": "Email newsletter sequence (5 emails)", "budget_min": 100, "budget_max": 180, "platform": "upwork", "client": "Ecommerce_Store"},
    {"title": "Technical blog posts about AI and machine learning", "budget_min": 250, "budget_max": 450, "platform": "upwork", "client": "AICompany"},
    {"title": "Social media captions for fitness brand (30 posts)", "budget_min": 60, "budget_max": 100, "platform": "fiverr", "client": "FitnessBrand"},
    {"title": "Case study writing for B2B software company", "budget_min": 120, "budget_max": 200, "platform": "upwork", "client": "B2BSoftware"},
    {"title": "Copywriting for landing page and Google Ads", "budget_min": 150, "budget_max": 280, "platform": "upwork", "client": "DigitalMarketer"},
]


def _make_job_id(platform: str, title: str) -> str:
    raw = f"{platform}:{title}:{datetime.now().date()}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _mock_scout(count: int = 5) -> list[dict]:
    selected = random.sample(MOCK_JOBS, min(count, len(MOCK_JOBS)))
    jobs = []
    for item in selected:
        job_id = _make_job_id(item["platform"], item["title"])
        jobs.append({
            "id": job_id,
            "platform": item["platform"],
            "title": item["title"],
            "description": f"[Mock] {item['title']}. Looking for an experienced content writer.",
            "budget_min": item["budget_min"],
            "budget_max": item["budget_max"],
            "client": item["client"],
            "url": f"https://{item['platform']}.com/job/{job_id}",
            "keywords": random.sample(SCOUT_KEYWORDS, 3),
        })
    return jobs


def _apify_scout(platform: str, keyword: str, limit: int = 10) -> list[dict]:
    """Scrape jobs via Apify. Requires APIFY_TOKEN."""
    if not APIFY_AVAILABLE or not APIFY_TOKEN:
        return []

    client = ApifyClient(APIFY_TOKEN)

    if platform == "upwork":
        actor_id = "curious_coder/upwork-scraper"
        run_input = {
            "searchQueries": [keyword],
            "maxItems": limit,
            "proxyConfiguration": {"useApifyProxy": True},
        }
    else:
        actor_id = "apify/web-scraper"
        run_input = {
            "startUrls": [{"url": f"https://www.fiverr.com/search/gigs?query={keyword.replace(' ', '+')}&source=top-bar&search_in=everywhere&search-autocomplete-original-term={keyword}"}],
            "maxCrawlingDepth": 1,
            "maxPagesPerCrawl": 3,
        }

    try:
        run = client.actor(actor_id).call(run_input=run_input, timeout_secs=120)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        jobs = []
        for item in items[:limit]:
            title = item.get("title", item.get("name", "Unknown"))
            budget_str = str(item.get("budget", item.get("price", "0")))
            budget = float("".join(c for c in budget_str if c.isdigit() or c == ".") or 0)
            if budget < SCOUT_MIN_BUDGET or budget > SCOUT_MAX_BUDGET:
                continue
            job_id = _make_job_id(platform, title)
            jobs.append({
                "id": job_id,
                "platform": platform,
                "title": title,
                "description": item.get("description", item.get("details", "")),
                "budget_min": budget * 0.8,
                "budget_max": budget,
                "client": item.get("client", item.get("seller", "Unknown")),
                "url": item.get("url", item.get("link", "")),
                "keywords": [keyword],
            })
        return jobs
    except Exception as e:
        print(f"[Scout] Apify error ({platform}/{keyword}): {e}")
        return []


def run_scout(platforms: list[str] = None, keywords: list[str] = None, use_mock: bool = None) -> dict:
    """
    Main Scout entry point.
    Returns: {"new_jobs": int, "jobs": list[dict], "mode": str}
    """
    platforms = platforms or ["upwork", "fiverr"]
    keywords  = keywords  or SCOUT_KEYWORDS[:3]
    use_mock  = use_mock if use_mock is not None else (not APIFY_TOKEN)

    all_jobs = []

    if use_mock:
        all_jobs = _mock_scout(count=8)
        mode = "mock"
    else:
        mode = "apify"
        for platform in platforms:
            for kw in keywords[:2]:  # limit API calls
                jobs = _apify_scout(platform, kw, limit=5)
                all_jobs.extend(jobs)

    # Filter by budget
    all_jobs = [j for j in all_jobs if SCOUT_MIN_BUDGET <= j.get("budget_max", 0) <= SCOUT_MAX_BUDGET]

    # Deduplicate by id
    seen = set()
    unique_jobs = []
    for j in all_jobs:
        if j["id"] not in seen:
            seen.add(j["id"])
            unique_jobs.append(j)

    # Save to DB
    new_count = sum(1 for j in unique_jobs if upsert_job(j))

    return {"new_jobs": new_count, "jobs": unique_jobs, "mode": mode}
