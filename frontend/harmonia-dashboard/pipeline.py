"""
Pipeline Zwiadowca → Egzekutor
ADRION 369 | Harmonia Lead Generation

5-etapowy pipeline automatyzacji:
  1. CHRONOS   — Cron trigger / scheduling
  2. SENTINEL  — Google Maps scraping (symulacja)
  3. AUDYTOR   — Filtracja jakości + blacklista (Guardian Law G8)
  4. BOOSTERLEVER — Generacja spersonalizowanych maili (Ollama)
  5. SAP       — Wysyłka / zapis do bazy

Uruchomienie:
  from pipeline import Pipeline
  p = Pipeline()
  result = await p.run("restauracje", "Kraków", radius_km=5)
"""

import asyncio
import json
import os
import re
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

try:
    import psycopg2
    import psycopg2.extras
    HAS_PG = True
except ImportError:
    HAS_PG = False

try:
    import urllib.request
    HAS_HTTP = True
except ImportError:
    HAS_HTTP = False

# ===== CONFIG =====
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
# Przełączam na lżejszy model phi3:mini dla uniknięcia timeoutów
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")
DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", 5432)),
    "dbname": os.getenv("PG_DB", "genesis_record"),
    "user": os.getenv("PG_USER", "adrion"),
    "password": os.getenv("PG_PASS", "adrion_pass"),
}
BLACKLIST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blacklist.json")
GENESIS_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "genesis_log.json")


# ===== DATA MODELS =====
@dataclass
class Lead:
    business_name: str
    city: str
    email: str
    phone: str = ""
    category: str = ""
    rating: float = 0.0
    reviews_count: int = 0
    photos_count: int = 0
    verified: bool = False
    score_wv: int = 0
    score_wr: int = 0
    score_we: int = 0
    score_total: int = 0
    verdict: str = ""
    lead_status: str = "NEW"
    ai_mail_subject: str = ""
    ai_mail_body: str = ""


@dataclass
class PipelineState:
    status: str = "idle"           # idle | running | completed | error
    current_stage: str = ""
    started_at: str = ""
    completed_at: str = ""
    niche: str = ""
    city: str = ""
    scraped_count: int = 0
    filtered_count: int = 0
    mails_generated: int = 0
    sent_count: int = 0
    logs: list = field(default_factory=list)
    error: str = ""


