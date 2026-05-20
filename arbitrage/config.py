"""ADRION 369 Configuration -- Pydantic Settings.

Migrated from raw os.getenv() to pydantic-settings BaseSettings.
All previous module-level names are re-exported at the bottom for
backward compatibility so that ``from arbitrage.config import LLM_BACKEND``
continues to work unchanged.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ─── Base directory (non-env, computed) ──────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent


class AdrionSettings(BaseSettings):
    """Typed, validated configuration sourced from environment / ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ═══ Database ═══
    db_path: str = Field(str(BASE_DIR / "arbitrage.db"), alias="DB_PATH")
    db_engine: str = Field("sqlite", alias="DB_ENGINE")
    database_url: str = Field("", alias="DATABASE_URL")

    # ═══ LLM Core ═══
    llm_backend: str = Field("auto", alias="LLM_BACKEND")
    openrouter_api_key: str = Field("", alias="OPENROUTER_API_KEY")
    openai_api_key: str = Field("", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field("", alias="ANTHROPIC_API_KEY")
    llm_model: str = Field("openai/gpt-3.5-turbo", alias="LLM_MODEL")

    # ═══ LM Studio (Local LLM Server) ═══
    lmstudio_url: str = Field("http://localhost:1234", alias="LMSTUDIO_URL")
    lmstudio_api_key: str = Field("", alias="LMSTUDIO_API_KEY")
    lmstudio_model: str = Field("neural-chat", alias="LMSTUDIO_MODEL")

    # ═══ Ollama (Local LLM Server) ═══
    ollama_url: str = Field("http://localhost:11434", alias="OLLAMA_URL")
    ollama_model: str = Field("deepseek:7b", alias="OLLAMA_MODEL")

    # ═══ Scraping ═══
    apify_token: str = Field("", alias="APIFY_API_TOKEN")

    # ═══ Bidding / Financial ═══
    daily_bid_limit: int = Field(20, alias="DAILY_BID_LIMIT")
    xrp_target: float = Field(1000, alias="XRP_TARGET")
    min_profit_usd: float = Field(30, alias="MIN_PROFIT_USD")
    min_analyzer_score: int = Field(7, alias="MIN_ANALYZER_SCORE")
    max_est_cost_per_bid_usd: float = Field(2.5, alias="MAX_EST_COST_PER_BID_USD")
    max_bids_per_client_per_day: int = Field(1, alias="MAX_BIDS_PER_CLIENT_PER_DAY")
    max_daily_est_cost_usd: float = Field(25, alias="MAX_DAILY_EST_COST_USD")

    # ═══ Event Caps ═══
    ugc_events_daily_cap: int = Field(4, alias="UGC_EVENTS_DAILY_CAP")
    resale_events_daily_cap: int = Field(4, alias="RESALE_EVENTS_DAILY_CAP")

    # ═══ G7 Privacy — External Service Allowlist ═══
    allowed_external_services: str = Field(
        "openrouter,openai,anthropic,apify,lmstudio,ollama",
        alias="ALLOWED_EXTERNAL_SERVICES",
    )

    # ═══ Source URLs / Tokens ═══
    ugc_source_url: str = Field("", alias="UGC_SOURCE_URL")
    resale_source_url: str = Field("", alias="RESALE_SOURCE_URL")
    streams_connector_token: str = Field("", alias="STREAMS_CONNECTOR_TOKEN")

    # ═══ LLM Prompts (overridable via env) ═══
    analyzer_system: str = Field(
        default=(
            "You are a freelance content writing expert evaluating job opportunities.\n"
            "Analyze the job and return ONLY a JSON object with:\n"
            "{\n"
            '  "score": <1-10>,\n'
            '  "fit": "<why this job fits a content writer>",\n'
            '  "risks": "<main risks or concerns>",\n'
            '  "est_hours": <estimated hours to complete>,\n'
            '  "our_price": <our recommended bid in USD>,\n'
            '  "est_cost": <estimated LLM/tools cost in USD, usually 0-5>,\n'
            '  "est_profit": <our_price minus est_cost>\n'
            "}\n"
            "Score criteria: 10=perfect fit, high budget, clear scope; "
            "1=off-topic, too complex, red flags.\n"
        ),
        alias="ANALYZER_SYSTEM",
    )
    analyzer_user: str = Field(
        default=(
            "Job Title: {title}\n"
            "Platform: {platform}\n"
            "Budget: ${budget_min} - ${budget_max}\n"
            "Description: {description}\n"
            "\n"
            "Evaluate this job opportunity."
        ),
        alias="ANALYZER_USER",
    )
    cover_letter_system: str = Field(
        default=(
            "You are a professional freelance content writer with 5+ years of experience.\n"
            "Write a concise, personalized cover letter for a freelance job proposal.\n"
            "Rules:\n"
            "- Max 200 words\n"
            "- Start with a specific hook about THEIR project (not generic opening)\n"
            "- Mention 1-2 relevant examples or skills\n"
            "- Include proposed timeline\n"
            "- End with a soft call to action\n"
            "- Tone: professional but approachable\n"
            "Return ONLY the cover letter text, no JSON, no headers.\n"
        ),
        alias="COVER_LETTER_SYSTEM",
    )
    cover_letter_user: str = Field(
        default=(
            "Write a cover letter for this job:\n"
            "Title: {title}\n"
            "Platform: {platform}\n"
            "Description: {description}\n"
            "Our bid price: ${our_price}\n"
            "Estimated delivery: {est_days} days"
        ),
        alias="COVER_LETTER_USER",
    )

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("ugc_source_url", "resale_source_url", "streams_connector_token", mode="before")
    @classmethod
    def _strip_whitespace(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v

    @field_validator("db_engine")
    @classmethod
    def _valid_db_engine(cls, v: str) -> str:
        if v not in ("sqlite", "postgres"):
            raise ValueError(f"DB_ENGINE must be 'sqlite' or 'postgres', got '{v}'")
        return v


# ─── Singleton ────────────────────────────────────────────────────────────────
settings = AdrionSettings()


# ─── Non-env constants ────────────────────────────────────────────────────────

SCOUT_KEYWORDS: List[str] = [
    "content writing",
    "blog post",
    "copywriting",
    "article writing",
    "ghostwriting",
    "SEO content",
]
SCOUT_MIN_BUDGET: int = 50
SCOUT_MAX_BUDGET: int = 500
SCOUT_PLATFORMS: List[str] = ["fiverr", "upwork"]

# Each channel: id, min_margin %, solfeggio frequency Hz, keywords
QUANTUM_SCAN_CHANNELS: List[dict] = [
    {"id": "AUDIO_PREMIUM", "min_margin": 15, "frequency": 432, "keywords": ["audio", "DAC", "headphones", "speakers", "hi-fi"]},
    {"id": "SMART_ENERGY", "min_margin": 18, "frequency": 528, "keywords": ["solar", "inverter", "battery", "EV charger", "smart home"]},
    {"id": "ROBOTICS_AI", "min_margin": 20, "frequency": 396, "keywords": ["robot", "drone", "3D printer", "CNC", "automation"]},
    {"id": "REFURBISHED_LUX", "min_margin": 15, "frequency": 174, "keywords": ["refurbished", "renewed", "outlet", "open-box", "B-stock"]},
    {"id": "BIOTECH_HEALTH", "min_margin": 25, "frequency": 528, "keywords": ["supplement", "biohacking", "health tech", "wearable", "lab"]},
]

# Security policy: wallet address is entered manually at transfer time and is
# not persisted in code/env.


# ─── Backward-compatible module-level exports ─────────────────────────────────
# Existing code does ``from arbitrage.config import DB_PATH`` etc.
# These aliases keep that working without any downstream changes.

DB_PATH: Path = Path(settings.db_path)
DB_ENGINE: str = settings.db_engine
DB_URL: str = settings.database_url

LLM_BACKEND: str = settings.llm_backend
OPENROUTER_KEY: str = settings.openrouter_api_key
OPENAI_KEY: str = settings.openai_api_key
ANTHROPIC_KEY: str = settings.anthropic_api_key
LLM_MODEL: str = settings.llm_model

LMSTUDIO_URL: str = settings.lmstudio_url
LMSTUDIO_API_KEY: str = settings.lmstudio_api_key
LMSTUDIO_MODEL: str = settings.lmstudio_model

OLLAMA_URL: str = settings.ollama_url
OLLAMA_MODEL: str = settings.ollama_model

APIFY_TOKEN: str = settings.apify_token

DAILY_BID_LIMIT: int = settings.daily_bid_limit
XRP_TARGET: float = settings.xrp_target
MIN_PROFIT_USD: float = settings.min_profit_usd
MIN_ANALYZER_SCORE: int = settings.min_analyzer_score
MAX_EST_COST_PER_BID_USD: float = settings.max_est_cost_per_bid_usd
MAX_BIDS_PER_CLIENT_PER_DAY: int = settings.max_bids_per_client_per_day
MAX_DAILY_EST_COST_USD: float = settings.max_daily_est_cost_usd

UGC_EVENTS_DAILY_CAP: int = settings.ugc_events_daily_cap
RESALE_EVENTS_DAILY_CAP: int = settings.resale_events_daily_cap
UGC_SOURCE_URL: str = settings.ugc_source_url
RESALE_SOURCE_URL: str = settings.resale_source_url
STREAMS_CONNECTOR_TOKEN: str = settings.streams_connector_token

ANALYZER_SYSTEM: str = settings.analyzer_system
ANALYZER_USER: str = settings.analyzer_user
COVER_LETTER_SYSTEM: str = settings.cover_letter_system
COVER_LETTER_USER: str = settings.cover_letter_user

ALLOWED_EXTERNAL_SERVICES: list[str] = [
    s.strip().lower()
    for s in settings.allowed_external_services.split(",")
    if s.strip()
]


# ─── Helper functions ─────────────────────────────────────────────────────────


def check_external_service_allowed(service: str) -> None:
    """G7 Autonomy gate: raise PermissionError if service not in ALLOWED_EXTERNAL_SERVICES.

    Call this before making any external API call (OpenRouter, OpenAI, Apify, Stripe…).
    Configure via env: ALLOWED_EXTERNAL_SERVICES=openrouter,openai,anthropic,apify
    """
    if service.lower() not in ALLOWED_EXTERNAL_SERVICES:
        raise PermissionError(
            f"G7 Autonomy violation: external service '{service}' is not in "
            f"ALLOWED_EXTERNAL_SERVICES ({','.join(ALLOWED_EXTERNAL_SERVICES)}). "
            "Add it to the env var to permit this service."
        )


def get_active_llm_backend() -> str:
    """Auto-detect which LLM backend to use based on available API keys."""
    if settings.llm_backend != "auto":
        return settings.llm_backend
    if settings.openrouter_api_key:
        return "openrouter"
    if settings.openai_api_key:
        return "openai"
    if settings.anthropic_api_key:
        return "anthropic"
    if settings.lmstudio_url and _check_lmstudio_available():
        return "lmstudio"
    if settings.ollama_url and _check_ollama_available():
        return "ollama"
    return "mock"


def _check_lmstudio_available() -> bool:
    """Check if LM Studio server is running."""
    try:
        import requests

        resp = requests.get(f"{settings.lmstudio_url}/v1/models", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def _check_ollama_available() -> bool:
    """Check if Ollama server is running."""
    try:
        import requests

        resp = requests.get(f"{settings.ollama_url}/api/tags", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def validate_db_url(url: str) -> bool:
    """Validate that a DATABASE_URL has the expected PostgreSQL DSN format.

    Expected pattern: postgresql://user:pass@host:port/dbname

    Returns True if valid or url is empty (SQLite mode), False otherwise.
    """
    if not url:
        return True  # SQLite mode -- no URL required
    return url.startswith("postgresql://") or url.startswith("postgres://")
