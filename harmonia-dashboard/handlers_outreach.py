"""
ADRION 369 — Handlers: Outreach (Search → Analyze → Email)
Endpointy: /api/outreach/analyze, /api/outreach/generate-email
"""

import os
import json
import hashlib
from typing import Optional

from leads_db import get_db, LEADS_FILE

try:
    import psycopg2.extras
except ImportError:
    pass

try:
    from pipeline import genesis_log
    HAS_PIPELINE = True
except ImportError:
    HAS_PIPELINE = False


def register(router):
    """Rejestruj trasy outreach w routerze."""
    router.post("/api/outreach/analyze", handle_analyze)
    router.post("/api/outreach/generate-email", handle_generate_email)


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
        if os.path.exists(LEADS_FILE):
            with open(LEADS_FILE, "r", encoding="utf-8") as f:
                leads = json.load(f)
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

    issues = []
    recommendations = []

    wv = lead["score_wv"]
    wr = lead["score_wr"]
    we = lead["score_we"]
    total = lead["score_total"]

    if wv < 30:
        issues.append({"icon": "🔴", "text": f"Krytycznie niska widoczność (W_V={wv})", "severity": "critical"})
        recommendations.append("Pilna weryfikacja wizytówki Google + minimum 10 zdjęć z geotagami EXIF")
    elif wv < 50:
        issues.append({"icon": "🟡", "text": f"Słaba widoczność w Google Maps (W_V={wv})", "severity": "medium"})
        recommendations.append("Dodanie zdjęć z geotagami i uzupełnienie danych NAP")

    if wr < 30:
        issues.append({"icon": "🔴", "text": f"Bardzo słaba reputacja online (W_R={wr})", "severity": "critical"})
        recommendations.append("Strategia pozyskiwania opinii Google + odpowiedzi na recenzje")
    elif wr < 50:
        issues.append({"icon": "🟡", "text": f"Reputacja wymaga wzmocnienia (W_R={wr})", "severity": "medium"})
        recommendations.append("Kampania review-generation + automatyczne follow-upy po usługach")

    if we < 30:
        issues.append({"icon": "🔴", "text": f"Minimalne zaangażowanie klientów (W_E={we})", "severity": "critical"})
        recommendations.append("Regularne posty Google Business (min. 2/tydzień) + oferty specjalne")
    elif we < 50:
        issues.append({"icon": "🟡", "text": f"Zaangażowanie poniżej mediany (W_E={we})", "severity": "medium"})
        recommendations.append("Plan publikacji treści z pytaniami do klientów + Q&A")

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


def handle_analyze(handler, data):
    lead_id = data.get("lead_id")
    if not lead_id:
        handler._json_response(400, {"error": "lead_id required"})
        return
    result = analyze_client(lead_id)
    if result:
        handler._json_response(200, result)
    else:
        handler._json_response(404, {"error": "Lead not found"})


def handle_generate_email(handler, data):
    lead_id = data.get("lead_id")
    if not lead_id:
        handler._json_response(400, {"error": "lead_id required"})
        return
    result = generate_outreach_email(lead_id)
    handler._json_response(200, result)
