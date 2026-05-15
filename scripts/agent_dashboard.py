"""
Panel monitorowania agentów AI — Streamlit
Źródła danych: Prometheus (9090) | Loki (3100) | PostgreSQL (5432) | MCP health

Uruchomienie:
    streamlit run agent_dashboard.py

Zmienne środowiskowe (opcjonalne — domyślnie localhost):
    PROMETHEUS_URL=http://localhost:9090
    LOKI_URL=http://localhost:3100
    PG_DSN=postgresql://adrion:adrion_pass@localhost:5432/genesis_record
"""

import os
import random
import time
import logging
from datetime import datetime, timedelta

import requests
import streamlit as st

log = logging.getLogger("adrion.dashboard")

# ── Konfiguracja strony ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Agent Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Stałe infrastruktury ─────────────────────────────────────────────────────
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
LOKI_URL       = os.getenv("LOKI_URL",       "http://localhost:3100")
PG_DSN         = os.getenv("PG_DSN",         "postgresql://adrion:adrion_pass@localhost:5432/genesis_record")
_HTTP_TIMEOUT  = 3  # sekund

MCP_REGISTRY: dict[str, dict] = {
    "Vortex-MCP":  {"port": 9001, "model": "GPT-4o",      "health_path": "/health"},
    "Guardian-MCP":{"port": 9002, "model": "Claude-3.7",  "health_path": "/health"},
    "Oracle-MCP":  {"port": 9003, "model": "Mistral-L",   "health_path": "/health"},
    "Genesis-MCP": {"port": 9004, "model": "GPT-4o-mini", "health_path": "/health"},
    "Healer-MCP":  {"port": 9005, "model": "Llama-3.3",   "health_path": "/health"},
}

STATUS_COLORS = {"running": "🟢", "idle": "🟡", "error": "🔴", "unknown": "⚪"}

# ── Pomocnicze: import opcjonalny psycopg2 ────────────────────────────────────
try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


# ════════════════════════════════════════════════════════════════════════════
# Źródła danych — każda funkcja zwraca dane live lub demo przy błędzie
# ════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=15)
def prometheus_query(promql: str) -> list[dict] | None:
    """Wysyła instant query do Prometheus. Zwraca listę wyników lub None."""
    try:
        resp = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": promql},
            timeout=_HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "success":
            return data["data"]["result"]
    except Exception as exc:
        log.debug("Prometheus error: %s", exc)
    return None


@st.cache_data(ttl=15)
def prometheus_range(promql: str, minutes: int = 20) -> list[float]:
    """Zwraca szereg czasowy jako listę wartości float (ostatnie N minut)."""
    end   = datetime.utcnow()
    start = end - timedelta(minutes=minutes)
    try:
        resp = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query_range",
            params={
                "query": promql,
                "start": start.isoformat() + "Z",
                "end":   end.isoformat() + "Z",
                "step":  "60s",
            },
            timeout=_HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        result = resp.json()["data"]["result"]
        if result:
            return [float(v[1]) for v in result[0]["values"]]
    except Exception as exc:
        log.debug("Prometheus range error: %s", exc)
    # fallback
    base = 1000
    return [int(base + random.gauss(0, 200) * i / minutes) for i in range(minutes)]