# ===== GENESIS RECORD =====
def genesis_log(agent: str, action: str, detail: str = ""):
    """Append-only log. Guardian Law G7: dane nie opuszczają maszyny."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "action": action,
        "detail": detail,
    }
    logs = []
    if os.path.exists(GENESIS_LOG):
        try:
            with open(GENESIS_LOG, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except (json.JSONDecodeError, OSError):
            logs = []
    logs.append(entry)
    # Keep last 500 entries
    if len(logs) > 500:
        logs = logs[-500:]
    with open(GENESIS_LOG, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)
    return entry


def get_genesis_logs(limit: int = 100) -> list:
    if not os.path.exists(GENESIS_LOG):
        return []
    try:
        with open(GENESIS_LOG, "r", encoding="utf-8") as f:
            logs = json.load(f)
        return logs[-limit:]
    except (json.JSONDecodeError, OSError):
        return []


# ===== BLACKLIST (Guardian Law G8) =====
def load_blacklist() -> set:
    if not os.path.exists(BLACKLIST_FILE):
        return set()
    try:
        with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (json.JSONDecodeError, OSError):
        return set()


def add_to_blacklist(email: str):
    bl = load_blacklist()
    bl.add(email.lower().strip())
    with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(bl), f, ensure_ascii=False, indent=2)


# ===== OLLAMA =====
def query_ollama(system_prompt: str, user_msg: str, max_tokens: int = 600) -> Optional[str]:
    if not HAS_HTTP:
        return None
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": user_msg,
        "system": system_prompt,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": max_tokens},
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response")
    except Exception as e:
        print(f"[Ollama] Error: {e}")
        return None


# ===== HARMONY 369 SCORING =====
def calculate_harmony(lead: Lead) -> Lead:
    """W = (W_V × 3 + W_R × 6 + W_E × 9) / 18"""
    # W_V: Widoczność — based on verified, photos
    wv = 20
    if lead.verified:
        wv += 30
    wv += min(lead.photos_count * 5, 30)
    wv = min(wv, 100)

    # W_R: Reputacja — based on rating, reviews
    wr = 10
    wr += int(lead.rating * 12)
    wr += min(lead.reviews_count, 40)
    wr = min(wr, 100)

    # W_E: Zaangażowanie — hardest to score without real data
    we = 15
    if lead.reviews_count > 20:
        we += 15
    if lead.photos_count > 5:
        we += 10
    we = min(we, 100)

    total = round((wv * 3 + wr * 6 + we * 9) / 18)
    lead.score_wv = wv
    lead.score_wr = wr
    lead.score_we = we
    lead.score_total = total
    lead.lead_status = "HOT" if total < 50 else "WARM"

    if total >= 75:
        lead.verdict = "Wizytówka w dobrej kondycji — punkty optymalizacji."
    elif total >= 50:
        lead.verdict = "Wymaga uwagi — luki w geotagowaniu i NAP."
    elif total >= 30:
        lead.verdict = "Chaos informacyjny — krytyczne luki EXIF i NAP."
    else:
        lead.verdict = "ALARM — firma niewidoczna w Google Maps."

    return lead


# ===== STAGE 2: SENTINEL (Scraper — symulacja) =====
SIMULATED_BUSINESSES = [
    {"name": "Pizzeria Roma", "rating": 3.8, "reviews": 45, "photos": 3, "verified": True, "email": "roma@example.pl", "phone": "600111222"},
    {"name": "Salon Fryzjerski Elegancja", "rating": 4.2, "reviews": 12, "photos": 1, "verified": True, "email": "elegancja@example.pl", "phone": "600222333"},
    {"name": "Warsztat Samochodowy Auto-Fix", "rating": 3.1, "reviews": 8, "photos": 0, "verified": False, "email": "autofix@example.pl", "phone": "600333444"},
    {"name": "Kawiarnia Cukiernia Słodki Kąt", "rating": 4.5, "reviews": 67, "photos": 12, "verified": True, "email": "slodki@example.pl", "phone": "600444555"},
    {"name": "Kancelaria Prawna Lex", "rating": 4.8, "reviews": 5, "photos": 2, "verified": True, "email": "lex@example.pl", "phone": "600555666"},
    {"name": "Fitness Club Olimp", "rating": 3.5, "reviews": 23, "photos": 4, "verified": True, "email": "olimp@example.pl", "phone": "600666777"},
    {"name": "Dentysta Uśmiech", "rating": 2.9, "reviews": 3, "photos": 0, "verified": False, "email": "usmiech@example.pl", "phone": "600777888"},
    {"name": "Kwiaciarnia Pod Różą", "rating": 4.0, "reviews": 15, "photos": 6, "verified": True, "email": "roza@example.pl", "phone": "600888999"},
    {"name": "Restauracja Sushi King", "rating": 4.3, "reviews": 89, "photos": 15, "verified": True, "email": "sushiking@example.pl", "phone": "601111222"},
    {"name": "Sklep Zoologiczny Pupil", "rating": 3.2, "reviews": 7, "photos": 1, "verified": False, "email": "pupil@example.pl", "phone": "601222333"},
]


def sentinel_scrape(niche: str, city: str, radius_km: int = 5) -> list[Lead]:
    """Stage 2: Scraping Google Maps (symulacja z deterministycznymi danymi)."""
    leads = []
    for biz in SIMULATED_BUSINESSES:
        lead = Lead(
            business_name=biz["name"],
            city=city,
            email=biz["email"],
            phone=biz["phone"],
            category=niche,
            rating=biz["rating"],
            reviews_count=biz["reviews"],
            photos_count=biz["photos"],
            verified=biz["verified"],
        )
        leads.append(lead)
    return leads


# ===== STAGE 3: AUDYTOR (Filter + Blacklist) =====
def auditor_filter(leads: list[Lead]) -> list[Lead]:
    """Stage 3: Filtracja — email required, not blacklisted, low-quality signals."""
    blacklist = load_blacklist()
    filtered = []
    for lead in leads:
        # Must have email
        if not lead.email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', lead.email):
            continue
        # Guardian Law G8: blacklist check
        if lead.email.lower() in blacklist:
            genesis_log("AUDYTOR", "BLACKLIST_REJECT", f"{lead.business_name} ({lead.email})")
            continue
        # Calculate harmony score
        lead = calculate_harmony(lead)
        filtered.append(lead)
    return filtered


# ===== STAGE 4: BOOSTERLEVER (AI Mail Generation) =====
BOOSTER_SYSTEM_PROMPT = """Jesteś BoosterLever — agentem AI w systemie Harmonia 369, agencji "Wirtualny Punkt Odniesienia".
Twoim zadaniem jest napisanie KRÓTKIEGO, spersonalizowanego maila do właściciela firmy.

