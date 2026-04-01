import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
BASE_DIR = Path(__file__).parent.parent
DB_PATH  = Path(os.getenv('DB_PATH', str(BASE_DIR / 'arbitrage.db')))
DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite')  # sqlite | postgres
DB_URL    = os.getenv('DATABASE_URL', '')    # For Postgres connection
LLM_BACKEND    = os.getenv('LLM_BACKEND', 'auto')
OPENROUTER_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENAI_KEY     = os.getenv('OPENAI_API_KEY', '')
ANTHROPIC_KEY  = os.getenv('ANTHROPIC_API_KEY', '')
LLM_MODEL      = os.getenv('LLM_MODEL', 'openai/gpt-3.5-turbo')
APIFY_TOKEN    = os.getenv('APIFY_API_TOKEN', '')
DAILY_BID_LIMIT    = int(os.getenv('DAILY_BID_LIMIT', '20'))
XRP_TARGET         = float(os.getenv('XRP_TARGET', '1000'))
MIN_PROFIT_USD     = float(os.getenv('MIN_PROFIT_USD', '30'))
MIN_ANALYZER_SCORE = int(os.getenv('MIN_ANALYZER_SCORE', '7'))
MAX_EST_COST_PER_BID_USD = float(os.getenv('MAX_EST_COST_PER_BID_USD', '2.5'))
MAX_BIDS_PER_CLIENT_PER_DAY = int(os.getenv('MAX_BIDS_PER_CLIENT_PER_DAY', '1'))
MAX_DAILY_EST_COST_USD = float(os.getenv('MAX_DAILY_EST_COST_USD', '25'))
UGC_EVENTS_DAILY_CAP = int(os.getenv('UGC_EVENTS_DAILY_CAP', '4'))
RESALE_EVENTS_DAILY_CAP = int(os.getenv('RESALE_EVENTS_DAILY_CAP', '4'))
UGC_SOURCE_URL = os.getenv('UGC_SOURCE_URL', '').strip()
RESALE_SOURCE_URL = os.getenv('RESALE_SOURCE_URL', '').strip()
STREAMS_CONNECTOR_TOKEN = os.getenv('STREAMS_CONNECTOR_TOKEN', '').strip()
SCOUT_KEYWORDS = ['content writing','blog post','copywriting','article writing','ghostwriting','SEO content']
SCOUT_MIN_BUDGET = 50
SCOUT_MAX_BUDGET = 500
SCOUT_PLATFORMS  = ['fiverr', 'upwork']

# ═══ QUANTUM SCAN CHANNELS (Multi-Stream Scanner — PROGRAMATOR #10) ═══
# Each channel: id, min_margin %, solfeggio frequency Hz, keywords
QUANTUM_SCAN_CHANNELS = [
    {"id": "AUDIO_PREMIUM",    "min_margin": 15, "frequency": 432, "keywords": ["audio", "DAC", "headphones", "speakers", "hi-fi"]},
    {"id": "SMART_ENERGY",     "min_margin": 18, "frequency": 528, "keywords": ["solar", "inverter", "battery", "EV charger", "smart home"]},
    {"id": "ROBOTICS_AI",      "min_margin": 20, "frequency": 396, "keywords": ["robot", "drone", "3D printer", "CNC", "automation"]},
    {"id": "REFURBISHED_LUX",  "min_margin": 15, "frequency": 174, "keywords": ["refurbished", "renewed", "outlet", "open-box", "B-stock"]},
    {"id": "BIOTECH_HEALTH",   "min_margin": 25, "frequency": 528, "keywords": ["supplement", "biohacking", "health tech", "wearable", "lab"]},
]

# Security policy: wallet address is entered manually at transfer time and is not persisted in code/env.


def get_active_llm_backend() -> str:
    """Auto-detect which LLM backend to use based on available API keys."""
    if LLM_BACKEND != "auto":
        return LLM_BACKEND
    if OPENROUTER_KEY:
        return "openrouter"
    if OPENAI_KEY:
        return "openai"
    if ANTHROPIC_KEY:
        return "anthropic"
    return "mock"

