"""
ADRION 369 — Leads Database Layer
Wydzielone z webhook_server.py — operacje CRUD na leadach (Postgres + JSON fallback).
"""

import json
import os
from datetime import datetime

try:
    import psycopg2
    import psycopg2.extras
    HAS_PG = True
except ImportError:
    HAS_PG = False

DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", 5432)),
    "dbname": os.getenv("PG_DB", "genesis_record"),
    "user": os.getenv("PG_USER", "adrion"),
    "password": os.getenv("PG_PASS", "adrion_pass"),
    "connect_timeout": 3,
}
LEADS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.json")


def get_db():
    if not HAS_PG:
        return None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return None


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


def search_leads(query: str):
    """Search leads by business_name, city, or email."""
    conn = get_db()
    if not conn:
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