@st.cache_data(ttl=10)
def loki_logs(agent_name: str, limit: int = 8) -> list[dict]:
    """Pobiera ostatnie logi z Loki dla danego agenta. Fallback: dane demo."""
    app_label = agent_name.lower().replace("-", "_").replace(" ", "_")
    try:
        end   = datetime.utcnow()
        start = end - timedelta(minutes=10)
        resp = requests.get(
            f"{LOKI_URL}/loki/api/v1/query_range",
            params={
                "query": f'{{app=~".*{app_label}.*"}}',
                "start": str(int(start.timestamp() * 1e9)),
                "end":   str(int(end.timestamp()   * 1e9)),
                "limit": limit,
                "direction": "backward",
            },
            timeout=_HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        streams = resp.json().get("data", {}).get("result", [])
        entries: list[dict] = []
        for stream in streams:
            for ts_ns, line in stream.get("values", []):
                ts = datetime.fromtimestamp(int(ts_ns) / 1e9)
                level = "ERROR" if "error" in line.lower() else (
                        "WARN"  if "warn"  in line.lower() else "INFO")
                entries.append({
                    "time":  ts.strftime("%H:%M:%S"),
                    "level": level,
                    "msg":   line[:120],
                })
        if entries:
            return entries[:limit]
    except Exception as exc:
        log.debug("Loki error: %s", exc)
    return _demo_logs(agent_name, limit)


@st.cache_data(ttl=20)
def pg_agent_stats() -> list[dict]:
    """Pobiera statystyki agentów z PostgreSQL. Fallback: dane demo."""
    if not HAS_PSYCOPG2:
        return _demo_agents()
    try:
        conn = psycopg2.connect(PG_DSN, connect_timeout=3)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Próbujemy ogólnej tabeli zdarzeń agentów
            cur.execute("""
                SELECT
                    agent_name,
                    COUNT(*) FILTER (WHERE status = 'completed') AS tasks,
                    COUNT(*) FILTER (WHERE status = 'error')     AS errors
                FROM agent_events
                GROUP BY agent_name
                ORDER BY agent_name
            """)
            rows = cur.fetchall()
        conn.close()
        if rows:
            result = []
            for row in rows:
                name = row["agent_name"]
                meta = MCP_REGISTRY.get(name, {})
                result.append({
                    "name":   name,
                    "status": _mcp_status(name),
                    "model":  meta.get("model", "unknown"),
                    "tasks":  int(row["tasks"]  or 0),
                    "errors": int(row["errors"] or 0),
                })
            return result
    except Exception as exc:
        log.debug("PostgreSQL error: %s", exc)
    return _demo_agents()


def _mcp_status(name: str) -> str:
    """Sprawdza health endpoint MCP serwera. Zwraca status jako string."""
    info = MCP_REGISTRY.get(name)
    if not info:
        return "unknown"
    try:
        resp = requests.get(
            f"http://localhost:{info['port']}{info['health_path']}",
            timeout=2,
        )
        if resp.status_code == 200:
            body = resp.json() if resp.headers.get("content-type", "").startswith("application") else {}
            return body.get("status", "running")
        return "error"
    except Exception:
        return "unknown"


# ── Dane demo (fallback) ──────────────────────────────────────────────────────

def _demo_agents() -> list[dict]:
    statuses = ["running", "running", "idle", "error", "running"]
    return [
        {
            "name":   name,
            "status": statuses[i % len(statuses)],
            "model":  info["model"],
            "tasks":  random.randint(40, 250),
            "errors": random.randint(0, 8),
        }
        for i, (name, info) in enumerate(MCP_REGISTRY.items())
    ]


def _demo_logs(agent_name: str, count: int = 8) -> list[dict]:
    levels = ["INFO", "INFO", "INFO", "WARN", "ERROR"]
    msgs = [
        "Task completed successfully",
        "Waiting for tool response",
        "Retrying API call (attempt 2/3)",
        "Memory context pruned",
        "Received new task from orchestrator",
        "Tool call: web_search",
        "Latency spike detected (2.4 s)",
        "Stream closed unexpectedly",
    ]
    now = datetime.now()
    return [
        {
            "time":  (now - timedelta(seconds=random.randint(0, 300))).strftime("%H:%M:%S"),
            "level": random.choice(levels),
            "msg":   random.choice(msgs),
        }
        for _ in range(count)
    ]

# ════════════════════════════════════════════════════════════════════════════
# Ładowanie danych (cache 15 s)
# ════════════════════════════════════════════════════════════════════════════

AGENTS = pg_agent_stats()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 Agent Control")
    st.markdown("---")

    # Źródło danych
    _prom_ok = prometheus_query("up") is not None
    _loki_ok = False
    try:
        requests.get(f"{LOKI_URL}/ready", timeout=2)
        _loki_ok = True
    except Exception:
        pass

    st.markdown("**Źródła danych:**")
    st.markdown(f"{'🟢' if _prom_ok else '🔴'} Prometheus `{PROMETHEUS_URL}`")
    st.markdown(f"{'🟢' if _loki_ok else '🔴'} Loki `{LOKI_URL}`")
    st.markdown(f"{'🟢' if HAS_PSYCOPG2 else '🟡'} PostgreSQL {'(aktywny)' if HAS_PSYCOPG2 else '(brak psycopg2)'}")
    st.markdown("---")

    selected_agent = st.selectbox(
        "Wybierz agenta",
        options=[a["name"] for a in AGENTS],
    )
    agent = next(a for a in AGENTS if a["name"] == selected_agent)

    st.markdown(f"**Model:** `{agent['model']}`")
    st.markdown(f"**Status:** {STATUS_COLORS.get(agent['status'], '⚪')} `{agent['status'].upper()}`")
    st.markdown("---")

    auto_refresh = st.toggle("Auto-odświeżanie (15 s)", value=False)
    if auto_refresh:
        time.sleep(15)
        st.cache_data.clear()
        st.rerun()

    if st.button("🔄 Wymuś odświeżenie danych", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Nagłówek ─────────────────────────────────────────────────────────────────
st.title("🧠 AI Agent Dashboard — ADRION 369")
st.caption(f"Ostatnia aktualizacja: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · "
           f"{'Prometheus ✓' if _prom_ok else 'Prometheus ✗'} · "
           f"{'Loki ✓' if _loki_ok else 'Loki ✗'} · "
           f"{'PostgreSQL ✓' if HAS_PSYCOPG2 else 'fallback demo'}")

# ── KPI — górny rząd ─────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

total_tasks  = sum(a["tasks"]  for a in AGENTS)
total_errors = sum(a["errors"] for a in AGENTS)
running_cnt  = sum(1 for a in AGENTS if a["status"] == "running")
error_rate   = round(total_errors / max(total_tasks, 1) * 100, 2)

# Prometheus: żywa liczba zapytań z ostatniej minuty (jeśli dostępne)
prom_rps_raw = prometheus_query('sum(rate(http_requests_total[1m]))')
live_rps = round(float(prom_rps_raw[0]["value"][1]), 2) if prom_rps_raw else None

col1.metric("Łączne zadania",  total_tasks)
col2.metric("Aktywne agenty",  f"{running_cnt}/{len(AGENTS)}")
col3.metric("Error rate",      f"{error_rate} %", delta_color="inverse")
col4.metric(
    "RPS (live)" if live_rps is not None else "Błędy łącznie",
    f"{live_rps} req/s" if live_rps is not None else total_errors,
    delta_color="inverse" if live_rps is None else "normal",
)

st.markdown("---")

# ── Wybrany agent — szczegóły ─────────────────────────────────────────────────
st.subheader(f"📌 Szczegóły: {selected_agent}")

c1, c2 = st.columns([2, 1])

with c1:
    # Prometheus: tokeny agenta; fallback = demo
    agent_label = selected_agent.lower().replace("-mcp", "").replace("-", "_")
    token_series = prometheus_range(
        f'sum(increase(llm_tokens_total{{agent="{agent_label}"}}[1m]))',
        minutes=20,
    )
    st.markdown("#### 📈 Zużycie tokenów (ostatnie 20 minut)")
    st.line_chart({"Tokeny": token_series}, height=220)

with c2:
    st.markdown("#### 📋 Statystyki")
    st.metric("Wykonane zadania", agent["tasks"])
    st.metric("Błędy",           agent["errors"], delta_color="inverse")
    st.metric("Model",           agent["model"])
    st.markdown(f"**Status:** {STATUS_COLORS.get(agent['status'], '⚪')} `{agent['status'].upper()}`")

# ── Logi agenta z Loki ────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📜 Logi agenta")

logs = loki_logs(selected_agent)
logs.sort(key=lambda x: x["time"], reverse=True)

level_filter = st.multiselect(
    "Filtruj poziom logów",
    options=["INFO", "WARN", "ERROR"],
    default=["INFO", "WARN", "ERROR"],
)

for entry in logs:
    if entry["level"] in level_filter:
        icon  = {"INFO": "ℹ️", "WARN": "⚠️", "ERROR": "❌"}.get(entry["level"], "")
        color = {"INFO": "#dbeafe", "WARN": "#fef9c3", "ERROR": "#fee2e2"}.get(entry["level"], "#fff")
        st.markdown(
            f"<div style='background:{color};padding:6px 12px;border-radius:6px;margin:3px 0'>"
            f"<code>{entry['time']}</code> {icon} <b>{entry['level']}</b> — {entry['msg']}"
            f"</div>",
            unsafe_allow_html=True,
        )

# ── Przegląd wszystkich agentów ───────────────────────────────────────────────
st.markdown("---")
st.subheader("🌐 Wszystkie agenty — przegląd")

cols = st.columns(len(AGENTS))
for col, agent_info in zip(cols, AGENTS):
    with col:
        icon = STATUS_COLORS.get(agent_info["status"], "⚪")
        st.markdown(
            f"<div style='border:1px solid #e2e8f0;border-radius:10px;padding:14px;text-align:center'>"
            f"<b>{agent_info['name']}</b><br>{icon} {agent_info['status']}<br>"
            f"<small>{agent_info['model']}</small><br>"
            f"✅ {agent_info['tasks']} zadań &nbsp; ❌ {agent_info['errors']} błędów"
            f"</div>",
            unsafe_allow_html=True,
        )

# ── Stopka ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("ADRION 369 · AI Agent Dashboard v2.0 · Streamlit + Prometheus + Loki + PostgreSQL · 2026")