ZASADY:
- Ton: profesjonalny, konkretny, życzliwy — NIGDY agresywny spam
- Pokaż że znasz ich sytuację (użyj danych z analizy)
- Wspomnij konkretne braki (EXIF, NAP, brak postów)
- Zaproponuj jedną konkretną wartość (audyt wizytówki)
- Max 150 słów
- Na końcu: "Pozdrawiam, Zespół Harmonia 369 | Wirtualny Punkt Odniesienia"
- Napisz TYLKO treść maila, BEZ tematu"""

BOOSTER_SUBJECT_PROMPT = """Na podstawie danych o firmie napisz JEDEN krótki temat maila (max 60 znaków).
Temat ma być konkretny, personalny i zachęcający do otwarcia.
Napisz TYLKO temat, nic więcej."""


def boosterlever_generate(lead: Lead) -> Lead:
    """Stage 4: Generate personalized email via Ollama."""
    user_data = f"""Firma: {lead.business_name} ({lead.city})
Kategoria: {lead.category}
Score Harmonii: {lead.score_total}/100 (W_V={lead.score_wv}, W_R={lead.score_wr}, W_E={lead.score_we})
Ocena Google: {lead.rating}/5, Opinie: {lead.reviews_count}, Zdjęcia: {lead.photos_count}
Zweryfikowana: {'Tak' if lead.verified else 'Nie'}
Diagnoza: {lead.verdict}"""

    # Generate subject
    subject = query_ollama(BOOSTER_SUBJECT_PROMPT, user_data, max_tokens=80)
    if subject:
        lead.ai_mail_subject = subject.strip().strip('"').strip("'")
    else:
        lead.ai_mail_subject = f"{lead.business_name} — Twoja wizytówka traci klientów (Score: {lead.score_total}%)"

    # Generate body
    body = query_ollama(BOOSTER_SYSTEM_PROMPT, user_data, max_tokens=400)
    if body:
        lead.ai_mail_body = body.strip()
    else:
        lead.ai_mail_body = _fallback_mail(lead)

    return lead


def _fallback_mail(lead: Lead) -> str:
    """Fallback template when Ollama is unavailable."""
    issues = []
    if lead.score_we < 30:
        issues.append("brak regularnych postów z geotagowanymi zdjęciami")
    if lead.photos_count < 3:
        issues.append(f"tylko {lead.photos_count} zdjęć (brak danych EXIF)")
    if not lead.verified:
        issues.append("wizytówka niezweryfikowana")
    if lead.score_wr < 50:
        issues.append(f"niska reputacja online ({lead.rating}/5, {lead.reviews_count} opinii)")
    issue_text = ", ".join(issues) if issues else "luki w optymalizacji wizytówki Google Maps"

    return f"""Dzień dobry,

Nasz system Harmonia 369 przeanalizował wizytówkę "{lead.business_name}" w Google Maps i wykrył kilka obszarów wymagających uwagi.

Wskaźnik Harmonii Twojej wizytówki wynosi {lead.score_total}/100. Główne sygnały: {issue_text}.

Oznacza to, że potencjalni klienci szukający usług w {lead.city} mogą trafiać do konkurencji zamiast do Ciebie — nawet jeśli Twoja oferta jest lepsza.

Chętnie pokażę Ci w 5-minutowej sesji, jak nasz Rój Agentów AI może to naprawić. Bezpłatnie.

