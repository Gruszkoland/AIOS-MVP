"""
ADRION 369 — Control Dashboard (Live)
Streamlit + Plotly connected to real ADRION API endpoints.

Run:
    cd dashboard
    streamlit run app.py

Requires: UAP API on port 8002, optional WebSocket on 8004.
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ── Config ────────────────────────────────────────────────────────────────
API_BASE = os.getenv("ADRION_API_URL", "http://localhost:8002/mapi/v1")
API_KEY = os.getenv("UAP_API_KEY", "")
WS_URL = os.getenv("ADRION_WS_URL", "ws://localhost:8004")
REFRESH_INTERVAL = int(os.getenv("DASHBOARD_REFRESH", "10"))

st.set_page_config(
    page_title="Adrion-369 Control Dashboard",
    page_icon="🌀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load Theme CSS ────────────────────────────────────────────────────────
_css_path = Path(__file__).parent / "theme.css"
if _css_path.exists():
    st.markdown(f"<style>{_css_path.read_text()}</style>", unsafe_allow_html=True)


# ── API Helper ────────────────────────────────────────────────────────────
def api_get(endpoint: str, params: dict = None) -> dict | list | None:
    """GET from ADRION API with error handling."""
    headers = {"X-API-Key": API_KEY} if API_KEY else {}
    try:
        resp = requests.get(f"{API_BASE}{endpoint}", headers=headers,
                            params=params, timeout=3)
        if resp.status_code == 200:
            return resp.json()
        st.warning(f"API {endpoint}: HTTP {resp.status_code}")
    except requests.ConnectionError:
        return None
    except Exception as e:
        st.error(f"API error: {e}")
    return None


def api_post(endpoint: str, data: dict = None) -> dict | None:
    """POST to ADRION API."""
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"} if API_KEY else {"Content-Type": "application/json"}
    try:
        resp = requests.post(f"{API_BASE}{endpoint}", headers=headers,
                             json=data or {}, timeout=5)
        return resp.json()
    except Exception:
        return None


# ── Data Fetchers (cached) ────────────────────────────────────────────────
@st.cache_data(ttl=REFRESH_INTERVAL)
def fetch_health():
    return api_get("/health")


@st.cache_data(ttl=REFRESH_INTERVAL)
def fetch_agent_scores():
    return api_get("/agent/scores")


@st.cache_data(ttl=REFRESH_INTERVAL)
def fetch_ebdi_telemetry():
    return api_get("/ebdi/telemetry")


@st.cache_data(ttl=REFRESH_INTERVAL)
def fetch_guardian_laws():
    return api_get("/guardian/laws")


@st.cache_data(ttl=REFRESH_INTERVAL)
def fetch_task_list():
    return api_get("/task/list")


@st.cache_data(ttl=REFRESH_INTERVAL)
def fetch_genesis_logs():
    return api_get("/genesis/logs", {"limit": "50", "since": "24h"})


@st.cache_data(ttl=REFRESH_INTERVAL)
def fetch_status():
    return api_get("/status") or api_get("/../mapi/v1/status")


@st.cache_data(ttl=REFRESH_INTERVAL)
def fetch_leaderboard():
    return api_get("/agents/leaderboard")


# ── Fetch all data ────────────────────────────────────────────────────────
health = fetch_health()
scores_data = fetch_agent_scores()
ebdi_data = fetch_ebdi_telemetry()
guardian_data = fetch_guardian_laws()
tasks_data = fetch_task_list()
genesis_data = fetch_genesis_logs()
leaderboard = fetch_leaderboard()

API_ONLINE = health is not None

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<h1 style="text-align:center; color:#00D4FF; font-size:28px;">'
        'ADRION-369</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="text-align:center; color:{"#34D399" if API_ONLINE else "#FF4B4B"};">'
        f'API: {"CONNECTED" if API_ONLINE else "OFFLINE"}</p>',
        unsafe_allow_html=True,
    )

    st.markdown("### 4 Warstwy Krytyczne")
    page = st.radio(
        "Nawigacja:",
        ["Overview", "1. Osobowosc (EBDI)", "2. Orkiestracja", "3. Decyzja (Guardian)",
         "4. Real-time", "Chat"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption(f"Auto-refresh: {REFRESH_INTERVAL}s")
    if st.button("Odswiez dane"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.caption(f"API: {API_BASE}")
    st.caption(f"WS: {WS_URL}")


# ══════════════════════════════════════════════════════════════════════════
#  OVERVIEW
# ══════════════════════════════════════════════════════════════════════════
if page == "Overview":
    # ── AI Orb + Status ───────────────────────────────────────────────────
    col_orb, col_status = st.columns([2, 3])

    with col_orb:
        orb_color = "#34D399" if API_ONLINE else "#FF4B4B"
        st.markdown(f"""
        <div style="text-align:center; padding:20px;">
            <div class="ai-orb" style="width:240px;height:240px;margin:auto;border-radius:50%;
                display:flex;align-items:center;justify-content:center;font-size:64px;color:white;">
                🌀
            </div>
            <h2 style="margin:15px 0 5px; color:{orb_color};">
                Orchestrator {'LIVE' if API_ONLINE else 'OFFLINE'}
            </h2>
            <p style="color:#00D4FF;">Multi-Agent System z osobowoscia • 9 Personas</p>
        </div>
        """, unsafe_allow_html=True)

    with col_status:
        if health:
            st.metric("Status", health.get("status", "unknown").upper())
            st.metric("Uptime", f"{health.get('uptime', 0):.0f}s")
            st.metric("Ollama", health.get("ollama", "unknown"))
            st.metric("LLM Available", "Yes" if health.get("llm_available") else "No")
            st.metric("Database", health.get("db", "unknown"))
        else:
            st.warning("API niedostepne — uruchom `python uap/backend/api.py`")

    # ── 4 Layer Cards ─────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("4 Warstwy Krytyczne Systemu")
    c1, c2, c3, c4 = st.columns(4)

    # Layer 1: Personality / EBDI
    with c1:
        st.markdown('<div class="card layer-personality">', unsafe_allow_html=True)
        st.markdown("#### 1. Osobowosc")
        if scores_data:
            avg_trust = scores_data.get("average_trust_score", 0)
            agents_list = scores_data.get("agents", [])
            st.metric("Avg Trust Score", f"{avg_trust:.1%}")
            st.metric("Agents Online", f"{len(agents_list)} / 9")
            crisis = ebdi_data.get("crisis_agents", []) if ebdi_data else []
            if crisis:
                st.markdown(f'<span class="status-alert">CRISIS: {", ".join(crisis)}</span>',
                            unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-ok">No crisis</span>', unsafe_allow_html=True)
        else:
            st.caption("Brak danych")
        st.caption("EBDI state + Trust Score + 9 agentow")
        st.markdown("</div>", unsafe_allow_html=True)

    # Layer 2: Orchestration
    with c2:
        st.markdown('<div class="card layer-orchestration">', unsafe_allow_html=True)
        st.markdown("#### 2. Orkiestracja")
        if tasks_data:
            tasks_list = tasks_data if isinstance(tasks_data, list) else tasks_data.get("tasks", [])
            executing = sum(1 for t in tasks_list if isinstance(t, dict) and t.get("status") == "executing")
            total = len(tasks_list)
            st.metric("Active Tasks", executing)
            st.metric("Total Tasks", total)
        else:
            st.caption("Brak danych")
        st.caption("Chat → Intent → Routing → KROK 1-4 → Genesis")
        st.markdown("</div>", unsafe_allow_html=True)

    # Layer 3: Decision / Guardian
    with c3:
        st.markdown('<div class="card layer-decision">', unsafe_allow_html=True)
        st.markdown("#### 3. Decyzja")
        if guardian_data:
            laws = guardian_data.get("laws", [])
            compliant = guardian_data.get("compliant", 0)
            total_laws = guardian_data.get("total", 9)
            st.metric("Guardian Compliance", f"{compliant}/{total_laws}")
            violations = [l for l in laws if not l.get("active", True)]
            if violations:
                st.markdown(f'<span class="status-warn">{len(violations)} violation(s)</span>',
                            unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-ok">All laws compliant</span>',
                            unsafe_allow_html=True)
        else:
            st.caption("Brak danych")
        st.caption("Trinity + Guardian + Oracle pipeline")
        st.markdown("</div>", unsafe_allow_html=True)

    # Layer 4: Real-time
    with c4:
        st.markdown('<div class="card layer-realtime">', unsafe_allow_html=True)
        st.markdown("#### 4. Real-time")
        if genesis_data:
            logs = genesis_data if isinstance(genesis_data, list) else genesis_data.get("logs", [])
            st.metric("Genesis Events (24h)", len(logs))
        else:
            st.metric("Genesis Events", "N/A")
        st.caption("WebSocket + Session management")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Leaderboard ───────────────────────────────────────────────────────
    if leaderboard:
        st.markdown("---")
        st.subheader("Agent Leaderboard")
        agents = leaderboard if isinstance(leaderboard, list) else leaderboard.get("agents", [])
        if agents:
            import pandas as pd
            df = pd.DataFrame(agents)
            if "trust_score" in df.columns:
                df = df.sort_values("trust_score", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════
#  PAGE 1: OSOBOWOSC (EBDI)
# ══════════════════════════════════════════════════════════════════════════
elif page == "1. Osobowosc (EBDI)":
    st.header("Warstwa 1: Osobowosc — EBDI Telemetria")

    if ebdi_data and ebdi_data.get("telemetry"):
        telemetry = ebdi_data["telemetry"]

        # EBDI Heatmap
        agents_names = list(telemetry.keys())
        pad_dims = ["pleasure", "arousal", "dominance"]
        z_values = [[telemetry[a].get(d, 0) for a in agents_names] for d in pad_dims]

        fig_heat = go.Figure(data=go.Heatmap(
            z=z_values,
            x=agents_names,
            y=["Pleasure", "Arousal", "Dominance"],
            colorscale="RdYlGn",
            zmin=-1, zmax=1,
            text=[[f"{v:.2f}" for v in row] for row in z_values],
            texttemplate="%{text}",
            textfont={"size": 12},
        ))
        fig_heat.update_layout(
            title="EBDI PAD Vectors — All Agents (Live)",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E0D4FF",
            height=350,
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        # Crisis detection
        crisis_agents = ebdi_data.get("crisis_agents", [])
        if crisis_agents:
            st.error(f"CRISIS MODE: {', '.join(crisis_agents)} (arousal > 0.7)")
        else:
            st.success("All agents PAD vectors within normal range")

        # Per-agent detail
        st.subheader("Per-Agent Detail")
        cols = st.columns(3)
        for i, (agent, pad) in enumerate(telemetry.items()):
            with cols[i % 3]:
                st.markdown(f'<div class="card">', unsafe_allow_html=True)
                st.markdown(f"**{agent}**")
                for dim in pad_dims:
                    val = pad.get(dim, 0)
                    color = "#FF4B4B" if dim == "arousal" and val > 0.7 else "#00D4FF"
                    st.markdown(f'{dim.capitalize()}: <span style="color:{color};">{val:.3f}</span>',
                                unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("EBDI telemetry niedostepna — sprawdz API")

    # Trust Scores
    if scores_data and scores_data.get("agents"):
        st.markdown("---")
        st.subheader("Trust Scores (TSPA)")
        agents_scores = scores_data["agents"]
        names = [a["agent"] for a in agents_scores]
        values = [a["trust_score"] for a in agents_scores]
        colors = ["#FF4B4B" if v < 0.6 else "#FCD34D" if v < 0.8 else "#34D399" for v in values]

        fig_bar = go.Figure(go.Bar(
            x=names, y=values,
            marker_color=colors,
            text=[f"{v:.2f}" for v in values],
            textposition="outside",
        ))
        fig_bar.update_layout(
            title="Trust Score per Agent (threshold: 0.6)",
            yaxis_range=[0, 1.1],
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E0D4FF",
            height=400,
        )
        fig_bar.add_hline(y=0.6, line_dash="dash", line_color="#FF4B4B",
                          annotation_text="Block threshold")
        st.plotly_chart(fig_bar, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════
#  PAGE 2: ORKIESTRACJA
# ══════════════════════════════════════════════════════════════════════════
elif page == "2. Orkiestracja":
    st.header("Warstwa 2: Orkiestracja — Task Pipeline")

    if tasks_data:
        tasks_list = tasks_data if isinstance(tasks_data, list) else tasks_data.get("tasks", [])
        if tasks_list:
            import pandas as pd
            df = pd.DataFrame(tasks_list)
            # Status distribution
            if "status" in df.columns:
                status_counts = df["status"].value_counts()
                fig_pie = px.pie(
                    names=status_counts.index,
                    values=status_counts.values,
                    hole=0.4,
                    color_discrete_sequence=["#00D4FF", "#34D399", "#FF4B4B", "#FCD34D", "#A020F0"],
                )
                fig_pie.update_layout(
                    title="Task Status Distribution",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#E0D4FF",
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            # Agent distribution
            if "assigned_agent" in df.columns:
                agent_counts = df["assigned_agent"].value_counts()
                fig_agent = px.bar(
                    x=agent_counts.index, y=agent_counts.values,
                    color_discrete_sequence=["#6366F1"],
                )
                fig_agent.update_layout(
                    title="Tasks per Agent",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#E0D4FF",
                )
                st.plotly_chart(fig_agent, use_container_width=True)

            # Task table
            st.subheader("Task List")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Brak taskow w systemie")
    else:
        st.warning("Task API niedostepna")

    # Pipeline diagram
    st.markdown("---")
    st.subheader("Pipeline Flow")
    st.markdown("""
    ```
    User Message
       │
       ▼
    [analyze_intent] ──LLM──→ QUERY / DELEGATE / HEAL / CONTINUE / CLARIFY
       │                      ──keyword fallback──→ scoring (priority: QUERY>DELEGATE>HEAL)
       ▼
    [_generate_response] ──LLM + RAG context──→ Natural language response
       │                  ──template fallback──→ Canned response
       ▼
    [_execute_*] ──Delegate──→ Master Orchestrator KROK 1-4
                 ──Heal──────→ Healer agent
                 ──Continue──→ Resume from session
       │
       ▼
    [Genesis Record] ── Audit trail logged
    ```
    """)


# ══════════════════════════════════════════════════════════════════════════
#  PAGE 3: DECYZJA (GUARDIAN)
# ══════════════════════════════════════════════════════════════════════════
elif page == "3. Decyzja (Guardian)":
    st.header("Warstwa 3: Decyzja — Guardian Laws + Trinity")

    # Guardian Radar
    if guardian_data:
        laws = guardian_data.get("laws", [])
        if laws:
            categories = [f"G{i+1} {l.get('name', '')}" for i, l in enumerate(laws)]
            values = [1.0 if l.get("active", True) else 0.3 for l in laws]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=values, theta=categories, fill="toself",
                name="Compliance", line_color="#00D4FF",
                fillcolor="rgba(0, 212, 255, 0.2)",
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=[0.87] * len(categories), theta=categories,
                fill=None, name="Threshold", line_dash="dash",
                line_color="#FF4B4B",
            ))
            fig_radar.update_layout(
                title="Guardian Compliance Radar (9 Laws — Live)",
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 1.1]),
                    bgcolor="rgba(0,0,0,0)",
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#E0D4FF",
                height=500,
            )
            st.plotly_chart(fig_radar, use_container_width=True)

            # Law details table
            st.subheader("Guardian Laws Detail")
            for law in laws:
                status = "✅" if law.get("active", True) else "❌"
                st.markdown(f"**{law.get('id', '')} — {law.get('name', '')}** {status}: {law.get('description', '')}")
    else:
        st.warning("Guardian Laws API niedostepna")

    # Healer — Guardian enforcement results
    st.markdown("---")
    st.subheader("Healer — Guardian Enforcement (G1-G9 Health Checks)")
    st.markdown("""
    | Check | Law | Opis |
    |---|---|---|
    | Core tables exist | G1 Unity | `tasks`, `autopilot_runs` tables in SQLite |
    | FK integrity | G2 Harmony | `PRAGMA foreign_key_check` |
    | Autopilot rhythm | G3 Rhythm | Last run < 2h ago |
    | Task traceability | G4 Causality | All tasks have `agent_id` + `created_at` |
    | Audit log exists | G5 Transparency | `genesis_audit.jsonl` non-empty |
    | No plaintext secrets | G7 Privacy | Regex scan of `.py` files |
    | DB size limit | G9 Sustainability | Database < 500MB |
    """)


# ══════════════════════════════════════════════════════════════════════════
#  PAGE 4: REAL-TIME
# ══════════════════════════════════════════════════════════════════════════
elif page == "4. Real-time":
    st.header("Warstwa 4: Real-time — Genesis Logs + Telemetria")

    # Genesis audit trail
    if genesis_data:
        logs = genesis_data if isinstance(genesis_data, list) else genesis_data.get("logs", [])
        if logs:
            st.subheader(f"Genesis Log (ostatnie {len(logs)} events)")
            import pandas as pd
            df_logs = pd.DataFrame(logs)
            st.dataframe(df_logs, use_container_width=True, hide_index=True, height=400)

            # Event type distribution
            if "event_type" in df_logs.columns:
                event_counts = df_logs["event_type"].value_counts()
                fig_events = px.bar(
                    x=event_counts.index, y=event_counts.values,
                    color_discrete_sequence=["#A020F0"],
                )
                fig_events.update_layout(
                    title="Event Type Distribution (24h)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#E0D4FF",
                )
                st.plotly_chart(fig_events, use_container_width=True)
        else:
            st.info("Brak eventow w ostatnich 24h")
    else:
        st.warning("Genesis API niedostepna")

    # WebSocket status
    st.markdown("---")
    st.subheader("WebSocket Telemetry")
    st.markdown(f"""
    <div class="card">
        <h4>WebSocket Server</h4>
        <p>URL: <code>{WS_URL}</code></p>
        <p>Protocol: EBDI PAD vectors broadcast every 200ms</p>
        <p>Events: <code>telemetry</code> (periodic) + <code>ebdi_event</code> (on change)</p>
    </div>
    """, unsafe_allow_html=True)

    st.info("Live WebSocket telemetry wymaga `streamlit-ws-connector` lub dedykowanego komponentu JS. "
            "Aktualnie dane odswiezane przez REST API polling.")


# ══════════════════════════════════════════════════════════════════════════
#  CHAT
# ══════════════════════════════════════════════════════════════════════════
elif page == "Chat":
    st.header("Chat z Orchestratorem")

    # Chat history in session state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant",
             "content": "Witaj w Adrion-369. Jestem Orchestratorem. "
                        "Opisz zadanie — przeprowadze je przez 4 warstwy systemu."}
        ]

    # Display history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User input
    if prompt := st.chat_input("Wpisz zapytanie..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Send to real ChatOrchestrator via task/delegate endpoint
        with st.chat_message("assistant"):
            with st.spinner("Przetwarzam przez 4 warstwy..."):
                result = api_post("/task/delegate", {
                    "task_description": prompt,
                    "agent_hint": None,
                    "dry_run": False,
                })

            if result and not result.get("error"):
                task_id = result.get("task_id", "unknown")
                agent = result.get("assigned_agent", "unknown")
                status = result.get("status", "unknown")

                response = (
                    f"**Zadanie przyjete i zdelegowane:**\n\n"
                    f"- **Task ID:** `{task_id}`\n"
                    f"- **Agent:** {agent}\n"
                    f"- **Status:** {status}\n"
                    f"- **Pipeline:** Intent → Routing → KROK → Genesis\n\n"
                    f"Mozesz sprawdzic status w zakladce *2. Orkiestracja*."
                )
            elif result and result.get("error"):
                response = f"Blad API: {result['error']}"
            else:
                response = ("API niedostepne. Upewnij sie ze serwer UAP dziala na porcie 8002.\n\n"
                            f"```\ncd '162 demencje w schemacie 369'\npython uap/backend/api.py\n```")

            st.markdown(response)
            st.session_state.chat_messages.append({"role": "assistant", "content": response})


# ── Footer ────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    f"ADRION 369 Control Dashboard • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • "
    f"API: {'Connected' if API_ONLINE else 'Offline'}"
)
