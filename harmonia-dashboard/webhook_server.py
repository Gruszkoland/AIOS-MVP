"""
Harmonia 369 — Webhook Backend Server v2
ADRION 369 | Centrum Dowodzenia

Endpoints:
  POST /webhook/harmonia-369       → zapis leada do PostgreSQL
  GET  /api/leads                  → lista leadów
  GET  /api/stats                  → statystyki KPI
  GET  /api/genesis                → Genesis Record logs
  GET  /api/swarm/status           → agent swarm status
  GET  /api/pipeline/status        → pipeline state
  POST /api/pipeline/run           → uruchom pipeline Zwiadowca→Egzekutor
  POST /api/ai/report              → Agent Interakcji weekly report
  GET  /health                     → health check

Port: 3691
"""
import json
import os
import sys
import http.server
import urllib.parse
import threading
from datetime import datetime

# PostgreSQL — psycopg2
try:
    import psycopg2
    import psycopg2.extras
    HAS_PG = True
except ImportError:
    HAS_PG = False
    print("[WARN] psycopg2 niedostępny — leady zapisywane do pliku JSON")

PORT = 3691
DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", 5432)),
    "dbname": os.getenv("PG_DB", "genesis_record"),
    "user": os.getenv("PG_USER", "adrion"),
    "password": os.getenv("PG_PASS", "adrion_pass"),
    "connect_timeout": 3,
}
LEADS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.json")

# Pipeline module
try:
    from pipeline import (
        run_pipeline_sync, get_pipeline_state, get_swarm_status,
        get_genesis_logs, genesis_log, generate_weekly_report,
    )
    HAS_PIPELINE = True
except ImportError:
    HAS_PIPELINE = False
    print("[WARN] pipeline.py niedostępny — endpointy AI/pipeline wyłączone")

# Feedback Engine (OODA + V.E.R.A. + Judge)
try:
    from feedback_engine import get_feedback_loop
    HAS_FEEDBACK = True
except ImportError:
    HAS_FEEDBACK = False
    print("[WARN] feedback_engine.py niedostępny — endpointy OODA/V.E.R.A. wyłączone")

# RAG Memory
try:
    from rag_memory import get_memory
    HAS_RAG = True
except ImportError:
    HAS_RAG = False
    print("[WARN] rag_memory.py niedostępny — RAG memory wyłączone")

# Memory Event Bus
try:
    from memory_events import get_event_bus
    HAS_EVENT_BUS = True
except ImportError:
    HAS_EVENT_BUS = False
    print("[WARN] memory_events.py niedostępny — event bus wyłączony")


def get_db():
    if not HAS_PG:
        return None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return None


def save_lead_db(data):
    conn = get_db()
    if not conn:
        return save_lead_file(data)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO leads (timestamp, business_name, city, email, phone,
                                   score_total, score_wv, score_wr, score_we,
                                   verdict, lead_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data.get("timestamp", datetime.utcnow().isoformat()),
                data.get("business_name", ""),
                data.get("city", ""),
                data.get("email", ""),
                data.get("phone", ""),
                data.get("score_total", 0),
                data.get("score_wv", 0),
                data.get("score_wr", 0),
                data.get("score_we", 0),
                data.get("verdict", ""),
                "HOT" if data.get("score_total", 0) < 50 else "WARM",
            ))
            conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB INSERT ERROR] {e}")
        conn.close()
        return save_lead_file(data)


def update_lead_confirmed(data):
    conn = get_db()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE leads SET lead_status = 'CONFIRMED' WHERE email = %s AND business_name = %s",
                (data.get("email", ""), data.get("business_name", ""))
            )
            conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB UPDATE ERROR] {e}")
        conn.close()
        return False


def save_lead_file(data):
    """Fallback: zapis do JSON gdy Postgres niedostępny."""
    leads = []
    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, "r", encoding="utf-8") as f:
            leads = json.load(f)
    leads.append(data)
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)
    return True