Pozdrawiam,
Zespół Harmonia 369 | Wirtualny Punkt Odniesienia"""


# ===== STAGE 5: SAP (Save + Send) =====
def sap_save_leads(leads: list[Lead]) -> int:
    """Stage 5: Save processed leads to database."""
    if not HAS_PG:
        return 0
    saved = 0
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            for lead in leads:
                cur.execute("""
                    INSERT INTO leads (timestamp, business_name, city, email, phone,
                                       score_total, score_wv, score_wr, score_we,
                                       verdict, lead_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    datetime.now(timezone.utc).isoformat(),
                    lead.business_name, lead.city, lead.email, lead.phone,
                    lead.score_total, lead.score_wv, lead.score_wr, lead.score_we,
                    lead.verdict, lead.lead_status,
                ))
                saved += 1
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[SAP] DB Error: {e}")
    return saved


# ===== PIPELINE ORCHESTRATOR =====
# Global state — singleton per process
_pipeline_state = PipelineState()


def get_pipeline_state() -> dict:
    return asdict(_pipeline_state)


def get_swarm_status() -> list:
    """Return current agent statuses based on pipeline state."""
    stage = _pipeline_state.current_stage
    status = _pipeline_state.status

    def agent_status(name):
        if status == "idle":
            return "idle"
        if status == "completed":
            return "done"
        if status == "error":
            return "error" if stage == name else "idle"
        stages_order = ["CHRONOS", "SENTINEL", "AUDYTOR", "BOOSTERLEVER", "SAP"]
        if name in stages_order:
            idx_current = stages_order.index(stage) if stage in stages_order else -1
            idx_name = stages_order.index(name)
            if idx_name < idx_current:
                return "done"
            if idx_name == idx_current:
                return "active"
        return "idle"

    return [
        {"agent": "SENTINEL", "status": agent_status("SENTINEL"), "ebdi": [0.1, 0.6, 0.6]},
        {"agent": "AUDYTOR", "status": agent_status("AUDYTOR"), "ebdi": [0.0, -0.2, 0.8]},
        {"agent": "BOOSTERLEVER", "status": agent_status("BOOSTERLEVER"), "ebdi": [0.3, 0.4, 0.7]},
        {"agent": "SAP", "status": agent_status("SAP"), "ebdi": [0.1, 0.2, 0.7]},
        {"agent": "CHRONOS", "status": agent_status("CHRONOS"), "ebdi": [0.0, 0.0, 0.5]},
        {"agent": "LIBRARIAN", "status": "idle", "ebdi": [0.0, -0.1, 0.6]},
    ]


def run_pipeline_sync(niche: str, city: str, radius_km: int = 5, generate_mails: bool = True) -> dict:
    """
    Execute the full Zwiadowca→Egzekutor pipeline synchronously.
    Returns PipelineState as dict.
    """
    global _pipeline_state
    state = _pipeline_state
    state.status = "running"
    state.started_at = datetime.now(timezone.utc).isoformat()
    state.completed_at = ""
    state.niche = niche
    state.city = city
    state.scraped_count = 0
    state.filtered_count = 0
    state.mails_generated = 0
    state.sent_count = 0
    state.logs = []
    state.error = ""

    def log(agent, msg):
        entry = {"ts": datetime.now(timezone.utc).isoformat(), "agent": agent, "msg": msg}
        state.logs.append(entry)
        genesis_log(agent, "PIPELINE", msg)

    try:
        # Stage 1: CHRONOS
        state.current_stage = "CHRONOS"
        log("CHRONOS", f"Pipeline uruchomiony. Nisza: {niche}, Miasto: {city}, Promień: {radius_km}km")
        time.sleep(0.5)

        # Stage 2: SENTINEL
        state.current_stage = "SENTINEL"
        log("SENTINEL", f"Scraping Google Maps — nisza: {niche}, {city}...")
        leads = sentinel_scrape(niche, city, radius_km)
        state.scraped_count = len(leads)
        log("SENTINEL", f"Wykryto {len(leads)} wizytówek.")

        # Stage 3: AUDYTOR
        state.current_stage = "AUDYTOR"
        log("AUDYTOR", f"Filtracja jakości + sprawdzanie blacklisty (Guardian Law G8)...")
        filtered = auditor_filter(leads)
        state.filtered_count = len(filtered)
        rejected = len(leads) - len(filtered)
        log("AUDYTOR", f"Po filtracji: {len(filtered)} kwalifikujących się. Odrzucono: {rejected}.")

        hot_count = sum(1 for l in filtered if l.lead_status == "HOT")
        warm_count = sum(1 for l in filtered if l.lead_status == "WARM")
        log("AUDYTOR", f"HOT: {hot_count}, WARM: {warm_count}")

        # Stage 4: BOOSTERLEVER
        state.current_stage = "BOOSTERLEVER"
        if generate_mails:
            hot_leads = [l for l in filtered if l.lead_status == "HOT"]
            log("BOOSTERLEVER", f"Generowanie spersonalizowanych maili dla {len(hot_leads)} leadów HOT...")
            for lead in hot_leads:
                boosterlever_generate(lead)
                state.mails_generated += 1
                log("BOOSTERLEVER", f"Mail wygenerowany: {lead.business_name} — temat: {lead.ai_mail_subject[:50]}...")
        else:
            log("BOOSTERLEVER", "Generacja maili pominięta (tryb testowy).")

        # Stage 5: SAP
        state.current_stage = "SAP"
        log("SAP", f"Zapisywanie {len(filtered)} leadów do bazy...")
        saved = sap_save_leads(filtered)
        state.sent_count = saved
        log("SAP", f"Zapisano {saved} leadów. Genesis Record zaktualizowany.")

        state.status = "completed"
        state.completed_at = datetime.now(timezone.utc).isoformat()
        state.current_stage = ""
        log("SYSTEM", f"Pipeline zakończony. Scraped: {state.scraped_count}, Filtered: {state.filtered_count}, Mails: {state.mails_generated}, Saved: {state.sent_count}")

    except Exception as e:
        state.status = "error"
        state.error = str(e)
        log("SYSTEM", f"PIPELINE ERROR: {e}")

    return asdict(state)