def get_leads():
    conn = get_db()
    if not conn:
        if os.path.exists(LEADS_FILE):
            with open(LEADS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM leads ORDER BY created_at DESC LIMIT 100")
            rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[DB SELECT ERROR] {e}")
        conn.close()
        return []


def get_stats():
    conn = get_db()
    if not conn:
        return {"total": 0, "hot": 0, "warm": 0, "confirmed": 0, "avg_score": 0}
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN lead_status = 'HOT' THEN 1 ELSE 0 END) as hot,
                    SUM(CASE WHEN lead_status = 'WARM' THEN 1 ELSE 0 END) as warm,
                    SUM(CASE WHEN lead_status = 'CONFIRMED' THEN 1 ELSE 0 END) as confirmed,
                    COALESCE(AVG(score_total), 0) as avg_score
                FROM leads
            """)
            row = cur.fetchone()
        conn.close()
        if row:
            result = dict(row)
            result["avg_score"] = round(float(result.get("avg_score", 0)), 1)
            result["total"] = int(result.get("total", 0))
            result["hot"] = int(result.get("hot", 0))
            result["warm"] = int(result.get("warm", 0))
            result["confirmed"] = int(result.get("confirmed", 0))
            return result
        return {"total": 0, "hot": 0, "warm": 0, "confirmed": 0, "avg_score": 0}
    except Exception as e:
        print(f"[DB STATS ERROR] {e}")
        conn.close()
        return {"total": 0}


# ===== OUTREACH: SEARCH + ANALYZE + EMAIL =====

def search_leads(query: str):
    """Search leads by business_name, city, or email. Empty query returns recent 20."""
    conn = get_db()
    if not conn:
        # Fallback: search in JSON file
        if os.path.exists(LEADS_FILE):
            with open(LEADS_FILE, "r", encoding="utf-8") as f:
                leads = json.load(f)
            if query:
                q = query.lower()
                leads = [l for l in leads if q in (l.get("business_name", "") or "").lower()
                         or q in (l.get("city", "") or "").lower()
                         or q in (l.get("email", "") or "").lower()]
            return leads[:50]
        return []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if query:
                param = f"%{query}%"
                cur.execute("""
                    SELECT id, business_name, city, email, phone,
                           score_total, score_wv, score_wr, score_we,
                           verdict, lead_status, created_at
                    FROM leads
                    WHERE business_name ILIKE %s OR city ILIKE %s OR email ILIKE %s
                    ORDER BY created_at DESC LIMIT 50
                """, (param, param, param))
            else:
                cur.execute("""
                    SELECT id, business_name, city, email, phone,
                           score_total, score_wv, score_wr, score_we,
                           verdict, lead_status, created_at
                    FROM leads ORDER BY created_at DESC LIMIT 20
                """)
            rows = cur.fetchall()
        conn.close()
        results = []
        for r in rows:
            d = dict(r)
            d["score_total"] = int(d.get("score_total") or 0)
            d["score_wv"] = int(d.get("score_wv") or 0)
            d["score_wr"] = int(d.get("score_wr") or 0)
            d["score_we"] = int(d.get("score_we") or 0)
            results.append(d)
        return results
    except Exception as e:
        print(f"[SEARCH ERROR] {e}")
        conn.close()
        return []


def analyze_client(lead_id):
    """Analyze a single lead's needs based on Harmony 369 scores."""
    lead = None
    conn = get_db()
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM leads WHERE id = %s", (int(lead_id),))
                row = cur.fetchone()
            conn.close()
            if row:
                lead = dict(row)
        except Exception as e:
            print(f"[ANALYZE ERROR] {e}")
            conn.close()
    else:
        # Fallback: find in JSON file
        if os.path.exists(LEADS_FILE):
            with open(LEADS_FILE, "r", encoding="utf-8") as f:
                leads = json.load(f)
            # Match by id field or by list index (1-based)
            for i, l in enumerate(leads):
                if str(l.get("id", "")) == str(lead_id) or i == int(lead_id) - 1:
                    lead = l
                    break

    if not lead:
        return None

    lead["score_total"] = int(lead.get("score_total") or 0)
    lead["score_wv"] = int(lead.get("score_wv") or 0)
    lead["score_wr"] = int(lead.get("score_wr") or 0)
    lead["score_we"] = int(lead.get("score_we") or 0)

    # Analyze issues
    issues = []
    recommendations = []

    wv = lead["score_wv"]
    wr = lead["score_wr"]
    we = lead["score_we"]
    total = lead["score_total"]

    # Visibility analysis (W_V)
    if wv < 30:
        issues.append({"icon": "🔴", "text": f"Krytycznie niska widoczność (W_V={wv})", "severity": "critical"})
        recommendations.append("Pilna weryfikacja wizytówki Google + minimum 10 zdjęć z geotagami EXIF")
    elif wv < 50:
        issues.append({"icon": "🟡", "text": f"Słaba widoczność w Google Maps (W_V={wv})", "severity": "medium"})
        recommendations.append("Dodanie zdjęć z geotagami i uzupełnienie danych NAP")

    # Reputation analysis (W_R)
    if wr < 30:
        issues.append({"icon": "🔴", "text": f"Bardzo słaba reputacja online (W_R={wr})", "severity": "critical"})
        recommendations.append("Strategia pozyskiwania opinii Google + odpowiedzi na recenzje")
    elif wr < 50:
        issues.append({"icon": "🟡", "text": f"Reputacja wymaga wzmocnienia (W_R={wr})", "severity": "medium"})
        recommendations.append("Kampania review-generation + automatyczne follow-upy po usługach")

    # Engagement analysis (W_E)
    if we < 30:
        issues.append({"icon": "🔴", "text": f"Minimalne zaangażowanie klientów (W_E={we})", "severity": "critical"})
        recommendations.append("Regularne posty Google Business (min. 2/tydzień) + oferty specjalne")
    elif we < 50:
        issues.append({"icon": "🟡", "text": f"Zaangażowanie poniżej mediany (W_E={we})", "severity": "medium"})
        recommendations.append("Plan publikacji treści z pytaniami do klientów + Q&A")

    # Overall
    if total < 30:
        issues.append({"icon": "🚨", "text": f"ALARM: Firma praktycznie niewidoczna online (Score {total}/100)", "severity": "critical"})
    elif total < 50:
        issues.append({"icon": "⚠️", "text": f"Firma traci klientów na rzecz konkurencji (Score {total}/100)", "severity": "medium"})

    if not issues:
        issues.append({"icon": "✅", "text": f"Wizytówka w dobrej kondycji (Score {total}/100)", "severity": "ok"})
        recommendations.append("Utrzymanie pozycji + monitorowanie konkurencji")

    return {
        "lead": lead,
        "issues": issues,
        "recommendations": recommendations,
        "summary": f"Score Harmonii: {total}/100 | W_V={wv} W_R={wr} W_E={we} | Wykryte problemy: {len([i for i in issues if i['severity'] != 'ok'])}",
    }


def generate_outreach_email(lead_id):
    """Generate a personalized outreach email via Ollama for a specific lead."""
    analysis = analyze_client(lead_id)
    if not analysis:
        return {"status": "error", "error": "Lead not found"}

    lead = analysis["lead"]
    issues = analysis["issues"]
    recs = analysis["recommendations"]

    if not HAS_PIPELINE:
        return {"status": "error", "error": "Pipeline/Ollama unavailable"}

    from pipeline import query_ollama, OLLAMA_MODEL
    import time

    issue_text = "\n".join(f"- {i['text']}" for i in issues)
    rec_text = "\n".join(f"- {r}" for r in recs)

    system_prompt = """Jesteś BoosterLever — AI agentem w systemie Harmonia 369, agencji "Wirtualny Punkt Odniesienia".
Twoim zadaniem jest napisanie SPERSONALIZOWANEGO maila do właściciela firmy.

ZASADY:
- Ton: profesjonalny, empatyczny, konkretny — NIGDY agresywny spam
- Pokaż że znasz ich sytuację (użyj danych z analizy)
- Wspomnij KONKRETNE problemy wykryte przez system
- Zaproponuj JEDNĄ konkretną wartość (bezpłatny audyt wizytówki)
- Max 180 słów
- Zakończ: "Pozdrawiam, Zespół Harmonia 369 | Wirtualny Punkt Odniesienia"
- Napisz TYLKO treść maila, BEZ tematu"""

    user_msg = f"""Firma: {lead.get('business_name', '')} ({lead.get('city', '')})
Email: {lead.get('email', '')}
Score Harmonii: {lead.get('score_total', 0)}/100
Widoczność (W_V): {lead.get('score_wv', 0)}/100
Reputacja (W_R): {lead.get('score_wr', 0)}/100
Zaangażowanie (W_E): {lead.get('score_we', 0)}/100
Status: {lead.get('lead_status', 'UNKNOWN')}
Diagnoza: {lead.get('verdict', '')}

Wykryte problemy:
{issue_text}

Rekomendacje:
{rec_text}"""

    subject_prompt = """Na podstawie danych o firmie napisz JEDEN krótki temat maila (max 60 znaków).
Temat ma być konkretny, personalny i zachęcający do otwarcia.
Wspomnij nazwę firmy lub branżę.
Napisz TYLKO temat, nic więcej."""

    t0 = time.time()

    subject = query_ollama(subject_prompt, user_msg, max_tokens=80)
    body = query_ollama(system_prompt, user_msg, max_tokens=500)

    gen_time = round(time.time() - t0, 1)

    if not subject:
        subject = f"{lead.get('business_name', 'Firma')} — Twoja wizytówka traci klientów (Score: {lead.get('score_total', '?')}%)"
    else:
        subject = subject.strip().strip('"').strip("'")

    if not body:
        # Fallback
        body = f"""Dzień dobry,

Nasz system Harmonia 369 przeanalizował wizytówkę "{lead.get('business_name', '')}" w Google Maps.

Wskaźnik Harmonii wynosi {lead.get('score_total', 0)}/100. To oznacza, że potencjalni klienci mogą trafiać do konkurencji.

Oferujemy bezpłatną analizę wizytówki z konkretnymi rekomendacjami poprawy widoczności.

Pozdrawiam,
Zespół Harmonia 369 | Wirtualny Punkt Odniesienia"""

    if HAS_PIPELINE:
        genesis_log("BOOSTERLEVER", "OUTREACH_EMAIL",
                     f"Generated for {lead.get('business_name', '')} (ID: {lead_id}, score: {lead.get('score_total', 0)})")

    return {
        "status": "ok",
        "subject": subject.strip(),
        "body": body.strip(),
        "model": OLLAMA_MODEL if HAS_PIPELINE else "fallback",
        "gen_time_s": gen_time,
        "lead_id": lead_id,
    }