# ===== AGENT INTERAKCJI: WEEKLY REPORT =====
AGENT_INTERACTION_PROMPT = """Jesteś Agentem Interakcji w systemie Harmonia 369 — agencji "Wirtualny Punkt Odniesienia".
Na podstawie danych analitycznych napisz profesjonalny raport tygodniowy (Weekly Insights) dla właściciela firmy.

ZASADY:
- Ton: profesjonalny, konkretny, zorientowany na matematyczny zysk, życzliwy
- Pokaż że system aktywnie reaguje na ruchy rynku w czasie rzeczywistym
- Użyj konkretnych liczb i terminologii: Wskaźnik Harmonii, Local Grid, EXIF, NAP
- Podpisz się jako "Twój Rój Agentów ADRION 369"
- Uporządkuj w sekcje: Kluczowe Liczby, Akcje Agentów, Następne Kroki
- Max 250 słów"""


def generate_weekly_report(client_name: str, period: str = "ostatni tydzień", context: str = "") -> dict:
    """Generate a Weekly Insights report via Ollama."""
    user_msg = f"""Klient: {client_name}
Okres: {period}
{f'Dodatkowy kontekst: {context}' if context else ''}

Wygeneruj kompletny raport Weekly Insights."""

    result = query_ollama(AGENT_INTERACTION_PROMPT, user_msg, max_tokens=600)
    genesis_log("AGENT_INTERAKCJI", "REPORT_GENERATED", f"Klient: {client_name}, Okres: {period}")

    if result:
        return {"status": "ok", "report": result, "source": "ollama", "model": OLLAMA_MODEL}
    else:
        return {"status": "ok", "report": _fallback_weekly_report(client_name, period), "source": "template", "model": "fallback"}


def _fallback_weekly_report(client_name: str, period: str) -> str:
    return f"""📊 Weekly Insights — {client_name}
Okres: {period}

Kluczowe Liczby:
• Wskaźnik Harmonii: w trakcie kalkulacji
• Połączenia z wizytówki: dane zbierane
• Konwersja: monitorowana

Akcje Agentów:
1. Agent Analityk — przeskanował Local Grid w promieniu 5km
2. Agent Twórca — przygotował propozycje postów z EXIF
3. Agent Interakcji — generuje ten raport

Następne Kroki:
- Finalizacja audytu wizytówki Google Maps
- Wdrożenie strategii postów z geotagowaniem
- Uruchomienie monitoringu konkurencji

Pozdrawiam,
Twój Rój Agentów ADRION 369"""