class WebhookHandler(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json_response(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            data = json.loads(raw) if raw else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._json_response(400, {"error": "Invalid JSON"})
            return

        if self.path == "/webhook/harmonia-369":
            ts = datetime.now().strftime("%H:%M:%S")
            event = data.get("event", "scan")

            if event == "lead_confirmed":
                update_lead_confirmed(data)
                print(f"[{ts}] CONFIRMED: {data.get('business_name')} ({data.get('email')})")
                if HAS_PIPELINE:
                    genesis_log("WEBHOOK", "LEAD_CONFIRMED", f"{data.get('business_name')} ({data.get('email')})")
                self._json_response(200, {"status": "confirmed"})
            else:
                save_lead_db(data)
                score = data.get("score_total", "?")
                print(f"[{ts}] NEW LEAD: {data.get('business_name')} | Score: {score} | {data.get('email')}")
                if HAS_PIPELINE:
                    genesis_log("WEBHOOK", "NEW_LEAD", f"{data.get('business_name')} | Score: {score}")
                self._json_response(200, {"status": "saved", "score": score})

        elif self.path == "/api/pipeline/run":
            if not HAS_PIPELINE:
                self._json_response(503, {"error": "Pipeline module unavailable"})
                return
            niche = data.get("niche", "restauracje")
            city = data.get("city", "Kraków")
            radius = data.get("radius_km", 5)
            gen_mails = data.get("generate_mails", True)

            # Run pipeline in background thread
            def _run():
                run_pipeline_sync(niche, city, radius, gen_mails)
            thread = threading.Thread(target=_run, daemon=True)
            thread.start()
            self._json_response(200, {"status": "started", "niche": niche, "city": city})

        elif self.path == "/api/ai/report":
            if not HAS_PIPELINE:
                self._json_response(503, {"error": "Pipeline module unavailable"})
                return
            client = data.get("client_name", "")
            period = data.get("period", "ostatni tydzień")
            context = data.get("context", "")
            if not client:
                self._json_response(400, {"error": "client_name required"})
                return
            result = generate_weekly_report(client, period, context)
            self._json_response(200, result)

        elif self.path == "/api/blacklist":
            if not HAS_PIPELINE:
                self._json_response(503, {"error": "Pipeline module unavailable"})
                return
            from pipeline import add_to_blacklist, load_blacklist
            email = data.get("email", "").strip()
            if not email:
                self._json_response(400, {"error": "email required"})
                return
            add_to_blacklist(email)
            genesis_log("AUDYTOR", "BLACKLIST_ADD", f"Added: {email}")
            self._json_response(200, {"status": "added", "email": email, "total": len(list(load_blacklist()))})

        # ===== FEEDBACK ENGINE (OODA + V.E.R.A.) =====
        elif self.path == "/api/feedback/observe":
            if not HAS_FEEDBACK:
                self._json_response(503, {"error": "Feedback engine unavailable"})
                return
            prompt = data.get("prompt", "")
            response = data.get("response", "")
            if not prompt or not response:
                self._json_response(400, {"error": "prompt and response required"})
                return
            loop = get_feedback_loop()
            result = loop.observe(
                prompt=prompt, response=response,
                model=data.get("model", ""),
                latency_ms=data.get("latency_ms", 0),
                category=data.get("category", "general"),
                rag_context_used=data.get("rag_context_used", False),
            )
            self._json_response(200, result)

        elif self.path == "/api/feedback/orient":
            if not HAS_FEEDBACK:
                self._json_response(503, {"error": "Feedback engine unavailable"})
                return
            iid = data.get("interaction_id", "")
            if not iid:
                self._json_response(400, {"error": "interaction_id required"})
                return
            loop = get_feedback_loop()
            result = loop.orient(
                interaction_id=iid,
                accepted=data.get("accepted", False),
                correction=data.get("correction"),
                score=data.get("score", 0),
            )
            self._json_response(200, result)

        elif self.path == "/api/feedback/act":
            if not HAS_FEEDBACK:
                self._json_response(503, {"error": "Feedback engine unavailable"})
                return
            prompt = data.get("prompt", "")
            if not prompt:
                self._json_response(400, {"error": "prompt required"})
                return
            loop = get_feedback_loop()
            result = loop.act(prompt)
            self._json_response(200, result)

        elif self.path == "/api/golden":
            if not HAS_FEEDBACK:
                self._json_response(503, {"error": "Feedback engine unavailable"})
                return
            prompt = data.get("prompt", "")
            golden_response = data.get("golden_response", "")
            if not prompt or not golden_response:
                self._json_response(400, {"error": "prompt and golden_response required"})
                return
            loop = get_feedback_loop()
            gid = loop.golden.add(
                prompt=prompt, golden_response=golden_response,
                category=data.get("category", "general"),
                source=data.get("source", "user"),
            )
            # Also store in RAG long-term memory
            if loop.memory and loop.memory.available:
                loop.memory.add_golden_answer(prompt, golden_response, data.get("category", "general"))
            self._json_response(200, {"status": "added", "id": gid})

        # ===== OUTREACH: ANALYZE CLIENT =====
        elif self.path == "/api/outreach/analyze":
            lead_id = data.get("lead_id")
            if not lead_id:
                self._json_response(400, {"error": "lead_id required"})
                return
            result = analyze_client(lead_id)
            if result:
                self._json_response(200, result)
            else:
                self._json_response(404, {"error": "Lead not found"})

        # ===== OUTREACH: GENERATE EMAIL =====
        elif self.path == "/api/outreach/generate-email":
            lead_id = data.get("lead_id")
            if not lead_id:
                self._json_response(400, {"error": "lead_id required"})
                return
            result = generate_outreach_email(lead_id)
            self._json_response(200, result)

        else:
            self._json_response(404, {"error": "Not found"})

    def do_GET(self):
        if self.path == "/api/leads":
            leads = get_leads()
            self._json_response(200, leads)
        elif self.path == "/api/stats":
            stats = get_stats()
            self._json_response(200, stats)
        elif self.path == "/api/genesis":
            if HAS_PIPELINE:
                logs = get_genesis_logs(200)
                self._json_response(200, logs)
            else:
                self._json_response(200, [])
        elif self.path == "/api/swarm/status":
            if HAS_PIPELINE:
                swarm = get_swarm_status()
                self._json_response(200, swarm)
            else:
                self._json_response(200, [])
        elif self.path == "/api/pipeline/status":
            if HAS_PIPELINE:
                state = get_pipeline_state()
                self._json_response(200, state)
            else:
                self._json_response(200, {"status": "unavailable"})
        elif self.path == "/api/blacklist":
            if HAS_PIPELINE:
                from pipeline import load_blacklist
                bl = sorted(load_blacklist())
                self._json_response(200, {"blacklist": bl, "total": len(bl)})
            else:
                self._json_response(200, {"blacklist": [], "total": 0})
        # ===== FEEDBACK ENGINE GET ENDPOINTS =====
        elif self.path == "/api/feedback/decide":
            if not HAS_FEEDBACK:
                self._json_response(200, {"error": "Feedback engine unavailable"})
                return
            loop = get_feedback_loop()
            result = loop.decide()
            self._json_response(200, result)

        elif self.path == "/api/feedback/status":
            if not HAS_FEEDBACK:
                self._json_response(200, {"available": False})
                return
            loop = get_feedback_loop()
            result = loop.get_full_status()
            self._json_response(200, result)

        elif self.path == "/api/golden":
            if not HAS_FEEDBACK:
                self._json_response(200, [])
                return
            loop = get_feedback_loop()
            self._json_response(200, loop.golden.get_all())

        elif self.path == "/api/memory/stats":
            if HAS_RAG:
                mem = get_memory()
                self._json_response(200, mem.get_stats())
            else:
                self._json_response(200, {"available": False})

        elif self.path == "/api/events/metrics":
            if HAS_EVENT_BUS:
                bus = get_event_bus()
                self._json_response(200, bus.get_metrics())
            else:
                self._json_response(200, {"available": False})

        elif self.path == "/health":
            caps = {
                "status": "ok",
                "system": "Harmonia 369 Webhook v3",
                "pipeline": HAS_PIPELINE,
                "postgres": HAS_PG,
                "feedback_engine": HAS_FEEDBACK,
                "rag_memory": HAS_RAG,
                "event_bus": HAS_EVENT_BUS,
            }
            self._json_response(200, caps)

        elif self.path.startswith("/api/leads/search"):
            # Search leads by query (name, city, email)
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            query = qs.get("q", [""])[0].strip()
            results = search_leads(query)
            self._json_response(200, results)

        else:
            self._json_response(404, {"error": "Not found"})

    def log_message(self, format, *args):
        pass  # Suppress default log to keep terminal clean


if __name__ == "__main__":
    import socketserver
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True

    with ThreadedHTTPServer(("", PORT), WebhookHandler) as httpd:
        print(f"[Harmonia 369] Webhook Backend v3 aktywny: http://localhost:{PORT}")
        print(f"[Harmonia 369] Pipeline module:   {'✓' if HAS_PIPELINE else '✗'}")
        print(f"[Harmonia 369] PostgreSQL:        {'✓' if HAS_PG else '✗ (fallback JSON)'}")
        print(f"[Harmonia 369] Feedback Engine:   {'✓' if HAS_FEEDBACK else '✗'}")
        print(f"[Harmonia 369] RAG Memory:        {'✓' if HAS_RAG else '✗'}")
        print(f"[Harmonia 369] Endpoints:")
        print(f"  POST /webhook/harmonia-369    — Lead webhook")
        print(f"  GET  /api/leads               — Lista leadów")
        print(f"  GET  /api/stats               — Statystyki KPI")
        print(f"  GET  /api/genesis             — Genesis Record")
        print(f"  GET  /api/swarm/status        — Swarm agent status")
        print(f"  GET  /api/pipeline/status     — Pipeline state")
        print(f"  POST /api/pipeline/run        — Uruchom pipeline")
        print(f"  POST /api/ai/report           — Weekly report (Ollama)")
        print(f"  POST /api/blacklist           — Dodaj do blacklist")
        print(f"  GET  /api/blacklist           — Lista blacklist")
        print(f"  --- Feedback Engine (OODA + V.E.R.A.) ---")
        print(f"  POST /api/feedback/observe    — Log interaction")
        print(f"  POST /api/feedback/orient     — User feedback")
        print(f"  GET  /api/feedback/decide     — Trends + recommendations")
        print(f"  POST /api/feedback/act        — RAG context augmentation")
        print(f"  GET  /api/feedback/status     — Full system status")
        print(f"  POST /api/golden              — Add golden answer")
        print(f"  GET  /api/golden              — List golden answers")
        print(f"  GET  /api/memory/stats        — RAG memory stats")
        print(f"  --- Outreach (Search → Analyze → Email) ---")
        print(f"  GET  /api/leads/search?q=...  — Szukaj klientów")
        print(f"  POST /api/outreach/analyze    — Analiza potrzeb klienta")
        print(f"  POST /api/outreach/generate-email — Generuj email (Ollama)")
        httpd.serve_forever()
